"""
agent 组装模块，供 main.py 和 evals/run_eval.py 共用。
把 llm + tools + prompt + executor 的构建逻辑集中在这里，
避免 main.py 和 eval 各自重复一份。
"""

from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from observability.callback import ObservabilityCallback
from prompts.manager import load_prompt
from tools.registry import get_tools
import config


def build_agent_executor(verbose: bool = False,
                         return_intermediate_steps: bool = False,
                         enable_observability: bool = True,
                         prompt_version: str = "v2",
                         mock_tools: bool = False) -> AgentExecutor:
    """
    构建并返回 AgentExecutor。

    参数：
      verbose:                   是否打印每步中间过程，默认关闭（eval 时不需要）
      return_intermediate_steps: 是否在结果中返回工具调用的中间步骤，eval 时需要开启
      enable_observability:      是否开启链路追踪，默认开启
      prompt_version:            使用哪个版本的 prompt，对应 prompts/{version}.yaml
      mock_tools:                是否使用 mock 工具（eval 时传 True，不真实调用外部服务）
    """
    llm: ChatOpenAI = ChatOpenAI(
        model=config.MODEL,
        api_key=config.API_KEY,
        base_url=config.BASE_URL,
    )

    # 从 registry 获取工具列表，mock 模式下不真实调用外部服务
    tools: list = get_tools(mock=mock_tools)

    # 从 YAML 文件加载 prompt
    prompt: PromptTemplate = load_prompt(prompt_version)

    agent = create_react_agent(llm, tools, prompt)

    # 如果开启可观测性，注入 callback
    callbacks: list = [ObservabilityCallback()] if enable_observability else []

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,
        return_intermediate_steps=return_intermediate_steps,
        callbacks=callbacks,
    )
