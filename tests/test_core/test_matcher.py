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


def test_multiple_keywords_can_match_across_course_fields():
    matcher = CourseMatcher()
    course = Course(
        id="1",
        name="羽毛球-男生1.8.11.12班",
        teacher="吴培峰",
        class_name="羽毛球男生班",
    )

    result = matcher.match_best(
        "吴培峰 男生 羽毛球",
        [course],
        auto_confirm_threshold=80,
        confirm_threshold=50,
    )

    assert result is not None
    assert result.confidence == "high"
    assert result.score >= 80
    assert result.matched_fields == [
        "吴培峰→teacher",
        "男生→class_name",
        "羽毛球→class_name",
    ]


def test_multiple_keywords_use_and_semantics():
    matcher = CourseMatcher()
    course = Course(id="1", name="羽毛球-男生1.8.11.12班", teacher="吴培峰")

    assert matcher.match("吴培峰,男生,乒乓球", [course]) == []


def test_multiple_keywords_accept_common_separators():
    matcher = CourseMatcher()

    assert matcher._split_keywords("吴培峰，男生、羽毛球") == [
        "吴培峰",
        "男生",
        "羽毛球",
    ]
