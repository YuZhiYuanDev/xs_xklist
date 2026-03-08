"""
测试HTML解析器
"""

import pytest
from course_selector.parser.html_parser import HtmlParser
from course_selector.core.models import EnrollmentStatus


class TestHtmlParser:
    """测试HtmlParser类"""

    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return HtmlParser()

    def test_parse_form_fields(self, parser, sample_html_response):
        """测试表单字段解析"""
        fields = parser.parse_form_fields(sample_html_response)

        assert '__VIEWSTATE' in fields
        assert '__EVENTVALIDATION' in fields
        assert fields['__VIEWSTATE'] == 'test_viewstate'

    def test_parse_course_list(self, parser, sample_html_response):
        """测试课程列表解析"""
        courses = parser.parse_course_list(sample_html_response)

        assert len(courses) == 1
        assert courses[0].id == '12345'
        assert courses[0].name == '高等数学'
        assert courses[0].teacher == '张老师'

    def test_check_enrollment_result_success(self, parser):
        """测试报名成功检测"""
        html = """
        <span id="ctl00_ContentPlaceHolder1_DataList1">
            <span id="ctl00_ContentPlaceHolder1_DataList1_ctl00_Label1">
                [高等数学 高二(1-6)]张老师1班
            </span>
        </span>
        """
        status = parser.check_enrollment_result(html, '123', '高等数学')

        assert status == EnrollmentStatus.SUCCESS

    def test_check_enrollment_result_failed(self, parser):
        """测试报名失败检测"""
        html = """
        <span id="ctl00_ContentPlaceHolder1_DataList1">
            <span id="ctl00_ContentPlaceHolder1_DataList1_ctl00_Label1">
                [其他课程 高二(1-6)]李老师1班
            </span>
        </span>
        """
        status = parser.check_enrollment_result(html, '123', '高等数学')

        assert status == EnrollmentStatus.FAILED

    def test_check_enrollment_result_empty(self, parser):
        """测试空已选列表"""
        html = '<span id="ctl00_ContentPlaceHolder1_DataList1"></span>'
        status = parser.check_enrollment_result(html, '123', '高等数学')

        assert status == EnrollmentStatus.FAILED
