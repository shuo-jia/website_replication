from .models import News
from django.db.models import Max
from django.utils import timezone
from django.shortcuts import render
from stock.models import CompositeIndex, SectorMovement, StockFollow, \
    StockPrice


def getRecentNewsWrap(news_type: int) -> list[News]:
    """返回最近 5 条新闻（如为空，返回一条标题为'暂无新闻'的新闻）.
    """
    news_list = News.objects.filter(news_type=news_type) \
        .order_by("-publication_date")[:5]
    if len(news_list) == 0:
        now = timezone.now()
        news_list = [News(title='暂无新闻', publication_date=now)]
    return news_list


def getIndexWrap(code: str) -> CompositeIndex:
    """返回指数数据（如为空，返回名为'暂无指数数据'的指数
    """
    try:
        obj = CompositeIndex.objects.filter(code=code).latest('update_time')
    except CompositeIndex.DoesNotExist:
        now = timezone.now()
        obj = CompositeIndex(code='000000', name='暂无指数数据', price=0,
                             price_change=0, pct_change=0, update_time=now)
    return obj


# Create your views here.
def index(request):
    # 新闻数据
    top_news_list = getRecentNewsWrap(1)
    domestic_news_list = getRecentNewsWrap(2)
    foreign_news_list = getRecentNewsWrap(3)

    # 指数数据
    index = [['sh000001', 'sz399001', 'sz399006'], ['HSI', 'HSTECH', 'IXIC']]
    index_query = []
    for row in index:
        index_query.append([getIndexWrap(code) for code in row])

    # 板块数据（如无数据，sector_list 将是空集）
    max_date = SectorMovement.objects.aggregate(Max("update_time"))
    max_date = max_date['update_time__max']
    sector_list = SectorMovement.objects.filter(update_time=max_date) \
        .order_by("-movement_count")[:10]

    # 热门股票数据（如无数据，stock_follow_list 将包含两个空集）
    max_date = StockFollow.objects.aggregate(Max("update_time"))
    max_date = max_date['update_time__max']
    stock_list = StockFollow.objects.filter(update_time=max_date) \
        .order_by("-follow")[:10]
    max_date = StockPrice.objects.aggregate(Max("update_time"))
    max_date = max_date['update_time__max']
    stock_follow_list = [
        [StockPrice.objects.get(code=stock.code, update_time=max_date)
         for stock in stock_list[:5]],
        [StockPrice.objects.get(code=stock.code, update_time=max_date)
         for stock in stock_list[5:]],
    ]
    context = {
        "top_news_list": list(top_news_list),
        "domestic_news_list": list(domestic_news_list),
        "foreign_news_list": list(foreign_news_list),
        "index_list": index_query,
        "sector_list": list(sector_list),
        "stock_follow_list": stock_follow_list,
    }

    return render(request, "news/index.html", context)
