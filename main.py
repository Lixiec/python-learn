"""
入口文件，负责启动 agent 并运行一个问题。
工具和 agent 组装逻辑见 agent_executor_builder.py。
"""

from agent_executor_builder import build_agent_executor


def main() -> None:
    # verbose=True：打印每一步的中间过程，方便学习和调试
    agent_executor = build_agent_executor(verbose=True)

    result: dict = agent_executor.invoke({"input": "帮我看一下，相亲市场中，大厂程序员的生态位如何"})
    print("最终结果：", result["output"])


if __name__ == "__main__":
    main()
