"""
先单独测试百度搜索逻辑，确认能跑通后再集成到 agent
"""
import requests
from bs4 import BeautifulSoup


def baidu_search(keyword: str) -> str:
    # 请求头，伪装成浏览器，否则百度会拒绝请求
    headers: dict = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }

    # 百度搜索 URL，wd 参数是关键词
    url: str = f"https://www.baidu.com/s?wd={keyword}"

    # 发送 GET 请求
    response = requests.get(url, headers=headers, timeout=10)
    response.encoding = "utf-8"

    # 用 BeautifulSoup 解析 HTML，提取纯文字
    soup = BeautifulSoup(response.text, "html.parser")
    all_text: str = soup.get_text()

    # 按行分割，过滤掉太短或太长的行，以及导航栏等无意义内容
    skip_keywords: list = ["登录", "设置", "贴吧", "hao123", "网页", "图片", "视频", "换一换", "热搜榜"]
    lines: list = []
    seen: set = set()  # 用于去重

    for line in all_text.split("\n"):
        line = line.strip()
        # 过滤条件：长度合适、没重复、不包含导航关键词
        if (15 < len(line) < 150
                and line not in seen
                and not any(kw in line for kw in skip_keywords)):
            seen.add(line)
            lines.append(f"- {line}")
        if len(lines) >= 10:  # 最多返回 10 条
            break

    return "\n".join(lines) if lines else "未找到搜索结果"


# 直接运行测试
if __name__ == "__main__":
    result: str = baidu_search("Python 是什么")
    print(result)
