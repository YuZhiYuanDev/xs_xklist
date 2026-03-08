"""
测试配置管理器
"""

import pytest
import json
import tempfile
from pathlib import Path
from course_selector.config.manager import ConfigManager, AppConfig


class TestConfigManager:
    """测试ConfigManager类"""

    def test_load_existing_config(self, sample_config_data):
        """测试加载存在的配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_config_data, f)
            config_path = f.name

        try:
            manager = ConfigManager(config_path)
            config = manager.load()

            assert config.cookies == 'test_cookie_string'
            assert len(config.target_courses) == 2
            assert config.semester == '2025/2026下'

        finally:
            Path(config_path).unlink()

    def test_load_nonexistent_config(self):
        """测试加载不存在的配置文件"""
        manager = ConfigManager('nonexistent_config.json')
        config = manager.load()

        # 应该返回默认配置
        assert config.cookies == ''
        assert config.target_courses == []
        assert config.semester == '2025/2026下'

    def test_save_config(self, sample_config_data):
        """测试保存配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name

        try:
            manager = ConfigManager(config_path)
            config = AppConfig(**sample_config_data)
            manager.save(config)

            # 验证文件已创建
            assert Path(config_path).exists()

            # 验证内容
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert data['cookies'] == 'test_cookie_string'

        finally:
            Path(config_path).unlink()

    def test_get_config_value(self, sample_config_data):
        """测试获取配置项"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_config_data, f)
            config_path = f.name

        try:
            manager = ConfigManager(config_path)
            manager.load()

            assert manager.get('cookies') == 'test_cookie_string'
            assert manager.get('timeout') == 30
            assert manager.get('nonexistent', 'default') == 'default'

        finally:
            Path(config_path).unlink()
