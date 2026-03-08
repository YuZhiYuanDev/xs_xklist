"""
测试数据模型 - 基于真实数据
"""

import pytest
from course_selector.core.models import (
    Course,
    EnrollmentResult,
    EnrollmentSummary,
    EnrollmentStatus
)


class TestCourse:
    """测试Course类"""

    def test_course_creation(self, sample_course_data):
        """测试课程创建 - 使用真实数据"""
        course = Course(**sample_course_data)
        
        # 验证真实数据的字段
        assert course.id == '62065'
        assert course.name == '高中数学竞赛辅导'
        assert course.category == '知识拓展'
        assert course.teacher == '陈孝春'
        assert course.credit == '2'
        assert course.schedule == '四8,四9'
        assert course.enroll_event_target == 'ctl00$ContentPlaceHolder1$GridView1$ctl02$lk_delpxbq'

    def test_course_has_capacity_true(self, sample_course):
        """测试课程有剩余容量"""
        # 真实数据: remaining='32'
        assert sample_course.has_capacity() is True

    def test_course_has_capacity_false(self):
        """测试课程无剩余容量"""
        course = Course(
            id='123',
            name='测试课程',
            remaining='0'
        )
        assert course.has_capacity() is False

    def test_course_has_capacity_invalid(self):
        """测试课程剩余容量无效"""
        course = Course(
            id='123',
            name='测试课程',
            remaining='N/A'
        )
        assert course.has_capacity() is False

    def test_course_str(self, sample_course):
        """测试课程字符串表示"""
        course_str = str(sample_course)
        # 使用真实数据的课程名称
        assert '高中数学竞赛辅导' in course_str
        assert '62065' in course_str
        assert '陈孝春' in course_str


class TestEnrollmentResult:
    """测试EnrollmentResult类"""

    def test_enrollment_result_creation(self):
        """测试报名结果创建"""
        result = EnrollmentResult(
            course_id='62065',
            course_name='高中数学竞赛辅导',
            status=EnrollmentStatus.SUCCESS,
            message='报名成功'
        )

        assert result.course_id == '62065'
        assert result.course_name == '高中数学竞赛辅导'
        assert result.status == EnrollmentStatus.SUCCESS
        assert result.message == '报名成功'
        assert result.timestamp is not None

    def test_is_success_true(self):
        """测试报名成功判断"""
        result = EnrollmentResult(
            course_id='62065',
            course_name='高中数学竞赛辅导',
            status=EnrollmentStatus.SUCCESS
        )
        assert result.is_success() is True

    def test_is_success_false(self):
        """测试报名失败判断"""
        result = EnrollmentResult(
            course_id='62065',
            course_name='高中数学竞赛辅导',
            status=EnrollmentStatus.FAILED
        )
        assert result.is_success() is False


class TestEnrollmentSummary:
    """测试EnrollmentSummary类"""

    def test_summary_creation(self):
        """测试报名汇总创建"""
        summary = EnrollmentSummary(
            success=['高中数学竞赛辅导'],
            failed=['数学文化漫谈'],
            not_found=['物理实验']
        )

        assert len(summary.success) == 1
        assert len(summary.failed) == 1
        assert len(summary.not_found) == 1

    def test_summary_total(self):
        """测试总数计算"""
        summary = EnrollmentSummary(
            success=['高中数学竞赛辅导', '数学文化漫谈'],
            failed=['新概念英语的欣赏'],
            not_found=['物理实验']
        )

        assert summary.total == 4

    def test_summary_str(self):
        """测试汇总字符串表示"""
        summary = EnrollmentSummary(
            success=['高中数学竞赛辅导'],
            failed=['数学文化漫谈'],
            not_found=['物理实验']
        )

        summary_str = str(summary)
        assert '成功 1' in summary_str
        assert '失败 1' in summary_str
        assert '未找到 1' in summary_str
