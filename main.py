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
import requests
from bs4 import BeautifulSoup
import config


# ─────────────────────────────────────────────
# 工具定义
# @tool 装饰器会把普通函数注册为 agent 可调用的工具
# 函数的 docstring 非常重要：agent 靠它来判断什么时候该用这个工具
# ─────────────────────────────────────────────

@tool
def baidu_search(keyword: str) -> str:
    """在百度上搜索关键词，返回相关信息摘要。当需要查询实时信息或不知道答案时使用。"""
    # 请求头，伪装成浏览器，否则百度会拒绝请求
    headers: dict = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }
    url: str = f"https://www.baidu.com/s?wd={keyword}"
    response = requests.get(url, headers=headers, timeout=10)
    response.encoding = "utf-8"

    # 解析 HTML，提取纯文字内容
    soup = BeautifulSoup(response.text, "html.parser")
    all_text: str = soup.get_text()

    # 过滤无意义的导航栏内容
    skip_keywords: list = ["登录", "设置", "贴吧", "hao123", "网页", "图片", "视频", "换一换", "热搜榜"]
    lines: list = []
    seen: set = set()  # 去重集合

    for line in all_text.split("\n"):
        line = line.strip()
        if (15 < len(line) < 150
                and line not in seen
                and not any(kw in line for kw in skip_keywords)):
            seen.add(line)
            lines.append(line)
        if len(lines) >= 10:
            break

    return "\n".join(lines) if lines else "未找到搜索结果"


@tool
def minus(input : str) -> str:
    """计算两个整数之差。输入格式：两个数字用逗号分割，例如'18.25'"""
    parts : list = input.split(",")
    a: int = int(parts[0].strip())
    b: int = int(parts[1].strip())
    return str(a - b)


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
tools: list = [add, to_upper, minus, baidu_search]


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
    result: dict = agent_executor.invoke({"input": "帮我搜索一下 LangChain 是什么"})

    # result["output"] 是 agent 的最终答案
    print("最终结果：", result["output"])


if __name__ == "__main__":
    main()
