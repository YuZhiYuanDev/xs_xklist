"""
测试数据模型
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
        """测试课程创建"""
        course = Course(**sample_course_data)

        assert course.id == '12345'
        assert course.name == '高等数学'
        assert course.category == '必修课'
        assert course.teacher == '张老师'
        assert course.credit == '4'

    def test_course_has_capacity_true(self, sample_course):
        """测试课程有剩余容量"""
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
        assert '高等数学' in course_str
        assert '12345' in course_str


class TestEnrollmentResult:
    """测试EnrollmentResult类"""

    def test_enrollment_result_creation(self):
        """测试报名结果创建"""
        result = EnrollmentResult(
            course_id='12345',
            course_name='高等数学',
            status=EnrollmentStatus.SUCCESS,
            message='报名成功'
        )

        assert result.course_id == '12345'
        assert result.course_name == '高等数学'
        assert result.status == EnrollmentStatus.SUCCESS
        assert result.message == '报名成功'
        assert result.timestamp is not None

    def test_is_success_true(self):
        """测试报名成功判断"""
        result = EnrollmentResult(
            course_id='123',
            course_name='测试',
            status=EnrollmentStatus.SUCCESS
        )
        assert result.is_success() is True

    def test_is_success_false(self):
        """测试报名失败判断"""
        result = EnrollmentResult(
            course_id='123',
            course_name='测试',
            status=EnrollmentStatus.FAILED
        )
        assert result.is_success() is False


class TestEnrollmentSummary:
    """测试EnrollmentSummary类"""

    def test_summary_creation(self):
        """测试报名汇总创建"""
        summary = EnrollmentSummary(
            success=['课程1'],
            failed=['课程2'],
            not_found=['课程3']
        )

        assert len(summary.success) == 1
        assert len(summary.failed) == 1
        assert len(summary.not_found) == 1

    def test_summary_total(self):
        """测试总数计算"""
        summary = EnrollmentSummary(
            success=['课程1', '课程2'],
            failed=['课程3'],
            not_found=['课程4']
        )

        assert summary.total == 4

    def test_summary_str(self):
        """测试汇总字符串表示"""
        summary = EnrollmentSummary(
            success=['课程1'],
            failed=['课程2'],
            not_found=['课程3']
        )

        summary_str = str(summary)
        assert '成功 1' in summary_str
        assert '失败 1' in summary_str
        assert '未找到 1' in summary_str
