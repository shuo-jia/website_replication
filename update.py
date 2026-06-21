import os
import django
import argparse
import datetime
from django.db.models import Max


def updateNews():
    """更新新闻数据.
    """
    from news.models import News
    from django.utils import timezone
    new_items = News.getTopNews() + News.getDomesticNews() + \
        News.getForeignNews()
    News.objects.bulk_create(new_items)

    # 仅保留 7 天数据
    oldest_date = timezone.now() - datetime.timedelta(days=7)
    News.objects.filter(publication_date__lt=oldest_date).delete()


def updateStock():
    """更新股票数据（除去历史 K 线数据之外）.
    """
    from stock import models as custom_models
    from django.utils import timezone
    # 更新股票指数
    new_items = custom_models.CompositeIndex.getLatestAStock() + \
        custom_models.CompositeIndex.getLatestUSStock() + \
        custom_models.CompositeIndex.getLatestUSStock()
    custom_models.CompositeIndex.objects.bulk_create(new_items)

    # 更新板块异动表
    new_items = custom_models.SectorMovement.getLatestData()
    custom_models.SectorMovement.objects.bulk_create(new_items)

    # 更新股价表
    new_items = custom_models.StockPrice.getLatestData()
    custom_models.StockPrice.objects.bulk_create(new_items)

    # 更新股票热度表
    new_items = custom_models.StockFollow.getLatestData()
    custom_models.StockFollow.objects.bulk_create(new_items)

    # 仅保留 7 天数据
    oldest_date = timezone.now() - datetime.timedelta(days=7)
    custom_models.CompositeIndex.objects.filter(update_time__lt=oldest_date) \
        .delete()
    custom_models.SectorMovement.objects.filter(update_time__lt=oldest_date) \
        .delete()
    custom_models.StockPrice.objects.filter(update_time__lt=oldest_date) \
        .delete()
    custom_models.StockFollow.objects.filter(update_time__lt=oldest_date) \
        .delete()

    # 对于 StockProfitPredict 表，保留 30 天数据
    oldest_date = timezone.now() - datetime.timedelta(days=30)
    custom_models.StockProfitPredict.objects.filter(
        update_time__lt=oldest_date
    ).delete()


def updateStockHistory():
    """更新 K 线数据.
    """
    from stock.models import StockPriceHistory, StockPrice
    # 每个股票历史数据的最新日期
    stock_history = StockPriceHistory.objects.values('code') \
        .annotate(max_date=Max('date'))
    data = []
    for stock in stock_history:
        # StockPrice 表给出了最近一段时间内股票的当日数据，
        # 此处得到股票当天内最新数据的插入时间
        stock_time = StockPrice.objects.filter(
                code=stock['code'], update_time__date__gt=stock['max_date']
        ).values('update_time__date').annotate(max_time=Max('update_time'))
        # 从每天最新插入数据的时间得到最新插入数据
        new_data = [StockPrice.objects.filter(
            code=stock['code'], update_time=item['max_time']
        ) for item in stock_time]
        # 构造 StockPriceHistory 类型的变量
        data.extend([StockPriceHistory(
            code=item[0].code, close_today=item[0].price,
            open_today=item[0].open_today, high=item[0].high, low=item[0].low,
            volume=item[0].volume, date=item[0].update_time.date()
        ) for item in new_data])
    StockPriceHistory.objects.bulk_create(data)


if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    parser = argparse.ArgumentParser(
            prog='update',
            description='股票资讯数据更新程序.'
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--news', action='store_true', help='更新新闻资讯')
    group.add_argument('--stock', action='store_true', help='更新股票实时数据')
    group.add_argument('--history-price', action='store_true',
                       help='更新股票历史 K 线数据')

    args = parser.parse_args()
    if args.news is True:
        updateNews()
    elif args.stock is True:
        updateStock()
    elif args.history_price is True:
        updateStockHistory()
