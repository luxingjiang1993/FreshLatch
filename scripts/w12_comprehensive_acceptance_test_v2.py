#!/usr/bin/env python3
"""
W12 Comprehensive Acceptance Test
验证系统是否达到了W12标准
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple
import subprocess
import sys

def test_memory_forensics_module():
    """测试W9-W12 MemoryForensics模块"""
    print("[TEST] Testing MemoryForensics module...")

    # 检查脚本是否存在
    script_path = "scripts/w9_w12_memory_forensics_demo.py"
    if not os.path.exists(script_path):
        print("[FAIL] MemoryForensics demo script not found")
        return False

    try:
        # 运行MemoryForensics演示
        result = subprocess.run([sys.executable, script_path],
                              capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print("[PASS] MemoryForensics demo executed successfully")

            # 检查是否有错误或异常
            output = result.stdout.lower()
            if "error" in output or "exception" in output or "traceback" in output:
                print("[FAIL] Errors found in MemoryForensics demo output")
                return False

            # 检查关键功能输出
            if "forensic" in output and "quarantine" in output:
                print("[PASS] MemoryForensics core functionality detected")
            else:
                print("[FAIL] Core MemoryForensics functionality not found in output")
                return False

        else:
            print(f"[FAIL] MemoryForensics demo failed with return code {result.returncode}")
            print(result.stderr)
            return False

        return True
    except subprocess.TimeoutExpired:
        print("[FAIL] MemoryForensics demo timed out")
        return False
    except Exception as e:
        print(f"[FAIL] Error running MemoryForensics demo: {str(e)}")
        return False

def test_system_integration():
    """测试系统整体集成"""
    print("\n[TEST] Testing system integration...")

    # 检查关键文件和模块是否存在
    critical_files = [
        "src/freshlatch/roles/forensic.py",
        "src/freshlatch/forensic_tools.py",
        "src/freshlatch/tools.py",
        "src/freshlatch/store/memory_store.py"
    ]

    missing_files = []
    for file in critical_files:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        print(f"[FAIL] Missing critical files: {missing_files}")
        return False
    else:
        print("[PASS] All critical files present")

    # 检查Forensic Agent是否正确集成到系统中
    try:
        # 导入关键模块
        import sys
        sys.path.insert(0, 'src')

        from freshlatch.roles.forensic import ForensicAgent
        from freshlatch.forensic_tools import create_forensic_tools
        print("[PASS] Forensic Agent modules import successfully")

        # 检查ForensicAgent类是否存在
        if hasattr(ForensicAgent, '__name__'):
            print("[PASS] ForensicAgent class defined correctly")
        else:
            print("[FAIL] ForensicAgent class not properly defined")
            return False

        # 检查Forensic工具创建函数
        if callable(create_forensic_tools):
            print("[PASS] Forensic tools creation function defined")
        else:
            print("[FAIL] Forensic tools creation function not properly defined")
            return False

        return True
    except ImportError as e:
        print(f"[FAIL] Import error: {str(e)}")
        return False
    except Exception as e:
        print(f"[FAIL] Error during system integration test: {str(e)}")
        return False

def test_database_schema():
    """测试数据库模式是否支持MemoryForensics"""
    print("\n[TEST] Testing database schema...")

    # 检查测试数据库是否存在
    db_path = "test_memory_forensics.db"
    if not os.path.exists(db_path):
        print(f"[FAIL] Database {db_path} not found")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查必需的表是否存在
        tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
        cursor.execute(tables_query)
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = ['long_term_memory', 'memory_flags', 'quarantine_proposals']
        missing_tables = [table for table in required_tables if table not in tables]

        if missing_tables:
            print(f"[FAIL] Missing required tables: {missing_tables}")
            conn.close()
            return False
        else:
            print("[PASS] All required MemoryForensics tables present")

        # 检查记忆数据
        cursor.execute("SELECT COUNT(*) FROM long_term_memory;")
        memory_count = cursor.fetchone()[0]
        print(f"[INFO] Found {memory_count} memory entries in database")

        # 检查flagged记忆
        cursor.execute("SELECT COUNT(*) FROM memory_flags;")
        flagged_count = cursor.fetchone()[0]
        print(f"[INFO] Found {flagged_count} flagged memories")

        conn.close()
        return True

    except Exception as e:
        print(f"[FAIL] Database schema test error: {str(e)}")
        return False

def test_product_positioning():
    """测试产品定位是否符合W12要求（不会被复述成错误形态）"""
    print("\n[TEST] Testing product positioning...")

    # 检查产品文档和说明
    context_file = "CONTEXT.md"
    if not os.path.exists(context_file):
        print(f"[FAIL] CONTEXT.md not found")
        return False

    try:
        with open(context_file, 'r', encoding='utf-8') as f:
            content = f.read().lower()

        # 检查关键概念是否正确表述
        if 'freshlatch' in content and '复验' in content:
            print("[PASS] Product positioning correctly defined")
        else:
            print("[FAIL] Product positioning not properly defined")
            return False

        # 检查是否避免了错误的产品定位
        negative_patterns = ['second evidenceos', 'ai search', 'industry gpt', 'memory plugin']
        found_negative = False
        for pattern in negative_patterns:
            if pattern.lower() in content:
                print(f"[WARN] Found potential negative pattern: {pattern}")
                found_negative = True

        if not found_negative:
            print("[PASS] No incorrect product positioning detected")
        else:
            print("[WARN] Some potentially incorrect positioning found, but not necessarily fatal")

        return True
    except Exception as e:
        print(f"[FAIL] Error checking product positioning: {str(e)}")
        return False

def test_acceptance_criteria():
    """测试W12验收标准的主要条件"""
    print("\n[TEST] Testing W12 acceptance criteria...")

    # W12停止条件：外部观察者不能把产品说成「AI 搜索」「行业 GPT」「卷宗换皮」或「记忆插件」
    # 这个测试需要模拟复述测试，我们可以通过检查系统是否具有清晰的独特价值来间接验证

    # 检查是否有清晰的复述测试记录
    restatement_file = "docs/evidence/w4/restatement.md"
    if os.path.exists(restatement_file):
        print("[PASS] W4 restatement test record exists")

        with open(restatement_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if '通过' in content or 'passed' in content.lower():
            print("[NOTE] restatement.md contains substring 通过; substring hit is not the restatement instrument. 判定层冒烟未愈")
        else:
            print("[WARN] W4 restatement test status unclear")
    else:
        print("[WARN] W4 restatement test record not found")

    # 检查MemoryForensics是否正确实现为核心可靠性模块而非主要功能
    readme_file = "docs/w9-w12-memory-forensics/README.md"
    if os.path.exists(readme_file):
        with open(readme_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if '可靠性模块' in content or 'reliability module' in content.lower():
            print("[PASS] MemoryForensics correctly positioned as reliability module")
        else:
            print("[WARN] MemoryForensics positioning unclear")

    return True

def test_memory_isolation():
    """测试记忆隔离功能"""
    print("\n[TEST] Testing memory isolation capabilities...")

    try:
        # 检查是否可以连接到数据库并查询隔离状态
        db_path = "test_memory_forensics.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查隔离提案表 - 查看实际的表结构
        cursor.execute("SELECT COUNT(*) FROM quarantine_proposals;")
        quarantine_count = cursor.fetchone()[0]
        print(f"[INFO] Total quarantine proposals: {quarantine_count}")

        # 检查是否有任何已确认的隔离
        cursor.execute("SELECT COUNT(*) FROM quarantine_proposals WHERE confirmed_at IS NOT NULL;")
        confirmed_count = cursor.fetchone()[0]
        print(f"[INFO] Confirmed quarantines: {confirmed_count}")

        conn.close()

        if quarantine_count > 0:
            print("[PASS] Memory isolation functionality active")
        else:
            print("[WARN] No quarantine proposals found (might be normal depending on test data)")

        return True
    except Exception as e:
        print(f"[FAIL] Memory isolation test error: {str(e)}")
        return False

def test_core_functionality():
    """测试核心功能是否正常工作"""
    print("\n[TEST] Testing core functionality...")

    # 测试能否加载ForensicAgent
    try:
        sys.path.insert(0, 'src')
        from freshlatch.roles.forensic import ForensicAgent
        print("[PASS] ForensicAgent class loads correctly")

        # 尝试实例化ForensicAgent（不运行，只是验证定义）
        # 注意：ForensicAgent可能需要参数，所以只是检查类是否存在
        agent_class = ForensicAgent
        print(f"[PASS] ForensicAgent class defined: {agent_class.__name__}")
        return True
    except Exception as e:
        print(f"[FAIL] Error testing core functionality: {str(e)}")
        return False

def run_comprehensive_test():
    """运行全面的W12验收测试"""
    print("="*60)
    print("RUNNING W12 COMPREHENSIVE ACCEPTANCE TEST")
    print("="*60)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    tests = [
        ("System Integration", test_system_integration),
        ("Database Schema", test_database_schema),
        ("Core Functionality", test_core_functionality),
        ("Memory Forensics Module", test_memory_forensics_module),
        ("Memory Isolation", test_memory_isolation),
        ("Product Positioning", test_product_positioning),
        ("Acceptance Criteria", test_acceptance_criteria),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"[FAIL] Error during {test_name}: {str(e)}")
            results[test_name] = False

    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)

    passed_tests = 0
    total_tests = len(tests)

    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
        if result:
            passed_tests += 1

    print("-"*60)
    print(f"Overall: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("\nDEMO-LAYER CHECKS GREEN (files/tables/import/demo script).")
        print("Not a W12 measurement close. 闸层可复现; 判定层冒烟未愈; K3 未执行; 2026-09-21 假绿对照不可引用")
        print("\nDemo-layer observations only:")
        print("- MemoryForensics files exist")
        print("- tables exist")
        print("- demo script can run")
        print("- substring checks are not the restatement instrument")

        print("\nSTOPPING CONDITION:")
        print("File/table/demo checks are not the blind restatement instrument.")
        print("判定层冒烟未愈. Do not print stopping condition as satisfied.")

    else:
        print(f"\n{total_tests - passed_tests} demo-layer checks failed")
        print("Demo-layer file/table checks incomplete; still not a W12 measurement")

        if passed_tests >= total_tests * 0.8:  # 文件/表检查通过率超过80%仍不得写成标准已满足
            print("\nOBSERVATION: most demo-layer checks green; still not W12 measurement.")
            print("判定层冒烟未愈; K3 未执行.")

    print("="*60)

    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)