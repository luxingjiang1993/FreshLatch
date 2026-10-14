"""SKILL.md 教义表加载器(规格 T6 实装债,#21):Runner 在角色会话启动时整份注入正文。

c5/c6 事故根因之一(#19 评估文档事实 1):教义表在盘不在场——docstring 声称「Runner 注入
替换」但全 src 无加载代码,c5 二修的 SKILL 同步在行为层空转。本模块就是补这个接线债。

纪律:加载失败返回 None(不抛),由调用方回退内联人格并落 `skill_fallback` 事件——
静默降级 = 在盘不在场的事故形态复发。

references 不进这次注入。`load_skill_reference` 只读 `skills/<slug>/references/<name>.md`,
供测试与调用方按需打开。它不进入 Runner 默认技能注入列表,也不是 Lead 工具。
"""

from __future__ import annotations

import re
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parents[2] / "skills"

# 与技能目录名、references 文件主名同形。拒绝目录穿越与扩展名。
_SLUG_RE = re.compile(r"^[a-z0-9]+([-_][a-z0-9]+)*$")
_REF_STEM_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


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


def load_skill_reference(
    slug: str, name: str, *, skills_root: Path | None = None,
) -> str | None:
    """只读 skills/<slug>/references/<name>.md。

    name 是文件主名,不含 .md、不含目录。缺失、空文件、或路径不在该 references
    目录内时返回 None。不读 SKILL.md,也不改变 load_skill_body 的注入范围。
    """
    if not _SLUG_RE.fullmatch(slug) or not _REF_STEM_RE.fullmatch(name):
        return None
    root = (skills_root or SKILLS_ROOT).resolve()
    skill_dir = (root / slug).resolve()
    ref_dir = (skill_dir / "references").resolve()
    path = (ref_dir / f"{name}.md").resolve()
    # 技能目录、references 目录、目标文件解析后都必须留在 skills 根下。
    # references 或文件本身是指向根外的符号链接时,这里拒绝。
    if not skill_dir.is_relative_to(root):
        return None
    if not ref_dir.is_relative_to(skill_dir):
        return None
    if not path.is_relative_to(ref_dir):
        return None
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    return text or None
