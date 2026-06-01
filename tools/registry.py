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
    # User-Agent 伪装成浏览器访问，否则百度会识别为爬虫并拒绝请求
    headers: dict = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }
    # 百度搜索的 URL，wd 参数就是搜索关键词
    url: str = f"https://www.baidu.com/s?wd={keyword}"

    # 发送 HTTP GET 请求，timeout=10 表示超过 10 秒没响应就报错，避免卡死
    response = requests.get(url, headers=headers, timeout=10)
    # 指定编码为 utf-8，防止中文乱码
    response.encoding = "utf-8"

    # 用 BeautifulSoup 解析 HTML，"html.parser" 是 Python 内置的解析器，不需要额外安装
    soup = BeautifulSoup(response.text, "html.parser")
    # get_text() 提取页面所有纯文字，去掉所有 HTML 标签
    all_text: str = soup.get_text()

    # 这些词出现在导航栏/广告里，对搜索结果没有意义，过滤掉
    skip_keywords: list = ["登录", "设置", "贴吧", "hao123", "网页", "图片", "视频", "换一换", "热搜榜"]
    lines: list = []
    seen: set = set()  # 用集合去重，同样的句子只保留一次

    for line in all_text.split("\n"):
        line = line.strip()  # 去掉行首行尾的空白字符
        # 过滤条件：长度在 15~150 之间（太短没意义，太长可能是广告）、未重复、不含导航词
        if (15 < len(line) < 150
                and line not in seen
                and not any(kw in line for kw in skip_keywords)):
            seen.add(line)
            lines.append(line)
        if len(lines) >= 10:  # 最多取 10 条，避免返回内容太长
            break

    # 用换行符拼接所有有效行；如果一条都没有，返回兜底提示
    return "\n".join(lines) if lines else "未找到搜索结果"


@tool
def minus(input: str) -> str:
    """计算两个整数之差。输入格式：两个数字用逗号分隔，例如 '18,25'"""
    parts: list = input.split(",")   # 用逗号切割，得到 ["18", "25"]
    a: int = int(parts[0].strip())   # 取第一个数并转成整数
    b: int = int(parts[1].strip())   # 取第二个数并转成整数
    return str(a - b)                # 结果转成字符串返回（工具返回值必须是字符串）


@tool
def add(input: str) -> str:
    """计算两个整数之和。输入格式：两个数字用逗号分隔，例如 '18,25'"""
    parts: list = input.split(",")   # 用逗号切割，得到 ["18", "25"]
    a: int = int(parts[0].strip())   # 取第一个数并转成整数
    b: int = int(parts[1].strip())   # 取第二个数并转成整数
    return str(a + b)                # 结果转成字符串返回


@tool
def to_upper(text: str) -> str:
    """将文本转换为大写"""
    # str.upper() 是 Python 内置方法，把所有字母转成大写
    return text.upper()


# ── Mock 工具（eval 专用）────────────────────

@tool
def baidu_search_mock(keyword: str) -> str:
    """在百度上搜索关键词，返回相关信息摘要。当需要查询实时信息或不知道答案时使用。"""
    # ⚠️ 这是 mock（假）版本，不会真正发网络请求
    # eval 时使用，目的是让测试结果稳定可重复，不受网络波动和百度页面变化影响

    # 预设的假数据库：key 是关键词，value 是固定返回的内容
    mock_db: dict = {
        "Python": "Python 是一种高级编程语言，由 Guido van Rossum 创建，广泛用于数据分析、人工智能、Web开发等领域。",
        "LangChain": "LangChain 是一个用于开发大语言模型应用的开源框架，提供工具链、记忆、agent 等能力。",
        "编程": "编程是指编写计算机程序的过程，常见编程语言有 Python、Java、C++ 等。",
    }

    # 模糊匹配：只要关键词里包含 mock_db 的某个 key，就返回对应的假数据
    # 例如：搜索 "Python 是什么" → 命中 "Python" → 返回对应假数据
    for key, value in mock_db.items():
        if key in keyword:
            print(f"🔧 [Mock] baidu_search mock 命中：'{key}'")
            return value

    # 没有命中任何预设数据时，返回一个通用的兜底假数据
    return f"Mock 搜索结果：关于 '{keyword}' 的相关信息，包含编程、语言、Python 等内容。"


# ── 注册表 ────────────────────────────────────

# 真实工具列表（生产环境使用，会真实调用百度等外部服务）
_REAL_TOOLS: list = [add, minus, to_upper, baidu_search]

# mock 工具列表（eval 时使用，baidu_search 替换为不联网的 mock 版本）
# add/minus/to_upper 是纯计算，不依赖外部服务，真实版和 mock 版一样
_MOCK_TOOLS: list = [add, minus, to_upper, baidu_search_mock]


def get_tools(mock: bool = False) -> list:
    """
    获取工具列表。

    参数：
      mock: True 时返回 mock 工具列表（用于 eval），False 时返回真实工具列表（用于生产）

    使用示例：
      tools = get_tools()          # 生产环境，真实调用百度
      tools = get_tools(mock=True) # eval 环境，返回假数据
    """
    if mock:
        print("🔧 [ToolRegistry] 使用 mock 工具列表")
        return _MOCK_TOOLS
    return _REAL_TOOLS
