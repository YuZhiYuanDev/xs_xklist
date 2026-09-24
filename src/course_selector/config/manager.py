"""
配置管理模块

管理应用配置的加载和保存
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Any
import json
from pathlib import Path

from ..utils.logger import get_logger


@dataclass
class AppConfig:
    """
    应用配置

    Attributes:
        cookies: Cookie字符串
        semester: 学期
        request_interval: 请求间隔（秒）
        timeout: 请求超时时间（秒）
    """

    cookies: str = ""
    target_courses: list[str] = field(default_factory=list)
    semester: str = "2025/2026下"
    request_interval: float = 1.0
    timeout: int = 30


class ConfigManager:
    """
    配置管理器

    负责配置文件的加载、保存和访问
    """

    DEFAULT_CONFIG_PATH = "config.json"

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径（可选，默认为config.json）
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.logger = get_logger(__name__)
        self._config: Optional[AppConfig] = None

    def load(self) -> AppConfig:
        """
        加载配置

        Returns:
            应用配置对象
        """
        config_file = Path(self.config_path)

        if not config_file.exists():
            self.logger.warning(f"配置文件 {self.config_path} 不存在，使用默认配置")
            self._config = AppConfig()
            return self._config

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._config = AppConfig(
                cookies=data.get("cookies", ""),
                target_courses=data.get("target_courses", []),
                semester=data.get("semester", "2025/2026下"),
                request_interval=data.get("request_interval", 1.0),
                timeout=data.get("timeout", 30),
            )

            self.logger.info(f"成功加载配置文件: {self.config_path}")
            return self._config

        except json.JSONDecodeError as e:
            self.logger.error(f"配置文件格式错误: {e}")
            self._config = AppConfig()
            return self._config
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            self._config = AppConfig()
            return self._config

    def save(self, config: AppConfig) -> None:
        """
        保存配置

        Args:
            config: 应用配置对象
        """
        config_file = Path(self.config_path)

        try:
            # 确保父目录存在
            config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(asdict(config), f, indent=4, ensure_ascii=False)

            self.logger.info(f"配置已保存到: {self.config_path}")
            self._config = config

        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取单个配置项

        Args:
            key: 配置项名称
            default: 默认值

        Returns:
            配置项值
        """
        if self._config is None:
            self.load()

        return getattr(self._config, key, default)

    @property
    def config(self) -> AppConfig:
        """获取当前配置"""
        if self._config is None:
            self.load()
        assert self._config is not None
        return self._config
