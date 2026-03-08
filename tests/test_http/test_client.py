"""
测试HTTP客户端 - 基于真实HTTP请求
"""

import pytest
from unittest.mock import Mock, patch
from course_selector.http.client import HttpClient, HttpResponse


class TestHttpClient:
    """测试HttpClient类"""

    @pytest.fixture
    def http_client(self):
        """创建HTTP客户端实例"""
        return HttpClient(
            cookies='test_cookie',
            base_url='https://xkglpt.zjedu.gov.cn',
            timeout=30
        )

    def test_client_creation(self):
        """测试客户端创建"""
        client = HttpClient(
            cookies='my_cookie',
            base_url='https://xkglpt.zjedu.gov.cn',
            timeout=60
        )
        assert client.timeout == 60
        assert client.base_url == 'https://xkglpt.zjedu.gov.cn'
        assert 'Cookie' in client.headers  # cookies存储在headers中

    def test_get_request(self, http_client):
        """测试GET请求"""
        with patch('requests.Session.get') as mock_get:
            # 模拟真实响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '<html><body>Test</body></html>'
            mock_response.headers = {'Content-Type': 'text/html'}
            mock_get.return_value = mock_response

            response = http_client.get('/test')

            assert response.success is True
            assert response.status_code == 200
            assert 'Test' in response.text

    def test_post_request(self, http_client):
        """测试POST请求"""
        with patch('requests.Session.post') as mock_post:
            # 模拟真实响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '<html><body>Success</body></html>'
            mock_response.headers = {'Content-Type': 'text/html'}
            mock_post.return_value = mock_response

            data = {'key': 'value'}
            response = http_client.post('/test', data=data)

            assert response.success is True
            assert response.status_code == 200
            assert 'Success' in response.text

    def test_request_with_error(self, http_client):
        """测试请求错误处理"""
        with patch('requests.Session.get') as mock_get:
            # 模拟错误响应
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = 'Internal Server Error'
            mock_response.headers = {}
            mock_get.return_value = mock_response

            response = http_client.get('/test')

            assert response.success is False
            assert response.status_code == 500

    def test_request_with_timeout(self, http_client):
        """测试请求超时"""
        with patch('requests.Session.get') as mock_get:
            # 模拟超时异常
            import requests
            mock_get.side_effect = requests.Timeout('Timeout')

            # HttpClient会重新抛出异常
            with pytest.raises(requests.Timeout):
                http_client.get('/test')


class TestHttpResponse:
    """测试HttpResponse类"""

    def test_response_creation(self):
        """测试响应创建"""
        response = HttpResponse(
            status_code=200,
            text='<html>Test</html>',
            headers={'Content-Type': 'text/html'},
            success=True
        )

        assert response.status_code == 200
        assert response.text == '<html>Test</html>'
        assert response.success is True

    def test_response_failure(self):
        """测试失败响应"""
        response = HttpResponse(
            status_code=404,
            text='Not Found',
            headers={},
            success=False
        )

        assert response.status_code == 404
        assert response.success is False

    def test_response_error(self):
        """测试错误响应"""
        response = HttpResponse(
            status_code=0,
            text='',
            headers={},
            success=False
        )

        assert response.status_code == 0
        assert response.success is False
