"""
快速抢课模块

实现精确时间同步和快速抢课功能
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable
from dataclasses import dataclass
import ntplib
import socket

from ..utils.logger import get_logger


@dataclass
class SnatchResult:
    """
    抢课结果

    Attributes:
        success: 是否成功
        course_name: 课程名称
        message: 结果消息
        attempt_count: 尝试次数
        time_used: 耗时（秒）
    """
    success: bool
    course_name: str = ""
    message: str = ""
    attempt_count: int = 0
    time_used: float = 0.0


class TimeSync:
    """
    时间同步器

    使用NTP服务器获取精确的北京时间
    """

    # NTP服务器列表（按优先级排序）
    NTP_SERVERS = [
        "ntp.aliyun.com",       # 阿里云NTP
        "ntp.tencent.com",      # 腾讯云NTP
        "cn.ntp.org.cn",        # 中国NTP
        "time.windows.com",     # Windows时间服务器
        "pool.ntp.org",         # NTP池
    ]

    def __init__(self, timeout: float = 3.0):
        """
        初始化时间同步器

        Args:
            timeout: NTP请求超时时间（秒）
        """
        self.timeout = timeout
        self.logger = get_logger(__name__)
        self._offset: Optional[float] = None  # 本地时间与网络时间的偏移量
        self._last_sync_time: Optional[float] = None

    def sync(self) -> bool:
        """
        同步网络时间

        Returns:
            是否同步成功
        """
        ntp_client = ntplib.NTPClient()

        for server in self.NTP_SERVERS:
            try:
                self.logger.info(f"正在从 {server} 同步时间...")
                response = ntp_client.request(server, timeout=self.timeout)

                # 计算偏移量（网络时间 - 本地时间）
                self._offset = response.offset
                self._last_sync_time = time.time()

                network_time = datetime.fromtimestamp(response.tx_time)
                local_time = datetime.now()

                self.logger.info(f"时间同步成功!")
                self.logger.info(f"  网络时间: {network_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
                self.logger.info(f"  本地时间: {local_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
                self.logger.info(f"  偏移量: {self._offset * 1000:.2f} 毫秒")

                return True

            except (ntplib.NTPException, socket.timeout, socket.gaierror) as e:
                self.logger.warning(f"从 {server} 同步失败: {e}")
                continue
            except Exception as e:
                self.logger.warning(f"从 {server} 同步异常: {e}")
                continue

        self.logger.error("所有NTP服务器同步失败")
        return False

    def get_network_time(self) -> datetime:
        """
        获取精确的网络时间

        Returns:
            网络时间（北京时间）
        """
        if self._offset is None:
            # 如果没有同步过，返回本地时间
            return datetime.now()

        # 本地时间 + 偏移量 = 网络时间
        local_time = time.time()
        network_timestamp = local_time + self._offset
        return datetime.fromtimestamp(network_timestamp)

    def get_network_timestamp(self) -> float:
        """
        获取精确的网络时间戳

        Returns:
            网络时间戳（秒）
        """
        if self._offset is None:
            return time.time()

        return time.time() + self._offset

    @property
    def is_synced(self) -> bool:
        """是否已同步"""
        return self._offset is not None

    @property
    def offset_ms(self) -> float:
        """偏移量（毫秒）"""
        return self._offset * 1000 if self._offset else 0.0


class CourseSnatcher:
    """
    快速抢课器

    实现精确时间同步和快速抢课功能
    """

    def __init__(self, course_selector):
        """
        初始化抢课器

        Args:
            course_selector: CourseSelector实例
        """
        self.selector = course_selector
        self.logger = get_logger(__name__)
        self.time_sync = TimeSync()
        self._stop_flag = False
        self._snatch_thread: Optional[threading.Thread] = None

    def sync_time(self) -> bool:
        """
        同步网络时间

        Returns:
            是否同步成功
        """
        return self.time_sync.sync()

    def get_precise_time(self) -> datetime:
        """
        获取精确的网络时间

        Returns:
            网络时间
        """
        return self.time_sync.get_network_time()

    def wait_until(
        self,
        target_time: datetime,
        advance_seconds: float = 15.0,
        callback: Optional[Callable[[datetime, float], None]] = None
    ) -> bool:
        """
        等待到指定时间

        Args:
            target_time: 目标时间
            advance_seconds: 提前多少秒开始准备
            callback: 回调函数，用于显示等待进度

        Returns:
            是否正常到达目标时间
        """
        self._stop_flag = False

        while not self._stop_flag:
            current_time = self.get_precise_time()
            remaining = (target_time - current_time).total_seconds()

            if remaining <= 0:
                return True

            # 调用回调函数
            if callback:
                callback(current_time, remaining)

            # 根据剩余时间调整检查频率
            if remaining > 60:
                time.sleep(1.0)
            elif remaining > 30:
                time.sleep(0.5)
            elif remaining > 10:
                time.sleep(0.1)
            elif remaining > advance_seconds:
                time.sleep(0.05)
            else:
                # 最后阶段，高频检查
                time.sleep(0.01)

        return False

    def snatch_course(
        self,
        course_keyword: str,
        start_time: datetime,
        advance_seconds: float = 15.0,
        max_attempts: int = 1000
    ) -> SnatchResult:
        """
        快速抢课

        Args:
            course_keyword: 课程关键词
            start_time: 抢课开始时间
            advance_seconds: 提前多少秒开始准备
            max_attempts: 最大尝试次数

        Returns:
            抢课结果
        """
        self._stop_flag = False
        start_timestamp = time.time()

        # 1. 同步时间
        self.logger.info("=" * 60)
        self.logger.info("开始抢课流程")
        self.logger.info("=" * 60)

        if not self.time_sync.is_synced:
            self.logger.info("正在同步网络时间...")
            if not self.sync_time():
                self.logger.warning("时间同步失败，将使用本地时间")

        # 2. 预加载表单字段
        self.logger.info("正在预加载表单字段...")
        self._preload_form_fields()

        # 3. 等待到开始时间
        self.logger.info(f"目标抢课时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"将在开始前 {advance_seconds} 秒开始快速检测...")

        # 等待回调函数
        def wait_callback(current: datetime, remaining: float):
            if remaining > 60:
                if int(remaining) % 60 == 0:
                    self.logger.info(f"距离开始还有 {int(remaining)} 秒...")
            elif remaining > advance_seconds:
                if int(remaining) % 10 == 0:
                    self.logger.info(f"距离开始还有 {remaining:.1f} 秒")
            elif remaining > 0:
                self.logger.info(f"即将开始: {remaining:.2f} 秒")

        # 等待到开始时间
        self.logger.info("等待中...")
        if not self.wait_until(start_time, advance_seconds, wait_callback):
            return SnatchResult(
                success=False,
                message="抢课已取消",
                time_used=time.time() - start_timestamp
            )

        # 4. 开始快速抢课
        self.logger.info("=" * 60)
        self.logger.info("开始快速抢课!")
        self.logger.info("=" * 60)

        attempt_count = 0
        last_form_update = time.time()

        while attempt_count < max_attempts and not self._stop_flag:
            attempt_count += 1

            try:
                # 快速检测课程列表
                courses = self._quick_check_courses()

                if courses:
                    self.logger.info(f"检测到 {len(courses)} 门课程!")

                    # 查找目标课程
                    target_course = None
                    for course in courses:
                        if course_keyword.lower() in course.name.lower():
                            target_course = course
                            break

                    if target_course:
                        self.logger.info(f"找到目标课程: {target_course.name}")
                        self.logger.info(f"立即报名...")

                        # 立即报名
                        result = self.selector.enroll_course(target_course.id)

                        time_used = time.time() - start_timestamp

                        if result.is_success():
                            self.logger.info(f"抢课成功! 耗时: {time_used:.2f}秒")
                            return SnatchResult(
                                success=True,
                                course_name=target_course.name,
                                message="抢课成功",
                                attempt_count=attempt_count,
                                time_used=time_used
                            )
                        else:
                            self.logger.warning(f"报名失败: {result.message}")
                            # 继续尝试
                    else:
                        self.logger.debug(f"未找到目标课程，继续检测...")
                else:
                    # 每100次尝试输出一次
                    if attempt_count % 100 == 0:
                        self.logger.debug(f"已尝试 {attempt_count} 次，继续检测...")

                # 定期更新表单字段（每5秒）
                if time.time() - last_form_update > 5:
                    self._preload_form_fields()
                    last_form_update = time.time()

            except Exception as e:
                self.logger.debug(f"尝试 {attempt_count} 出错: {e}")
                # 出错不停止，继续尝试

        time_used = time.time() - start_timestamp
        return SnatchResult(
            success=False,
            course_name="",
            message=f"达到最大尝试次数 {max_attempts}，抢课失败",
            attempt_count=attempt_count,
            time_used=time_used
        )

    def _preload_form_fields(self) -> None:
        """预加载表单字段"""
        try:
            url = "/XS/xs_xklist.aspx"
            response = self.selector.http_client.get(url)
            if response.success:
                self.selector._form_fields = self.selector.parser.parse_form_fields(response.text)
                self.logger.debug(f"预加载了 {len(self.selector._form_fields)} 个表单字段")
        except Exception as e:
            self.logger.warning(f"预加载表单字段失败: {e}")

    def _quick_check_courses(self) -> list:
        """
        快速检测课程列表

        Returns:
            课程列表（如果有）
        """
        try:
            url = "/XS/xs_xklist.aspx"

            # 使用预加载的表单字段
            post_data = self.selector._form_fields.copy()

            # 添加查询参数
            post_data['ctl00$ContentPlaceHolder1$ddlXNXQ'] = '2025/2026下'
            post_data['ctl00$ContentPlaceHolder1$ddlKCLX'] = ''
            post_data['ctl00$ContentPlaceHolder1$ddlXQJ'] = ''
            post_data['ctl00$ContentPlaceHolder1$ddlJC'] = ''
            post_data['ctl00$ContentPlaceHolder1$btnQuery'] = '查询'
            post_data['__EVENTTARGET'] = ''
            post_data['__EVENTARGUMENT'] = ''

            response = self.selector.http_client.post(url, data=post_data)

            if response.success:
                # 更新表单字段
                self.selector._form_fields = self.selector.parser.parse_form_fields(response.text)
                # 解析课程列表
                courses = self.selector.parser.parse_course_list(response.text)
                return courses

        except Exception:
            pass

        return []

    def stop(self) -> None:
        """停止抢课"""
        self._stop_flag = True
        self.logger.info("正在停止抢课...")
