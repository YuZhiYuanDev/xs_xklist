"""
认证模块

提供浏览器登录和Cookie获取功能
"""

from .browser_login import (
    BrowserLogin,
    LoginResult,
    LoginStatus,
    LoginConfig,
    browser_login
)

__all__ = [
    "BrowserLogin",
    "LoginResult",
    "LoginStatus",
    "LoginConfig",
    "browser_login"
]
