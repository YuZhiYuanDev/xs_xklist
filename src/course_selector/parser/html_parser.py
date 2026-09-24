"""
HTML解析模块

解析HTML响应，提取表单字段、课程列表和报名结果
"""

import re
from typing import Optional
from bs4 import BeautifulSoup

from ..core.models import Course, EnrollmentStatus
from ..utils.logger import get_logger


class HtmlParser:
    """
    HTML内容解析器

    使用BeautifulSoup解析HTML，提取课程信息和表单数据
    """

    # 课程链接的正则模式
    COURSE_LINK_PATTERN = re.compile(r"view_kc\((\d+)\)")

    # 报名按钮的正则模式（ASP.NET __doPostBack）
    ENROLL_BUTTON_PATTERN = re.compile(r"__doPostBack\('([^']+)',?'([^']*)'\)")

    def __init__(self) -> None:
        """初始化HTML解析器"""
        self.logger = get_logger(__name__)

    def parse_form_fields(self, html: str) -> dict[str, str]:
        """
        解析HTML中的表单隐藏字段

        Args:
            html: HTML内容

        Returns:
            字段名到值的映射字典
        """
        soup = BeautifulSoup(html, "html.parser")
        form_fields = {}

        # 提取所有隐藏字段
        hidden_fields = soup.find_all("input", {"type": "hidden"})
        for field in hidden_fields:
            name = field.get("name")
            value = field.get("value", "")
            if name:
                form_fields[name] = value

        self.logger.info(f"提取到 {len(form_fields)} 个表单字段")
        return form_fields

    def parse_course_list(self, html: str) -> list[Course]:
        """
        解析课程列表

        Args:
            html: HTML内容

        Returns:
            课程列表
        """
        soup = BeautifulSoup(html, "html.parser")
        courses = []

        # 先提取所有报名按钮
        enroll_buttons = self.parse_enroll_buttons(html)

        # 查找所有包含view_kc函数的链接
        course_links = soup.find_all("a", onclick=self.COURSE_LINK_PATTERN)

        for link in course_links:
            course = self._parse_course_link(link)
            if course:
                # 添加报名按钮信息
                if course.id in enroll_buttons:
                    event_target, event_argument = enroll_buttons[course.id]
                    course.enroll_event_target = event_target
                    course.enroll_event_argument = event_argument

                courses.append(course)

        self.logger.info(f"解析到 {len(courses)} 门课程")
        return courses

    def check_enrollment_result(
        self, html: str, course_id: str, course_name: str = ""
    ) -> EnrollmentStatus:
        """
        检查报名结果

        Args:
            html: 响应HTML
            course_id: 课程ID
            course_name: 课程名称（用于验证）

        Returns:
            报名状态枚举值
        """
        # 检查已选课程列表
        enrolled_courses = self.parse_enrolled_courses(html)

        # 如果提供了课程名称，检查是否在已选列表中
        if course_name:
            for enrolled in enrolled_courses:
                # 检查课程名称是否匹配（支持部分匹配）
                if course_name.strip() and course_name.strip() in enrolled:
                    self.logger.info(
                        f"课程 {course_id} 报名成功: 已在已选列表中找到 '{enrolled}'"
                    )
                    return EnrollmentStatus.SUCCESS

        # 未在已选列表中找到
        self.logger.warning(f"课程 {course_id} 报名失败: 未在已选列表中找到")
        return EnrollmentStatus.FAILED

    def parse_enrolled_courses(self, html: str) -> list[str]:
        """
        解析已选课程列表

        Args:
            html: HTML内容

        Returns:
            已选课程名称列表
        """
        soup = BeautifulSoup(html, "html.parser")
        enrolled_courses = []

        # 查找DataList1控件（已选课程列表）
        datalist = soup.find("span", id="ctl00_ContentPlaceHolder1_DataList1")
        if datalist:
            # 查找所有Label控件
            labels = datalist.find_all(
                "span",
                id=re.compile(r"ctl00_ContentPlaceHolder1_DataList1_ctl\d+_Label1"),
            )
            for label in labels:
                course_text = label.get_text().strip()
                if course_text:
                    enrolled_courses.append(course_text)

        if enrolled_courses:
            self.logger.info(f"找到 {len(enrolled_courses)} 门已选课程")

        return enrolled_courses

    def parse_enroll_buttons(self, html: str) -> dict[str, tuple[str, str]]:
        """
        解析报名按钮信息

        Args:
            html: HTML内容

        Returns:
            课程ID到(eventTarget, eventArgument)的映射
        """
        soup = BeautifulSoup(html, "html.parser")
        enroll_buttons = {}

        # 查找所有包含__doPostBack的元素
        elements_with_postback = soup.find_all(
            lambda tag: tag.has_attr("href") and "__doPostBack" in tag.get("href", "")
        )

        for element in elements_with_postback:
            href = element.get("href", "")
            match = self.ENROLL_BUTTON_PATTERN.search(href)
            if match:
                event_target = match.group(1)
                event_argument = match.group(2) if match.group(2) else ""

                # 尝试从同一行提取课程ID
                tr = element.find_parent("tr")
                if tr:
                    # 查找课程链接
                    course_link = tr.find("a", onclick=self.COURSE_LINK_PATTERN)
                    if course_link:
                        onclick = course_link.get("onclick", "")
                        course_match = self.COURSE_LINK_PATTERN.search(onclick)
                        if course_match:
                            course_id = course_match.group(1)
                            enroll_buttons[course_id] = (event_target, event_argument)
                            self.logger.info(
                                f"找到课程 {course_id} 的报名按钮: "
                                f"eventTarget={event_target}, eventArgument={event_argument}"
                            )

        self.logger.info(f"找到 {len(enroll_buttons)} 个报名按钮")
        return enroll_buttons

    def _parse_course_link(self, link) -> Optional[Course]:
        """
        解析单个课程链接

        Args:
            link: BeautifulSoup的<a>标签对象

        Returns:
            Course对象，解析失败返回None
        """
        onclick = link.get("onclick", "")
        match = self.COURSE_LINK_PATTERN.search(onclick)
        if not match:
            return None

        course_id = match.group(1)
        course_name = link.get_text().strip()

        # 查找同一行中的所有信息
        parent_td = link.find_parent("td")
        if not parent_td:
            return Course(id=course_id, name=course_name, onclick=onclick)

        # 查找同一行的所有td
        tr = parent_td.find_parent("tr")
        if not tr:
            return Course(id=course_id, name=course_name, onclick=onclick)

        tds = tr.find_all("td")

        # 根据TD数量判断结构
        # 普通课程: 10个TD
        # 特殊课程(第一个): 13个TD
        if len(tds) == 10:
            # TD[0]: 课程类别
            # TD[1]: 课程名称
            # TD[2]: 班级名称
            # TD[3]: 教师
            # TD[4]: 学分
            # TD[5]: 上课时间
            # TD[6]: 容量
            # TD[7]: 已选
            # TD[8]: 剩余
            # TD[9]: 操作
            return Course(
                id=course_id,
                name=course_name,
                category=tds[0].get_text().strip(),
                class_name=tds[2].get_text().strip(),
                teacher=tds[3].get_text().strip(),
                credit=tds[4].get_text().strip(),
                schedule=tds[5].get_text().strip(),
                capacity=tds[6].get_text().strip(),
                enrolled=tds[7].get_text().strip(),
                remaining=tds[8].get_text().strip(),
                onclick=onclick,
            )
        elif len(tds) == 13:
            # TD[0-2]: 额外信息(时间范围等)
            # TD[3]: 课程类别
            # TD[4]: 课程名称
            # TD[5]: 班级名称
            # TD[6]: 教师
            # TD[7]: 学分
            # TD[8]: 上课时间
            # TD[9]: 容量
            # TD[10]: 已选
            # TD[11]: 剩余
            # TD[12]: 操作
            return Course(
                id=course_id,
                name=course_name,
                category=tds[3].get_text().strip(),
                class_name=tds[5].get_text().strip(),
                teacher=tds[6].get_text().strip(),
                credit=tds[7].get_text().strip(),
                schedule=tds[8].get_text().strip(),
                capacity=tds[9].get_text().strip(),
                enrolled=tds[10].get_text().strip(),
                remaining=tds[11].get_text().strip(),
                onclick=onclick,
            )
        else:
            # 未知结构，返回基本信息
            self.logger.warning(f"未知的表格结构，TD数量: {len(tds)}")
            return Course(id=course_id, name=course_name, onclick=onclick)
