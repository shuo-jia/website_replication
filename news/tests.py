from .models import News
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from stock.models import CompositeIndex, SectorMovement, StockFollow, \
    StockPrice


# Create your tests here.
class IndexViewTest(TestCase):
    """主页视图的测试.
    """
    def test_empty(self):
        """空页面测试
        """
        response = self.client.get(reverse("news:index"))
        # 对于一个没有数据的主页，测试其输出
        self.assertContains(response, '暂无新闻')
        self.assertContains(response, '暂无异动数据')
        self.assertContains(response, '暂无指数数据')
        self.assertContains(response, '暂无板块异动数据')
        self.assertContains(response, '暂无热门股票数据')

    def test_news(self):
        """新闻数据测试.
        """
        now = timezone.now()
        for i in range(3):
            News.objects.create(
                title='news title' + str(i), brief='news brief',
                text='news text', author='news author',
                publisher='news publisher', publication_date=now, news_type=i+1
            )
        response = self.client.get(reverse("news:index"))
        self.assertEqual(response.status_code, 200)
        # 测试模板变量是否正确传递
        for i in range(3):
            self.assertContains(response, "news title" + str(i))
        self.assertEqual(len(response.context["top_news_list"]), 1)
        self.assertEqual(len(response.context["domestic_news_list"]), 1)
        self.assertEqual(len(response.context["foreign_news_list"]), 1)

    def test_index(self):
        """指数数据测试.
        """
        index = [['sh000001', 'sz399001', 'sz399006'],
                 ['HSI', 'HSTECH', 'IXIC']]
        now = timezone.now()
        for row in index:
            for code in row:
                CompositeIndex.objects.create(code=code, price=11,
                                              update_time=now)
        CompositeIndex.objects.create(code='sz399006', price=12,
                                      update_time=now + timedelta(days=-8))
        response = self.client.get(reverse("news:index"))
        self.assertEqual(response.status_code, 200)
        # 测试模板变量是否正确传递，应不包含旧的数据（如前面最后创建的数据）
        for row1, row2 in zip(index, response.context["index_list"]):
            for code, index in zip(row1, row2):
                self.assertEqual(index.code, code)
                self.assertEqual(index.price, 11)
                self.assertEqual(index.update_time, now)

    def test_sector(self):
        """板块异动测试.
        """
        now = timezone.now()
        for i in range(4):
            SectorMovement.objects.create(name='板块' + str(i+1), pct_change=4,
                                          update_time=now)
        SectorMovement.objects.create(name='板块' + str(5), pct_change=4,
                                      update_time=now + timedelta(days=-4))
        SectorMovement.objects.create(name='板块' + str(1), pct_change=4,
                                      update_time=now + timedelta(days=-4))
        response = self.client.get(reverse("news:index"))
        self.assertEqual(response.status_code, 200)
        # 测试模板变量是否正确传递，应不包含旧的数据（如前面最后创建的数据）
        for i, sector in enumerate(response.context['sector_list'], start=1):
            self.assertEqual(sector.name, '板块' + str(i))
            self.assertEqual(sector.pct_change, 4)
            self.assertEqual(sector.update_time, now)

    def test_follow(self):
        """热门股票数据测试.
        """
        now = timezone.now()
        for i in range(14):
            StockFollow.objects.create(code=str(i), follow=i, update_time=now)
            StockPrice.objects.create(code=str(i), name='name',
                                      update_time=now)
        StockFollow.objects.create(code=str(3), follow=4,
                                   update_time=now + timedelta(days=-8))
        StockFollow.objects.create(code=str(8), follow=4,
                                   update_time=now + timedelta(days=-8))
        response = self.client.get(reverse("news:index"))
        self.assertEqual(response.status_code, 200)
        # 测试模板变量是否正确传递，股票应按最新关注度从高到低排序
        i = 13
        for row in response.context['stock_follow_list']:
            for stock in row:
                self.assertEqual(stock.code, str(i))
                self.assertEqual(stock.update_time, now)
                i -= 1
