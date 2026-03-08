"""
浏览器登录模块

通过Selenium WebDriver实现自动登录和Cookie提取
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ..utils.logger import get_logger


class LoginStatus(Enum):
    """登录状态枚举"""
    IDLE = "idle"              # 空闲
    WAITING = "waiting"        # 等待用户登录
    SUCCESS = "success"        # 登录成功
    TIMEOUT = "timeout"        # 登录超时
    CANCELLED = "cancelled"    # 用户取消
    ERROR = "error"            # 发生错误


@dataclass
class LoginResult:
    """
    登录结果数据模型

    Attributes:
        success: 是否登录成功
        cookies: Cookie字符串（成功时有效）
        message: 结果消息
        error_code: 错误码（失败时有效）
        login_time: 登录耗时（秒）
    """
    success: bool
    cookies: str = ""
    message: str = ""
    error_code: Optional[str] = None
    login_time: float = 0.0


@dataclass
class LoginConfig:
    """
    登录配置

    Attributes:
        login_url: 登录页面URL
        target_url: 登录成功后跳转的目标页面（选课系统）
        timeout: 超时时间（秒）
        auto_close: 成功后自动关闭浏览器
        browser: 浏览器类型（auto/chrome/firefox/edge）
    """
    login_url: str = "https://pjglpt.zjedu.gov.cn/logon.action"
    target_url: str = "https://xkglpt.zjedu.gov.cn/XS/xs_xklist.aspx"
    timeout: int = 300
    auto_close: bool = True
    browser: str = "auto"


class BrowserLogin:
    """
    浏览器登录管理器

    通过Selenium WebDriver打开浏览器，等待用户登录后自动提取Cookie
    """

    # 登录成功后Cookie中应包含的关键字段
    LOGIN_SUCCESS_INDICATORS = ["JSESSIONID", "ASP.NET_SessionId"]

    def __init__(
        self,
        login_url: str = "https://pjglpt.zjedu.gov.cn/logon.action",
        timeout: int = 300,
        auto_close: bool = True
    ) -> None:
        """
        初始化浏览器登录管理器

        Args:
            login_url: 登录页面URL
            timeout: 超时时间（秒）
            auto_close: 登录成功后是否自动关闭浏览器
        """
        self.config = LoginConfig(
            login_url=login_url,
            timeout=timeout,
            auto_close=auto_close
        )
        self.logger = get_logger(__name__)
        self._status = LoginStatus.IDLE
        self._driver = None
        self._start_time = 0.0
        self._cancelled = False

    @property
    def status(self) -> LoginStatus:
        """获取当前登录状态"""
        return self._status

    @property
    def is_running(self) -> bool:
        """是否正在登录"""
        return self._status == LoginStatus.WAITING

    def start_login(self) -> LoginResult:
        """
        启动浏览器登录流程

        Returns:
            LoginResult: 包含Cookie和状态的结果对象
        """
        self._start_time = time.time()
        self._cancelled = False

        try:
            # 初始化WebDriver
            self._status = LoginStatus.WAITING
            self.logger.info("正在初始化浏览器...")

            driver = self._init_webdriver()
            if driver is None:
                self._status = LoginStatus.ERROR
                return LoginResult(
                    success=False,
                    message="无法启动浏览器，请检查是否安装了Chrome浏览器",
                    error_code="BROWSER_INIT_FAILED",
                    login_time=time.time() - self._start_time
                )

            self._driver = driver

            # 打开登录页面
            self.logger.info(f"正在打开登录页面: {self.config.login_url}")
            driver.get(self.config.login_url)

            # 等待用户登录
            self.logger.info("请在浏览器中完成登录...")
            cookies = self._wait_for_login()

            login_time = time.time() - self._start_time

            if self._cancelled:
                self._status = LoginStatus.CANCELLED
                return LoginResult(
                    success=False,
                    message="登录已取消",
                    error_code="CANCELLED",
                    login_time=login_time
                )

            if cookies:
                self._status = LoginStatus.SUCCESS
                self.logger.info("登录成功！Cookie已获取")

                # 自动关闭浏览器
                if self.config.auto_close:
                    self._close_browser()

                return LoginResult(
                    success=True,
                    cookies=cookies,
                    message="登录成功",
                    login_time=login_time
                )
            else:
                self._status = LoginStatus.TIMEOUT
                self.logger.warning("登录超时")

                # 关闭浏览器
                self._close_browser()

                return LoginResult(
                    success=False,
                    message=f"登录超时（{self.config.timeout}秒），请重试",
                    error_code="TIMEOUT",
                    login_time=login_time
                )

        except Exception as e:
            self._status = LoginStatus.ERROR
            self.logger.error(f"登录过程发生错误: {e}")

            # 确保关闭浏览器
            self._close_browser()

            return LoginResult(
                success=False,
                message=f"登录失败: {str(e)}",
                error_code="ERROR",
                login_time=time.time() - self._start_time
            )

    def cancel(self) -> None:
        """取消登录"""
        self._cancelled = True
        self.logger.info("正在取消登录...")
        self._close_browser()

    def _detect_installed_browsers(self) -> list[str]:
        """
        检测系统中已安装的浏览器

        Returns:
            已安装浏览器列表，按优先级排序
        """
        import platform
        import os

        installed = []
        system = platform.system()

        if system == "Windows":
            # Windows下检测浏览器
            # Edge (Windows 10/11 默认)
            edge_paths = [
                os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
                os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
            ]
            for path in edge_paths:
                if os.path.exists(path):
                    installed.append("edge")
                    self.logger.info(f"检测到Edge浏览器: {path}")
                    break

            # Chrome
            chrome_paths = [
                os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            ]
            for path in chrome_paths:
                if os.path.exists(path):
                    installed.append("chrome")
                    self.logger.info(f"检测到Chrome浏览器: {path}")
                    break

            # Firefox
            firefox_paths = [
                os.path.expandvars(r"%ProgramFiles%\Mozilla Firefox\firefox.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe"),
            ]
            for path in firefox_paths:
                if os.path.exists(path):
                    installed.append("firefox")
                    self.logger.info(f"检测到Firefox浏览器: {path}")
                    break

        elif system == "Darwin":  # macOS
            # macOS下检测浏览器
            mac_paths = {
                "chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "edge": "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                "firefox": "/Applications/Firefox.app/Contents/MacOS/firefox",
            }
            for browser, path in mac_paths.items():
                if os.path.exists(path):
                    installed.append(browser)
                    self.logger.info(f"检测到{browser}浏览器: {path}")

        else:  # Linux
            # Linux下检测浏览器
            import shutil
            for browser in ["google-chrome", "chromium", "microsoft-edge", "firefox"]:
                if shutil.which(browser):
                    installed.append(browser.replace("google-", "").replace("microsoft-", ""))
                    self.logger.info(f"检测到{browser}浏览器")

        if not installed:
            self.logger.warning("未检测到已安装的浏览器，将尝试默认配置")

        return installed

    def _init_webdriver(self):
        """
        初始化Selenium WebDriver

        自动检测系统中已安装的浏览器，使用Selenium Manager自动管理驱动

        Returns:
            WebDriver实例，失败返回None
        """
        try:
            from selenium import webdriver
            from selenium.common.exceptions import WebDriverException

            # 检测已安装的浏览器
            self.logger.info("正在检测系统中已安装的浏览器...")
            installed_browsers = self._detect_installed_browsers()

            # Selenium 4.6+ 内置 Selenium Manager，自动管理驱动
            self.logger.info("使用Selenium Manager自动管理驱动")

            # 如果没有检测到浏览器，尝试所有支持的浏览器
            if not installed_browsers:
                installed_browsers = ["edge", "chrome", "firefox"]

            # 按检测到的顺序尝试启动浏览器
            for browser in installed_browsers:
                self.logger.info(f"正在尝试启动{browser}浏览器...")

                try:
                    if browser == "edge":
                        driver = self._init_edge_driver()
                    elif browser == "chrome":
                        driver = self._init_chrome_driver()
                    elif browser == "firefox":
                        driver = self._init_firefox_driver()
                    else:
                        continue

                    if driver:
                        self.logger.info(f"{browser}浏览器启动成功")
                        return driver

                except WebDriverException as e:
                    self.logger.warning(f"{browser}浏览器启动失败: {e}")
                    continue
                except Exception as e:
                    self.logger.warning(f"{browser}浏览器启动异常: {e}")
                    continue

            self.logger.error("所有浏览器启动失败")
            self.logger.error("请确保已安装Chrome/Edge/Firefox浏览器")
            return None

        except ImportError as e:
            self.logger.error(f"未安装selenium库: {e}")
            self.logger.error("请运行: pip install selenium>=4.6.0")
            return None

    def _init_edge_driver(self):
        """初始化Edge WebDriver"""
        from selenium import webdriver
        from selenium.webdriver.edge.options import Options as EdgeOptions

        options = EdgeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self.logger.info("正在初始化Edge驱动...")
        return webdriver.Edge(options=options)

    def _init_chrome_driver(self):
        """初始化Chrome WebDriver"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options as ChromeOptions

        options = ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self.logger.info("正在初始化Chrome驱动...")
        driver = webdriver.Chrome(options=options)

        # 隐藏webdriver特征
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
                """
            }
        )
        return driver

    def _init_firefox_driver(self):
        """初始化Firefox WebDriver"""
        from selenium import webdriver
        from selenium.webdriver.firefox.options import Options as FirefoxOptions

        options = FirefoxOptions()

        self.logger.info("正在初始化Firefox驱动...")
        return webdriver.Firefox(options=options)

    def _wait_for_login(self) -> Optional[str]:
        """
        等待用户完成登录

        用户需要：
        1. 在登录页面完成登录
        2. 手动导航到选课系统页面

        Returns:
            Cookie字符串，超时返回None
        """
        if self._driver is None:
            return None

        check_interval = 1  # 检查间隔（秒）
        elapsed = 0

        self.logger.info("请在浏览器中完成以下操作：")
        self.logger.info("1. 登录系统")
        self.logger.info("2. 进入选课系统页面")
        self.logger.info("程序将自动检测选课页面并提取Cookie")

        while elapsed < self.config.timeout:
            # 检查是否被取消
            if self._cancelled:
                return None

            # 检查浏览器是否被关闭
            try:
                # 尝试获取当前URL，如果浏览器已关闭会抛出异常
                current_url = self._driver.current_url
            except Exception:
                # 浏览器被关闭
                self.logger.info("检测到浏览器已关闭")
                return None

            # 检查是否已进入选课系统页面
            if self._check_course_page():
                self.logger.info("检测到选课系统页面，正在提取Cookie...")
                return self._extract_cookies()

            time.sleep(check_interval)
            elapsed += check_interval

            # 每30秒提示一次
            if elapsed % 30 == 0:
                remaining = self.config.timeout - elapsed
                self.logger.info(f"等待进入选课系统... 剩余时间: {remaining}秒")

        return None

    def _check_course_page(self) -> bool:
        """
        检查是否已进入选课系统页面

        Returns:
            是否在选课系统页面
        """
        if self._driver is None:
            return False

        try:
            current_url = self._driver.current_url

            # 检查URL是否包含选课系统路径
            if "xkglpt.zjedu.gov.cn" in current_url and "xs_xklist" in current_url:
                self.logger.info(f"检测到选课系统URL: {current_url}")
                return True

            # 检查页面内容
            page_source = self._driver.page_source
            if "xs_xklist" in page_source and ("报名" in page_source or "选课" in page_source):
                self.logger.info("检测到选课系统页面内容")
                return True

            return False

        except Exception as e:
            self.logger.debug(f"检查选课页面时出错: {e}")
            return False

    def _check_login_success(self) -> bool:
        """
        检查是否登录成功

        通过检测URL跳转和Cookie来判断

        Returns:
            是否登录成功
        """
        if self._driver is None:
            return False

        try:
            current_url = self._driver.current_url

            # 检查URL是否已跳转（登录成功后会跳转离开登录页面）
            if "logon" not in current_url.lower():
                self.logger.info(f"检测到URL跳转: {current_url}")
                return True

            # 检查Cookie
            cookies = self._driver.get_cookies()
            if cookies:
                # 检查是否有登录成功的Cookie标识
                for cookie in cookies:
                    name = cookie.get("name", "")
                    if any(indicator in name for indicator in self.LOGIN_SUCCESS_INDICATORS):
                        self.logger.info(f"检测到登录Cookie: {name}")
                        return True

            return False

        except Exception as e:
            self.logger.debug(f"检查登录状态时出错: {e}")
            return False

    def _extract_cookies(self) -> str:
        """
        从浏览器提取Cookie

        Returns:
            Cookie字符串，格式为"key1=value1; key2=value2"
        """
        if self._driver is None:
            return ""

        try:
            cookies = self._driver.get_cookies()
            cookie_str = "; ".join(
                f"{cookie['name']}={cookie['value']}"
                for cookie in cookies
            )
            return cookie_str
        except Exception as e:
            self.logger.error(f"提取Cookie失败: {e}")
            return ""

    def _navigate_to_target(self) -> bool:
        """
        导航到目标页面（选课系统）

        登录成功后，需要访问选课系统页面以获取正确的Cookie

        Returns:
            是否成功导航到目标页面
        """
        if self._driver is None:
            return False

        try:
            self.logger.info(f"正在访问选课系统: {self.config.target_url}")
            self._driver.get(self.config.target_url)

            # 等待页面加载
            time.sleep(3)

            # 检查是否被重定向
            current_url = self._driver.current_url
            self.logger.info(f"当前URL: {current_url}")

            # 如果被重定向到首页，说明需要重新登录
            if "Index.html" in current_url or "logon" in current_url.lower():
                self.logger.warning("页面被重定向，可能需要重新登录")
                return False

            # 检查页面内容是否包含选课列表
            page_source = self._driver.page_source
            if "xs_xklist" in page_source or "选课" in page_source:
                self.logger.info("选课系统页面加载成功")
                return True

            self.logger.info("选课系统页面加载完成")
            return True

        except Exception as e:
            self.logger.warning(f"导航到选课系统失败: {e}")
            return False

    def _close_browser(self) -> None:
        """关闭浏览器"""
        if self._driver is not None:
            try:
                self._driver.quit()
                self.logger.info("浏览器已关闭")
            except Exception as e:
                self.logger.debug(f"关闭浏览器时出错: {e}")
            finally:
                self._driver = None


def browser_login(
    login_url: str = "https://pjglpt.zjedu.gov.cn/logon.action",
    timeout: int = 300,
    auto_close: bool = True
) -> LoginResult:
    """
    便捷函数：启动浏览器登录

    Args:
        login_url: 登录页面URL
        timeout: 超时时间（秒）
        auto_close: 登录成功后是否自动关闭浏览器

    Returns:
        LoginResult: 登录结果对象

    Example:
        >>> result = browser_login()
        >>> if result.success:
        ...     print(f"Cookie: {result.cookies}")
    """
    login_manager = BrowserLogin(
        login_url=login_url,
        timeout=timeout,
        auto_close=auto_close
    )
    return login_manager.start_login()
