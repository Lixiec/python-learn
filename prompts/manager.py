"""
Prompt 管理模块：从 YAML 文件按版本号加载 PromptTemplate。

设计思路：
  - 每个版本对应 prompts/ 目录下的一个 YAML 文件
  - builder 通过 load_prompt(version) 加载，不直接硬编码 prompt 字符串
  - 这样修改 prompt 只需改 YAML，不需要动 Python 代码
  - 版本号记录在日志里，方便回溯"这次结果是用哪个 prompt 跑出来的"
"""

import os
import yaml
from langchain_core.prompts import PromptTemplate

# prompts/ 目录的绝对路径
PROMPTS_DIR: str = os.path.join(os.path.dirname(__file__))

# 默认使用的 prompt 版本
DEFAULT_VERSION: str = "v2"


def load_prompt(version: str = DEFAULT_VERSION) -> PromptTemplate:
    """
    按版本号加载 prompt。

    参数：
      version: prompt 版本号，对应 prompts/{version}.yaml

    返回：
      LangChain PromptTemplate 对象
    """
    file_path: str = os.path.join(PROMPTS_DIR, f"{version}.yaml")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Prompt 版本 '{version}' 不存在，文件路径：{file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data: dict = yaml.safe_load(f)

    template: str = data["template"]
    print(f"📝 [PromptManager] 加载 prompt {version}：{data.get('description', '')}")

    return PromptTemplate.from_template(template)
