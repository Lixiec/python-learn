"""
Tool Registry —— 工具注册中心。

职责：
  - 集中管理所有工具的注册与发现
  - 支持 mock 模式：eval 时注入假数据，不真实调用外部服务
  - builder 通过 get_tools(mock=False) 获取工具列表，不直接引用工具函数

mock 模式的意义：
  真实的 baidu_search 依赖网络，每次结果不同，
  eval 时用 mock 返回固定数据，让测试结果稳定可重复。
"""

from langchain_core.tools import tool
import requests
from bs4 import BeautifulSoup


# ── 真实工具 ──────────────────────────────────

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


# ── Mock 工具（eval 专用）────────────────────

@tool
def baidu_search_mock(keyword: str) -> str:
    """在百度上搜索关键词，返回相关信息摘要。当需要查询实时信息或不知道答案时使用。"""
    # 根据关键词返回固定的假数据，不真实发网络请求
    # 这样 eval 结果稳定，不受网络和百度页面变化影响
    mock_db: dict = {
        "Python": "Python 是一种高级编程语言，由 Guido van Rossum 创建，广泛用于数据分析、人工智能、Web开发等领域。",
        "LangChain": "LangChain 是一个用于开发大语言模型应用的开源框架，提供工具链、记忆、agent 等能力。",
        "编程": "编程是指编写计算机程序的过程，常见编程语言有 Python、Java、C++ 等。",
    }
    # 模糊匹配：关键词包含 mock_db 中的任意 key 就返回对应数据
    for key, value in mock_db.items():
        if key in keyword:
            print(f"🔧 [Mock] baidu_search mock 命中：'{key}'")
            return value

    return f"Mock 搜索结果：关于 '{keyword}' 的相关信息，包含编程、语言、Python 等内容。"


# ── 注册表 ────────────────────────────────────

# 真实工具列表（生产环境使用）
_REAL_TOOLS: list = [add, minus, to_upper, baidu_search]

# mock 工具列表（eval 时使用，baidu_search 替换为 mock 版本）
_MOCK_TOOLS: list = [add, minus, to_upper, baidu_search_mock]


def get_tools(mock: bool = False) -> list:
    """
    获取工具列表。

    参数：
      mock: True 时返回 mock 工具列表（用于 eval），False 时返回真实工具列表
    """
    if mock:
        print("🔧 [ToolRegistry] 使用 mock 工具列表")
        return _MOCK_TOOLS
    return _REAL_TOOLS
