"""
HTTP客户端封装
支持：重试机制、超时控制、日志记录、Token自动管理、环境切换
"""
import requests
import time
import logging
from functools import wraps
from typing import Optional, Dict, Any
from common.environment import env_manager

logger = logging.getLogger(__name__)


def retry(max_attempts=3, delay=1, exceptions=(requests.RequestException,)):
    """重试装饰器"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise
                    logger.warning(f"请求失败，{delay}秒后重试 (尝试 {attempt + 1}/{max_attempts}): {e}")
                    time.sleep(delay)
            return None

        return wrapper

    return decorator


class APIClient:
    """API客户端"""

    def __init__(self, base_url: str = None, timeout: int = None, env: str = None, use_env: bool = True):
        """
        初始化 API 客户端

        :param base_url: 基础URL，如果不指定则使用环境配置
        :param timeout: 超时时间
        :param env: 指定环境名称（local/dev/test/staging/prod）
        :param use_env: 是否使用环境管理器的配置
        """
        self.use_env = use_env

        if use_env and env:
            env_manager.set_environment(env)

        if use_env:
            self.env_config = env_manager.get_environment()
            self.base_url = base_url or self.env_config.base_url
            self.timeout = timeout or self.env_config.timeout
            self.readonly = self.env_config.readonly
            self.env_name = self.env_config.name
        else:
            self.base_url = base_url.rstrip('/') if base_url else "http://localhost:5000"
            self.timeout = timeout or 30
            self.readonly = False
            self.env_name = "自定义"

        self.base_url = self.base_url.rstrip('/')
        self.session = requests.Session()

        # User-Agent 不能包含中文，将中文环境名映射为英文
        env_name_en_map = {
            '本地环境': 'Local',
            '开发环境': 'Dev',
            '测试环境': 'Test',
            '预发布环境': 'Staging',
            '生产环境': 'Prod'
        }
        env_name_en = env_name_en_map.get(self.env_name, 'Unknown')

        self.session.headers.update({
            'User-Agent': f'EcommerceAPITest/1.0 ({env_name_en})',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

        if use_env and hasattr(self, 'env_config'):
            self.session.verify = self.env_config.verify_ssl

        self._token: Optional[str] = None

    @property
    def token(self) -> Optional[str]:
        return self._token

    @token.setter
    def token(self, value: str):
        self._token = value
        if value:
            self.session.headers.update({'Authorization': f'Bearer {value}'})
        elif 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """快捷登录方法"""
        response = self.post('/api/user/login', json={
            'username': username,
            'password': password
        })
        if response.status_code == 200 and response.json().get('code') == 200:
            self.token = response.json()['data']['token']
        return response.json()

    def _check_readonly(self, method: str):
        """检查只读环境"""
        if self.readonly and method.upper() not in ['GET', 'HEAD', 'OPTIONS']:
            raise RuntimeError(f"当前环境 [{self.env_name}] 为只读模式，不允许执行 {method} 请求")

    @retry(max_attempts=3)
    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """发送HTTP请求"""
        self._check_readonly(method)

        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)

        logger.info(f"[{method}] {url}")
        if 'json' in kwargs:
            logger.debug(f"请求体: {kwargs['json']}")

        response = self.session.request(method, url, **kwargs)

        logger.info(f"响应状态: {response.status_code}")
        if response.text:
            logger.debug(f"响应体: {response.text[:500]}")

        return response

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request('GET', endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request('POST', endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request('PUT', endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request('DELETE', endpoint, **kwargs)

    def get_env_info(self) -> Dict:
        """获取当前环境信息"""
        if self.use_env:
            return {
                'environment': self.env_name,
                'base_url': self.base_url,
                'timeout': self.timeout,
                'readonly': self.readonly
            }
        return {
            'environment': 'custom',
            'base_url': self.base_url,
            'timeout': self.timeout,
            'readonly': self.readonly
        }


class PublicAPIClient:
    """公开 API 客户端（专门用于测试公开接口）"""

    def __init__(self, api_name: str):
        """
        初始化公开 API 客户端

        :param api_name: API 名称（jsonplaceholder, reqres, dummyjson, fakestore）
        """
        from common.environment import env_manager

        self.api_config = env_manager.get_public_api(api_name)
        if not self.api_config:
            raise ValueError(f"未知的公开 API: {api_name}，可用: {env_manager.get_all_public_apis()}")

        self.base_url = self.api_config.base_url
        self.timeout = self.api_config.timeout
        self.api_name = api_name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'PublicAPITest/{api_name}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    @retry(max_attempts=2)
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """发送 GET 请求"""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)

        logger.info(f"[PublicAPI-{self.api_name}] GET {url}")
        response = self.session.get(url, **kwargs)
        logger.info(f"响应状态: {response.status_code}")

        return response

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """发送 POST 请求"""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)

        logger.info(f"[PublicAPI-{self.api_name}] POST {url}")
        response = self.session.post(url, **kwargs)
        logger.info(f"响应状态: {response.status_code}")

        return response