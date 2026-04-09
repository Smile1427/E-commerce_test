# 🚀 E-commerce API 自动化测试框架

[![CI](https://github.com/Smile1427/E-commerce_test/actions/workflows/test.yml/badge.svg)](https://github.com/Smile1427/E-commerce_test/actions/workflows/test.yml)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Allure Report](https://img.shields.io/badge/Allure-Report-brightgreen)](https://smile1427.github.io/E-commerce_test/allure-report/)

基于 **Python + Pytest + Allure** 的接口自动化测试框架，支持多环境切换、SQLite 数据库持久化、Mock 服务器。

## 📊 测试统计

| 模块 | 测试数量 |
|------|---------|
| 用户模块 | 7 |
| 商品模块 | 12 |
| 购物车模块 | 6 |
| 订单模块 | 6 |
| JSONPlaceholder 环境 | 8 |
| DummyJSON 环境 | 18 |
| **总计** | **57** |

## ✨ 核心特性

- ✅ **多环境支持**：本地 Mock / JSONPlaceholder / DummyJSON 一键切换
- ✅ **数据库持久化**：SQLite 存储数据，支持测试验证
- ✅ **Allure 报告**：可视化测试报告，按模块分类展示
- ✅ **Mock 服务器**：Flask 自建 Mock，完整模拟电商业务流程
- ✅ **Token 管理**：自动处理 JWT Token 和黑名单
- ✅ **重试机制**：请求失败自动重试，提高稳定性

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.12 | 主开发语言 |
| Pytest | 测试框架 |
| Allure | 测试报告 |
| Requests | HTTP 客户端 |
| Flask | Mock 服务器 |
| SQLite | 数据持久化 |
| PyJWT | Token 生成验证 |


## 📁 项目结构
```
E-commerce_test/
├── common/ # 公共模块
│ ├── api_client.py # HTTP 客户端封装
│ ├── database.py # SQLite 数据库
│ ├── environment.py # 环境管理
│ └── ...
├── config/ # 配置文件
│ ├── environments.yaml # 环境配置
│ └── public_apis.yaml # 公开 API 配置
├── testcases/ # 测试用例
│ ├── business/ # 业务测试
│ │ ├── test_user.py
│ │ ├── test_product.py
│ │ ├── test_cart.py
│ │ └── test_order.py
│ └── environments/ # 环境测试
│ ├── test_jsonplaceholder.py
│ └── test_dummyjson.py
├── reports/ # Allure 报告
├── mock_server.py # Mock 服务器
├── switch_env.py # 环境切换脚本
└── requirements.txt
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 Mock 服务器
```bash
# Windows
start_mock.bat

# 或直接运行
python mock_server.py
```

### 3. 运行测试
```bash
# 运行所有测试
pytest testcases/ -v

# 只运行业务测试
pytest testcases/business/ -v

# 只运行环境测试
pytest testcases/environments/ -v
```

### 4. 生成 Allure 报告
```bash
# 运行测试并生成原始数据
pytest testcases/ -v --alluredir=./reports/allure_raw

# 生成 HTML 报告
allure generate ./reports/allure_raw -o ./reports/allure_html --clean

# 打开报告
allure open ./reports/allure_html
```

## 🌍 环境切换
```bash
# 查看所有可用环境
python switch_env.py list

# 查看当前环境
python switch_env.py current

# 切换到指定环境
python switch_env.py local          # 本地 Mock 服务器
python switch_env.py jsonplaceholder # JSONPlaceholder 公开 API
python switch_env.py dummyjson      # DummyJSON 公开 API

# 指定环境运行测试
pytest --env=jsonplaceholder -v
```

## 📝测试用例示例

### 用户登录测试

```python
import allure

@allure.feature("用户模块")
class TestUser:
    
    @allure.story("登录功能")
    @allure.title("测试正常登录")
    def test_login_success(self, api_client, test_user):
        response = api_client.post('/api/user/login', json={
            'username': test_user['username'],
            'password': test_user['password']
        })
        assert response.status_code == 200
        assert 'token' in response.json()['data']
```

## 📊 Allure 报告展示

报告包含以下视图：

- **Overview**：测试概览和统计
- **Behaviors**：按 Feature/Story 分类
- **Suites**：按测试套件分类
- **Graphs**：测试趋势图表
- **Timeline**：执行时间线
- **Environment**：环境配置信息

## 🔧 环境配置

### environments.yaml

```yaml
environments:
  local:
    name: "本地环境"
    base_url: "http://localhost:5000"
    readonly: false
    
  jsonplaceholder:
    name: "JSONPlaceholder"
    base_url: "https://jsonplaceholder.typicode.com"
    readonly: true
```

## 📈 测试结果

| 状态         | 数量 |
|-------------|----|
| ✅ PASSED   | 57 |
| ⏭️ SKIPPED  | 0  |
| ❌ FAILED   | 0  |

## 🤝 贡献
欢迎提交 Issue 和 Pull Request！