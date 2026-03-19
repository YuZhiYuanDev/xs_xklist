"""
命令行入口点

Usage:
    python -m course_selector
    python -m course_selector --login
    python -m course_selector --snatch "课程名称" --time "2025-01-01 12:00:00"
    python -m course_selector --config /path/to/config.json
    python -m course_selector --help
"""

import argparse
import sys
import logging
from datetime import datetime

from .core import CourseSelector, CourseSnatcher
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
        "--snatch", "-s",
        type=str,
        default=None,
        help="快速抢课模式，指定课程关键词"
    )
    parser.add_argument(
        "--time",
        type=str,
        default=None,
        help="抢课开始时间，格式: 'YYYY-MM-DD HH:MM:SS'"
    )
    parser.add_argument(
        "--advance",
        type=float,
        default=15.0,
        help="提前多少秒开始检测（默认15秒）"
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=1000,
        help="最大尝试次数（默认1000次）"
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

    # 抢课模式
    if args.snatch:
        if not args.time:
            print("错误: 抢课模式需要指定 --time 参数")
            print("示例: --snatch \"数学\" --time \"2025-01-15 12:00:00\"")
            return 1

        try:
            start_time = datetime.strptime(args.time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print(f"错误: 时间格式不正确，应为 'YYYY-MM-DD HH:MM:SS'")
            return 1

        print("\n" + "=" * 80)
        print("快速抢课模式")
        print("=" * 80)
        print(f"目标课程: {args.snatch}")
        print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"提前检测: {args.advance} 秒")
        print(f"最大尝试: {args.max_attempts} 次")
        print("=" * 80)
        print()

        # 创建抢课器
        snatcher = CourseSnatcher(selector)

        # 开始抢课
        result = snatcher.snatch_course(
            course_keyword=args.snatch,
            start_time=start_time,
            advance_seconds=args.advance,
            max_attempts=args.max_attempts
        )

        # 显示结果
        print("\n" + "=" * 80)
        print("抢课结果")
        print("=" * 80)
        if result.success:
            print(f"[成功] {result.course_name}")
        else:
            print(f"[失败] {result.message}")
        print(f"尝试次数: {result.attempt_count}")
        print(f"耗时: {result.time_used:.2f} 秒")
        print("=" * 80)

        return 0 if result.success else 1

    print("\n程序仅提供自动抢课功能。")
    print('使用方式：python -m course_selector --snatch "课程名称" --time "YYYY-MM-DD HH:MM:SS"')
    return 0

if __name__ == "__main__":
    sys.exit(main())
