#!/usr/bin/env python3
"""
标注器探针脚本：直接测试自标误标率

根据 #32 任务要求实现：
- 12 条合成反证片段(六枚举各 2)，隔离标注不过闸
- 直接仪器测自标误标率，解决「e2e 绿 ≠ 标注器好」的问题
- temp=0 下 12 条跨六枚举、含对抗性分离样本，验证是否存在「机制-主题混淆」级别
  的系统性偏置
"""

import json
import os
from typing import Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path

from src.freshlatch.tools import FOCUS_DIMENSIONS


@dataclass
class SyntheticEvidence:
    """合成反证样本"""
    id: str
    evidence_text: str
    true_dimension: str  # 真实维度
    expected_annotation: str  # 期望的标注维度
    description: str  # 样本说明


def create_synthetic_evidence_set() -> List[SyntheticEvidence]:
    """
    创建 12 条合成反证片段，六枚举各 2 条，必含 c3 型机制-主题分离样本
    """
    samples = []

    # 每个维度创建2个样本
    dimension_samples = {
        "competitor_pricing": [
            {
                "id": "sample_1",
                "text": "根据最新竞品分析报告，对手XYZ公司将其旗舰产品价格从原来的299元降至249元，直接冲击我们的市场份额。",
                "dimension": "competitor_pricing",
                "desc": "竞品价格直接对比样本"
            },
            {
                "id": "sample_2",
                "text": "调查显示，主要竞争对手ABC公司的企业版订阅费用从每月499元调整为399元，对我们的定价策略构成压力。",
                "dimension": "competitor_pricing",
                "desc": "竞品定价压力样本"
            }
        ],
        "regulatory_stance": [
            {
                "id": "sample_3",
                "text": "银保监会最新发布的《金融科技创新管理办法》明确规定，所有第三方支付平台必须在2024年底前完成合规改造。",
                "dimension": "regulatory_stance",
                "desc": "监管政策更新样本"
            },
            {
                "id": "sample_4",
                "text": "国家网信办通知，所有AI服务提供商需在6月30日前完成算法备案，逾期将面临暂停服务风险。",
                "dimension": "regulatory_stance",
                "desc": "监管要求样本"
            }
        ],
        "interview_reversal": [
            {
                "id": "sample_5",
                "text": "在今日的管理层会议上，CTO明确表示之前的“所有API将在3个月内开放”承诺由于资源调配问题需要延期至6个月。",
                "dimension": "interview_reversal",
                "desc": "访谈改口样本 - c3型机制主题分离:内容涉及3个月期限(主题似成本),但证据源于访谈会议(机制维度 interview_reversal)"
            },
            {
                "id": "sample_6",
                "text": "CEO在季度总结会上提到，此前公布的“年底推出V3.0版本”的计划需要根据市场反馈进行调整，新时间表将另行通知。",
                "dimension": "interview_reversal",
                "desc": "访谈口径变化样本 - 证据类型是访谈纪要，无论内容是什么"
            }
        ],
        "cost_model": [
            {
                "id": "sample_7",
                "text": "最新财务测算显示，由于原材料价格上涨15%，我们的单客户获取成本从平均200元上升至230元。",
                "dimension": "cost_model",
                "desc": "成本模型变化样本"
            },
            {
                "id": "sample_8",
                "text": "运营数据显示，单位服务成本因服务器升级而增加20%，使得我们的利润率预测需要向下修正。",
                "dimension": "cost_model",
                "desc": "运营成本变化样本"
            }
        ],
        "market_structure": [
            {
                "id": "sample_9",
                "text": "行业研究报告指出，B2B SaaS市场在过去一年增长了32%，其中协作工具细分领域占比提升至28%。",
                "dimension": "market_structure",
                "desc": "市场结构变化样本"
            },
            {
                "id": "sample_10",
                "text": "最新统计显示，企业数字化转型加速，预计未来三年市场规模将达到1.2万亿，年复合增长率18%。",
                "dimension": "market_structure",
                "desc": "市场规模变化样本"
            }
        ],
        "tech_ecosystem": [
            {
                "id": "sample_11",
                "text": "AWS发布新版本API，不再支持我们当前使用的认证协议，必须在下个季度前完成技术栈迁移。",
                "dimension": "tech_ecosystem",
                "desc": "技术生态变化样本"
            },
            {
                "id": "sample_12",
                "text": "OpenAI更新了GPT-4 API的使用限制，对我们当前的技术架构产生直接影响，需要调整实施方案。",
                "dimension": "tech_ecosystem",
                "desc": "API生态变化样本"
            }
        ]
    }

    # 构建合成样本
    for dimension, samples_for_dim in dimension_samples.items():
        for i, sample in enumerate(samples_for_dim):
            samples.append(SyntheticEvidence(
                id=f"c3_probe_{dimension}_{i+1}",
                evidence_text=sample["text"],
                true_dimension=dimension,
                expected_annotation=dimension,
                description=sample["desc"]
            ))

    return samples


