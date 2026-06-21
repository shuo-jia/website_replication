from __future__ import annotations
import datetime
import akshare as ak
from time import sleep
from django.db import models
from django.utils import timezone


# Create your models here.
class CompositeIndex(models.Model):
    """数据模型：实时股票综合指数表.
    """

    # 综合指数代码
    code = models.CharField('指数代码', max_length=8, db_index=True)
    # 综合指数名称
    name = models.CharField('指数名称', max_length=128, null=True)
    # 综合指数的最新价
    price = models.FloatField('最新价', null=True)
    # 涨跌额
    price_change = models.FloatField('涨跌额', null=True)
    # 涨跌幅（单位 %）
    pct_change = models.FloatField('涨跌幅（单位：%）', null=True)
    # 昨日收盘价
    close_yesterday = models.FloatField('昨日收盘价', null=True)
    # 今日开盘价
    open_today = models.FloatField('今日开盘价', null=True)
    # 最高价
    high = models.FloatField('最高价', null=True)
    # 最低价
    low = models.FloatField('最低价', null=True)
    # 成交量（单位：手）
    volume = models.FloatField('成交量（单位：手）', null=True)
    # 成交额（单位：元）
    turnover = models.FloatField('成交额（单位：元）', null=True)
    # 更新时间
    update_time = models.DateTimeField('更新时间', db_index=True)

    def __str__(self):
        return '{}-{}-{}'.format(self.code, self.name, self.update_time)

    @staticmethod
    def getLatestAStock() -> list[CompositeIndex]:
        """获取 A 股实时指数.
        """
        data = ak.stock_zh_index_spot_sina()
        now = timezone.now()
        return [CompositeIndex(
            code=item[1]['代码'], name=item[1]['名称'], price=item[1]['最新价'],
            price_change=item[1]['涨跌额'], pct_change=item[1]['涨跌幅'],
            close_yesterday=item[1]['昨收'], open_today=item[1]['今开'],
            high=item[1]['最高'], low=item[1]['最低'], volume=item[1]['成交量'],
            turnover=item[1]['成交额'], update_time=now
        ) for item in data.iterrows()]

    @staticmethod
    def getLatestHKStock() -> list[CompositeIndex]:
        """获取港股实时指数.
        """
        try:
            now = timezone.now()
            data = ak.stock_hk_index_spot_sina()
            return [CompositeIndex(
                code=item[1]['代码'], name=item[1]['名称'],
                price=item[1]['最新价'], price_change=item[1]['涨跌额'],
                pct_change=item[1]['涨跌幅'], close_yesterday=item[1]['昨收'],
                open_today=item[1]['今开'], high=item[1]['最高'],
                low=item[1]['最低'], update_time=now
            ) for item in data.iterrows()]
        except ValueError:
            # 接口 stock_hk_index_spot_sina() 有时会禁 IP。如果禁了 IP，那就从
            # 历史数据中获取上一交易日的数据。下面的两个指数是主页需要的。
            data1 = ak.stock_hk_index_daily_sina(symbol='HSI')
            sleep(0.5)
            data2 = ak.stock_hk_index_daily_sina(symbol='HSTECH')
            chg1 = data1.iloc[-1]['close'] - data1.iloc[-2]['close']
            chg2 = data2.iloc[-1]['close'] - data2.iloc[-2]['close']
            pct_chg1 = chg1 / data1.iloc[-2]['close'] * 100
            pct_chg2 = chg2 / data2.iloc[-2]['close'] * 100
            data = [('HSI', '恒生指数', data1, chg1, pct_chg1),
                    ('HSTECH', '恒生科技指数', data2, chg2, pct_chg2)]
            return [CompositeIndex(
                code=item[0], name=item[1], price=item[2].iloc[-1]['close'],
                price_change=item[3], pct_change=item[4],
                close_yesterday=item[2].iloc[-2]['close'],
                open_today=item[2].iloc[-1]['open'],
                high=item[2].iloc[-1]['high'], low=item[2].iloc[-1]['low'],
                volume=item[2].iloc[-1]['volume'],
                update_time=datetime.datetime.combine(
                        item[2].iloc[-1]['date'], datetime.time(23, 59, 59)
                    ).replace(tzinfo=timezone.get_current_timezone())
            ) for item in data]

    @staticmethod
    def getLatestUSStock() -> list[CompositeIndex]:
        """获取美股指数数据（非实时，只能得到已收盘数据）.
        """
        args = (
            (".INX", "标普 500 指数"),
            (".IXIC", "纳斯达克综合指数"),
            (".DJI", "道琼斯指数"),
            (".NDX", "纳斯达克 100 指数"),
        )
        result = []
        now = timezone.now()
        for (code, name) in args:
            data = ak.index_us_stock_sina(symbol=code)
            last = data.iloc[-2]
            curr = data.iloc[-1]
            chg = curr['close'] - last['close']
            result.append(CompositeIndex(
                code=code[1:], name=name, price=curr['close'],
                price_change=chg, pct_change=chg / last['close'] * 100,
                close_yesterday=last['close'], open_today=curr['open'],
                high=curr['high'], low=curr['low'], volume=curr['volume'],
                update_time=now
            ))
        return result


