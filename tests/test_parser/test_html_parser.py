"""
测试HTML解析器 - 基于真实数据
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
        """测试表单字段解析 - 使用真实HTML"""
        fields = parser.parse_form_fields(sample_html_response)

        # 验证ASP.NET必需字段存在
        assert "__VIEWSTATE" in fields
        assert "__EVENTVALIDATION" in fields
        assert "__VIEWSTATEGENERATOR" in fields

        # 验证字段值不为空（真实数据）
        assert len(fields["__VIEWSTATE"]) > 100
        assert len(fields["__EVENTVALIDATION"]) > 100

    def test_parse_course_list(self, parser, sample_html_response):
        """测试课程列表解析 - 使用真实HTML"""
        courses = parser.parse_course_list(sample_html_response)

        # 真实数据有14门课程
        assert len(courses) == 14

        # 验证第一门课程（真实数据）
        assert courses[0].id == "62065"
        assert courses[0].name == "高中数学竞赛辅导"
        assert courses[0].teacher == "陈孝春"
        assert courses[0].category == "知识拓展"
        assert courses[0].credit == "2"

        # 验证报名按钮信息
        assert (
            courses[0].enroll_event_target
            == "ctl00$ContentPlaceHolder1$GridView1$ctl02$lk_delpxbq"
        )

        # 验证第二门课程
        assert courses[1].id == "1277277"
        assert courses[1].name == "数学文化漫谈"
        assert courses[1].teacher == "朱俊波"

    def test_check_enrollment_result_success(self, parser):
        """测试报名成功检测"""
        html = """
        <span id="ctl00_ContentPlaceHolder1_DataList1">
            <span id="ctl00_ContentPlaceHolder1_DataList1_ctl00_Label1">
                [高中数学竞赛辅导 高二(1-6)]陈孝春1班
            </span>
        </span>
        """
        status = parser.check_enrollment_result(html, "62065", "高中数学竞赛辅导")

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
        status = parser.check_enrollment_result(html, "62065", "高中数学竞赛辅导")

        assert status == EnrollmentStatus.FAILED

    def test_check_enrollment_result_empty(self, parser):
        """测试空已选列表"""
        html = '<span id="ctl00_ContentPlaceHolder1_DataList1"></span>'
        status = parser.check_enrollment_result(html, "62065", "高中数学竞赛辅导")

        assert status == EnrollmentStatus.FAILED

    def test_short_enrolled_name_does_not_create_false_success(self, parser):
        """已选课程名过短时不应反向包含误判成功。"""
        html = """
        <span id="ctl00_ContentPlaceHolder1_DataList1">
            <span id="ctl00_ContentPlaceHolder1_DataList1_ctl00_Label1">数学</span>
        </span>
        """

        status = parser.check_enrollment_result(html, "62065", "高中数学竞赛辅导")

        assert status == EnrollmentStatus.FAILED
