"""
入口文件 —— 程序从这里启动。

职责：
  1. 接收用户输入
  2. 用 input_guard 检查输入是否安全
  3. 调用 agent 处理问题
  4. 用 output_guard 检查输出是否安全
  5. 打印最终结果

注意：业务逻辑（工具、prompt、agent 组装）都在其他模块里，
main.py 只负责"串联流程"，保持简洁。
"""

from agent_executor_builder import build_agent_executor
from guard.guard import input_guard, output_guard, FALLBACK_REPLY, GuardResult


def main() -> None:
    # verbose=True：打印 agent 每一步的思考过程，方便学习调试
    agent_executor = build_agent_executor(verbose=True)

    user_input: str = "帮我搜索一下 LangChain 是什么"

    # ── 第一关：输入护栏 ──────────────────────
    # 在把用户输入送给 agent 之前，先做安全检查
    # 如果不通过（含敏感词、太长、prompt injection），直接返回兜底回复
    in_result: GuardResult = input_guard(user_input)
    if not in_result.passed:
        print(f"🚫 输入被拦截：{in_result.reason}")
        print(FALLBACK_REPLY)
        return  # 提前退出，不调用 agent

    # ── 调用 agent ────────────────────────────
    result: dict = agent_executor.invoke({"input": user_input})
    output: str = result["output"]  # agent 的最终回答

    # ── 第二关：输出护栏 ──────────────────────
    # agent 返回结果后，再检查一遍输出是否合规
    # 防止模型"绕过"输入检查，在输出里产生不合规内容
    out_result: GuardResult = output_guard(output)
    if not out_result.passed:
        print(f"🚫 输出被拦截：{out_result.reason}")
        print(FALLBACK_REPLY)
        return  # 不把不合规的输出展示给用户

    print("最终结果：", output)


if __name__ == "__main__":
    main()
