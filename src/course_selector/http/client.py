"""
HTTP客户端模块

封装requests库，提供HTTP请求功能
"""

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse
import requests

from ..utils.logger import get_logger


@dataclass
class HttpResponse:
    """
    HTTP响应封装

    Attributes:
        status_code: HTTP状态码
        text: 响应文本内容
        headers: 响应头
        success: 是否成功（状态码200）
    """
    status_code: int
    text: str
    headers: dict[str, str]
    success: bool


class HttpClient:
    """
    HTTP请求客户端

    封装requests.Session，提供GET/POST方法和会话管理
    """

    # 默认请求头配置（从原代码迁移）
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    def __init__(
        self,
        cookies: str,
        base_url: str,
        timeout: int = 30
    ) -> None:
        """
        初始化HTTP客户端

        Args:
            cookies: Cookie字符串
            base_url: 基础URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.logger = get_logger(__name__)

        # 设置请求头
        self.headers = self.DEFAULT_HEADERS.copy()
        self.headers['Cookie'] = cookies
        self.headers['Host'] = self._extract_host(base_url)
        self.headers['Origin'] = base_url

    def get(
        self,
        path: str,
        headers: Optional[dict[str, str]] = None
    ) -> HttpResponse:
        """
        发送GET请求

        Args:
            path: 请求路径
            headers: 额外请求头（可选）

        Returns:
            HTTP响应对象

        Raises:
            requests.RequestException: 请求失败时抛出
        """
        url = f"{self.base_url}{path}"
        request_headers = self.headers.copy()

        # 移除Content-Type（GET请求不需要）
        request_headers.pop('Content-Type', None)

        # 合并额外请求头
        if headers:
            request_headers.update(headers)

        self.logger.info(f"GET请求: {url}")

        try:
            response = self.session.get(
                url,
                headers=request_headers,
                timeout=self.timeout
            )

            return HttpResponse(
                status_code=response.status_code,
                text=response.text,
                headers=dict(response.headers),
                success=response.status_code == 200
            )
        except requests.RequestException as e:
            self.logger.error(f"GET请求失败: {e}")
            raise

    def post(
        self,
        path: str,
        data: dict[str, str],
        headers: Optional[dict[str, str]] = None
    ) -> HttpResponse:
        """
        发送POST请求

        Args:
            path: 请求路径
            data: 表单数据
            headers: 额外请求头（可选）

        Returns:
            HTTP响应对象

        Raises:
            requests.RequestException: 请求失败时抛出
        """
        url = f"{self.base_url}{path}"
        request_headers = self.headers.copy()

        # 设置Content-Type
        request_headers['Content-Type'] = 'application/x-www-form-urlencoded'

        # 合并额外请求头
        if headers:
            request_headers.update(headers)

        self.logger.info(f"POST请求: {url}")

        try:
            response = self.session.post(
                url,
                headers=request_headers,
                data=data,
                timeout=self.timeout
            )

            return HttpResponse(
                status_code=response.status_code,
                text=response.text,
                headers=dict(response.headers),
                success=response.status_code == 200
            )
        except requests.RequestException as e:
            self.logger.error(f"POST请求失败: {e}")
            raise

    def update_cookies(self, cookies: str) -> None:
        """
        更新Cookie

        Args:
            cookies: 新的Cookie字符串
        """
        self.headers['Cookie'] = cookies
        self.logger.info("Cookie已更新")

    def _extract_host(self, url: str) -> str:
        """
        从URL中提取主机名

        Args:
            url: 完整URL

        Returns:
            主机名（包含端口）
        """
        parsed = urlparse(url)
        return parsed.netloc
