"""
agent 组装模块，供 main.py 和 evals/run_eval.py 共用。
把 llm + tools + prompt + executor 的构建逻辑集中在这里，
避免 main.py 和 eval 各自重复一份。
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
# ─────────────────────────────────────────────

@tool
def baidu_search(keyword: str) -> str:
    """在百度上搜索关键词，返回相关信息摘要。当需要查询实时信息或不知道答案时使用。"""
    headers: dict = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }
    url: str = f"https://www.baidu.com/s?wd={keyword}"
    response = requests.get(url, headers=headers, timeout=10)
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")
    all_text: str = soup.get_text()

    skip_keywords: list = ["登录", "设置", "贴吧", "hao123", "网页", "图片", "视频", "换一换", "热搜榜"]
    lines: list = []
    seen: set = set()

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
def minus(input: str) -> str:
    """计算两个整数之差。输入格式：两个数字用逗号分隔，例如 '18,25'"""
    parts: list = input.split(",")
    a: int = int(parts[0].strip())
    b: int = int(parts[1].strip())
    return str(a - b)


@tool
def add(input: str) -> str:
    """计算两个整数之和。输入格式：两个数字用逗号分隔，例如 '18,25'"""
    parts: list = input.split(",")
    a: int = int(parts[0].strip())
    b: int = int(parts[1].strip())
    return str(a + b)


@tool
def to_upper(text: str) -> str:
    """将文本转换为大写"""
    return text.upper()


# 所有可用工具的列表
ALL_TOOLS: list = [add, minus, to_upper, baidu_search]


# ─────────────────────────────────────────────
# ReAct Prompt 模板
# ─────────────────────────────────────────────
PROMPT: PromptTemplate = PromptTemplate.from_template("""
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


def build_agent_executor(verbose: bool = False,
                         return_intermediate_steps: bool = False) -> AgentExecutor:
    """
    构建并返回 AgentExecutor。

    参数：
      verbose:                   是否打印每步中间过程，默认关闭（eval 时不需要）
      return_intermediate_steps: 是否在结果中返回工具调用的中间步骤，eval 时需要开启
    """
    llm: ChatOpenAI = ChatOpenAI(
        model=config.MODEL,
        api_key=config.API_KEY,
        base_url=config.BASE_URL,
    )

    agent = create_react_agent(llm, ALL_TOOLS, PROMPT)

    return AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        verbose=verbose,
        return_intermediate_steps=return_intermediate_steps,
    )
