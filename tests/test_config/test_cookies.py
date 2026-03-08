"""
测试Cookie管理器
"""

import pytest
import tempfile
from pathlib import Path
from course_selector.config.cookies import CookieManager


class TestCookieManager:
    """测试CookieManager类"""

    def test_load_existing_cookies(self):
        """测试加载存在的Cookie文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('test_cookie_string')
            cookie_path = f.name

        try:
            manager = CookieManager(cookie_path)
            cookies = manager.load()

            assert cookies == 'test_cookie_string'

        finally:
            Path(cookie_path).unlink()

    def test_load_nonexistent_cookies(self):
        """测试加载不存在的Cookie文件"""
        manager = CookieManager('nonexistent_cookies.txt')
        cookies = manager.load()

        assert cookies == ''

    def test_save_cookies(self):
        """测试保存Cookie"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            cookie_path = f.name

        try:
            manager = CookieManager(cookie_path)
            manager.save('new_cookie_string')

            # 验证文件已创建
            assert Path(cookie_path).exists()

            # 验证内容
            with open(cookie_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert content == 'new_cookie_string'

        finally:
            Path(cookie_path).unlink()

    def test_exists_true(self):
        """测试文件存在检查"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            cookie_path = f.name

        try:
            manager = CookieManager(cookie_path)
            assert manager.exists() is True

        finally:
            Path(cookie_path).unlink()

    def test_exists_false(self):
        """测试文件不存在检查"""
        manager = CookieManager('nonexistent_cookies.txt')
        assert manager.exists() is False
