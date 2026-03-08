"""
核心数据模型

定义课程选课系统的核心数据结构
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime


class EnrollmentStatus(Enum):
    """报名状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class Course:
    """
    课程数据模型

    Attributes:
        id: 课程唯一标识
        name: 课程名称
        category: 课程类别
        class_name: 教学班名称
        teacher: 授课教师
        credit: 学分
        schedule: 上课时间
        capacity: 容量
        enrolled: 已选人数
        remaining: 剩余名额
        onclick: onclick事件属性
        enroll_event_target: 报名按钮的EventTarget
        enroll_event_argument: 报名按钮的EventArgument
    """
    id: str
    name: str
    category: str = ""
    class_name: str = ""
    teacher: str = ""
    credit: str = ""
    schedule: str = ""
    capacity: str = ""
    enrolled: str = ""
    remaining: str = ""
    onclick: str = ""
    enroll_event_target: str = ""
    enroll_event_argument: str = ""

    def has_capacity(self) -> bool:
        """
        检查是否还有剩余容量

        Returns:
            如果剩余名额大于0返回True，否则返回False
        """
        try:
            return int(self.remaining) > 0
        except ValueError:
            return False

    def __str__(self) -> str:
        """返回课程的可读字符串表示"""
        return f"{self.name} (ID: {self.id}, 教师: {self.teacher}, 剩余: {self.remaining})"


@dataclass
class EnrollmentResult:
    """
    报名结果数据模型

    Attributes:
        course_id: 课程ID
        course_name: 课程名称
        status: 报名状态
        message: 结果消息
        timestamp: 时间戳
    """
    course_id: str
    course_name: str
    status: EnrollmentStatus
    message: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def is_success(self) -> bool:
        """检查是否报名成功"""
        return self.status == EnrollmentStatus.SUCCESS


@dataclass
class EnrollmentSummary:
    """
    报名结果汇总

    Attributes:
        success: 成功报名的课程列表
        failed: 报名失败的课程列表
        not_found: 未找到的课程列表
    """
    success: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    not_found: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        """返回总课程数"""
        return len(self.success) + len(self.failed) + len(self.not_found)

    def __str__(self) -> str:
        """返回汇总的可读字符串表示"""
        return (
            f"报名结果汇总: 成功 {len(self.success)} 门, "
            f"失败 {len(self.failed)} 门, "
            f"未找到 {len(self.not_found)} 门"
        )
