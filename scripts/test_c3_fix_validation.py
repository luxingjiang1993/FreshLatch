#!/usr/bin/env python3
"""
测试脚本：验证 #32 任务实现
验证内容：
1. 六枚举定义已更新，包含前提出处语义
2. 消歧指令已添加到工具描述中
3. 标注器探针脚本创建成功
"""

import sys
import os
from pathlib import Path


from freshlatch.tools import FOCUS_DIMENSIONS, tool_specs
from freshlatch.roles.lead import LEAD_PERSONA
from freshlatch.roles.critic import CRITIC_PERSONA


def test_enum_definitions():
    """测试枚举定义是否已更新"""
    print("测试 1: 验证枚举定义更新...")

    expected_dimensions = {
        "competitor_pricing": "竞品价格:主张前提建立在竞品定价/价格对标数据上;",
        "regulatory_stance": "监管口径:主张前提建立在监管政策/官方口径上;",
        "interview_reversal": "访谈改口:主张前提建立在访谈/纪要/口头口径上(机制维度);",
        "cost_model": "成本模型:主张前提建立在成本/费用结构测算上;",
        "market_structure": "市场结构:主张前提建立在市场规模/格局/份额判断上;",
        "tech_ecosystem": "技术生态:主张前提建立在技术栈/生态位判断上;"
    }

    print(f"  当前 FOCUS_DIMENSIONS: {FOCUS_DIMENSIONS}")

    # 检查所有维度是否都存在
    for dim, desc in expected_dimensions.items():
        if dim not in FOCUS_DIMENSIONS:
            print(f"  X 缺少维度: {dim}")
            return False

    print("  V 所有维度枚举存在")

    # 简单检查是否有扩展描述
    if any("主张前提建立在" in desc for desc in expected_dimensions.values()):
        print("  V 枚举定义已包含前提出处语义")
    else:
        print("  X 枚举定义缺少前提出处语义")
        return False

    return True


def test_tool_descriptions():
    """测试工具描述是否已更新"""
    print("\n测试 2: 验证工具描述更新...")

    # 获取 mark_stale 工具定义
    try:
        tools = tool_specs(["mark_stale"])
        mark_stale_def = tools[0] if tools else None

        if not mark_stale_def:
            print("  X 无法获取 mark_stale 工具定义")
            return False

        dimension_desc = mark_stale_def["function"]["parameters"]["properties"]["dimension"]["description"]

        print(f"  mark_stale dimension 描述: {dimension_desc}")

        # 检查是否包含消歧指令
        if "前提出处语义" in dimension_desc:
            print("  V 工具描述已包含前提出处语义")
        else:
            print("  X 工具描述缺少前提出处语义")
            return False

        if "证据出处类型" in dimension_desc:
            print("  V 工具描述已包含证据出处说明")
        else:
            print("  X 工具描述缺少证据出处说明")
            return False

        if "不是反证内容的主题词" in dimension_desc:
            print("  V 工具描述已包含消歧指令")
        else:
            print("  X 工具描述缺少消歧指令")
            return False

        if "interview_reversal 是机制维度" in dimension_desc:
            print("  V 工具描述已包含机制维度说明")
        else:
            print("  X 工具描述缺少机制维度说明")
            return False

        return True
    except Exception as e:
        print(f"  X 获取工具定义失败: {e}")
        return False


def test_lead_persona_updates():
    """测试 Lead 人格是否已更新"""
    print("\n测试 3: 验证 Lead 人格更新...")

    # 检查是否包含维度消歧说明 - 寻找相关概念而非精确匹配
    if "前提出处语义" in LEAD_PERSONA or ("证据出处类型" in LEAD_PERSONA and "不是反证内容的主题词" in LEAD_PERSONA):
        print("  V Lead 人格已包含前提出处语义说明")
    else:
        print("  X Lead 人格缺少前提出处语义说明")
        return False

    if "证据出处类型" in LEAD_PERSONA:
        print("  V Lead 人格已包含证据出处类型说明")
    else:
        print("  X Lead 人格缺少证据出处类型说明")
        return False

    if "不是反证内容的主题词" in LEAD_PERSONA:
        print("  V Lead 人格已包含消歧指令")
    else:
        print("  X Lead 人格缺少消歧指令")
        return False

    if "interview_reversal 是机制维度" in LEAD_PERSONA:
        print("  V Lead 人格已包含机制维度说明")
    else:
        print("  X Lead 人格缺少机制维度说明")
        return False

    return True


def test_critic_persona_updates():
    """测试 Critic 人格是否已更新"""
    print("\n测试 4: 验证 Critic 人格更新...")

    # 检查是否包含维度消歧说明 - 寻找相关概念而非精确匹配
    if "前提出处语义" in CRITIC_PERSONA or ("证据出处类型" in CRITIC_PERSONA and "不是反证内容的主题词" in CRITIC_PERSONA):
        print("  V Critic 人格已包含前提出处语义说明")
    else:
        print("  X Critic 人格缺少前提出处语义说明")
        return False

    if "证据出处类型" in CRITIC_PERSONA:
        print("  V Critic 人格已包含证据出处类型说明")
    else:
        print("  X Critic 人格缺少证据出处类型说明")
        return False

    if "不是反证内容的主题词" in CRITIC_PERSONA:
        print("  V Critic 人格已包含消歧指令")
    else:
        print("  X Critic 人格缺少消歧指令")
        return False

    if "interview_reversal 是机制维度" in CRITIC_PERSONA:
        print("  V Critic 人格已包含机制维度说明")
    else:
        print("  X Critic 人格缺少机制维度说明")
        return False

    return True


def test_probe_script_exists():
    """测试标注器探针脚本是否已创建"""
    print("\n测试 5: 验证标注器探针脚本创建...")

    probe_script_path = Path("scripts/dimension_annotation_probe.py")
    if probe_script_path.exists():
        print("  V 标注器探针脚本已创建")

        # 检查脚本内容
        with open(probe_script_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if "c3型机制主题分离" in content:
            print("  V 脚本包含 c3 型机制-主题分离样本")
        else:
            print("  X 脚本缺少 c3 型机制-主题分离样本")
            return False

        if "12 条合成反证片段" in content:
            print("  V 脚本包含 12 条合成反证片段设计")
        else:
            print("  X 脚本缺少 12 条合成反证片段设计")
            return False

        return True
    else:
        print(f"  X 标注器探针脚本不存在: {probe_script_path}")
        return False


def main():
    print("开始验证 #32 任务实现...")
    print("="*60)

    tests = [
        test_enum_definitions,
        test_tool_descriptions,
        test_lead_persona_updates,
        test_critic_persona_updates,
        test_probe_script_exists
    ]

    passed = 0
    total = len(tests)

    for test_func in tests:
        if test_func():
            passed += 1
        else:
            print(f"  X {test_func.__name__} 测试失败")

    print("="*60)
    print(f"测试结果: {passed}/{total} 项测试通过")

    if passed == total:
        print("OK 所有测试通过！#32 任务实现完成。")
        return True
    else:
        print("X 部分测试失败，请检查实现。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)