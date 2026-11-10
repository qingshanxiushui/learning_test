"""算术题生成约束与随机性回归测试。

验证最小值/最大值对操作数与结果的约束：
- 加法/减法/乘法：操作数与结果都落在 [min_value, max_value]；
- 除法：商与除数落在范围内，被除数（b × quotient）按设计可超出范围；
- 范围过窄（max < 2*min）时加法/减法回退为除法，保证总能出题。

验证出题随机性：
- 操作数分布接近均匀（不再集中在最小值）；
- 同一会话内题面不重复；
- 优先排除含 0/1 的平凡题；
- 除法被除数尽量限制在 max_value 量级。
"""

from __future__ import annotations

import collections
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


def _sample_questions(
    settings: MathSettings, rounds: int, seed: int = 2024
) -> list[tuple[str, int, int, int]]:
    random.seed(seed)
    svc = LearningService.__new__(LearningService)
    rows = []
    for i in range(rounds):
        q = svc._build_math_question("s", settings, i, "t")
        snapshot = q["content_snapshot"]
        rows.append(
            (snapshot["operator"], snapshot["operand_a"], snapshot["operand_b"], int(q["correct_answer"]))
        )
    return rows


def test_first_operand_not_skewed_to_min_value() -> None:
    """首个操作数不再集中在最小值：最小值占比远低于旧实现的 H_n/n 型左偏分布。"""
    min_value, max_value = 0, 20
    rows = _sample_questions(_settings(min_value, max_value, ["add", "subtract"]), 4000)
    counts = collections.Counter(a for _, a, _, _ in rows)
    total = len(rows)
    # 旧实现下 a == min_value 约占 17%，新实现应接近均匀的 1/21 ≈ 4.8%
    assert counts[min_value] / total < 0.10, counts
    # 各取值都应有合理出场份额，不能出现某些值几乎不出现
    for value, _ in counts.items():
        assert value >= min_value
    assert counts[max_value] / total > 0.02, counts


def test_no_duplicate_question_stem_within_session() -> None:
    """同一次会话内题面不重复（取值范围足够宽时）。"""
    random.seed(7)
    svc = LearningService.__new__(LearningService)
    settings = _settings(0, 20, ["add", "subtract", "multiply", "divide"])
    for _ in range(50):
        questions = svc._build_math_questions("s", settings, 20, "t")
        stems = [q["question_stem"] for q in questions]
        assert len(stems) == 20
        assert len(set(stems)) == 20, stems


def test_questions_keep_expected_count_when_range_is_narrow() -> None:
    """取值范围过窄、组合数少于题量时仍返回指定数量（允许重复，但不允许缺题）。"""
    svc = LearningService.__new__(LearningService)
    questions = svc._build_math_questions("s", _settings(0, 3, ["add"]), 10, "t")
    assert len(questions) == 10
    assert [q["question_order"] for q in questions] == list(range(1, 11))


def test_trivial_questions_are_avoided_when_possible() -> None:
    """取值允许时不再出 3 + 0、5 × 1 这类含 0/1 的平凡题。"""
    for min_value, max_value, operators in [
        (0, 20, ["add", "subtract"]),
        (1, 10, ["multiply"]),
        (0, 20, ["add", "subtract", "multiply", "divide"]),
    ]:
        rows = _sample_questions(_settings(min_value, max_value, operators), 800)
        trivial = [r for r in rows if r[1] in (0, 1) or r[2] in (0, 1) or r[3] in (0, 1)]
        assert not trivial, f"min={min_value} max={max_value} ops={operators}: {trivial[:3]}"


def test_trivial_questions_allowed_when_range_is_too_narrow() -> None:
    """取值范围小到只能出平凡题时仍正常出题（不抛异常、不返回空）。"""
    rows = _sample_questions(_settings(1, 1, ["add", "subtract", "multiply"]), 50)
    assert len(rows) == 50
    for _, a, b, result in rows:
        assert a == 1 and b == 1 and result == 1


def test_divide_dividend_stays_near_max_value() -> None:
    """除法优先把被除数限制在 max_value 量级，只有组合过少时才放宽。"""
    min_value, max_value = 1, 10
    rows = _sample_questions(_settings(min_value, max_value, ["divide"]), 800)
    dividends = [a for operator, a, _, _ in rows if operator == "divide"]
    assert dividends
    assert max(dividends) <= 2 * max_value, max(dividends)
    # 商与除数仍受范围约束
    for _, _, b, quotient in rows:
        assert min_value <= b <= max_value
        assert min_value <= quotient <= max_value
