"""
agent 组装模块，供 main.py 和 evals/run_eval.py 共用。

职责：把所有零件（llm、tools、prompt、observability）拼装成一个可以运行的 AgentExecutor。
其他文件只需调用 build_agent_executor()，不需要关心内部怎么组装的。

这是整个 harness 的"粘合层"：
  main.py        → build_agent_executor(verbose=True)
  run_eval.py    → build_agent_executor(mock_tools=True, return_intermediate_steps=True)
  两者用同一套代码，只是参数不同，保证 eval 和生产行为一致。
"""

from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from observability.callback import ObservabilityCallback  # 链路追踪
from prompts.manager import load_prompt                   # prompt 版本管理
from tools.registry import get_tools                      # 工具注册中心
import config                                             # API Key 等配置


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
    # 初始化大语言模型，所有配置从 config.py 读取
    llm: ChatOpenAI = ChatOpenAI(
        model=config.MODEL,
        api_key=config.API_KEY,
        base_url=config.BASE_URL,
    )

    # 从 registry 获取工具列表
    # mock=True 时返回假工具（eval 用），mock=False 时返回真实工具（生产用）
    tools: list = get_tools(mock=mock_tools)

    # 从 YAML 文件加载指定版本的 prompt
    # 这样改 prompt 不需要动 Python 代码，只改 YAML 文件即可
    prompt: PromptTemplate = load_prompt(prompt_version)

    # 把 llm + tools + prompt 组装成一个 ReAct agent
    # agent 负责"思考"：决定下一步调用哪个工具、传什么参数
    agent = create_react_agent(llm, tools, prompt)

    # callbacks 是 LangChain 的钩子机制，agent 运行时会自动调用里面的回调函数
    # ObservabilityCallback 利用这个机制来收集链路数据
    callbacks: list = [ObservabilityCallback()] if enable_observability else []

    # AgentExecutor 是真正的执行引擎：
    # 它循环驱动 agent（思考→调用工具→观察结果→再思考），直到得出最终答案
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,                                    # 是否打印中间过程
        return_intermediate_steps=return_intermediate_steps, # 是否在结果里附带工具调用记录
        callbacks=callbacks,                                # 注入可观测性回调
    )
