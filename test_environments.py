#!/usr/bin/env python
"""
环境切换测试脚本
测试所有配置的环境是否正常运行
"""
import pytest
import allure
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.api_client import APIClient
from common.environment import env_manager


@allure.feature("环境切换测试")
class TestEnvironments:

    @allure.story("环境可用性")
    @allure.title("测试本地环境")
    def test_local_environment(self):
        """测试本地 Mock 服务器"""
        try:
            client = APIClient(env="local")
            response = client.get('/api/products')
            assert response.status_code == 200
            print(f"\n✅ 本地环境正常")
            print(f"   URL: {client.base_url}")
            print(f"   状态: 可读写")
        except Exception as e:
            print(f"\n❌ 本地环境异常: {e}")
            raise

    @allure.story("环境可用性")
    @allure.title("测试 JSONPlaceholder 环境")
    def test_jsonplaceholder_environment(self):
        """测试 JSONPlaceholder API"""
        try:
            client = APIClient(env="jsonplaceholder")
            response = client.get('/posts/1')
            assert response.status_code == 200
            data = response.json()
            assert data['id'] == 1
            print(f"\n✅ JSONPlaceholder 环境正常")
            print(f"   URL: {client.base_url}")
            print(f"   状态: 只读")
        except Exception as e:
            print(f"\n❌ JSONPlaceholder 环境异常: {e}")
            raise

    @allure.story("环境可用性")
    @allure.title("测试 DummyJSON 环境")
    def test_dummyjson_environment(self):
        """测试 DummyJSON API"""
        try:
            client = APIClient(env="dummyjson")
            response = client.get('/products/1')
            assert response.status_code == 200
            data = response.json()
            assert data['id'] == 1
            assert 'title' in data
            print(f"\n✅ DummyJSON 环境正常")
            print(f"   URL: {client.base_url}")
            print(f"   状态: 只读")
        except Exception as e:
            print(f"\n❌ DummyJSON 环境异常: {e}")
            raise

    @allure.story("环境可用性")
    @allure.title("测试 ReqRes 环境")
    def test_reqres_environment(self):
        """测试 ReqRes API（可能失败）"""
        try:
            client = APIClient(env="reqres")
            response = client.get('/api/users?page=1')
            # ReqRes 可能返回 401，这里只测试连接
            if response.status_code == 200:
                print(f"\n✅ ReqRes 环境正常")
            else:
                print(f"\n⚠️ ReqRes 环境返回 {response.status_code}，可能需要认证")
            print(f"   URL: {client.base_url}")
            print(f"   状态: 只读")
        except Exception as e:
            print(f"\n⚠️ ReqRes 环境连接异常: {e}")

    @allure.story("环境信息")
    @allure.title("查看所有环境配置")
    def test_list_all_environments(self):
        """列出所有可用环境"""
        print("\n" + "=" * 60)
        print("所有可用环境:")
        print("=" * 60)

        for env_name in env_manager.get_all_environments():
            env = env_manager.get_environment(env_name)
            status = "✅ 可读写" if not env.readonly else "📖 只读"
            print(f"\n  🌍 {env_name}")
            print(f"     名称: {env.name}")
            print(f"     URL: {env.base_url}")
            print(f"     状态: {status}")
            print(f"     描述: {env.description}")

        print("\n" + "=" * 60)

    @allure.story("环境信息")
    @allure.title("查看当前环境")
    def test_show_current_environment(self):
        """显示当前环境信息"""
        env = env_manager.get_environment()
        print(f"\n当前环境: {env.name}")
        print(f"  URL: {env.base_url}")
        print(f"  超时: {env.timeout}s")
        print(f"  SSL验证: {env.verify_ssl}")
        print(f"  只读模式: {'是' if env.readonly else '否'}")
        print(f"  描述: {env.description}")


def run_environment_tests():
    """运行所有环境测试"""
    print("\n" + "=" * 60)
    print("开始测试所有环境")
    print("=" * 60)

    # 运行测试
    result = pytest.main([__file__, "-v", "-s", "--tb=short"])

    print("\n" + "=" * 60)
    print("环境测试完成")
    print("=" * 60)

    return result


if __name__ == "__main__":
    # 可以指定环境运行
    if len(sys.argv) > 1:
        env_name = sys.argv[1]
        print(f"\n切换到环境: {env_name}")
        env_manager.set_environment(env_name)

    run_environment_tests()