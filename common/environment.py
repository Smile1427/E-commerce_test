"""
环境管理模块
支持多环境切换、配置管理
"""
import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Environment:
    """环境配置"""
    name: str
    base_url: str
    timeout: int
    verify_ssl: bool
    description: str
    readonly: bool = False


@dataclass
class PublicAPI:
    """公开 API 配置"""
    name: str
    base_url: str
    timeout: int
    description: str
    endpoints: Dict[str, str]


class EnvironmentManager:
    """环境管理器（单例模式）"""

    _instance = None
    _config: Dict = {}
    _public_apis_config: Dict = {}
    _current_env: str = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
            cls._instance._load_public_apis_config()
        return cls._instance

    def _load_config(self):
        """加载环境配置文件"""
        config_path = Path(__file__).parent.parent / 'config' / 'environments.yaml'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            logger.info(f"已加载环境配置: {config_path}")
        else:
            # 默认配置
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            self._config = {
                'environments': {
                    'local': {
                        'name': '本地环境',
                        'base_url': 'http://localhost:5000',
                        'timeout': 30,
                        'verify_ssl': False,
                        'description': 'Mock服务器'
                    }
                },
                'active_environment': 'local'
            }

    def _load_public_apis_config(self):
        """加载公开 API 配置文件"""
        config_path = Path(__file__).parent.parent / 'config' / 'public_apis.yaml'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._public_apis_config = yaml.safe_load(f)
            logger.info(f"已加载公开API配置: {config_path}")
        else:
            logger.warning(f"公开API配置文件不存在: {config_path}")
            self._public_apis_config = {'public_apis': {}}

    def get_current_env(self) -> str:
        """获取当前环境名称"""
        if self._current_env:
            return self._current_env

        # 优先从环境变量读取
        env = os.environ.get('TEST_ENV', '')
        if env and env in self._config.get('environments', {}):
            return env

        # 使用配置文件中的默认环境
        return self._config.get('active_environment', 'local')

    def set_environment(self, env_name: str):
        """切换环境"""
        environments = self._config.get('environments', {})
        if env_name not in environments:
            raise ValueError(f"未知环境: {env_name}，可用环境: {list(environments.keys())}")
        self._current_env = env_name
        os.environ['TEST_ENV'] = env_name
        logger.info(f"已切换到环境: {environments[env_name]['name']}")

    def get_environment(self, env_name: str = None) -> Environment:
        """获取环境配置"""
        name = env_name or self.get_current_env()
        env_config = self._config.get('environments', {}).get(name)
        if not env_config:
            raise ValueError(f"环境配置不存在: {name}")

        return Environment(
            name=env_config.get('name', name),
            base_url=env_config.get('base_url', '').rstrip('/'),
            timeout=env_config.get('timeout', 30),
            verify_ssl=env_config.get('verify_ssl', True),
            description=env_config.get('description', ''),
            readonly=env_config.get('readonly', False)
        )

    def get_all_environments(self) -> List[str]:
        """获取所有可用环境"""
        return list(self._config.get('environments', {}).keys())

    def is_readonly(self) -> bool:
        """当前环境是否为只读"""
        return self.get_environment().readonly

    def get_public_api(self, api_name: str) -> Optional[PublicAPI]:
        """获取公开 API 配置"""
        apis = self._public_apis_config.get('public_apis', {})
        api_config = apis.get(api_name)
        if not api_config:
            return None

        return PublicAPI(
            name=api_config.get('name', api_name),
            base_url=api_config.get('base_url', '').rstrip('/'),
            timeout=api_config.get('timeout', 30),
            description=api_config.get('description', ''),
            endpoints=api_config.get('endpoints', {})
        )

    def get_all_public_apis(self) -> List[str]:
        """获取所有公开 API 名称"""
        return list(self._public_apis_config.get('public_apis', {}).keys())


# 全局单例
env_manager = EnvironmentManager()