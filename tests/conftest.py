"""
Pytest配置和公共fixtures
"""

import pytest
from course_selector.core.models import Course, EnrollmentStatus


@pytest.fixture
def sample_course_data():
    """示例课程数据"""
    return {
        'id': '12345',
        'name': '高等数学',
        'category': '必修课',
        'class_name': '数学1班',
        'teacher': '张老师',
        'credit': '4',
        'schedule': '周一 1-2节',
        'capacity': '50',
        'enrolled': '45',
        'remaining': '5',
        'onclick': 'view_kc(12345)'
    }


@pytest.fixture
def sample_course(sample_course_data):
    """示例Course对象"""
    return Course(**sample_course_data)


@pytest.fixture
def sample_html_response():
    """示例HTML响应"""
    return """
    <html>
    <body>
        <form>
            <input type="hidden" name="__VIEWSTATE" value="test_viewstate" />
            <input type="hidden" name="__EVENTVALIDATION" value="test_validation" />
        </form>
        <table>
            <tr>
                <td>必修课</td>
                <td><a onclick="view_kc(12345)">高等数学</a></td>
                <td>数学1班</td>
                <td>张老师</td>
                <td>4</td>
                <td>周一 1-2节</td>
                <td>50</td>
                <td>45</td>
                <td>5</td>
                <td>操作</td>
            </tr>
        </table>
    </body>
    </html>
    """


@pytest.fixture
def sample_config_data():
    """示例配置数据"""
    return {
        'cookies': 'test_cookie_string',
        'target_courses': ['高等数学', '大学物理'],
        'semester': '2025/2026下',
        'request_interval': 1.0,
        'timeout': 30
    }
