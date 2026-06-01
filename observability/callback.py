"""
Observability 模块 —— 追踪每次 agent 调用的完整链路。

实现方式：继承 LangChain 的 BaseCallbackHandler，
在 agent 运行的各个生命周期节点（开始/工具调用/结束/出错）自动触发回调，
把数据写入 JSONL 日志文件（每行一条 JSON，方便后续分析）。

JSONL 格式示例：
  {"run_id": "abc123", "input": "...", "tools_called": [...], "output": "...", "latency_ms": 1234, "error": null}
"""

import json
import time
import uuid
import os
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

# 日志文件路径
LOG_PATH: str = os.path.join(os.path.dirname(__file__), "runs.jsonl")


class ObservabilityCallback(BaseCallbackHandler):
    """
    LangChain 回调处理器。
    LangChain 在 agent 运行的每个关键节点都会调用对应的 on_* 方法，
    我们在这里收集数据，最终在 on_agent_finish 时写入日志。
    """

    def __init__(self) -> None:
        super().__init__()
        # 用 run_id 把一次完整对话的所有事件关联起来
        self.run_id: str = str(uuid.uuid4())[:8]
        self.start_time: float = 0.0
        self.input: str = ""
        self.output: str = ""
        self.tools_called: list = []   # 记录每次工具调用：[{"tool": ..., "input": ..., "output": ...}]
        self.error: str = ""

    def on_chain_start(self, serialized: dict, inputs: dict, **kwargs) -> None:
        """agent 链开始时触发，记录开始时间和用户输入"""
        # 只记录最顶层的 chain 启动（有 input 字段的那次）
        if "input" in inputs:
            self.start_time = time.time()
            self.input = inputs.get("input", "")

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs) -> None:
        """每次工具被调用前触发，记录工具名和输入"""
        tool_name: str = serialized.get("name", "unknown")
        # 先占位，output 等 on_tool_end 时填入
        self.tools_called.append({
            "tool": tool_name,
            "input": input_str,
            "output": None,
        })

    def on_tool_end(self, output: str, **kwargs) -> None:
        """工具执行完毕后触发，把输出填回最后一条工具记录"""
        if self.tools_called:
            self.tools_called[-1]["output"] = output

    def on_tool_error(self, error: Exception, **kwargs) -> None:
        """工具执行出错时触发"""
        if self.tools_called:
            self.tools_called[-1]["output"] = f"ERROR: {error}"
        self.error = str(error)

    def on_agent_finish(self, finish, **kwargs) -> None:
        """agent 得出最终答案时触发，写入日志"""
        self.output = finish.return_values.get("output", "")
        self._flush()

    def on_chain_error(self, error: Exception, **kwargs) -> None:
        """整个 chain 出错时触发"""
        self.error = str(error)
        self._flush()

    def _flush(self) -> None:
        """把本次运行的数据序列化成一行 JSON，追加写入日志文件"""
        latency_ms: int = int((time.time() - self.start_time) * 1000)

        record: dict = {
            "run_id":       self.run_id,
            "input":        self.input,
            "output":       self.output,
            "tools_called": self.tools_called,
            "latency_ms":   latency_ms,
            "error":        self.error or None,
        }

        # 追加写入，每行一条 JSON
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"\n📋 [Observability] run_id={self.run_id}  耗时={latency_ms}ms  "
              f"工具={[t['tool'] for t in self.tools_called]}  "
              f"{'❌ ' + self.error if self.error else '✅'}")
