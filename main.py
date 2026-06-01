"""
入口文件，负责启动 agent 并运行一个问题。
工具和 agent 组装逻辑见 agent_executor_builder.py。
Guard 层在调用前后做安全检查。
"""

from agent_executor_builder import build_agent_executor
from guard.guard import input_guard, output_guard, FALLBACK_REPLY, GuardResult


def main() -> None:
    agent_executor = build_agent_executor(verbose=True)

    user_input: str = "帮我搜索一下 LangChain 是什么"

    # ── 输入护栏 ──
    in_result: GuardResult = input_guard(user_input)
    if not in_result.passed:
        print(f"🚫 输入被拦截：{in_result.reason}")
        print(FALLBACK_REPLY)
        return

    result: dict = agent_executor.invoke({"input": user_input})
    output: str = result["output"]

    # ── 输出护栏 ──
    out_result: GuardResult = output_guard(output)
    if not out_result.passed:
        print(f"🚫 输出被拦截：{out_result.reason}")
        print(FALLBACK_REPLY)
        return

    print("最终结果：", output)


if __name__ == "__main__":
    main()
