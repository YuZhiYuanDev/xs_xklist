"""快速抢课器测试。"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from course_selector.core.models import Course
from course_selector.core.snatcher import CourseSnatcher


def test_quick_check_updates_selector_state_and_uses_configured_semester():
    course = Course(id="1", name="高中数学")
    selector = MagicMock()
    selector.semester = "2026/2027上"
    selector._form_fields = {"__VIEWSTATE": "old"}
    selector._courses = []
    selector.http_client.post.return_value = SimpleNamespace(
        success=True,
        status_code=200,
        text="html",
    )
    selector.parser.parse_form_fields.return_value = {"__VIEWSTATE": "new"}
    selector.parser.parse_course_list.return_value = [course]

    snatcher = CourseSnatcher(selector, request_interval=0.01)
    courses = snatcher._quick_check_courses()

    assert courses == [course]
    assert selector._courses == [course]
    post_data = selector.http_client.post.call_args.kwargs["data"]
    assert post_data["ctl00$ContentPlaceHolder1$ddlXNXQ"] == "2026/2027上"
    assert snatcher.request_interval == 0.05


def test_empty_keyword_is_rejected_without_network_requests():
    selector = MagicMock()
    selector.semester = "2026/2027上"
    snatcher = CourseSnatcher(selector)

    result = snatcher.snatch_course("  ", datetime.now())

    assert result.success is False
    assert result.message == "课程关键词不能为空"
    selector.http_client.get.assert_not_called()
    selector.http_client.post.assert_not_called()
