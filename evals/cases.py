"""
测试用例定义
每条用例包含：
  - id:             用例唯一标识
  - input:          发给 agent 的问题
  - expected_tools: 期望 agent 调用的工具名列表（顺序不限）
  - expected_keywords: 期望最终答案中包含的关键词（至少命中一个即通过）
"""

# 每条用例是一个 dict，所有用例放在列表里
CASES: list = [
    {
        "id": "math_add",
        "input": "帮我计算 10 + 20",
        "expected_tools": ["add"],
        "expected_keywords": ["30"],
    },
    {
        "id": "math_minus",
        "input": "帮我计算 50 减 18",
        "expected_tools": ["minus"],
        "expected_keywords": ["32"],
    },
    {
        "id": "text_upper",
        "input": "把 hello world 转成大写",
        "expected_tools": ["to_upper"],
        "expected_keywords": ["HELLO WORLD"],
    },
    {
        "id": "search_basic",
        "input": "帮我搜索一下 Python 是什么",
        "expected_tools": ["baidu_search_mock"],
        "expected_keywords": ["编程", "语言", "Python"],
    },
    {
        "id": "multi_step",
        "input": "帮我计算 6 + 7，然后把结果转成大写英文单词",
        "expected_tools": ["add", "to_upper"],
        "expected_keywords": ["THIRTEEN"],
    },
]
