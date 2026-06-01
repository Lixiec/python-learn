from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
import config


# 定义一个工具：计算两个数之和
@tool
def add(a: int, b: int) -> int:
    """计算两个整数之和"""
    return a + b


# 定义一个工具：将字符串转为大写
@tool
def to_upper(text: str) -> str:
    """将文本转换为大写"""
    return text.upper()


# 初始化 LLM（从 config.py 读取配置）
llm: ChatOpenAI = ChatOpenAI(
    model=config.MODEL,
    api_key=config.API_KEY,
    base_url=config.BASE_URL,
)

# 注册工具列表
tools: list = [add, to_upper]

# 定义 prompt 模板（agent 必须包含 agent_scratchpad）
prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages([
    ("system", "你是一个智能助手，可以使用工具帮助用户完成任务。"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# 创建 agent
agent = create_tool_calling_agent(llm, tools, prompt)

# 创建 agent 执行器
agent_executor: AgentExecutor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def main() -> None:
    # 运行 agent
    result: dict = agent_executor.invoke({"input": "请帮我计算 18 + 25，然后把结果转成大写英文单词"})
    print("最终结果：", result["output"])


if __name__ == "__main__":
    main()
