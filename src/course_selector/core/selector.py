"""
选课控制器模块

协调HTTP、Parser模块完成选课功能
"""

from typing import Optional

from .models import Course, EnrollmentResult, EnrollmentStatus
from ..http.client import HttpClient
from ..parser.html_parser import HtmlParser
from ..utils.logger import get_logger


class CourseSelector:
    """
    选课控制器

    负责协调各模块完成课程查询和报名功能
    """

    def __init__(
        self,
        cookies: str,
        base_url: str = "https://xkglpt.zjedu.gov.cn"
    ) -> None:
        """
        初始化选课控制器

        Args:
            cookies: Cookie字符串
            base_url: 基础URL
        """
        self.base_url = base_url
        self.logger = get_logger(__name__)

        # 初始化依赖模块
        self.http_client = HttpClient(cookies, base_url)
        self.parser = HtmlParser()

        # 状态数据
        self._courses: list[Course] = []
        self._form_fields: dict[str, str] = {}

    @property
    def courses(self) -> list[Course]:
        """获取课程列表"""
        return self._courses

    @property
    def form_fields(self) -> dict[str, str]:
        """获取表单字段"""
        return self._form_fields

    def get_course_list(self) -> list[Course]:
        """
        获取可选课程列表

        Returns:
            课程列表
        """
        try:
            url = "/XS/xs_xklist.aspx"

            # 第一步: GET请求获取ASP.NET必需的隐藏字段
            # __VIEWSTATE, __EVENTVALIDATION 等是ASP.NET安全机制必需的
            # POST请求必须包含这些字段，否则服务器会拒绝请求
            self.logger.info("正在获取页面表单字段...")
            get_response = self.http_client.get(url)

            if not get_response.success:
                self.logger.error(f"GET请求失败，状态码: {get_response.status_code}")
                return []

            # 提取表单隐藏字段（__VIEWSTATE, __EVENTVALIDATION等）
            self._form_fields = self.parser.parse_form_fields(get_response.text)
            self.logger.info(f"获取到 {len(self._form_fields)} 个表单字段")

            # 第二步: POST查询请求获取课程列表
            post_data = self._form_fields.copy()

            # 添加查询参数
            post_data['ctl00$ContentPlaceHolder1$ddlXNXQ'] = '2025/2026下'  # 学年学期
            post_data['ctl00$ContentPlaceHolder1$ddlKCLX'] = ''  # 课程类型
            post_data['ctl00$ContentPlaceHolder1$ddlXQJ'] = ''  # 周几
            post_data['ctl00$ContentPlaceHolder1$ddlJC'] = ''  # 节次
            post_data['ctl00$ContentPlaceHolder1$btnQuery'] = '查询'  # 查询按钮

            # 清空事件参数
            post_data['__EVENTTARGET'] = ''
            post_data['__EVENTARGUMENT'] = ''

            self.logger.info("发送POST查询请求...")
            post_response = self.http_client.post(url, data=post_data)

            if not post_response.success:
                self.logger.error(f"POST请求失败，状态码: {post_response.status_code}")
                return []

            # 解析课程信息
            self._form_fields = self.parser.parse_form_fields(post_response.text)
            self._courses = self.parser.parse_course_list(post_response.text)

            self.logger.info(f"成功获取 {len(self._courses)} 门课程")
            return self._courses

        except Exception as e:
            self.logger.error(f"获取课程列表时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return []

    def enroll_course(self, course_id: str) -> EnrollmentResult:
        """
        报名指定课程

        Args:
            course_id: 课程ID

        Returns:
            报名结果
        """
        # 查找课程
        course = next((c for c in self._courses if c.id == course_id), None)
        if not course:
            self.logger.error(f"未找到课程 {course_id}")
            return EnrollmentResult(
                course_id=course_id,
                course_name="",
                status=EnrollmentStatus.FAILED,
                message="课程未找到"
            )

        # 检查是否有报名按钮信息
        if not course.enroll_event_target:
            self.logger.error(f"课程 {course_id} 没有找到报名按钮信息")
            return EnrollmentResult(
                course_id=course_id,
                course_name=course.name,
                status=EnrollmentStatus.FAILED,
                message="未找到报名按钮"
            )

        try:
            # 构建POST数据 - 使用__doPostBack机制
            enroll_data = self._form_fields.copy()

            # 设置事件参数
            enroll_data['__EVENTTARGET'] = course.enroll_event_target
            enroll_data['__EVENTARGUMENT'] = course.enroll_event_argument

            url = "/XS/xs_xklist.aspx"

            self.logger.info(
                f"正在报名课程: {course.name} (ID: {course_id})"
            )
            self.logger.info(
                f"使用 EventTarget: {course.enroll_event_target}, "
                f"EventArgument: {course.enroll_event_argument}"
            )

            response = self.http_client.post(url, data=enroll_data)

            if not response.success:
                self.logger.error(f"报名失败，状态码: {response.status_code}")
                return EnrollmentResult(
                    course_id=course_id,
                    course_name=course.name,
                    status=EnrollmentStatus.FAILED,
                    message=f"HTTP错误: {response.status_code}"
                )

            # 检查结果（传递课程名称进行更精确的验证）
            status = self.parser.check_enrollment_result(
                response.text, 
                course_id,
                course.name
            )

            # 更新表单字段
            self._form_fields = self.parser.parse_form_fields(response.text)

            # 确定消息
            message = "报名成功" if status == EnrollmentStatus.SUCCESS else "报名失败"

            return EnrollmentResult(
                course_id=course_id,
                course_name=course.name,
                status=status,
                message=message
            )

        except Exception as e:
            self.logger.error(f"报名课程 {course_id} 时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return EnrollmentResult(
                course_id=course_id,
                course_name=course.name,
                status=EnrollmentStatus.FAILED,
                message=str(e)
            )

