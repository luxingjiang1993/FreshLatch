"""skill 一致性单测(决策三:4 断言,tests/unit,CI 零 LLM)。

断言 1:frontmatter 规则(check_a_skill 规则集纯 Python 重写:name/description/无 XML 标签/正文行数);
断言 2:skill 正文 + references 出现的工具名 ⊆ 该角色白名单代码常量(单一定量真相在代码);
断言 3:devil_advocate 的 focus-dimensions.md 6 值 == FOCUS_DIMENSIONS 代码常量(#14 延伸);
断言 4:拦截→纠正对照表只断「场景→原因→动作」映射存在,不断言错误文案(文案唯一真相在代码)。
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

from freshlatch.skills_loader import load_skill_body, load_skill_reference
from freshlatch.tools import (
    CRITIC_TOOLS, FOCUS_DIMENSIONS, LEAD_TOOLS_W3, AUDITOR_TOOLS, FORENSIC_TOOLS,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

ROLE_WHITELIST = {
    "reverify": set(LEAD_TOOLS_W3),
    "devil_advocate": set(CRITIC_TOOLS),
    "freshness_audit": set(AUDITOR_TOOLS),
    "memory_forensics": set(FORENSIC_TOOLS),
}

# L4-SK-02: 中文业务包。不进 Runner 默认注入。工具名仍须 ⊆ Lead 默认白名单。
BUSINESS_PACK_WHITELIST = {
    "earnings_figures": set(LEAD_TOOLS_W3),
    "event_timeline": set(LEAD_TOOLS_W3),
    "patch_diff": set(LEAD_TOOLS_W3),
    "strategy_walkthrough": set(LEAD_TOOLS_W3),
}

# 全量工具词汇:任何 skill 文件里反引号提到的工具名都必须落在本角色白名单内
TOOL_VOCABULARY = (
    set(LEAD_TOOLS_W3) | set(CRITIC_TOOLS) | set(AUDITOR_TOOLS)
    | {"spawn_auditor"} | set(FORENSIC_TOOLS) | {"spawn_forensic"}
)

ALL_WHITELIST = {**ROLE_WHITELIST, **BUSINESS_PACK_WHITELIST}
ALL_SLUGS = sorted(ALL_WHITELIST)
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


@pytest.mark.parametrize("slug", ALL_SLUGS)
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
    # 「~100 词」对中文按字符计(分词器不在依赖内;split() 对无空格中文恒真,形同虚设)
    assert 0 < len(fm["metadata"]) <= 200, "metadata ~100 词 ≈ 200 字符以内"

    body = text.split("---", 2)[2]
    assert not XML_TAG.search(body), "正文不得含 XML 标签(prompt 注入面)"
    assert len(body.splitlines()) <= 500, "正文 ≤500 行"


# -- 断言 2:工具名 ⊆ 角色白名单 -------------------------------------------


@pytest.mark.parametrize("slug", ALL_SLUGS)
def test_tool_names_subset_of_whitelist(slug):
    mentioned: set[str] = set()
    for path in _skill_paths(slug):
        mentioned.update(IDENT.findall(path.read_text(encoding="utf-8")))
    offending = (mentioned & TOOL_VOCABULARY) - ALL_WHITELIST[slug]
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


@pytest.mark.parametrize("slug", ALL_SLUGS)
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


# -- L4-SK-03:references 承诺与加载器一致 ------------------------------------

_FALSE_REFERENCE_CLAIM = "references 由循环内 read_source 按需读取"
_REFERENCE_ONLY = "名单的存储真相是 SQLite"


def test_reverify_frontmatter_matches_reference_loader():
    """frontmatter 承诺的只读入口真能读到一个 reference,且不再把这件事交给 read_source。"""
    text = (SKILLS_DIR / "reverify" / "SKILL.md").read_text(encoding="utf-8")
    desc = _frontmatter(text)["description"]
    assert _FALSE_REFERENCE_CLAIM not in text
    assert "read_source" not in desc
    assert "load_skill_reference" in desc
    assert "skills/{slug}/references/{name}.md" in desc

    got = load_skill_reference("reverify", "rerun-rules")
    assert got and _REFERENCE_ONLY in got

    body = load_skill_body("reverify")
    assert body and _REFERENCE_ONLY not in body
    assert "load_skill_reference" not in body
    assert "load_skill_reference" not in LEAD_TOOLS_W3


def test_load_skill_body_still_reads_only_skill_md(tmp_path):
    """load_skill_body 只返回 SKILL.md 正文;reference 由另一函数读取。"""
    skill = tmp_path / "reverify"
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: reverify\ndescription: 夹具\n---\n\n正文标记\n",
        encoding="utf-8",
    )
    (skill / "references" / "verdict-basis.md").write_text(
        "引用哨兵\n", encoding="utf-8",
    )

    body = load_skill_body("reverify", skills_root=tmp_path)
    assert body == "正文标记"
    assert load_skill_reference("reverify", "verdict-basis", skills_root=tmp_path) == "引用哨兵"

    empty = skill / "references" / "rerun-rules.md"
    empty.write_text("  \n", encoding="utf-8")
    assert load_skill_reference("reverify", "rerun-rules", skills_root=tmp_path) is None


def _dir_link_or_junction(link: Path, target: Path) -> None:
    """建目录级链接。POSIX / 有提权的 Windows 用符号链接；无提权 Windows
    （WinError 1314）退 junction——同为目录重解析点，resolve() 同样穿透，
    是该校验 Windows 下可构造的最强逃逸原语（I-06 #681）。"""
    try:
        link.symlink_to(target, target_is_directory=True)
        return
    except OSError:
        if os.name != "nt":
            raise
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        check=True,
        capture_output=True,
    )


