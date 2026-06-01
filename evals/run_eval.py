"""
Eval Harness 执行器

流程：
  遍历 cases.py 中的每条用例
    → 调用 agent
    → 检查工具调用是否符合预期
    → 检查输出是否包含期望关键词
    → 输出每条结果
  最终打印汇总得分
"""

import sys
import os

# 把上层目录加入模块搜索路径，才能 import main.py 里的 agent_executor
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent_executor_builder import build_agent_executor
from evals.cases import CASES


def run_eval() -> None:
    # 构建 agent 执行器（开启中间步骤返回，用于检查工具调用）
    agent_executor = build_agent_executor(return_intermediate_steps=True)

    total: int = len(CASES)    # 用例总数
    passed: int = 0            # 通过数量

    print("=" * 60)
    print(f"开始评估，共 {total} 条用例")
    print("=" * 60)

    for case in CASES:
        case_id: str = case["id"]
        user_input: str = case["input"]
        expected_tools: list = case["expected_tools"]
        expected_keywords: list = case["expected_keywords"]

        print(f"\n▶ [{case_id}] {user_input}")

        try:
            # 调用 agent，return_intermediate_steps=True 时结果里会包含中间步骤
            result: dict = agent_executor.invoke({"input": user_input})
            output: str = result.get("output", "")

            # 从中间步骤里提取实际调用的工具名列表
            # intermediate_steps 格式：[(AgentAction, observation), ...]
            # AgentAction.tool 就是工具名
            intermediate_steps: list = result.get("intermediate_steps", [])
            actual_tools: list = [step[0].tool for step in intermediate_steps]

            # ── 检查一：工具调用是否符合预期 ──
            # 要求 expected_tools 里的每个工具都出现在实际调用中
            tools_ok: bool = all(t in actual_tools for t in expected_tools)

            # ── 检查二：输出是否包含期望关键词 ──
            # 至少命中一个关键词即视为通过
            keywords_ok: bool = any(kw in output for kw in expected_keywords)

            # 两项都通过才算整体通过
            case_passed: bool = tools_ok and keywords_ok

            if case_passed:
                passed += 1
                print(f"  ✅ PASS")
            else:
                print(f"  ❌ FAIL")

            # 打印详细信息方便排查
            print(f"  工具调用: 期望={expected_tools}  实际={actual_tools}  {'✓' if tools_ok else '✗'}")
            print(f"  输出关键词: 期望含{expected_keywords}  {'✓' if keywords_ok else '✗'}")
            print(f"  输出: {output[:100]}{'...' if len(output) > 100 else ''}")

        except Exception as e:
            # 捕获异常，避免一条用例失败导致整个评估中断
            print(f"  💥 ERROR: {e}")

    # 汇总报告
    print("\n" + "=" * 60)
    print(f"评估完成：{passed} / {total} 通过  得分：{passed / total * 100:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    run_eval()
