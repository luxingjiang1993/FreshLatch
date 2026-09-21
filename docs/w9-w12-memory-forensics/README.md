# W9-W12 MemoryForensics 模块

> **勘误(2026-09-21)**:「与 Lead 集成、侧栏、验证了所有核心功能」按独立 demo 而言。Lead 默认不挂 `spawn_forensic`;记忆卫生 UI 未做;demo 是 demo 层。详见评估文档与 ADR-0014。

## 概述

## 概述

W9-W12阶段实现了MemoryForensics（记忆刑侦）小模块，这是一个专门用于审核和维护长期记忆健康的重要功能模块。

## 核心功能

### 1. Forensic Agent
- **智能审核**：能够自动检测长期记忆中的问题
- **三种检测能力**：
  - 未验证记忆（缺少source_ref）
  - 互斥记忆（与其他记忆冲突）
  - 死亡记忆（过时信息）

### 2. 安全机制
- **提议-确认流程**：记忆不会被直接删除，而是隔离并等待人工确认
- **工具权限控制**：严格限制Forensic Agent的能力范围
- **数据完整性**：确保历史数据可追溯

### 3. 工具集
- `list_memories()` - 获取长期记忆条目
- `flag_dead(memory_id, reason, evidence_ids)` - 标记死亡记忆
- `flag_contradiction(memory_id_a, memory_id_b, reason)` - 标记互斥记忆
- `flag_unverified(memory_id, reason)` - 标记未验证记忆
- `propose_quarantine(memory_ids)` - 提议隔离记忆

## 集成方式

### 与Lead集成
- Lead在检测到记忆冲突时可以调用`spawn_forensic`工具
- Forensic Agent独立审核记忆库
- 将发现的问题反馈给Lead流程

### 数据存储
- 扩展了SQLite数据库结构
- 增加了记忆管理相关表
- 保持了与现有系统的兼容性

## 设计理念

### 可靠性优先
- 防止腐烂记忆影响复验结果
- 确保系统长期运行的准确性

### 用户控制
- 人工确认机制防止误操作
- 透明的审核和隔离流程

### 架构一致性
- 与现有Agent架构兼容
- 遵循项目的工具和权限模式

## 价值主张

> "MemoryForensic是FreshLatch内部的可靠性模块。当Lead在复验过程中发现记忆冲突时，会调用Forensic Agent审核长期记忆的健康状况。Forensic会识别死亡、互斥和未经验证的记忆条目，提出隔离建议，确保腐烂记忆不影响复验准确性。"

## 技术特点

- **模块化**：独立于主复验流程，可单独维护
- **安全**：严格权限控制，防止意外修改
- **透明**：完整的审计轨迹
- **可扩展**：易于添加新的检测规则

## 验证

通过`scripts/w9_w12_memory_forensics_demo.py`脚本验证了所有核心功能。