class SectorMovement(models.Model):
    """数据模型：板块异动表.
    """

    # 板块名称
    name = models.CharField('板块名称', max_length=128)
    # 板块涨跌幅
    pct_change = models.FloatField('涨跌幅（单位：%）', null=True)
    # 板块异动总次数
    movement_count = models.IntegerField('板块异动总次数', db_index=True,
                                         null=True)
    # 主力净流入
    net_inflow = models.FloatField('主力净流入（单位：万元）', null=True)
    # 异动最频繁的个股（股票代码）
    stock_code = models.CharField('异动最频繁个股（股票代码）', max_length=8,
                                  null=True)
    # 异动最频繁的个股（股票名称）
    stock_name = models.CharField('异动最频繁个股（股票名称）', max_length=128,
                                  null=True)
    # 更新时间
    update_time = models.DateTimeField('更新时间', db_index=True)

    def __str__(self):
        return '{}-{}'.format(self.name, self.update_time)

    @staticmethod
    def getLatestData() -> list[SectorMovement]:
        """返回抓取的最新数据.
        """
        data = ak.stock_board_change_em()
        now = timezone.now()
        return [SectorMovement(
            name=item[1]['板块名称'], pct_change=item[1]['涨跌幅'],
            movement_count=item[1]['板块异动总次数'],
            net_inflow=item[1]['主力净流入'],
            stock_code=item[1]['板块异动最频繁个股及所属类型-股票代码'],
            stock_name=item[1]['板块异动最频繁个股及所属类型-股票名称'],
            update_time=now
        ) for item in data.iterrows()]


class StockPrice(models.Model):
    """股价表
    """

    # 股票代码
    code = models.CharField('股票代码', max_length=8, db_index=True)
    # 股票名称
    name = models.CharField('股票名称', max_length=128, null=True)
    # 最新价
    price = models.FloatField('最新价', null=True)
    # 涨跌额
    price_change = models.FloatField('涨跌额', null=True)
    # 涨跌幅（单位 %）
    pct_change = models.FloatField('涨跌幅（单位：%）', null=True)
    # 昨日收盘价
    close_yesterday = models.FloatField('昨日收盘价', null=True)
    # 今日开盘价
    open_today = models.FloatField('今日开盘价', null=True)
    # 最高价
    high = models.FloatField('最高价', null=True)
    # 最低价
    low = models.FloatField('最低价', null=True)
    # 成交量（单位：手）
    volume = models.FloatField('成交量（单位：手）', null=True)
    # 成交额（单位：元）
    turnover = models.FloatField('成交额（单位：元）', null=True)
    # 更新时间
    update_time = models.DateTimeField('更新时间', db_index=True)

    def __str__(self):
        return '{}-{}-{}'.format(self.code, self.name, self.update_time)

    @staticmethod
    def getLatestData() -> list[StockPrice]:
        """返回抓取的最新数据（由于反爬的问题，不可连续抓取，需等待几分钟）.
        """
        data = ak.stock_zh_a_spot()
        now = timezone.now()
        return [StockPrice(
            code=item[1]['代码'], name=item[1]['名称'], price=item[1]['最新价'],
            price_change=item[1]['涨跌额'], pct_change=item[1]['涨跌幅'],
            close_yesterday=item[1]['昨收'], open_today=item[1]['今开'],
            high=item[1]['最高'], low=item[1]['最低'],
            volume=item[1]['成交量'] / 100, turnover=item[1]['成交额'],
            update_time=now
        ) for item in data.iterrows()]


