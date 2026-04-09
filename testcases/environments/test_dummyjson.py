"""
DummyJSON 环境独立测试
API 文档: https://dummyjson.com/docs
"""
import pytest
import allure
from common.api_client import APIClient
from common.assert_helper import AssertHelper


@allure.feature("DummyJSON环境")
class TestDummyJSONEnv:
    """DummyJSON 电商 API 测试"""

    @allure.story("连接测试")
    @allure.title("验证环境可访问")
    def test_environment_reachable(self):
        """测试环境是否可访问"""
        client = APIClient(env="dummyjson")
        response = client.get('/products/1')
        AssertHelper.assert_status_code(response, 200)
        print("✅ DummyJSON 环境正常")

    @allure.story("商品接口")
    @allure.title("获取商品列表")
    def test_get_products(self):
        """GET /products - 获取商品列表"""
        client = APIClient(env="dummyjson")
        response = client.get('/products?limit=10')

        AssertHelper.assert_status_code(response, 200)
        data = response.json()
        assert 'products' in data
        assert 'total' in data
        assert 'limit' in data
        assert len(data['products']) <= 10

    @allure.story("商品接口")
    @allure.title("获取商品列表（分页）")
    @pytest.mark.parametrize("skip,limit", [
        (0, 10),
        (10, 10),
        (20, 5)
    ])
    def test_get_products_pagination(self, skip, limit):
        """GET /products?skip=&limit= - 分页测试"""
        client = APIClient(env="dummyjson")
        response = client.get(f'/products?skip={skip}&limit={limit}')

        AssertHelper.assert_status_code(response, 200)
        data = response.json()
        assert len(data['products']) <= limit

    @allure.story("商品接口")
    @allure.title("获取单个商品")
    def test_get_product_by_id(self):
        """GET /products/{id} - 获取指定商品"""
        client = APIClient(env="dummyjson")
        response = client.get('/products/1')

        AssertHelper.assert_status_code(response, 200)
        product = response.json()
        assert product['id'] == 1
        assert 'title' in product
        assert 'price' in product
        assert 'description' in product
        assert 'brand' in product

    @allure.story("商品接口")
    @allure.title("获取不存在的商品")
    def test_get_product_not_exist(self):
        """GET /products/{id} - 获取不存在的商品"""
        client = APIClient(env="dummyjson")
        response = client.get('/products/99999')

        # DummyJSON 返回 404
        assert response.status_code == 404

    @allure.story("搜索功能")
    @allure.title("商品搜索")
    @pytest.mark.parametrize("keyword,expected_min", [
        ("phone", 1),
        ("laptop", 1),
        ("watch", 1),
        ("nonexistent", 0)
    ])
    def test_search_products(self, keyword, expected_min):
        """GET /products/search?q= - 搜索商品"""
        client = APIClient(env="dummyjson")
        response = client.get(f'/products/search?q={keyword}')

        AssertHelper.assert_status_code(response, 200)
        data = response.json()
        assert 'products' in data
        assert len(data['products']) >= expected_min

    @allure.story("分类功能")
    @allure.title("获取商品分类")
    def test_get_categories(self):
        """GET /products/categories - 获取所有分类"""
        client = APIClient(env="dummyjson")
        response = client.get('/products/categories')

        AssertHelper.assert_status_code(response, 200)
        categories = response.json()
        assert len(categories) > 0

        # 检查分类名称（API 返回的是对象数组）
        category_names = [c['name'] for c in categories]
        assert "Smartphones" in category_names or "Laptops" in category_names
        print(f"✅ 共 {len(categories)} 个分类")

    @allure.story("分类功能")
    @allure.title("获取指定分类的商品")
    @pytest.mark.parametrize("category", ["smartphones", "laptops", "fragrances"])
    def test_get_products_by_category(self, category):
        """GET /products/category/{category} - 获取分类商品"""
        client = APIClient(env="dummyjson")
        response = client.get(f'/products/category/{category}')

        AssertHelper.assert_status_code(response, 200)
        data = response.json()
        assert 'products' in data
        for product in data['products']:
            assert product['category'] == category

    @allure.story("购物车接口")
    @allure.title("获取购物车")
    def test_get_carts(self):
        """GET /carts - 获取购物车列表"""
        client = APIClient(env="dummyjson")
        response = client.get('/carts')

        AssertHelper.assert_status_code(response, 200)
        data = response.json()
        assert 'carts' in data
        assert len(data['carts']) > 0

    @allure.story("购物车接口")
    @allure.title("获取用户购物车")
    def test_get_cart_by_user(self):
        """GET /carts/user/{id} - 获取用户购物车"""
        client = APIClient(env="dummyjson")
        response = client.get('/carts/user/1')

        AssertHelper.assert_status_code(response, 200)
        data = response.json()
        assert 'carts' in data

    @allure.story("认证接口")
    @allure.title("用户登录")
    def test_auth_login(self):
        """POST /auth/login - 用户登录"""
        client = APIClient(env="dummyjson")
        response = client.post('/auth/login', json={
            "username": "emilys",
            "password": "emilyspass"
        })

        AssertHelper.assert_status_code(response, 200)
        data = response.json()
        # DummyJSON 返回 accessToken 而不是 token
        assert 'accessToken' in data
        assert data['username'] == "emilys"
        assert data['id'] == 1
        print(f"✅ 登录成功，用户: {data['username']}")