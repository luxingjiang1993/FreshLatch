"""PROTOTYPE 假数据 — 供 ui_fastapi / ui_streamlit 两个糙样共用。生产代码不许 import。"""

# 复验单行(红/绿/灰 = stale/fresh/unknown)
CLAIMS = [
    {"id": "C1", "text": "FreshLatch 专业版定价为 299 元/席/月", "verdict": "stale",
     "reason": "D04:299 元档 2026-06-01 已下线,合并入 399 元团队版",
     "evidence": [("D01", "专业版 299 元/席/月"), ("D04", "专业版 299 元档正式下线")]},
    {"id": "C2", "text": "FreshLatch 复验席位可跨项目共享", "verdict": "fresh",
     "reason": "D02 支持,后续公告未推翻",
     "evidence": [("D02", "复验席位可跨项目共享")]},
    {"id": "C3", "text": "北京办公室正在招聘高级后端工程师", "verdict": "stale",
     "reason": "D06:岗位已满编,停止接收简历",
     "evidence": [("D05", "开放高级后端工程师岗位"), ("D06", "已停止接收简历,团队已满编")]},
    {"id": "C4", "text": "客户数据只能存储在华北 1 地域", "verdict": "stale",
     "reason": "D08:新增华东 2 可选地域",
     "evidence": [("D07", "所有客户数据存储于华北 1 地域"), ("D08", "新增华东 2 地域选项")]},
    {"id": "C5", "text": "认证实施伙伴覆盖华东与华南", "verdict": "fresh",
     "reason": "D10:扩至 20 家仍含华东华南",
     "evidence": [("D10", "认证实施伙伴扩至 20 家,新增西南大区")]},
    {"id": "C6", "text": "webhook 支持配置重放窗口", "verdict": "fresh",
     "reason": "D12:API v2 新增该能力",
     "evidence": [("D12", "webhook 新增重放窗口配置,默认 5 分钟")]},
    {"id": "C7", "text": "专业版按自然月计费", "verdict": "stale",
     "reason": "D03:2026-06 起改 30 天滚动计费",
     "evidence": [("D03", "改为按 30 天滚动计费")]},
    {"id": "C8", "text": "webhook 仅支持验签", "verdict": "unknown",
     "reason": "D11/D12 冲突,未读到 v2 全文,证据不足",
     "evidence": [("D11", "webhook 仅支持验签"), ("D12", "新增重放窗口配置")]},
]

# T0 = 签发时快照;T1 = 复验时刻快照
DOCS_T0 = {
    "D01": "FreshLatch 官网定价页(2026-03):专业版 299 元/席/月,含 5 个复验席位。",
    "D02": "FreshLatch 帮助中心(2026-04):复验席位可跨项目共享,按自然月计费。",
    "D05": "招聘页(2026-02):FreshLatch 北京办公室开放高级后端工程师岗位。",
    "D07": "安全白皮书(2026-01):所有客户数据存储于华北 1 地域。",
    "D09": "合作伙伴名录(2026-03):认证实施伙伴共 12 家,覆盖华东与华南。",
    "D11": "API 文档 v1(2026-02):webhook 仅支持验签,不支持重放窗口配置。",
}
DOCS_T1 = {
    "D03": "内部公告(2026-05-15):自 2026-06-01 起,专业版取消按自然月计费,改为按 30 天滚动计费。",
    "D04": "内部公告(2026-06-01):专业版 299 元档正式下线,合并入 399 元团队版。",
    "D06": "招聘页(2026-04):北京办公室高级后端岗位已停止接收简历,团队已满编。",
    "D08": "合规更新(2026-05):新增华东 2 地域选项,客户可自选存储地域。",
    "D10": "合作伙伴名录(2026-06):认证实施伙伴扩至 20 家,新增西南大区。",
    "D12": "API 文档 v2(2026-05):webhook 新增重放窗口配置,默认 5 分钟。",
}

# 工具轨迹(展示用,不是首页)
TRACE = [
    {"t": 1, "actor": "Lead", "tool": "list_claims", "args": "{}", "note": "读取 8 条待复验主张"},
    {"t": 2, "actor": "Lead", "tool": "search_docs", "args": '{"query":"定价"}', "note": "命中 D01 D04"},
    {"t": 3, "actor": "Lead", "tool": "read_doc", "args": '{"doc_id":"D04"}', "note": "T1 原文:299 元档下线"},
    {"t": 4, "actor": "Lead", "tool": "write_verdict", "args": '{"claim_id":"C1","verdict":"stale"}', "note": "引用 D04"},
    {"t": 5, "actor": "Critic", "tool": "search_docs", "args": '{"query":"计费"}', "note": "被派驻:只找已死反证"},
    {"t": 6, "actor": "Critic", "tool": "read_doc", "args": '{"doc_id":"D03"}', "note": "反证:C7 按自然月计费已死"},
    {"t": 7, "actor": "Lead", "tool": "spawn_auditor", "args": '{"focus":"C8"}', "note": "C8 证据冲突,派驻 Auditor"},
    {"t": 8, "actor": "Auditor", "tool": "write_verdict", "args": '{"claim_id":"C8","verdict":"unknown"}', "note": "D11/D12 冲突,无全文,判 unknown"},
]

LATCH_LOG = []  # 人审动作记录(PROTOTYPE 内存态)
