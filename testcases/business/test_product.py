"""
商品模块测试用例
"""
import pytest
import allure
from common.assert_helper import AssertHelper


@allure.feature("商品模块")
class TestProduct:

    @allure.story("商品列表")
    @allure.title("测试获取商品列表")
    def test_get_products(self, api_client):
        """测试获取商品列表"""
        response = api_client.get('/api/products')

        AssertHelper.assert_status_code(response, 200)
        AssertHelper.assert_business_code(response, 200)

        data = response.json()['data']
        AssertHelper.assert_field_exists(data, 'list')
        AssertHelper.assert_field_exists(data, 'total')
        AssertHelper.assert_field_exists(data, 'page')
        AssertHelper.assert_field_exists(data, 'pageSize')

        # 验证列表不为空
        assert len(data['list']) > 0, "商品列表为空"

    @allure.story("商品列表")
    @allure.title("测试分页功能")
    @pytest.mark.parametrize("page,page_size", [
        (1, 2),
        (1, 5),
        (2, 2),
        (1, 20),
    ])
    def test_product_pagination(self, api_client, page, page_size):
        """测试分页功能"""
        response = api_client.get('/api/products', params={
            'page': page,
            'pageSize': page_size
        })

        AssertHelper.assert_status_code(response, 200)
        data = response.json()['data']

        assert data['page'] == page
        assert data['pageSize'] == page_size
        assert len(data['list']) <= page_size

    @allure.story("商品搜索")
    @allure.title("测试商品搜索")
    @pytest.mark.parametrize("keyword,expected_min_count", [
        ("小米", 1),
        ("华为", 1),
        ("iPhone", 1),
        ("不存在的商品", 0),
    ])
    def test_search_products(self, api_client, keyword, expected_min_count):
        """测试商品搜索功能"""
        response = api_client.get('/api/products', params={'keyword': keyword})

        AssertHelper.assert_status_code(response, 200)
        data = response.json()['data']

        assert len(data['list']) >= expected_min_count

        # 验证搜索结果包含关键词
        if expected_min_count > 0:
            for product in data['list']:
                assert keyword in product['name']

    @allure.story("商品详情")
    @allure.title("测试获取商品详情")
    def test_get_product_detail(self, api_client):
        """测试获取商品详情"""
        response = api_client.get('/api/products/1')

        AssertHelper.assert_status_code(response, 200)
        AssertHelper.assert_business_code(response, 200)

        data = response.json()['data']
        AssertHelper.assert_field_exists(data, 'id')
        AssertHelper.assert_field_exists(data, 'name')
        AssertHelper.assert_field_exists(data, 'price')
        AssertHelper.assert_field_exists(data, 'stock')
        AssertHelper.assert_field_exists(data, 'description')

        assert data['id'] == 1

    @allure.story("商品详情")
    @allure.title("测试获取不存在的商品")
    def test_get_product_not_exist(self, api_client):
        """测试获取不存在的商品"""
        response = api_client.get('/api/products/99999')

        AssertHelper.assert_status_code(response, 404)
        AssertHelper.assert_business_code(response, 404)

    @allure.story("商品分类")
    @allure.title("测试获取商品分类")
    def test_get_categories(self, api_client):
        """测试获取商品分类"""
        response = api_client.get('/api/categories')

        AssertHelper.assert_status_code(response, 200)
        AssertHelper.assert_business_code(response, 200)

        categories = response.json()['data']
        assert len(categories) > 0

        # 验证分类结构
        for category in categories:
            AssertHelper.assert_field_exists(category, 'id')
            AssertHelper.assert_field_exists(category, 'name')