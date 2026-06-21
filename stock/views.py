import json
from time import sleep
from django.urls import reverse
from django.db.models import Max
from django.utils import timezone
from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404
from .models import StockPrice, StockPriceHistory, StockProfitPredict, \
    StockFollow


def getPredictWrap(code: str) -> StockProfitPredict:
    """尝试从数据库拉取股票预测数据（今年），如果不存在则从网络拉取.
    """
    now = timezone.localtime(timezone.now())
    try:
        stock = StockProfitPredict.objects.filter(code=code, year=now.year) \
            .latest('update_time')
    except StockProfitPredict.DoesNotExist:
        data = StockProfitPredict.getPredict(code)
        StockProfitPredict.objects.bulk_create(data)
        stock = data[0]
        sleep(0.4)

    return stock


def getStockNameWrap(code: str) -> str:
    """获取股票名，如果不存在，则股票名暂定为'-'
    """
    try:
        name = StockPrice.objects.filter(code=code).latest('update_time').name
    except StockPrice.DoesNotExist:
        name = '-'
    return name


# Create your views here.
def forecast(request):
    # 展示热门股票的预测
    max_date = StockFollow.objects.aggregate(Max("update_time"))
    max_date = max_date['update_time__max']
    stock_list = StockFollow.objects.filter(update_time=max_date) \
        .order_by("-follow")[:10]
    predict_list = [getPredictWrap(stock.code) for stock in stock_list]
    stock_name_list = [getStockNameWrap(stock.code) for stock in stock_list]

    context = {
        # 实际上 zip() 对象也可作为模板参数
        "stock_list": list(zip(stock_name_list, predict_list)),
    }
    return render(request, "stock/forecast.html", context)


def searchIndex(request):
    return render(request, "stock/search.html", {})


def search(request):
    # 暂不考虑模糊匹配
    if len(request.GET["stock_code"]) < 6:
        raise Http404("Stock does not exist.")
    try:
        stock = StockPrice.objects.filter(
            code__endswith=request.GET["stock_code"]
        ).latest('update_time')
    except StockPrice.DoesNotExist:
        raise Http404("Stock does not exist.")
    return HttpResponseRedirect(reverse("stock:detail", args=(stock.code,)))


def detail(request, code):
    try:
        stock = StockPrice.objects.filter(code=code).latest('update_time')
    except StockPrice.DoesNotExist:
        raise Http404("Stock does not exist.")

    price_list = list(StockPriceHistory.objects.filter(code=code)
                      .order_by('-date')[:90])
    price_list.reverse()
    if len(price_list) == 0:
        # 数据不存在时，从网络拉取数据
        data = StockPriceHistory.getHistory(code)
        StockPriceHistory.objects.bulk_create(data)
        price_list = data[-90:]

    context = {
        "stock_info": stock,
        "x_axis_label": json.dumps([item.date.strftime('%Y-%m-%d')
                                    for item in price_list]),
        "series": json.dumps([
            [item.open_today, item.close_today, item.low, item.high]
            for item in price_list
        ]),
    }
    return render(request, "stock/detail.html", context)
