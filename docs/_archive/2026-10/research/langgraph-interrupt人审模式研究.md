# LangGraph 1.0.x checkpoint/interrupt 人审模式研究

> **研究工单**: FreshLatch 立项切片 — "LangGraph 只用于 checkpoint / interrupt 等人续命,图不是 Agent"
> **研究日期**: 2026-09-19
> **研究范围**: LangGraph 1.0.x (当前最新稳定版) 的 human-in-the-loop 中断/恢复机制
> **本地参考代码盘点结论**: 参考代码库中所有 LangGraph 用法均为 `compile()` 无 checkpointer,**无任何 `interrupt()` / `Command(resume)` / checkpointer 现成代码**。自研门闩备选参照: `project 多agent/src/missions/runner.py` 的 `blocked_for_human → approve_promotion` 模式。

---

## 1. 结论速览

**推荐模式**: LangGraph 1.0.x 的 human-in-the-loop 由三个原语组成 —— `interrupt(value)` 在节点内暂停、`Command(resume=X)` 从外部恢复、`SqliteSaver` 跨进程持久化状态。在 FreshLatch 场景下,**图仅承担「跑到一半 → interrupt 落盘 → 进程可退出 → 人审后 Command(resume) 恢复」的职责**,Agent 循环(Lead/Critic)仍由裸 chat.completions + tools 自行实现。

**最小可运行示例**(单文件,依赖 `langgraph` + `langgraph-checkpoint-sqlite`):

```python
# pip install langgraph langgraph-checkpoint-sqlite
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.sqlite import SqliteSaver

class State(TypedDict):
    claim_id: str
    decision: str          # "" → 待审 / "renew" / "discard"

def human_review(state: State) -> dict:
    """中断点: 暂停并展示待审信息, 等人的决定"""
    answer = interrupt({
        "claim_id": state["claim_id"],
        "question": "作废(discard) 还是续命(renew)?"
    })
    return {"decision": answer}

def execute(state: State) -> dict:
    if state["decision"] == "renew":
        return {"claim_id": f"[续命] {state['claim_id']}"}
    return {"claim_id": f"[作废] {state['claim_id']}"}

builder = StateGraph(State)
builder.add_node("human_review", human_review)
builder.add_node("execute", execute)
builder.add_edge(START, "human_review")
builder.add_edge("human_review", "execute")
builder.add_edge("execute", END)

# 持久化到 SQLite 文件
with SqliteSaver.from_conn_string("freshlatch_checkpoints.db") as saver:
    graph = builder.compile(checkpointer=saver)
    config = {"configurable": {"thread_id": "claim-001"}}

    # 第一次调用: 跑到 interrupt() 处暂停, 状态已落盘
    result = graph.invoke({"claim_id": "c1", "decision": ""}, config)
    print("暂停:", result)

    # 用户几小时后回来点按钮 → 第二次调用恢复
    result = graph.invoke(Command(resume="renew"), config)
    print("完成:", result)
```

