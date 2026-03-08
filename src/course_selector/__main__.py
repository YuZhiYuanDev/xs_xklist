"""
命令行入口点

Usage:
    python -m course_selector
    python -m course_selector --config /path/to/config.json
    python -m course_selector --help
"""

import argparse
import sys
import logging

from .core import CourseSelector
from .config import ConfigManager, CookieManager
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

    # 如果没有Cookie，提示用户输入
    if not config.cookies:
        print("请输入Cookie (从浏览器开发者工具中复制):")
        config.cookies = input("Cookie: ").strip()

        print("\n请输入要报名的课程名称 (多个课程用逗号分隔,直接回车跳过):")
        course_input = input("课程名称: ").strip()
        if course_input:
            config.target_courses = [name.strip() for name in course_input.split(',') if name.strip()]

        # 保存Cookie
        if config.cookies:
            cookie_manager = CookieManager()
            cookie_manager.save(config.cookies)
            print("Cookie已保存到 cookies.txt 文件")

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
