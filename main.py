"""
简单的 LangChain Agent 示例
流程：用户输入问题 → agent 思考 → 选择工具 → 执行工具 → 得出答案

ReAct 模式：Reasoning（推理）+ Acting（行动）交替进行，
每一步都先思考（Thought），再行动（Action），再观察结果（Observation）
"""

from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
import config


# ─────────────────────────────────────────────
# 工具定义
# @tool 装饰器会把普通函数注册为 agent 可调用的工具
# 函数的 docstring 非常重要：agent 靠它来判断什么时候该用这个工具
# ─────────────────────────────────────────────

@tool
def add(input: str) -> str:
    """计算两个整数之和。输入格式：两个数字用逗号分隔，例如 '18,25'"""
    # ReAct agent 的工具输入统一是字符串，需要手动解析
    parts: list = input.split(",")
    a: int = int(parts[0].strip())  # 取第一个数，strip() 去掉多余空格
    b: int = int(parts[1].strip())  # 取第二个数
    return str(a + b)               # 返回值也必须是字符串


@tool
def to_upper(text: str) -> str:
    """将文本转换为大写"""
    return text.upper()


# ─────────────────────────────────────────────
# 初始化 LLM
# ChatOpenAI 是对 OpenAI Chat 接口的封装，也兼容其他支持 OpenAI 格式的模型
# 配置项从 config.py 读取，避免硬编码敏感信息
# ─────────────────────────────────────────────
llm: ChatOpenAI = ChatOpenAI(
    model=config.MODEL,       # 模型名称，例如 gpt-4o-mini
    api_key=config.API_KEY,   # API 密钥
    base_url=config.BASE_URL, # 接口地址，可替换为第三方代理
)

# 将所有工具放入列表，后续传给 agent 和执行器
tools: list = [add, to_upper]


# ─────────────────────────────────────────────
# Prompt 模板
# ReAct agent 要求 prompt 中必须包含以下四个占位符：
#   {tools}          - 自动填入工具的名称和描述
#   {tool_names}     - 自动填入工具名称列表
#   {input}          - 用户的输入问题
#   {agent_scratchpad} - agent 的中间思考过程（自动填入，不需要手动传）
# ─────────────────────────────────────────────
prompt: PromptTemplate = PromptTemplate.from_template("""
你是一个智能助手，可以使用以下工具：

{tools}

请按照如下格式回答：

Question: 需要回答的问题
Thought: 思考要做什么
Action: 要使用的工具，必须是 [{tool_names}] 中的一个
Action Input: 工具的输入参数
Observation: 工具返回的结果
...（可以重复 Thought/Action/Action Input/Observation）
Thought: 我现在知道最终答案了
Final Answer: 对原始问题的最终答案

开始！

Question: {input}
Thought: {agent_scratchpad}
""")


# ─────────────────────────────────────────────
# 创建 agent 和执行器
# create_react_agent：把 llm + tools + prompt 组装成一个 ReAct agent
# AgentExecutor：驱动 agent 循环执行（思考→行动→观察），直到得出 Final Answer
#   verbose=True：打印每一步的中间过程，方便调试和学习
# ─────────────────────────────────────────────
agent = create_react_agent(llm, tools, prompt)

agent_executor: AgentExecutor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def main() -> None:
    # 调用 agent，传入用户问题
    # agent 会自动决定调用哪些工具、调用几次，最终返回答案
    result: dict = agent_executor.invoke({"input": "请帮我计算 18 + 25，然后把结果转成大写英文单词"})

    # result["output"] 是 agent 的最终答案
    print("最终结果：", result["output"])


if __name__ == "__main__":
    main()
