---
doc_id: s6-d0-t1-01-patch
as_of: T1
source_type: public
title: 系统补丁与流程变更日志
provenance: synthetic
license: synthetic
domain: D0
genre: S6
---
## p1
系统内复验窗口配置已由14天调整为21天，对应变更已在本次补丁中部署，旧窗口设置保留用于回溯比对，不参与新流程。
## p2
战略判断模块的输出状态字段已修改，从“已签发”切换为“待复验”，该变更同步至前端展示与审批流节点，确保状态透明。
## p3
相关变更已通过内部测试验证，确认不影响现有业务流程运行，且已在发布说明中明确标注为重要更新项。
