from __future__ import annotations
import time
import requests
import datetime
from bs4 import BeautifulSoup
from django.db import models
from django.db.models import Max
from django.utils import timezone


# Create your models here.
class News(models.Model):
    """数据模型：新闻资讯表.
    """
    # 可能的新闻类型：
    NEWS_TYPE_CHOICES = {
        1: "头条新闻",
        2: "国内资讯",
        3: "外围资讯",
    }

    # 新闻标题
    title = models.CharField(max_length=1024)
    # 新闻简介
    brief = models.CharField(max_length=10240)
    # 新闻内容
    text = models.TextField()
    # 作者
    author = models.CharField(max_length=512)
    # 出版社
    publisher = models.CharField(max_length=1024)
    # 发布时间
    publication_date = models.DateTimeField(db_index=True)
    # 原文链接
    link = models.CharField(max_length=1024)
    # 新闻类型
    news_type = models.PositiveSmallIntegerField(choices=NEWS_TYPE_CHOICES)

    def __str__(self):
        return self.title

    @staticmethod
    def getTopNews() -> list[News]:
        """返回近期财联社新增头条新闻，不包含数据库已有的部分.
        """
        url = "https://www.cls.cn/v3/depth/home/assembled/1000?" + \
            "app=CailianpressWeb&os=web&sv=8.7.9&" + \
            "sign=b02d8f7bc4c45eeb3e86904203597da2"
        return News._getNews(url, 1)

    @staticmethod
    def getDomesticNews() -> list[News]:
        """返回近期财联社新增国内资讯，不包含数据库已有的部分.
        """
        url = "https://www.cls.cn/v3/depth/home/assembled/1003?" + \
            "app=CailianpressWeb&os=web&sv=8.7.9&" + \
            "sign=b02d8f7bc4c45eeb3e86904203597da2"
        return News._getNews(url, 2)

    @staticmethod
    def getForeignNews() -> list[News]:
        """返回近期财联社新增外围资讯，不包含数据库已有的部分.
        """
        url = "https://www.cls.cn/v3/depth/home/assembled/1007?" + \
            "app=CailianpressWeb&os=web&sv=8.7.9&" + \
            "sign=b02d8f7bc4c45eeb3e86904203597da2"
        return News._getNews(url, 3)

    @staticmethod
    def _getHeader() -> str:
        """返回浏览器伪装 User-Agent 字符串.
        """
        return {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) " +
                "Gecko/20100101 Firefox/102.0"}

    @staticmethod
    def _jsonItem2News(data: dict, news_type: int) -> News:
        link = 'https://www.cls.cn/detail/{}'.format(data['id'])
        response = requests.get(link, headers=News._getHeader())
        # response.text 有时会出错，最好事先指定编码
        response.encoding = 'utf-8'
        if not response.ok:
            raise RuntimeError("数据请求失败：{}".format(link))
        time.sleep(1)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.find("div", class_='detail-content')
        if text is not None:
            text = text.getText()
        else:
            text = ''
        source = soup.find_all("div", class_="f-l m-r-10")
        source = ["", ""] if len(source) < 2 else source[1].getText().split()
        publication_date = datetime.datetime.fromtimestamp(data['ctime']) \
            .replace(tzinfo=timezone.get_current_timezone())
        return News(
            title=data['title'], brief=data['brief'], text=text,
            author="" if len(source) == 1 else source[1], publisher=source[0],
            publication_date=publication_date, link=link, news_type=news_type
        )

    @staticmethod
    def _getNews(url: str, news_type: int) -> list[News]:
        """返回近期财联社新增新闻.

        Args:
            url (str): JSON 接口 URL
            news_type (int): 新闻类型（NEWS_TYPE_CHOICES）

        Returns:
            list[News]: 新增的新闻列表（不包含数据库已有的）
        """
        # 抓取数据
        response = requests.get(url, headers=News._getHeader())
        response.encoding = 'utf-8'
        if not response.ok:
            raise RuntimeError("数据请求失败：{}".format(url))
        data = response.json()['data']
        data = data['top_article'] + data['depth_list']

        # 数据库最新数据的时间
        last_time = timezone.now() + datetime.timedelta(days=-1)
        max_date = News.objects.filter(news_type=news_type) \
            .aggregate(Max("publication_date"))['publication_date__max']
        if max_date is None:
            max_date = last_time
        max_date = timezone.localtime(max_date).replace(tzinfo=None)

        # 新增经过滤的数据
        return [News._jsonItem2News(item, news_type) for item in data
                if datetime.datetime.fromtimestamp(item['ctime']) > max_date]
