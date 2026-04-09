#!/usr/bin/env python
"""
环境切换脚本
用法: python switch_env.py [local|dev|test|staging|prod|list]
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.environment import env_manager


def print_current_env():
    """打印当前环境信息"""
    env = env_manager.get_environment()
    print("\n" + "=" * 50)
    print(f"当前环境: {env.name}")
    print(f"  Base URL: {env.base_url}")
    print(f"  超时时间: {env.timeout}s")
    print(f"  SSL验证: {env.verify_ssl}")
    print(f"  只读模式: {'是' if env.readonly else '否'}")
    print(f"  描述: {env.description}")
    print("=" * 50 + "\n")


def print_all_environments():
    """打印所有可用环境"""
    print("\n可用环境:")
    print("-" * 40)
    for env_name in env_manager.get_all_environments():
        env = env_manager.get_environment(env_name)
        print(f"  {env_name}: {env.name}")
        print(f"    URL: {env.base_url}")
        print(f"    描述: {env.description}")
    print("-" * 40 + "\n")


def main():
    if len(sys.argv) < 2:
        print("用法: python switch_env.py <command>")
        print("\n命令:")
        print("  list              - 列出所有可用环境")
        print("  current           - 显示当前环境")
        print("  <环境名>          - 切换到指定环境")
        print("\n示例:")
        print("  python switch_env.py list")
        print("  python switch_env.py current")
        print("  python switch_env.py local")
        print("  python switch_env.py test")
        sys.exit(0)

    command = sys.argv[1]

    if command == "list":
        print_all_environments()
    elif command == "current":
        print_current_env()
    else:
        try:
            env_manager.set_environment(command)
            print(f"✅ 已切换到环境: {command}")
            print_current_env()
        except ValueError as e:
            print(f"❌ {e}")
            print_all_environments()
            sys.exit(1)


if __name__ == "__main__":
    main()