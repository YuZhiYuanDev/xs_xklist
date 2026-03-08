"""
浙江省普通高中选课管理系统 - 自动化选课程序

Usage:
    from course_selector import CourseSelector, ConfigManager

    config = ConfigManager().load()
    selector = CourseSelector(config.cookies)
    courses = selector.get_course_list()
"""

from .core.selector import CourseSelector
from .core.models import Course, EnrollmentResult, EnrollmentSummary, EnrollmentStatus
from .config.manager import ConfigManager, AppConfig
from .config.cookies import CookieManager
from .auth import browser_login, BrowserLogin, LoginResult

__version__ = "2.0.0"
__author__ = "Course Selector Team"

__all__ = [
    # Core
    "CourseSelector",
    "Course",
    "EnrollmentResult",
    "EnrollmentSummary",
    "EnrollmentStatus",
    # Config
    "ConfigManager",
    "AppConfig",
    "CookieManager",
    # Auth
    "browser_login",
    "BrowserLogin",
    "LoginResult",
]