def run_annotation_test(evidence_samples: List[SyntheticEvidence], model_client) -> Dict:
    """
    运行标注测试，模拟模型对合成证据的维度标注

    Args:
        evidence_samples: 合成证据样本列表
        model_client: 语言模型客户端

    Returns:
        包含测试结果的字典
    """
    results = {
        "total_samples": len(evidence_samples),
        "correct_annotations": 0,
        "incorrect_annotations": 0,
        "errors": [],
        "details": []
    }

    for sample in evidence_samples:
        try:
            # 模拟调用模型进行维度标注
            # 注意：这里的提示工程应该使用更新后的维度定义和消歧指令
            prompt = f"""
            请分析以下反证文本，并选择最适合的维度标签。

            反证文本：
            {sample.evidence_text}

            维度标签定义（前提出处语义）：
            - competitor_pricing: 主张前提建立在竞品定价/价格对标数据上
            - regulatory_stance: 主张前提建立在监管政策/官方口径上
            - interview_reversal: 主张前提建立在访谈/纪要/口头口径上（机制维度）
            - cost_model: 主张前提建立在成本/费用结构测算上
            - market_structure: 主张前提建立在市场规模/格局/份额判断上
            - tech_ecosystem: 主张前提建立在技术栈/生态位判断上

            消歧指令：
            - 维度 = 本反证所攻击之主张前提的证据出处类型，不是反证内容的主题词
            - 判法：问「原主张凭什么为真？」——答所依赖的证据类型即维度
            - interview_reversal 是机制维度：凡证据出自访谈/纪要/口头口径，无论其内容谈的是定价、成本还是监管，一律填 interview_reversal

            请只回答维度标签名称（例如：cost_model 或 interview_reversal）：
            """

            # 模拟模型调用
            model_response = model_client.annotate_dimension(prompt)

            # 解析响应，确保是有效维度
            annotated_dimension = model_response.strip().lower()
            if annotated_dimension not in FOCUS_DIMENSIONS:
                # 如果模型输出无效，尝试从响应中提取关键词
                for dim in FOCUS_DIMENSIONS:
                    if dim in model_response.lower():
                        annotated_dimension = dim
                        break

            # 记录结果
            is_correct = annotated_dimension == sample.expected_annotation
            result_detail = {
                "sample_id": sample.id,
                "true_dimension": sample.true_dimension,
                "annotated_dimension": annotated_dimension,
                "expected_dimension": sample.expected_annotation,
                "is_correct": is_correct,
                "evidence_text": sample.evidence_text,
                "description": sample.description
            }

            results["details"].append(result_detail)

            if is_correct:
                results["correct_annotations"] += 1
            else:
                results["incorrect_annotations"] += 1

        except Exception as e:
            error_detail = {
                "sample_id": sample.id,
                "error": str(e),
                "evidence_text": sample.evidence_text
            }
            results["errors"].append(error_detail)
            results["incorrect_annotations"] += 1

    # 计算准确率
    if results["total_samples"] > 0:
        results["accuracy"] = results["correct_annotations"] / results["total_samples"]
    else:
        results["accuracy"] = 0.0

    return results


def print_results(results: Dict):
    """打印测试结果"""
    print("=" * 80)
    print("标注器探针测试结果")
    print("=" * 80)
    print(f"总样本数: {results['total_samples']}")
    print(f"正确标注: {results['correct_annotations']}")
    print(f"错误标注: {results['incorrect_annotations']}")
    print(f"准确率: {results['accuracy']:.2%}")
    print()

    if results['errors']:
        print(f"错误数: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  - {error['sample_id']}: {error['error']}")
        print()

    print("详细结果:")
    for detail in results['details']:
        status = "✓" if detail['is_correct'] else "✗"
        print(f"  {status} {detail['sample_id']}")
        print(f"    真实维度: {detail['true_dimension']}")
        print(f"    标注维度: {detail['annotated_dimension']}")
        print(f"    期望维度: {detail['expected_dimension']}")
        print(f"    说明: {detail['description']}")
        print()

    # 特别关注 c3 型机制-主题分离样本
    c3_samples = [d for d in results['details'] if 'c3型机制主题分离' in d['description']]
    if c3_samples:
        print("c3 型机制-主题分离样本特别分析:")
        for sample in c3_samples:
            print(f"  {sample['sample_id']}: {'通过' if sample['is_correct'] else '未通过'}")
            print(f"    描述: {sample['description']}")
            print()


def create_mock_model_client():
    """创建模拟模型客户端用于演示"""
    class MockModelClient:
        def annotate_dimension(self, prompt: str):
            # 简单的规则基础标注（实际使用时替换为真实的模型调用）
            # 模拟之前可能出现的混淆情况
            if "访谈" in prompt or "会议" in prompt or "CTO" in prompt or "CEO" in prompt:
                # 如果检测到访谈相关的词汇，正确标注为 interview_reversal
                return "interview_reversal"
            elif "竞品" in prompt or "对手" in prompt:
                return "competitor_pricing"
            elif "监管" in prompt or "银保监会" in prompt or "网信办" in prompt:
                return "regulatory_stance"
            elif "成本" in prompt or "费用" in prompt:
                return "cost_model"
            elif "市场" in prompt or "规模" in prompt:
                return "market_structure"
            elif "API" in prompt or "技术" in prompt or "生态" in prompt:
                return "tech_ecosystem"
            else:
                # 默认返回第一个维度
                return FOCUS_DIMENSIONS[0]

    return MockModelClient()


def main():
    print("开始执行标注器探针测试...")

    # 创建合成证据样本
    evidence_samples = create_synthetic_evidence_set()
    print(f"已创建 {len(evidence_samples)} 个合成反证样本")

    # 创建模型客户端（演示用，实际使用时替换为真实模型）
    model_client = create_mock_model_client()

    # 运行测试
    results = run_annotation_test(evidence_samples, model_client)

    # 打印结果
    print_results(results)

    # 检查是否通过测试（0 错误才算通过）
    if results['incorrect_annotations'] == 0:
        print("✅ 标注器探针测试通过！误标率为 0/12")
        return True
    else:
        print(f"❌ 标注器探针测试未通过！误标率为 {results['incorrect_annotations']}/12")
        return False


if __name__ == "__main__":
    main()