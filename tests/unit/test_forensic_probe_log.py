"""#335:Forensic 探测失败仍视为不存在,并留下异常类型日志。"""

import asyncio
import logging

from freshlatch.roles.forensic import ForensicAgent


def test_probe_exception_does_not_mark_source_exists(caplog):
    agent = ForensicAgent()

    def read_source(_doc_id, *, as_of):
        raise RuntimeError(f"探测失败不应进日志 {as_of}")

    items = [{"memory_id": "m1", "source_ref": "doc-a#p1@T1"}]
    with caplog.at_level(logging.WARNING):
        exists = asyncio.run(
            agent._build_source_exists(items, read_source=read_source)
        )
    assert exists("doc-a") is False
    warnings = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
    assert any("exc_type=RuntimeError" in message for message in warnings)
    joined = "\n".join(warnings)
    assert "探测失败不应进日志" not in joined
    assert "T0" in joined and "T1" in joined
