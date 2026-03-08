"""
Cookie管理模块

管理Cookie的加载和保存
"""

from typing import Optional
from pathlib import Path

from ..utils.logger import get_logger


class CookieManager:
    """
    Cookie管理器

    负责Cookie文件的读取和写入
    """

    DEFAULT_COOKIE_FILE = "cookies.txt"

    def __init__(self, file_path: Optional[str] = None) -> None:
        """
        初始化Cookie管理器

        Args:
            file_path: Cookie文件路径（可选，默认为cookies.txt）
        """
        self.file_path = file_path or self.DEFAULT_COOKIE_FILE
        self.logger = get_logger(__name__)

    def load(self) -> str:
        """
        从文件加载Cookie

        Returns:
            Cookie字符串
        """
        cookie_file = Path(self.file_path)

        if not cookie_file.exists():
            self.logger.warning(f"Cookie文件 {self.file_path} 不存在")
            return ""

        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = f.read().strip()

            self.logger.info(f"成功加载Cookie文件: {self.file_path}")
            return cookies

        except Exception as e:
            self.logger.error(f"读取Cookie文件失败: {e}")
            return ""

    def save(self, cookies: str) -> None:
        """
        保存Cookie到文件

        Args:
            cookies: Cookie字符串
        """
        cookie_file = Path(self.file_path)

        try:
            # 确保父目录存在
            cookie_file.parent.mkdir(parents=True, exist_ok=True)

            with open(cookie_file, 'w', encoding='utf-8') as f:
                f.write(cookies)

            self.logger.info(f"Cookie已保存到: {self.file_path}")

        except Exception as e:
            self.logger.error(f"保存Cookie文件失败: {e}")
            raise

    def exists(self) -> bool:
        """
        检查Cookie文件是否存在

        Returns:
            文件存在返回True，否则返回False
        """
        return Path(self.file_path).exists()