class StockFollow(models.Model):
    """股价热度表
    """

    # 股票代码
    code = models.CharField('股票代码', max_length=8, db_index=True)
    # 关注
    follow = models.IntegerField('股票关注数', null=True)
    # 更新时间
    update_time = models.DateTimeField('更新时间', db_index=True)

    def __str__(self):
        return "{}-{}-{}".format(self.code, self.follow, self.update_time)

    @staticmethod
    def getLatestData() -> list[StockPrice]:
        """返回抓取的最新数据（本周新增关注）.
        """
        data = ak.stock_hot_follow_xq(symbol="本周新增")
        now = timezone.now()
        return [StockFollow(
            code=item[1]['股票代码'].lower(), follow=item[1]['关注'],
            update_time=now
        ) for item in data.iterrows()]


class StockPriceHistory(models.Model):
    """历史股价表.
    """
    # 股票代码
    code = models.CharField('股票代码', max_length=8, db_index=True)
    # 今日收盘价
    close_today = models.FloatField('今日收盘价', null=True)
    # 今日开盘价
    open_today = models.FloatField('今日开盘价', null=True)
    # 最高价
    high = models.FloatField('最高价', null=True)
    # 最低价
    low = models.FloatField('最低价', null=True)
    # 成交量（单位：手）
    volume = models.FloatField('成交量（单位：手）', null=True)
    # 交易日
    date = models.DateField('交易日', db_index=True)

    def __str__(self):
        return '{}-{}'.format(self.code, self.date)

    @staticmethod
    def getHistory(code: str) -> list[StockPriceHistory]:
        """获取给定股票近十年 K 线数据（股票代码必须包含交易所前缀）.
        """
        now = timezone.localtime(timezone.now())
        end_date = now.strftime('%Y%m%d')
        start_date = str(now.year - 10) + end_date[-4:]
        data = ak.stock_zh_a_hist_tx(symbol=code, start_date=start_date,
                                     end_date=end_date)
        return [StockPriceHistory(
            code=code, close_today=item[1]['open'],
            open_today=item[1]['close'], high=item[1]['high'],
            low=item[1]['low'], volume=item[1]['amount'],
            date=item[1]['date']
        ) for item in data.iterrows()]


class StockProfitPredict(models.Model):
    """股票净利润预测表
    """
    # 股票代码
    code = models.CharField('股票代码', max_length=8, db_index=True)
    # 年度
    year = models.PositiveSmallIntegerField('年度')
    # 预测机构数
    institution = models.IntegerField('预测机构数', null=True)
    # 最小值
    min_profit = models.FloatField('最小值', null=True)
    # 均值
    avg_profit = models.FloatField('均值', null=True)
    # 最大值
    max_profit = models.FloatField('最大值', null=True)
    # 更新时间
    update_time = models.DateTimeField('更新时间', db_index=True)

    def __str__(self):
        return '{}-{}-{}'.format(self.code, self.year, self.update_time)

    @staticmethod
    def getPredict(code: str) -> list[StockProfitPredict]:
        """获取给定股票利润预测数据.
        """
        data = ak.stock_profit_forecast_ths(symbol=code[-6:],
                                            indicator="预测年报净利润")
        now = timezone.now()

        return [StockProfitPredict(
            code=code, year=item[1]['年度'],
            institution=item[1]['预测机构数'],
            min_profit=item[1]['最小值'],
            avg_profit=item[1]['均值'],
            max_profit=item[1]['最大值'],
            update_time=now,
        ) for item in data.iterrows()]
