"""skill 一致性单测(决策三:4 断言,tests/unit,CI 零 LLM)。

断言 1:frontmatter 规则(check_a_skill 规则集纯 Python 重写:name/description/无 XML 标签/正文行数);
断言 2:skill 正文 + references 出现的工具名 ⊆ 该角色白名单代码常量(单一定量真相在代码);
断言 3:devil_advocate 的 focus-dimensions.md 6 值 == FOCUS_DIMENSIONS 代码常量(#14 延伸);
断言 4:拦截→纠正对照表只断「场景→原因→动作」映射存在,不断言错误文案(文案唯一真相在代码)。
"""

import re
from pathlib import Path

import pytest

from freshlatch.tools import CRITIC_TOOLS, FOCUS_DIMENSIONS, LEAD_TOOLS_W3, AUDITOR_TOOLS

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# W9–W12 记忆卫生工具名(W1–W4 未挂载,无代码常量;与 test_whitelist.py 同一份名单)
FORENSIC_TOOLS = {
    "list_memories", "flag_dead", "flag_contradiction",
    "flag_unverified", "propose_quarantine",
}

ROLE_WHITELIST = {
    "reverify": set(LEAD_TOOLS_W3),
    "devil_advocate": set(CRITIC_TOOLS),
    "freshness_audit": set(AUDITOR_TOOLS),
    "memory_forensics": FORENSIC_TOOLS,
}

# 全量工具词汇:任何 skill 文件里反引号提到的工具名都必须落在本角色白名单内
TOOL_VOCABULARY = (
    set(LEAD_TOOLS_W3) | set(CRITIC_TOOLS) | set(AUDITOR_TOOLS)
    | {"spawn_auditor"} | FORENSIC_TOOLS | {"spawn_forensic"}
)

SLUGS = sorted(ROLE_WHITELIST)
XML_TAG = re.compile(r"<[A-Za-z/!][^>]*>")
IDENT = re.compile(r"`([a-z][a-z0-9_]*)`")
KEBAB = re.compile(r"^[a-z0-9]+([-_][a-z0-9]+)*$")  # 小写连字符/下划线(#10 总表 slug 用下划线)


def _skill_paths(slug: str) -> list[Path]:
    paths = [SKILLS_DIR / slug / "SKILL.md"]
    paths.extend(sorted((SKILLS_DIR / slug / "references").glob("*.md")))
    return paths


def _frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    assert lines[0].strip() == "---", "frontmatter 必须以 --- 起始"
    end = lines.index("---", 1)
    fm: dict[str, str] = {}
    for line in lines[1:end]:
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()
    return fm


# -- 断言 1:frontmatter 规则 ----------------------------------------------


@pytest.mark.parametrize("slug", SLUGS)
def test_frontmatter_rules(slug):
    text = (SKILLS_DIR / slug / "SKILL.md").read_text(encoding="utf-8")
    fm = _frontmatter(text)

    assert KEBAB.match(fm["name"]), f"name 须小写连字符: {fm['name']}"
    assert fm["name"] == slug, "name 必须等于目录名"
    assert len(fm["name"]) <= 64

    desc = fm["description"]
    assert desc and len(desc) <= 1024, "description 非空且 ≤1024 字符"
    assert not XML_TAG.search(desc), "description 不得含 XML 标签"

    assert "metadata" in fm, "metadata 字段在位"
    assert len(fm["metadata"].split()) <= 200

    body = text.split("---", 2)[2]
    assert not XML_TAG.search(body), "正文不得含 XML 标签(prompt 注入面)"
    assert len(body.splitlines()) <= 500, "正文 ≤500 行"


# -- 断言 2:工具名 ⊆ 角色白名单 -------------------------------------------


@pytest.mark.parametrize("slug", SLUGS)
def test_tool_names_subset_of_whitelist(slug):
    mentioned: set[str] = set()
    for path in _skill_paths(slug):
        mentioned.update(IDENT.findall(path.read_text(encoding="utf-8")))
    offending = (mentioned & TOOL_VOCABULARY) - ROLE_WHITELIST[slug]
    assert not offending, (
        f"{slug} 提及了白名单外的工具(禁令唯一真相在代码): {sorted(offending)}"
    )


# -- 断言 3:focus 词表 == 代码常量 ------------------------------------------


def test_focus_dimensions_match_code_constant():
    text = (SKILLS_DIR / "devil_advocate" / "references" / "focus-dimensions.md").read_text(
        encoding="utf-8"
    )
    listed = IDENT.findall(text)
    focus_values = [t for t in listed if t in FOCUS_DIMENSIONS]
    assert tuple(focus_values) == FOCUS_DIMENSIONS, (
        f"focus-dimensions.md 词表与 FOCUS_DIMENSIONS 常量漂移: {focus_values}"
    )


# -- 断言 4:拦截→纠正对照表映射存在(不断言文案) ----------------------------


@pytest.mark.parametrize("slug", SLUGS)
def test_doctrine_correction_table_present(slug):
    text = (SKILLS_DIR / slug / "SKILL.md").read_text(encoding="utf-8")
    section = re.search(r"## 教义.*?(?=\n## |\Z)", text, re.S)
    assert section, "「教义:约束与纠正」一节在位"
    rows = [ln for ln in section.group(0).splitlines() if ln.strip().startswith("|")]
    data_rows = [r for r in rows if not set(r) <= set("|- ")]  # 去掉表头分隔行
    assert len(data_rows) >= 3, "对照表至少 3 行场景映射"
    for row in data_rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        assert len(cells) >= 3, "每行须为 场景|原因|动作 三列映射"
        assert cells[0] and cells[-1], "场景与正确动作均不得为空"
    assert "以工具层返回为准" in section.group(0) or "以代码" in section.group(0), (
        "对照表须注明错误文案以代码为准(文案唯一真相在代码)"
    )