**来源**: [Interrupts 官方文档](https://docs.langchain.com/oss/python/langgraph/interrupts) · [Persistence 官方文档](https://docs.langchain.com/oss/python/langgraph/persistence) · [interrupt() API](https://reference.langchain.com/python/langgraph/types/interrupt) · [Command API](https://reference.langchain.com/python/langgraph/types/Command)

---

## 2. 各研究问题的答案

### 2.1 推荐 API: interrupt() / Command(resume) / checkpointer 各自怎么用、怎么配合

#### 核心三原语

| 原语 | Import | 作用 | 配合方式 |
|------|--------|------|----------|
| `interrupt(value)` | `from langgraph.types import interrupt` | 节点内调用,暂停图执行,`value` 暴露给调用方 | 必须有 checkpointer; 恢复时此调用返回 `resume` 值 |
| `Command(resume=X)` | `from langgraph.types import Command` | 作为 `graph.invoke()` 的输入,恢复中断的图 | `X` 成为 `interrupt()` 的返回值 |
| Checkpointer | `from langgraph.checkpoint.sqlite import SqliteSaver` 等 | 保存/加载图的完整状态快照 | 编译时传入 `compile(checkpointer=...)` |

#### 配合流程

```
graph.invoke(initial_input, config)
    ↓ 执行节点...
    ↓ 遇到 interrupt(value)
    ↓ checkpointer 自动保存完整 state
    ↓ invoke 返回(携带 __interrupt__ 信息)
    ↓ ... 时间流逝, 进程可以退出 ...
graph.invoke(Command(resume=human_decision), config)  ← 同一 thread_id
    ↓ checkpointer 加载上次保存的 state
    ↓ 包含 interrupt() 的节点从头重新执行
    ↓ interrupt() 之前的代码会再跑一次(幂等性要求!)
    ↓ interrupt() 调用返回 human_decision
    ↓ 节点继续执行后续逻辑
    ↓ 图继续往下跑直到结束或下一个 interrupt
```

**⚠️ 关键行为: 节点从头重执行**

当 `Command(resume=X)` 恢复时,包含 `interrupt()` 的节点会**从头重新执行**,`interrupt()` 之前的代码会再跑一次。LangGraph 内部通过"重放匹配"机制——第 N 次 `interrupt()` 调用对应第 N 个 `resume` 值——来保证多次 `interrupt()` 场景的正确性。

**设计含义**: `interrupt()` 之前的代码必须是**幂等的**(idempotent),不能有不可重复的副作用(如发邮件、扣款)。如果有副作用,应放到 `interrupt()` 之后,或用 state 中的 flag 来跳过。

来源: [interrupt() API Reference](https://reference.langchain.com/python/langgraph/types/interrupt) · [HITL Interrupt Patterns (Turion.ai)](https://turion.ai/blog/langgraph-human-in-the-loop-interrupt-tutorial/)

#### Checkpointer 选择

| Checkpointer | Import 路径 | pip 包名 | 持久化 | 适用场景 |
|---|---|---|---|---|
| `InMemorySaver` | `langgraph.checkpoint.memory` | `langgraph`(内置) | ❌ 内存 | 开发/测试 |
| `SqliteSaver` | `langgraph.checkpoint.sqlite` | `langgraph-checkpoint-sqlite` | ✅ SQLite 文件 | **FreshLatch 推荐**: Windows 本地单机 |
| `AsyncSqliteSaver` | `langgraph.checkpoint.sqlite.aio` | `langgraph-checkpoint-sqlite` | ✅ SQLite 文件 | 异步 FastAPI 场景 |
| `PostgresSaver` | `langgraph.checkpoint.postgres` | `langgraph-checkpoint-postgres` | ✅ PostgreSQL | 多进程/分布式 |

> **注**: `MemorySaver` 是 `InMemorySaver` 的向后兼容别名,功能完全相同。新代码推荐用 `InMemorySaver`。

来源: [Persistence 官方文档](https://docs.langchain.com/oss/python/langgraph/persistence) · [PyPI: langgraph-checkpoint-sqlite](https://pypi.org/project/langgraph-checkpoint-sqlite/)

---

### 2.2 中断状态如何跨进程持久化

#### 场景映射: FreshLatch (Windows 本地 + Python 3.11 + FastAPI/Streamlit)

**推荐方案**: `SqliteSaver` + 文件落盘

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 方式 1: context manager (推荐, 自动管理连接)
with SqliteSaver.from_conn_string("freshlatch_checkpoints.db") as saver:
    graph = builder.compile(checkpointer=saver)
    # ... invoke ...

# 方式 2: 手动管理 (FastAPI lifespan 场景)
saver = SqliteSaver.from_conn_string("freshlatch_checkpoints.db")
# FastAPI startup 时:
saver.setup()  # 初始化数据库表
# 使用期间:
graph = builder.compile(checkpointer=saver)
# FastAPI shutdown 时:
# (SqliteSaver 无显式 close, 连接随 GC 回收)
```

#### thread_id 设计: 对应「一次复验运行」

`thread_id` 是 LangGraph 持久化的核心标识——同一 `thread_id` 的所有 `invoke()` 共享同一个状态历史。

**FreshLatch 推荐**: `thread_id = f"reverify-{claim_id}-{run_timestamp}"`

```python
import uuid
from datetime import datetime

def make_thread_id(claim_id: str) -> str:
    """一次复验运行 = 一个唯一的 thread_id"""
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"reverify-{claim_id}-{ts}"

# 示例: "reverify-c1-20260919-143052"
```

| 设计选择 | 说明 |
|----------|------|
| 一次复验 = 一个 thread_id | 每次发起新的复验,生成新 thread_id |
| 同一复验的多次交互 = 同一 thread_id | interrupt → 人审 → resume 都用同一 thread_id |
| 建议存到业务数据库 | thread_id 和 claim_id 的映射关系存业务表,方便查询 |

#### 跨进程恢复示例(FastAPI)

```python
# === FastAPI app.py ===
from fastapi import FastAPI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

app = FastAPI()
CHECKPOINT_DB = "freshlatch_checkpoints.db"

# 启动时初始化 checkpointer
saver = SqliteSaver.from_conn_string(CHECKPOINT_DB)
saver.setup()
graph = build_review_graph()  # 你的图构建函数
graph = builder.compile(checkpointer=saver)

@app.post("/reverify/start")
def start_reverify(claim_id: str):
    thread_id = make_thread_id(claim_id)
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(
        {"claim_id": claim_id, "decision": ""},
        config
    )
    # result 包含 __interrupt__ 信息, 告诉前端需要什么
    return {"thread_id": thread_id, "status": "paused", "interrupt": result}

@app.post("/reverify/decide")
def decide(thread_id: str, action: str):
    """用户点了「作废」或「续命」按钮"""
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(
        Command(resume=action),  # "renew" 或 "discard"
        config
    )
    return {"thread_id": thread_id, "status": "completed", "result": result}
```

**关键点**: 即使 FastAPI 进程重启(用户关掉页面几小时后再回来),只要:
1. SQLite 文件还在
2. thread_id 相同
3. 图代码和 State 定义兼容

就能正确恢复。

来源: [Persistence 官方文档](https://docs.langchain.com/oss/python/langgraph/persistence) · [Reddit: thread_id 工作原理](https://www.reddit.com/r/LangChain/comments/1iof5rk/how_does_thread_id_and_state_persistence_work/)

---

### 2.3 图外事件驱动恢复: UI 按钮 → FastAPI → 被中断的图

#### 完整流程

```
┌──────────────────────────────────────────────────────────────┐
│  UI (Streamlit/FastAPI 前端)                                  │
│  [作废] [续命] [确认隔离] 按钮                                 │
└───────────────┬──────────────────────────────────────────────┘
                │ POST /reverify/decide
                │ body: { thread_id: "...", action: "renew",
                │         claim_id: "c1", t1_evidence_id: "..." }
                ▼
┌──────────────────────────────────────────────────────────────┐
│  FastAPI 路由                                                 │
│  1. 从请求中取 thread_id + action                             │
│  2. 构造 Command(resume=action)                               │
│  3. graph.invoke(Command(resume=action), config)              │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│  LangGraph 内部                                               │
│  1. checkpointer 按 thread_id 加载上次保存的 state             │
│  2. 包含 interrupt() 的节点从头重执行                           │
│  3. interrupt() 返回 resume 值(即 action)                     │
│  4. 节点后续逻辑根据 action 分支执行                            │
│  5. 图继续往下跑                                               │
└──────────────────────────────────────────────────────────────┘
```

#### 传递复杂结构(不只是字符串)

`Command(resume=...)` 的 `resume` 参数可以是**任意 Python 对象**(字典、列表等)。因此 UI 传来的复杂决定可以直接透传:

```python
# FastAPI 端点接收复杂结构
@app.post("/reverify/decide")
def decide(request: DecisionRequest):
    # request 包含: thread_id, action, claim_id, t1_evidence_id, ...
    resume_payload = {
        "action": request.action,           # "renew" / "discard" / "isolate"
        "claim_id": request.claim_id,
        "t1_evidence_id": request.t1_evidence_id,
        "reviewer_note": request.note,
    }
    config = {"configurable": {"thread_id": request.thread_id}}
    result = graph.invoke(
        Command(resume=resume_payload),
        config
    )
    return result
```

```python
# 节点内接收
def human_review(state: State) -> dict:
    decision = interrupt({
        "claim_id": state["claim_id"],
        "question": "请审批"
    })
    # decision 就是 resume_payload 字典
    action = decision["action"]
    evidence = decision["t1_evidence_id"]
    return {
        "decision": action,
        "evidence_id": evidence,
        "reviewer_note": decision["reviewer_note"]
    }
```

#### 查询中断状态(不恢复,只看看)

```python
# 查看当前 state(不执行任何节点)
current_state = graph.get_state(config)
print(current_state.values)     # 当前 state 字典
print(current_state.next)       # 下一个要执行的节点名(元组)
# 如果 next 非空,说明图被中断了,在等 resume
```

来源: [Command API Reference](https://reference.langchain.com/python/langgraph/types/Command) · [Interrupts and Commands (dev.to)](https://dev.to/jamesbmour/interrupts-and-commands-in-langgraph-building-human-in-the-loop-workflows-4ngl)

---

### 2.4 备选方案对比: LangGraph interrupt vs 自研门闩

#### 自研门闩模式(参考 `project 多agent/src/missions/runner.py`)

自研门闩的核心实现:

```python
# runner.py 中的门闩:
# 1. 阻塞侧: 设置 blocked_for_human flag, 保存 state, 退出循环
state.phase = "blocked_for_human"
state.handoffs.append(HandoffRecord(blocked_for_human=True, block_reason="..."))
self.store.save_state(state)  # Pydantic → JSON 落盘

# 2. 恢复侧: approve_promotion 加载 state, 修改 flag, 保存
def approve_promotion(self, state, *, approved_by="human"):
    state.human_approval.approved = True
    state.phase = "promoted"
    self.store.save_state(state)

# 3. FastAPI 端点:
@app.post("/api/approve")
def approve(mission_id: str):
    state = store.load_state(mission_id)
    runner.approve_promotion(state, approved_by="human")
    return {"status": "approved"}
```

#### 取舍对照表

| 维度 | LangGraph interrupt + SqliteSaver | 自研门闩(JSON/SQLite + 进程退出 + 重启) |
|------|-----------------------------------|------------------------------------------|
| **代码量** | 少(3 个 API 调用: interrupt / Command / compile) | 多(需自写: state 序列化、flag 管理、恢复入口、重试逻辑) |
| **状态一致性** | LangGraph 内部保证(checkpoint 原子写入) | 需自己保证(写入中途崩溃 → 可能状态损坏) |
| **节点重执行** | ⚠️ interrupt() 前代码会重跑,需幂等 | ✅ 不存在重执行,恢复 = 从 flag 处继续 |
| **图复杂度** | 适合简单线性/分支图(「图不是 Agent」) | 无图概念,纯状态机 + 函数调用 |
| **调试可见性** | LangGraph Studio 可视化 checkpoint 历史 | 自己打印日志 / 读 JSON |
| **依赖** | `langgraph` + `langgraph-checkpoint-sqlite` | 零额外依赖(纯 Python + sqlite3/json) |
| **升级风险** | LangGraph 版本迭代可能改 API(0.x→1.0.x 已发生过) | 零外部 API 变化风险 |
| **多 interrupt 串联** | 原生支持(一个节点内可多次 interrupt) | 需自己设计状态机转换 |
| **回退/倒带** | 原生支持 `graph.update_state()` 回到任意 checkpoint | 需自己实现状态回滚 |
| **学习曲线** | 需理解 StateGraph / config / thread_id 等概念 | 低(就是读写 JSON + if/else) |
| **FreshLatch 适配度** | ✅ 高 — 「图不是 Agent」约束下,图只做 checkpoint 容器 | ✅ 高 — 已有参考实现,验证过 |

#### 什么情况下自研更简单可靠?

1. **中断逻辑极简**: 只有一两个固定的「等人审批」点,不存在多 interrupt 串联或回退需求
2. **对依赖零容忍**: 不想引入 `langgraph` 这个较重的依赖(及其版本迭代风险)
3. **需要精确控制恢复行为**: 不希望节点代码被重执行(如副作用难以幂等化)
4. **团队已熟悉门闩模式**: `project 多agent` 的代码就是参照,迁移成本低
5. **需要与现有业务 state 深度耦合**: 如 state 需要同时被 LangGraph 外的系统读写

#### 什么情况下 LangGraph interrupt 更好?

1. **需要 checkpoint 历史回溯**: 比如人审后想「撤销」回到之前的状态
2. **多个中断点串联**: 一个复验流程可能要经过多轮人审(初审 → 证据补充 → 复审)
3. **快速原型**: 3 行代码就能跑通,自研门闩需要写更多胶水
4. **未来可能扩展到更复杂的图**: 如果 FreshLatch 后续需要增加节点,LangGraph 的图抽象更方便

---

### 2.5 版本坑: 0.x → 1.0.x 迁移中的 API 变化

#### 变化对照表

| 变更项 | 0.x 写法 (旧,⚠️ 网上教程大量使用) | 1.0.x 写法 (当前推荐) | 兼容状态 |
|--------|----------------------------------|-----------------------|----------|
| **中断函数** | `raise NodeInterrupt("msg")` | `answer = interrupt(value)` | ❌ `NodeInterrupt` 自 v0.2 起已弃用 |
| **中断导入** | `from langgraph.errors import NodeInterrupt` | `from langgraph.types import interrupt` | ❌ 旧路径 |
| **内存 saver** | `MemorySaver()` | `InMemorySaver()` (`MemorySaver` 仍可用但为别名) | ✅ 向后兼容 |
| **静态断点** | `compile(interrupt_before=["node"])` | 仅调试用; 生产用 `interrupt()` | ⚠️ 仍可用,定位变化 |
| **checkpoint 包** | 内置于 `langgraph` 主包 | 拆分为独立包: `langgraph-checkpoint-sqlite` 等 | ⚠️ import 路径不变,但需显式 pip install |
| **预构建 agent** | `from langgraph.prebuilt import create_react_agent` | 已弃用,迁移到 `langchain.agents` | ❌ 已弃用 |
| **Python 版本** | 3.9+ | **3.10+** (1.0 放弃 3.9) | ❌ 3.9 不再支持 |
| **中断返回值** | `GraphInterrupt` 异常对象 | `result` 中 `__interrupt__` 字段 | ✅ 行为变化但更清晰 |
| **恢复方式** | `graph.invoke(None, config)` (传 None 恢复) | `graph.invoke(Command(resume=X), config)` | ❌ 必须用 Command |

#### 关键变化详解

**1. `NodeInterrupt` → `interrupt()` (最重要的变化)**

```python
# ❌ 0.x 旧写法 (网上大量教程还在用)
from langgraph.errors import NodeInterrupt

def approval_node(state):
    if not state.get("approved"):
        raise NodeInterrupt("需要人类审批")  # 抛异常
    return state

# ✅ 1.0.x 新写法
from langgraph.types import interrupt

def approval_node(state):
    answer = interrupt("需要人类审批")  # 函数调用, 返回值 = resume 值
    state["human_answer"] = answer
    return state
```

核心区别:
- `NodeInterrupt` 是异常,无法返回值,恢复时只能重跑整个节点
- `interrupt()` 是函数,返回值就是 `Command(resume=X)` 中的 `X`,支持双向数据传递

**2. 恢复方式变化**

```python
# ❌ 0.x: 传 None 或空 input 恢复
graph.invoke(None, config)

# ✅ 1.0.x: 必须用 Command(resume=...)
graph.invoke(Command(resume="approved"), config)
```

**3. `interrupt_before` / `interrupt_after` 定位变化**

```python
# ⚠️ 这些参数仍然可用, 但官方定位为"调试工具"
# 用于 LangGraph Studio 中暂停检查状态
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["sensitive_node"],   # 节点执行前暂停
    interrupt_after=["another_node"],      # 节点执行后暂停
)
# 生产环境的 HITL 应使用 interrupt() 函数
```

来源: [NodeInterrupt (Deprecated)](https://reference.langchain.com/python/langgraph/errors/NodeInterrupt) · [LangGraph v1 Migration Guide](https://docs.langchain.com/oss/python/migrate/langgraph-v1) · [LangGraph v0.2 Blog](https://www.langchain.com/blog/langgraph-v0-2) · [LangChain/LangGraph 1.0 Blog](https://www.langchain.com/blog/langchain-langgraph-1dot0)

---

## 3. 0.x vs 1.0.x API 变化对照表 (完整汇总)

见上方 2.5 节。补充说明:

- **v1 相比 v0.6.6 没有破坏性变更**(no breaking changes),核心图原语(StateGraph / nodes / edges / compile)保持不变
- 主要变化集中在: 弃用项清理、包名重组、Python 最低版本提升
- 如果你看到的教程用 `NodeInterrupt` + `graph.invoke(None, config)`,**那是 0.x 写法,1.0.x 不要用**

来源: [What's New in LangGraph v1](https://docs.langchain.com/oss/javascript/releases/langgraph-v1) · [GitHub Issue #6062 (v1 Alpha)](https://github.com/langchain-ai/langgraph/issues/6062)

---

## 4. LangGraph interrupt vs 自研门闩的取舍 + 对 FreshLatch 的推荐

### 对 FreshLatch 的推荐

**结论: 推荐用 LangGraph interrupt + SqliteSaver, 但保持极简。**

理由:

1. **「图不是 Agent」约束天然契合**: FreshLatch 的图只做「跑到一半 → 中断 → 等人 → 恢复」,这正是 LangGraph interrupt 的最佳用例。图不需要有 Agent 循环、ToolNode、LLM 调用——它就是一个人审管道。

2. **Windows 本地 + 无 Docker**: SqliteSaver 零配置落盘,不需要外部服务(不像 PostgresSaver 需要 PG 实例)。一个 `.db` 文件搞定。

3. **代码量优势**: 3 个 API 调用 vs 自研门闩需要写 state 序列化 + flag 管理 + 恢复入口 + 错误处理。FreshLatch 已经有够多业务逻辑要写,不要在基础设施上花精力。

4. **多轮人审**: 复验流程可能需要「初审 → 证据补充 → 复审」多轮中断,LangGraph 原生支持一个图内多个 `interrupt()` 点。

5. **未来扩展**: 如果后续需要「撤销人审决定,回退到之前的 checkpoint」,LangGraph 的 `graph.update_state()` 原生支持。

### 推荐架构

```
FreshLatch 系统架构:

┌────────────────────────────────────────────────────────┐
│  Agent 循环 (裸 chat.completions + tools, 自己写)       │
│  Lead Agent ←→ Critic Agent ←→ Evidence Gatherer       │
│                                                        │
│  当遇到需要人审的节点时:                                  │
│    ↓ 调 LangGraph 图                                    │
│                                                        │
│  ┌──────────────────────────────────────────────┐      │
│  │  LangGraph 图 (仅做人审 checkpoint)            │      │
│  │                                              │      │
│  │  START → prepare_review → interrupt() ──┐    │      │
│  │                    ↑                     │    │      │
│  │                    │   (人审决定)          │    │      │
│  │                    └── resume ──→ execute → END      │
│  │                                              │      │
│  │  checkpointer = SqliteSaver("checkpoints.db") │     │
│  └──────────────────────────────────────────────┘      │
│                                                        │
│  FastAPI 提供 /reverify/start 和 /reverify/decide      │
│  Streamlit 前端展示待审信息 + [作废] [续命] 按钮          │
└────────────────────────────────────────────────────────┘
```

### pip install 清单

```bash
pip install langgraph langgraph-checkpoint-sqlite
# Python >= 3.10
```

---

## 5. 遗留风险/未决问题

### 已确认的风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| **节点重执行**: `interrupt()` 前的代码会重跑 | 如果有非幂等副作用(发邮件/扣款),会重复执行 | 将副作用代码放到 `interrupt()` 之后; 或用 state flag 跳过 |
| **SQLite 并发**: SqliteSaver 不支持高并发写入 | 多个用户同时人审可能锁冲突 | FreshLatch 是单人本地使用,影响小; 如需多用户考虑 PostgresSaver |
| **版本迭代**: LangGraph 仍在快速迭代(0.x→1.0.x 已有大量 API 变化) | 未来升级可能需要改代码 | 锁定版本(`langgraph>=1.0,<2.0`); 隔离 LangGraph 用法到单独模块 |
| **checkpoint 膨胀**: 每次 checkpoint 保存完整 state | 长时间运行 + 大 state → 数据库文件增长 | 定期清理旧 checkpoint; 或使用 TTL 策略 |
| **AsyncSqliteSaver vs SqliteSaver**: FastAPI 是异步框架 | 同步 SqliteSaver 在 async 端点中会阻塞事件循环 | FastAPI 中用 `AsyncSqliteSaver` 或用 `run_in_executor` 包装 |

### 未决问题(需后续实验验证)

1. **SqliteSaver 在 Windows 上的文件锁行为**: Windows 的 SQLite 文件锁与 Linux 不同,需实测 FastAPI 多请求并发时是否正常
2. **AsyncSqliteSaver 的实际 API 差异**: 文档中 AsyncSqliteSaver 的 `from_conn_string` 是否为 async context manager?需写 demo 验证
3. **checkpoint 清理策略**: LangGraph 是否提供内置的 checkpoint 清理 API?还是需要直接操作 SQLite 表?
4. **多 interrupt 串联时的 resume 匹配**: 如果一个节点内有 2 个 `interrupt()`,第一次 resume 恢复第一个,第二次 resume 如何触发?需写 demo 验证
5. **State 兼容性**: 如果修改了 State TypedDict 的字段(加/删字段),旧的 checkpoint 能否正常恢复?

### 建议下一步

1. **写一个最小 POC**: 基于本报告的示例代码,在 FreshLatch 项目中跑通 `SqliteSaver + interrupt + Command(resume)` 的完整流程
2. **测试 FastAPI 集成**: 用 FastAPI 端点包装,验证跨 HTTP 请求的 interrupt → resume 流程
3. **测试进程重启恢复**: 启动图 → interrupt → 杀掉进程 → 重启 → resume,验证 SQLite 持久化可靠
4. **评估 AsyncSqliteSaver**: 如果 FastAPI 用 async 端点,测试 AsyncSqliteSaver 的兼容性

---

## 附录: 所有来源 URL

### 官方文档
- [Interrupts (Python)](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [Persistence (Python)](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangGraph v1 Migration Guide](https://docs.langchain.com/oss/python/migrate/langgraph-v1)
- [What's New in LangGraph v1](https://docs.langchain.com/oss/javascript/releases/langgraph-v1)
- [LangChain/LangGraph 1.0 Blog](https://www.langchain.com/blog/langchain-langgraph-1dot0)
- [LangGraph v0.2 Blog](https://www.langchain.com/blog/langgraph-v0-2)
- [Making HITL Easier Blog](https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt)
- [Backward Compatibility](https://docs.langchain.com/oss/python/langgraph/backward-compatibility)

### API 参考
- [interrupt() Reference](https://reference.langchain.com/python/langgraph/types/interrupt)
- [Command Reference](https://reference.langchain.com/python/langgraph/types/Command)
- [InMemorySaver Reference](https://reference.langchain.com/python/langgraph.checkpoint/memory/InMemorySaver)
- [NodeInterrupt Reference (Deprecated)](https://reference.langchain.com/python/langgraph/errors/NodeInterrupt)
- [SqliteSaver Reference](https://reference.langchain.com/python/langgraph.checkpoint.sqlite/SqliteSaver)

### PyPI 包
- [langgraph-checkpoint-sqlite](https://pypi.org/project/langgraph-checkpoint-sqlite/)
- [langgraph-checkpoint-postgres](https://pypi.org/project/langgraph-checkpoint-postgres/)

### GitHub
- [LangGraph 主仓库](https://github.com/langchain-ai/langgraph)
- [types.py 源码](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/types.py)
- [v1 Alpha 讨论 (Issue #6062)](https://github.com/langchain-ai/langgraph/issues/6062)

### 社区教程
- [Interrupts and Commands (dev.to)](https://dev.to/jamesbmour/interrupts-and-commands-in-langgraph-building-human-in-the-loop-workflows-4ngl)
- [HITL Interrupt Patterns (Turion.ai)](https://turion.ai/blog/langgraph-human-in-the-loop-interrupt-tutorial/)
- [HITL: Pausing & Rewinding (Towards AI)](https://pub.towardsai.net/langgraph-human-in-the-loop-pausing-reviewing-and-rewinding-your-agent-4028bd05b049)
- [LangGraph State Management (ActiveWizards)](https://activewizards.com/blog/langgraph-state-management-checkpointing-recovery-and-the-persistence-layer-decision/)
