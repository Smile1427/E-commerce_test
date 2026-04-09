"""
Pytest配置和Fixtures
"""
import pytest
import yaml
import sys
import io
import platform
from pathlib import Path
from common.api_client import APIClient, PublicAPIClient
from common.logger import logger
from common.db_helper import db
from common.environment import env_manager

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

# 强制设置标准输出编码为 UTF-8（解决 Windows 中文乱码）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def pytest_addoption(parser):
    """添加命令行参数"""
    parser.addoption(
        "--env",
        action="store",
        default=None,
        help="指定测试环境: local, jsonplaceholder, dummyjson"
    )


def pytest_configure(config):
    """pytest 配置钩子"""
    # 设置环境
    env = config.getoption("--env")
    if env:
        env_manager.set_environment(env)
        logger.info(f"已切换到环境: {env}")


@pytest.fixture(scope="session")
def config():
    """加载配置"""
    config_path = ROOT_DIR / 'data' / 'test_data.yaml'
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


@pytest.fixture(scope="session")
def test_environment():
    """获取当前测试环境"""
    return env_manager.get_environment()


@pytest.fixture(scope="session")
def api_client(test_environment):
    """API客户端（支持环境切换）"""
    return APIClient()


@pytest.fixture(scope="session")
def test_user(config):
    """测试用户"""
    return config.get('test_user', {
        'username': 'testuser',
        'password': 'Test123456'
    })


@pytest.fixture(scope="function")
def auth_token(api_client, test_user):
    """认证Token（自动登录）"""
    response = api_client.post('/api/user/login', json={
        'username': test_user['username'],
        'password': test_user['password']
    })

    if response.status_code == 200 and response.json().get('code') == 200:
        token = response.json()['data']['token']
        api_client.token = token
        return token

    pytest.fail(f"登录失败: {response.text}")


@pytest.fixture(scope="function", autouse=True)
def clean_cart(api_client, auth_token):
    """清理购物车（每个测试前后自动清理）"""
    # 测试前清理
    api_client.delete('/api/cart/clear')
    logger.info("测试前清理购物车")

    yield

    # 测试后清理
    api_client.delete('/api/cart/clear')
    logger.info("测试后清理购物车")


@pytest.fixture(scope="function")
def db_verifier():
    """数据库验证器"""
    return db


@pytest.fixture(scope="function")
def cleanup_user():
    """清理测试创建的用户的 fixture"""
    created_users = []

    def _register_and_track(username, email, password):
        created_users.append(username)
        return username

    yield _register_and_track

    if created_users:
        from common.database import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            for username in created_users:
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()
                if row:
                    user_id = row[0]
                    cursor.execute("DELETE FROM carts WHERE user_id = ?", (user_id,))
                    cursor.execute("DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE user_id = ?)", (user_id,))
                    cursor.execute("DELETE FROM orders WHERE user_id = ?", (user_id,))
                    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        logger.info(f"清理测试用户: {created_users}")


@pytest.fixture(scope="function")
def get_current_user_id(auth_token, api_client):
    """获取当前登录用户的ID"""
    response = api_client.get('/api/user/info')
    if response.status_code == 200:
        return response.json()['data']['id']
    return None


# ==================== 公开 API Fixtures ====================

@pytest.fixture(scope="session")
def jsonplaceholder_client():
    """JSONPlaceholder 客户端"""
    return PublicAPIClient("jsonplaceholder")


@pytest.fixture(scope="session")
def dummyjson_client():
    """DummyJSON 客户端"""
    return PublicAPIClient("dummyjson")


# ==================== Allure 环境信息配置 ====================

def pytest_sessionfinish(session):
    """测试会话结束时，生成 Allure 环境信息文件"""
    allure_dir = ROOT_DIR / 'reports' / 'allure_raw'
    allure_dir.mkdir(parents=True, exist_ok=True)

    env_file = allure_dir / 'environment.properties'

    # 获取当前环境信息
    current_env = env_manager.get_current_env()
    env_config = env_manager.get_environment()

    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(f"Python Version={sys.version.split()[0]}\n")
        f.write(f"Pytest Version={pytest.__version__}\n")
        f.write(f"Platform={platform.platform()}\n")
        f.write(f"OS={platform.system()} {platform.release()}\n")
        f.write(f"Processor={platform.processor() or 'Unknown'}\n")
        f.write(f"Host={platform.node()}\n")
        f.write(f"Environment={env_config.name}\n")
        f.write(f"Environment Code={current_env}\n")
        f.write(f"Base URL={env_config.base_url}\n")
        f.write(f"Timeout={env_config.timeout}s\n")
        f.write(f"Readonly Mode={'Yes' if env_config.readonly else 'No'}\n")
        f.write(f"Database=SQLite\n")
        f.write(f"Mock Server=Flask 3.1.3\n")

    logger.info(f"Allure 环境信息已生成: {env_file}")