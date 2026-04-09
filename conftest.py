"""
Pytest 全局配置 - 管理 Mock 服务器生命周期
"""
import pytest
import subprocess
import time
import requests
import os
import sys


@pytest.fixture(scope="session", autouse=True)
def mock_server():
    """自动启动和关闭 Mock 服务器"""
    # 检查是否已有 Mock 服务器在运行
    try:
        response = requests.get("http://localhost:5000/api/products", timeout=2)
        if response.status_code == 200:
            print("Mock 服务器已在运行")
            yield
            return
    except:
        pass

    # 启动 Mock 服务器
    print("启动 Mock 服务器...")
    proc = subprocess.Popen(
        [sys.executable, "mock_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    )

    # 等待服务器启动
    max_attempts = 10
    for i in range(max_attempts):
        try:
            response = requests.get("http://localhost:5000/api/products", timeout=2)
            if response.status_code == 200:
                print("Mock 服务器已启动")
                break
        except:
            pass
        time.sleep(1)
    else:
        print("警告: Mock 服务器可能未成功启动")

    yield

    # 关闭服务器
    proc.terminate()
    time.sleep(1)
    proc.kill()
    print("Mock 服务器已关闭")