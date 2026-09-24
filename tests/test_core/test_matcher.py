"""课程匹配器测试。"""

from course_selector.core.matcher import CourseMatcher
from course_selector.core.models import Course


def test_empty_query_does_not_match_any_course():
    matcher = CourseMatcher()
    course = Course(id="1", name="高中数学", teacher="张老师")

    assert matcher.match("  ", [course]) == []


def test_course_name_can_produce_high_confidence_match():
    matcher = CourseMatcher()
    course = Course(id="1", name="高中数学", teacher="张老师")

    result = matcher.match_best("高中数学", [course], auto_confirm_threshold=80)

    assert result is not None
    assert result.score == 100
    assert result.confidence == "high"


def test_teacher_only_match_cannot_trigger_high_confidence():
    matcher = CourseMatcher()
    course = Course(id="1", name="高中数学", teacher="张老师")

    result = matcher.match_best(
        "张老师",
        [course],
        auto_confirm_threshold=80,
        confirm_threshold=50,
    )

    assert result is not None
    assert result.score < 80
    assert result.confidence == "medium"