def test_load_skill_reference_rejects_symlink_escape(tmp_path):
    """references 目录或文件指向 skills 根之外时,不读取。"""
    skills_root = tmp_path / "skills"
    skill = skills_root / "reverify"
    skill.mkdir(parents=True)
    outside = tmp_path / "escaped"
    outside.mkdir()
    (outside / "verdict-basis.md").write_text("外部哨兵", encoding="utf-8")
    _dir_link_or_junction(skill / "references", outside)
    assert load_skill_reference(
        "reverify", "verdict-basis", skills_root=skills_root,
    ) is None

    (skill / "references").unlink()
    ref_dir = skill / "references"
    ref_dir.mkdir()
    try:
        (ref_dir / "verdict-basis.md").symlink_to(outside / "verdict-basis.md")
    except OSError:
        if os.name != "nt":
            raise
        # 文件级符号链接在无提权 Windows 上不可构造；改测同一 resolve 容性
        # 守卫族的 skill 目录级逃逸（junction），仍必须拒绝读取。
        ref_dir.rmdir()
        skill.rmdir()
        _dir_link_or_junction(skill, outside)
    assert load_skill_reference(
        "reverify", "verdict-basis", skills_root=skills_root,
    ) is None


@pytest.mark.parametrize("slug,name", [
    ("reverify", "../SKILL"),
    ("reverify", "verdict-basis/../../etc"),
    ("reverify", "rerun-rules.md"),
    ("../skills", "rerun-rules"),
    ("reverify", "no-such-ref"),
    ("no_such_skill", "rerun-rules"),
])
def test_load_skill_reference_rejects_unsafe_or_missing(slug, name):
    assert load_skill_reference(slug, name) is None


# pin 27acda75 的 Runner 默认教义块。业务包不得出现在这段注入里。
_PINNED_RUNNER_DOCTRINE = """\
        self._doctrine: dict[str, str | None] = {
            "reverify": load_skill_body("reverify"),
            "devil_advocate": load_skill_body("devil_advocate"),
            "freshness_audit": load_skill_body("freshness_audit"),  # Auditor(#20/ADR-0009,#22 接线)
        }"""

_CJK = re.compile(r"[\u4e00-\u9fff]")


def test_runner_default_skill_injection_unchanged():
    """默认注入仍是三次 load_skill_body,不调用 reference 加载器,也不加载业务包。"""
    src = (REPO_ROOT / "src/freshlatch/runner.py").read_text(encoding="utf-8")
    assert "load_skill_reference" not in src
    assert src.count("load_skill_body(") == 3
    assert src.count('load_skill_body("reverify")') == 1
    assert src.count('load_skill_body("devil_advocate")') == 1
    assert src.count('load_skill_body("freshness_audit")') == 1
    assert _PINNED_RUNNER_DOCTRINE in src
    lead = (REPO_ROOT / "src/freshlatch/roles/lead.py").read_text(encoding="utf-8")
    loop = (REPO_ROOT / "src/freshlatch/roles/loop.py").read_text(encoding="utf-8")
    for slug in BUSINESS_PACK_WHITELIST:
        assert f'load_skill_body("{slug}")' not in src
        assert f"skills/{slug}" not in src
        assert f"skills/{slug}" not in lead
        assert f"skills/{slug}" not in loop
    assert LEAD_TOOLS_W3 == (
        "retrieve",
        "read_source",
        "reverify_claim",
        "mark_stale",
        "mark_gap",
        "finish_reverify",
        "spawn_critic",
    )


@pytest.mark.parametrize("slug", sorted(BUSINESS_PACK_WHITELIST))
def test_business_pack_utf8_chinese_and_real_references(slug):
    """业务包正文为 UTF-8 中文;frontmatter 写的读取器必须能真读到 reference。"""
    path = SKILLS_DIR / slug / "SKILL.md"
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    assert b"\xef\xbf\xbd" not in raw
    fm = _frontmatter(text)
    body = text.split("---", 2)[2]
    assert _CJK.search(fm["description"])
    assert _CJK.search(fm["metadata"])
    assert _CJK.search(body)
    assert _FALSE_REFERENCE_CLAIM not in text
    assert "read_source" not in fm["description"]
    assert "不进入 Runner" in fm["description"]
    assert "不进入 Lead 系统提示" in fm["description"]
    assert "load_skill_reference" in fm["description"]
    assert "skills/{slug}/references/{name}.md" in fm["description"]
    assert "load_skill_reference" not in body
    refs = sorted((SKILLS_DIR / slug / "references").glob("*.md"))
    assert refs
    for ref in refs:
        got = load_skill_reference(slug, ref.stem)
        assert got
        assert _CJK.search(got)


def test_patch_diff_line_delta_counts_rows_only():
    """可选脚本只计 before/after 行差,不触碰事件账。"""
    import importlib.util

    script = SKILLS_DIR / "patch_diff" / "scripts" / "line_delta.py"
    spec = importlib.util.spec_from_file_location("patch_diff_line_delta", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.line_delta("甲\n乙\n", "甲\n丙\n") == {
        "removed": 1,
        "added": 1,
        "before_lines": 2,
        "after_lines": 2,
    }
    assert module.line_delta("甲\n甲\n", "甲\n")["removed"] == 1
    assert module.line_delta("", "") == {
        "removed": 0,
        "added": 0,
        "before_lines": 0,
        "after_lines": 0,
    }
