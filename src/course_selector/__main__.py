"""
命令行入口点

Usage:
    python -m course_selector
    python -m course_selector --login
    python -m course_selector --config /path/to/config.json
    python -m course_selector --help
"""

import argparse
import sys
import logging

from .core import CourseSelector
from .config import ConfigManager, CookieManager
from .auth import browser_login
from .utils.logger import setup_logging, get_logger


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数

    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        prog="course_selector",
        description="浙江省普通高中选课管理系统 - 自动化选课程序"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=None,
        help="配置文件路径 (默认: config.json)"
    )
    parser.add_argument(
        "--login", "-l",
        action="store_true",
        help="通过浏览器登录获取Cookie"
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=300,
        help="登录超时时间（秒），默认300秒"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细日志"
    )
    return parser.parse_args()


def main() -> int:
    """
    主函数

    Returns:
        退出码（0表示成功，非0表示失败）
    """
    args = parse_args()

    # 配置日志
    setup_logging(logging.DEBUG if args.verbose else logging.INFO)
    logger = get_logger(__name__)

    print("=" * 80)
    print("浙江省普通高中选课管理系统 - 自动化选课程序")
    print("=" * 80)
    print()

    # 加载配置
    config_manager = ConfigManager(args.config)
    config = config_manager.load()

    # 获取Cookie
    if not config.cookies:
        cookie_manager = CookieManager()
        config.cookies = cookie_manager.load()

    # 如果指定了--login参数或没有Cookie，启动浏览器登录
    if args.login or not config.cookies:
        print("\n正在启动浏览器登录...")
        print("提示：请在弹出的浏览器中完成登录操作")
        print(f"超时时间: {args.timeout}秒\n")

        result = browser_login(timeout=args.timeout)

        if result.success:
            config.cookies = result.cookies
            # 保存Cookie
            cookie_manager = CookieManager()
            cookie_manager.save(result.cookies)
            print(f"\n登录成功！Cookie已保存到 cookies.txt 文件")
            print(f"登录耗时: {result.login_time:.1f}秒\n")
        else:
            print(f"\n登录失败: {result.message}")
            if result.error_code:
                print(f"错误码: {result.error_code}")

            # 如果是浏览器启动失败，提示手动输入
            if result.error_code == "BROWSER_INIT_FAILED":
                print("\n请手动输入Cookie (从浏览器开发者工具中复制):")
                config.cookies = input("Cookie: ").strip()
                if config.cookies:
                    cookie_manager.save(config.cookies)
                    print("Cookie已保存到 cookies.txt 文件")
            else:
                return 1

    if not config.cookies:
        logger.error("Cookie不能为空!")
        return 1

    # 创建选择器
    selector = CourseSelector(config.cookies)

    # 获取并显示课程列表
    selector.display_courses()

    # 自动报名
    if config.target_courses:
        print(f"\n开始自动报名课程: {', '.join(config.target_courses)}")
        results = selector.auto_enroll_by_keywords(config.target_courses)

        # 显示结果
        print("\n" + "=" * 80)
        print("报名结果")
        print("=" * 80)
        print(f"成功: {len(results.success)} 门")
        for course in results.success:
            print(f"  [成功] {course}")

        print(f"\n失败: {len(results.failed)} 门")
        for course in results.failed:
            print(f"  [失败] {course}")

        print(f"\n未找到: {len(results.not_found)} 门")
        for course in results.not_found:
            print(f"  [未找到] {course}")
        print("=" * 80)
    else:
        print("\n未指定要报名的课程，程序结束。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
