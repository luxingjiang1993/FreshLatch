"""SKILL.md 教义表加载器(规格 T6 实装债,#21):Runner 在角色会话启动时整份注入正文。

c5/c6 事故根因之一(#19 评估文档事实 1):教义表在盘不在场——docstring 声称「Runner 注入
替换」但全 src 无加载代码,c5 二修的 SKILL 同步在行为层空转。本模块就是补这个接线债。

纪律:加载失败返回 None(不抛),由调用方回退内联人格并落 `skill_fallback` 事件——
静默降级 = 在盘不在场的事故形态复发。
"""

from __future__ import annotations

from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2] / "skills"


def load_skill_body(slug: str, *, skills_root: Path | None = None) -> str | None:
    """读取 skills/<slug>/SKILL.md 正文(frontmatter 剥掉);文件缺失或正文为空返回 None。"""
    path = (skills_root or SKILLS_ROOT) / slug / "SKILL.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    body = text
    if lines and lines[0].strip() == "---":
        try:
            end = lines.index("---", 1)
            body = "\n".join(lines[end + 1:])
        except ValueError:  # frontmatter 未闭合:整份按正文处理,不猜
            body = text
    body = body.strip()
    return body or None
