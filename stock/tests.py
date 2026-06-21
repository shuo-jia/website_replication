import json
from django.test import TestCase
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from .models import StockPriceHistory, StockPrice, StockProfitPredict, \
    StockFollow


# Create your tests here.
class DetailViewTest(TestCase):
    """股票详情视图测试.
    """
    def test_empty_database(self):
        """空数据库的测试，应返回 404.
        """
        url = reverse("stock:detail", args=('sz000001', ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_error_stock_code(self):
        """不存在的股票代码应返回 404.
        """
        now = timezone.now()
        StockPrice.objects.create(code='sz000001', update_time=now)
        url = reverse("stock:detail", args=('sz000002', ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_history_data_in_database(self):
        """测试从数据库取数的 K 线图.
        """
        now = timezone.now()
        StockPrice.objects.create(code='sz000001', update_time=now)
        for i in range(10):
            StockPriceHistory.objects.create(
                code='sz000001', close_today=i+20, open_today=i+10, high=i+30,
                low=i+5, volume=44,
                date=now.date() + timedelta(days=i)
            )
        url = reverse("stock:detail", args=('sz000001', ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['stock_info'].code, 'sz000001')
        i = 0
        for (label, price) in zip(json.loads(response.context['x_axis_label']),
                                  json.loads(response.context['series'])):
            date = now.date() + timedelta(days=i)
            self.assertEqual(label, date.strftime('%Y-%m-%d'))
            self.assertEqual(price[0], i+10)
            self.assertEqual(price[1], i+20)
            self.assertEqual(price[2], i+5)
            self.assertEqual(price[3], i+30)
            i += 1


class ForecastViewTest(TestCase):
    """股票利润预测视图测试.
    """
    def test_empty_database(self):
        """空数据库的测试，应能正常访问.
        """
        response = self.client.get(reverse("stock:forecast"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['stock_list']), 0)

    def test_with_some_data(self):
        """加入一些人造数据的测试.
        """
        now = timezone.localtime(timezone.now())
        StockProfitPredict.objects.create(code='sz000001', year=now.year,
                                          avg_profit=111, update_time=now)
        StockProfitPredict.objects.create(code='sz000001', year=now.year+1,
                                          avg_profit=112, update_time=now)
        StockProfitPredict.objects.create(code='sz000001', year=now.year+2,
                                          avg_profit=113, update_time=now)
        # 如果 StockFollow 表无数据，即无热门股票，则输出为空
        response = self.client.get(reverse("stock:forecast"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['stock_list']), 0)
        # 如果 StockPrice 表无相关股票，股票名应为'-'
        StockFollow.objects.create(code='sz000001', update_time=now)
        response = self.client.get(reverse("stock:forecast"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['stock_list'][0][0], '-')
        self.assertEqual(response.context['stock_list'][0][1].year, now.year)
        self.assertEqual(response.context['stock_list'][0][1].avg_profit, 111)
        # 如果 StockPrice 表有相关股票，股票名应正确显示
        StockPrice.objects.create(code='sz000001', name='平安银行',
                                  update_time=now)
        StockPrice.objects.create(code='sz000001', name='-',
                                  update_time=now + timedelta(days=-8))
        response = self.client.get(reverse("stock:forecast"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['stock_list'][0][0], '平安银行')
