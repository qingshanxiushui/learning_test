"""算术题生成约束回归测试。

验证最小值/最大值对操作数与结果的约束：
- 加法/减法/乘法：操作数与结果都落在 [min_value, max_value]；
- 除法：商与除数落在范围内，被除数（b × quotient）按设计可超出范围；
- 范围过窄（max < 2*min）时加法/减法回退为除法，保证总能出题。
"""

from __future__ import annotations

import random

from app.models import MathSettings
from app.services.learning_service import LearningService


def _settings(min_value: int, max_value: int, operators: list[str]) -> MathSettings:
    return MathSettings(
        id="x",
        child_id="c",
        min_value=min_value,
        max_value=max_value,
        operators=operators,
        status=1,
        created_at="t",
        updated_at="t",
    )


def _probe(settings: MathSettings, rounds: int = 500) -> list[tuple[str, int, int, int]]:
    svc = LearningService.__new__(LearningService)
    bad = []
    for _ in range(rounds):
        q = svc._build_math_question("s", settings, 1, "t")
        a = q["content_snapshot"]["operand_a"]
        b = q["content_snapshot"]["operand_b"]
        result = int(q["correct_answer"])
        lo, hi = settings.min_value, settings.max_value
        if not (lo <= a <= hi and lo <= b <= hi and lo <= result <= hi):
            bad.append((q["question_stem"], a, b, result))
    return bad


def test_add_subtract_multiply_constrain_operands_and_result() -> None:
    """加法/减法/乘法的操作数与结果都必须落在 [min, max] 内。"""
    for min_value, max_value, operators in [
        (0, 20, ["add", "subtract", "multiply"]),
        (1, 10, ["add", "subtract", "multiply"]),
        (3, 10, ["add", "subtract", "multiply", "divide"]),
        (10, 20, ["add", "subtract", "multiply", "divide"]),
        (0, 1, ["add", "subtract", "multiply"]),
        (1, 1, ["add", "subtract", "multiply"]),
        (5, 9, ["add", "subtract", "multiply"]),
    ]:
        bad = _probe(_settings(min_value, max_value, operators))
        # 除法被除数按设计可超出范围，其余运算必须完全合规
        bad = [t for t in bad if " ÷ " not in t[0]]
        assert not bad, f"min={min_value} max={max_value} ops={operators}: {bad[:3]}"


def test_divide_constrains_divisor_and_quotient() -> None:
    """除法约束商与除数在范围内；被除数按设计可超出（否则退化为平凡题）。"""
    svc = LearningService.__new__(LearningService)
    settings = _settings(1, 10, ["divide"])
    for _ in range(200):
        q = svc._build_math_question("s", settings, 1, "t")
        b = q["content_snapshot"]["operand_b"]
        quotient = int(q["correct_answer"])
        assert 1 <= b <= 10
        assert 1 <= quotient <= 10
        # 被除数 = b × quotient，验证算式自洽
        assert b * quotient == int(q["question_stem"].split(" ÷ ")[0])


def test_narrow_range_falls_back_to_divide() -> None:
    """范围过窄（max < 2*min）时加法/减法回退为除法，不崩溃且恒出题。"""
    svc = LearningService.__new__(LearningService)
    for min_value, max_value in [(5, 7), (7, 7), (2, 3), (5, 9)]:
        settings = _settings(min_value, max_value, ["add", "subtract"])
        for _ in range(100):
            q = svc._build_math_question("s", settings, 1, "t")
            assert q["content_snapshot"]["operator"] == "divide"
            b = q["content_snapshot"]["operand_b"]
            quotient = int(q["correct_answer"])
            assert min_value <= b <= max_value
            assert min_value <= quotient <= max_value


def test_multiply_infeasible_falls_back_to_divide() -> None:
    """乘法无合法整除组合（min² > max）时回退为除法，不崩溃。"""
    svc = LearningService.__new__(LearningService)
    settings = _settings(2, 3, ["multiply"])
    for _ in range(100):
        q = svc._build_math_question("s", settings, 1, "t")
        assert q["content_snapshot"]["operator"] == "divide"
        b = q["content_snapshot"]["operand_b"]
        quotient = int(q["correct_answer"])
        assert 2 <= b <= 3
        assert 2 <= quotient <= 3


def test_generated_questions_are_deterministic_seedable() -> None:
    """同一种子生成相同的题目序列（可复现）。"""
    random.seed(42)
    svc = LearningService.__new__(LearningService)
    settings = _settings(1, 10, ["add", "subtract", "multiply", "divide"])
    first = [svc._build_math_question("s", settings, i, "t")["question_stem"] for i in range(10)]
    random.seed(42)
    second = [svc._build_math_question("s", settings, i, "t")["question_stem"] for i in range(10)]
    assert first == second
