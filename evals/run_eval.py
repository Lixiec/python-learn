"""
Eval Harness 执行器 —— 自动化评估 agent 质量。

流程：
  遍历 cases.py 中的每条用例
    → 调用 agent（使用 mock 工具，不真实联网）
    → 检查工具调用是否符合预期（agent 有没有用对工具）
    → 检查输出是否包含期望关键词（答案对不对）
    → 打印每条结果（PASS / FAIL）
  最终打印汇总得分

为什么 eval 和 main.py 分开？
  eval 是独立的观测框架，agent 不需要为"被测试"做任何改动。
  每次修改 prompt、工具、模型后，跑一遍 eval 就知道有没有退步。

运行方式：
  python3 -m evals.run_eval
"""

import sys
import os

# 把项目根目录加入 Python 的模块搜索路径
# 因为 run_eval.py 在 evals/ 子目录里，默认找不到上层的 agent_executor_builder 等模块
# sys.path.insert(0, ...) 把根目录插到搜索路径最前面，优先从这里找模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent_executor_builder import build_agent_executor
from evals.cases import CASES  # 导入所有测试用例


def run_eval() -> None:
    # eval 时的特殊配置：
    #   mock_tools=True            → 不真实调用百度，用假数据，结果稳定
    #   return_intermediate_steps  → 返回工具调用记录，用来检查 agent 用了哪些工具
    #   enable_observability=False → 关闭日志追踪，eval 时不需要写日志文件
    agent_executor = build_agent_executor(
        return_intermediate_steps=True,
        enable_observability=False,
        mock_tools=True,
    )

    total: int = len(CASES)  # 用例总数
    passed: int = 0          # 通过的用例数

    print("=" * 60)
    print(f"开始评估，共 {total} 条用例")
    print("=" * 60)

    for case in CASES:
        case_id: str = case["id"]                        # 用例唯一标识，方便定位问题
        user_input: str = case["input"]                  # 发给 agent 的问题
        expected_tools: list = case["expected_tools"]    # 期望 agent 调用的工具名列表
        expected_keywords: list = case["expected_keywords"]  # 期望答案包含的关键词

        print(f"\n▶ [{case_id}] {user_input}")

        try:
            # 调用 agent，得到结果
            # result 是一个 dict，包含 "output"（最终答案）和 "intermediate_steps"（中间步骤）
            result: dict = agent_executor.invoke({"input": user_input})
            output: str = result.get("output", "")

            # intermediate_steps 的格式是：[(AgentAction, observation), ...]
            # AgentAction.tool 就是这一步调用的工具名
            # 这里把所有工具名提取出来，得到一个列表，如 ["add", "to_upper"]
            intermediate_steps: list = result.get("intermediate_steps", [])
            actual_tools: list = [step[0].tool for step in intermediate_steps]

            # ── 检查一：工具调用是否符合预期 ──────────────
            # all(...) 表示"所有条件都满足"
            # 即 expected_tools 里的每一个工具都必须出现在 actual_tools 里
            tools_ok: bool = all(t in actual_tools for t in expected_tools)

            # ── 检查二：输出是否包含期望关键词 ──────────────
            # any(...) 表示"至少满足一个条件"
            # 即 expected_keywords 里至少有一个关键词出现在输出里
            keywords_ok: bool = any(kw in output for kw in expected_keywords)

            # 两项检查都通过，才算这条用例 PASS
            case_passed: bool = tools_ok and keywords_ok

            if case_passed:
                passed += 1
                print(f"  ✅ PASS")
            else:
                print(f"  ❌ FAIL")

            # 打印详细信息，方便排查失败原因
            print(f"  工具调用: 期望={expected_tools}  实际={actual_tools}  {'✓' if tools_ok else '✗'}")
            print(f"  输出关键词: 期望含{expected_keywords}  {'✓' if keywords_ok else '✗'}")
            # 只打印前 100 个字符，避免输出太长
            print(f"  输出: {output[:100]}{'...' if len(output) > 100 else ''}")

        except Exception as e:
            # 捕获所有异常，确保一条用例出错不会导致整个评估崩溃
            # 出错的用例直接算 FAIL，继续跑下一条
            print(f"  💥 ERROR: {e}")

    # ── 汇总报告 ────────────────────────────────
    print("\n" + "=" * 60)
    # f-string 里的 :.1f 表示保留一位小数
    print(f"评估完成：{passed} / {total} 通过  得分：{passed / total * 100:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    run_eval()
