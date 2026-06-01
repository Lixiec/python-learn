"""
Guard Layer —— 护栏层，在 agent 输入输出前后加校验。

职责：
  输入端（input_guard）：
    - 过滤敏感词
    - 检测 prompt injection 攻击（用户试图让 agent 忽略指令）
    - 输入过长截断

  输出端（output_guard）：
    - 检测输出是否为空
    - 检测输出是否包含敏感词
    - 返回标准化的 GuardResult，包含是否通过和原因

使用方式：
  在调用 agent 前调用 input_guard，在 agent 返回后调用 output_guard，
  任何一端不通过就直接返回兜底回复，不让结果透出。
"""


# ── 配置 ──────────────────────────────────────

# 敏感词列表（实际项目中可从配置文件或数据库加载）
SENSITIVE_WORDS: list = ["暴力", "色情", "赌博", "诈骗", "毒品"]

# prompt injection 特征词：用户试图改变 agent 行为
INJECTION_PATTERNS: list = [
    "忽略上面的指令",
    "忽略所有指令",
    "ignore previous",
    "ignore all instructions",
    "你现在是",
    "forget your instructions",
]

# 输入最大字符数
MAX_INPUT_LENGTH: int = 500


# ── 数据结构 ──────────────────────────────────

class GuardResult:
    """
    护栏检查结果。
    passed=True 表示通过，可以继续；passed=False 表示拦截，reason 说明原因。
    """

    def __init__(self, passed: bool, reason: str = "") -> None:
        self.passed: bool = passed
        self.reason: str = reason

    def __repr__(self) -> str:
        status: str = "✅ 通过" if self.passed else "🚫 拦截"
        return f"GuardResult({status}, reason='{self.reason}')"


# ── 输入护栏 ──────────────────────────────────

def input_guard(user_input: str) -> GuardResult:
    """
    对用户输入进行安全检查。

    检查顺序：
      1. 长度检查
      2. prompt injection 检查
      3. 敏感词检查
    """

    # 1. 长度检查
    if len(user_input) > MAX_INPUT_LENGTH:
        return GuardResult(
            passed=False,
            reason=f"输入过长（{len(user_input)} 字符），最大允许 {MAX_INPUT_LENGTH} 字符"
        )

    # 2. prompt injection 检查
    lower_input: str = user_input.lower()
    for pattern in INJECTION_PATTERNS:
        if pattern.lower() in lower_input:
            return GuardResult(
                passed=False,
                reason=f"检测到 prompt injection 攻击：'{pattern}'"
            )

    # 3. 敏感词检查
    for word in SENSITIVE_WORDS:
        if word in user_input:
            return GuardResult(
                passed=False,
                reason=f"输入包含敏感词：'{word}'"
            )

    return GuardResult(passed=True)


# ── 输出护栏 ──────────────────────────────────

def output_guard(output: str) -> GuardResult:
    """
    对 agent 输出进行安全检查。

    检查顺序：
      1. 空输出检查
      2. 敏感词检查
    """

    # 1. 空输出检查
    if not output or not output.strip():
        return GuardResult(passed=False, reason="输出为空")

    # 2. 敏感词检查
    for word in SENSITIVE_WORDS:
        if word in output:
            return GuardResult(
                passed=False,
                reason=f"输出包含敏感词：'{word}'"
            )

    return GuardResult(passed=True)


# ── 兜底回复 ──────────────────────────────────

# 被拦截时统一返回这句话，不暴露拦截原因给用户
FALLBACK_REPLY: str = "抱歉，我无法回答这个问题。"
