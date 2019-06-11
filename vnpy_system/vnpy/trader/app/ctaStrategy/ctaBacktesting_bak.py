# encoding: UTF-8

'''
本文件中包含的是CTA模块的回测引擎，回测引擎的API和CTA引擎一致，
可以使用和实盘相同的代码进行回测。
'''
from __future__ import division
from __future__ import print_function

from datetime import datetime, timedelta
from collections import OrderedDict
from itertools import product
import multiprocessing
import copy

import pymongo
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from vnpy.rpc import RpcClient, RpcServer, RemoteException
import prettytable as pt
import sys
import os

# 如果安装了seaborn则设置为白色风格
try:
    import seaborn as sns       
    sns.set_style('whitegrid')  
except ImportError:
    pass

from vnpy.trader.vtGlobal import globalSetting
from vnpy.trader.vtObject import VtTickData, VtBarData
from vnpy.trader.vtConstant import *
from vnpy.trader.vtGateway import VtOrderData, VtTradeData

from .ctaBase import *


########################################################################
class BacktestingEngine(object):
    """
    CTA回测引擎
    函数接口和策略引擎保持一样，
    从而实现同一套代码从回测到实盘。
    """
    
    TICK_MODE = 'tick'
    BAR_MODE = 'bar'

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        # 本地停止单
        self.stopOrderCount = 0     # 编号计数：stopOrderID = STOPORDERPREFIX + str(stopOrderCount)
        
        # 本地停止单字典, key为stopOrderID，value为stopOrder对象
        self.stopOrderDict = {}             # 停止单撤销后不会从本字典中删除
        self.workingStopOrderDict = {}      # 停止单撤销后会从本字典中删除
        
        self.engineType = ENGINETYPE_BACKTESTING    # 引擎类型为回测
        
        self.outputshow = True      # outputshow是否显示
        
        self.strategy = None        # 回测策略
        self.mode = self.BAR_MODE   # 回测模式，默认为K线
        
        self.startDate = ''
        self.initDays = 0        
        self.endDate = ''

        self.capital = 1000000      # 回测时的起始本金（默认100万）
        self.interest= self.capital # 回测时的权益
        self.slippage = 0           # 回测时假设的滑点
        self.rate = 0               # 回测时假设的佣金比例（适用于百分比佣金）
        self.size = 1               # 合约大小，默认为1    
        self.priceTick = 0          # 价格最小变动 
        
        self.dbClient = None        # 数据库客户端
        self.dbCursor = None        # 数据库指针
        self.hdsClient = None       # 历史数据服务器客户端
        
        self.initData = []          # 初始化用的数据
        self.dbName = ''            # 回测数据库名
        self.symbol = ''            # 回测集合名
        
        self.dataStartDate = None       # 回测数据开始日期，datetime对象
        self.dataEndDate = None         # 回测数据结束日期，datetime对象
        self.strategyStartDate = None   # 策略启动日期（即前面的数据用于初始化），datetime对象
        
        self.limitOrderCount = 0                    # 限价单编号
        self.limitOrderDict = OrderedDict()         # 限价单字典
        self.workingLimitOrderDict = OrderedDict()  # 活动限价单字典，用于进行撮合用
        
        self.tradeCount = 0             # 成交编号
        self.tradeDict = OrderedDict()  # 成交字典
        
        self.logList = []               # 日志记录
        
        self.poolscount=[0,0]       #根据运行参数确定的计算的总次数,已经执行结束的参数的次数
        
        # 当前最新数据，用于模拟成交用
        self.tick = None
        self.bar = None
        self.dt = None      # 最新的时间
        
        # 日线回测结果计算用
        self.dailyResultDict = OrderedDict()
    
    #------------------------------------------------
    # 通用功能
    #------------------------------------------------    
    
    #----------------------------------------------------------------------
    def roundToPriceTick(self, price):
        """取整价格到合约最小价格变动"""
        if not self.priceTick:
            return price
        
        newPrice = round(price/self.priceTick, 0) * self.priceTick
        return newPrice

    #----------------------------------------------------------------------
    def output(self, content):
        """输出内容"""
        if self.outputshow :
            print(str(datetime.now()) + "\t" + content)     
        pass
        
        
    #------------------------------------------------
    # 参数设置相关
    #------------------------------------------------
    
    #----------------------------------------------------------------------
    def setStartDate(self, startDate='20100416', initDays=10):
        """设置回测的启动日期"""
        self.startDate = startDate
        self.initDays = initDays
        
        self.dataStartDate = datetime.strptime(startDate, '%Y%m%d')
        
        initTimeDelta = timedelta(initDays)
        self.strategyStartDate = self.dataStartDate + initTimeDelta
        
    #----------------------------------------------------------------------
    def setEndDate(self, endDate=''):
        """设置回测的结束日期"""
        self.endDate = endDate
        
        if endDate:
            self.dataEndDate = datetime.strptime(endDate, '%Y%m%d')
            
            # 若不修改时间则会导致不包含dataEndDate当天数据
            self.dataEndDate = self.dataEndDate.replace(hour=23, minute=59)    
        
    #----------------------------------------------------------------------
    def setBacktestingMode(self, mode):
        """设置回测模式"""
        self.mode = mode
    
    #----------------------------------------------------------------------
    def setDatabase(self, dbName, symbol):
        """设置历史数据所用的数据库"""
        self.dbName = dbName
        self.symbol = symbol
    
    #----------------------------------------------------------------------
    def setCapital(self, capital):
        """设置资本金"""
        self.capital = capital
        self.interest= capital
    
    #----------------------------------------------------------------------
    def setSlippage(self, slippage):
        """设置滑点点数"""
        self.slippage = slippage
        
    #----------------------------------------------------------------------
    def setSize(self, size):
        """设置合约大小"""
        self.size = size
        
    #----------------------------------------------------------------------
    def setRate(self, rate):
        """设置佣金比例"""
        self.rate = rate
        
    #----------------------------------------------------------------------
    def setPriceTick(self, priceTick):
        """设置价格最小变动"""
        self.priceTick = priceTick
    
    #------------------------------------------------
    # 数据回放相关
    #------------------------------------------------    
    
    #----------------------------------------------------------------------
    def initHdsClient(self):
        """初始化历史数据服务器客户端"""
        reqAddress = 'tcp://localhost:5555'
        subAddress = 'tcp://localhost:7777'   
        
        self.hdsClient = RpcClient(reqAddress, subAddress)
        self.hdsClient.start()
    
    #----------------------------------------------------------------------
    def loadHistoryData(self):
        """载入历史数据"""
        self.dbClient = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
        collection = self.dbClient[self.dbName][self.symbol]          

        self.output(u'开始载入数据')
        
        # 首先根据回测模式，确认要使用的数据类
        if self.mode == self.BAR_MODE:
            dataClass = VtBarData
            func = self.newBar
        else:
            dataClass = VtTickData
            func = self.newTick

        # 载入初始化需要用的数据        
        if self.hdsClient:
            initCursor = self.hdsClient.loadHistoryData(self.dbName,
                                                        self.symbol,
                                                        self.dataStartDate,
                                                        self.strategyStartDate)
        else:
            flt = {'datetime':{'$gte':self.dataStartDate,
                               '$lt':self.strategyStartDate}}        
            initCursor = collection.find(flt).sort('datetime')
        
        # 将数据从查询指针中读取出，并生成列表
        self.initData = []              # 清空initData列表
        for d in initCursor:
            data = dataClass()
            data.__dict__ = d
            self.initData.append(data)      
        
        # 载入回测数据
        if self.hdsClient:
            self.dbCursor = self.hdsClient.loadHistoryData(self.dbName,
                                                           self.symbol,
                                                           self.strategyStartDate,
                                                           self.dataEndDate)
        else:
            if not self.dataEndDate:
                flt = {'datetime':{'$gte':self.strategyStartDate}}   # 数据过滤条件
            else:
                flt = {'datetime':{'$gte':self.strategyStartDate,
                                   '$lte':self.dataEndDate}}  
            self.dbCursor = collection.find(flt).sort('datetime')
        
        if isinstance(self.dbCursor, list):
            count = len(initCursor) + len(self.dbCursor)
        else:
            count = initCursor.count() + self.dbCursor.count()
        self.output(u'载入完成，数据量：%s' %count)
        
    #----------------------------------------------------------------------
    def runBacktesting(self):
        """运行回测"""
        # 载入历史数据
        self.loadHistoryData()
        
        # 首先根据回测模式，确认要使用的数据类
        if self.mode == self.BAR_MODE:
            dataClass = VtBarData
            func = self.newBar
        else:
            dataClass = VtTickData
            func = self.newTick

        self.output(u'开始回测')
        
        self.strategy.onInit()
        self.strategy.inited = True
        self.output(u'策略初始化完成')
        
        self.strategy.trading = True
        self.strategy.onStart()
        self.output(u'策略启动完成')
        
        self.output(u'开始回放数据')

        for d in self.dbCursor:
            data = dataClass()
            data.__dict__ = d
            func(data)     
            
        self.output(u'数据回放结束')
        
    #----------------------------------------------------------------------
    def newBar(self, bar):
        """新的K线"""
        self.bar = bar
        self.dt  = bar.datetime
        
        '''源代码
        self.crossLimitOrder()      # 先撮合限价单
        self.crossStopOrder()       # 再撮合停止单
        self.strategy.onBar(bar)    # 推送K线到策略中
        '''
        
        '''任建军修改'''
        self.strategy.onBar(bar)    # 推送K线到策略中
        self.crossLimitOrder()      # 先撮合限价单
        self.crossStopOrder()       # 再撮合停止单
        
        self.updateDailyClose(bar.datetime, bar.close)
    
    #----------------------------------------------------------------------
    def newTick(self, tick):
        """新的Tick"""
        self.tick = tick
        self.dt = tick.datetime
        
        self.crossLimitOrder()
        self.crossStopOrder()
        self.strategy.onTick(tick)
        
        self.updateDailyClose(tick.datetime, tick.lastPrice)
        
    #----------------------------------------------------------------------
    def initStrategy(self, strategyClass, setting=None):
        """
        初始化策略
        setting是策略的参数设置，如果使用类中写好的默认设置则可以不传该参数
        """
        self.strategy = strategyClass(self, setting)
        self.strategy.name = self.strategy.className
    
    #----------------------------------------------------------------------
    def crossLimitOrder(self):
        """基于最新数据撮合限价单"""
        # 先确定会撮合成交的价格
        if self.mode == self.BAR_MODE:
            buyCrossPrice = self.bar.low        # 若买入方向限价单价格高于该价格，则会成交
            sellCrossPrice = self.bar.high      # 若卖出方向限价单价格低于该价格，则会成交
            buyBestCrossPrice = self.bar.open   # 在当前时间点前发出的买入委托可能的最优成交价
            sellBestCrossPrice = self.bar.open  # 在当前时间点前发出的卖出委托可能的最优成交价          
        else:
            buyCrossPrice = self.tick.askPrice1
            sellCrossPrice = self.tick.bidPrice1
            buyBestCrossPrice = self.tick.askPrice1
            sellBestCrossPrice = self.tick.bidPrice1
        
        # 遍历限价单字典中的所有限价单
        for orderID, order in self.workingLimitOrderDict.items():
            # 推送委托进入队列（未成交）的状态更新
            if not order.status:
                order.status = STATUS_NOTTRADED
                self.strategy.onOrder(order)

            ###原始代码
            '''
            # 判断是否会成交
            buyCross = (order.direction==DIRECTION_LONG and 
                        order.price>=buyCrossPrice and
                        buyCrossPrice > 0)      # 国内的tick行情在涨停时askPrice1为0，此时买无法成交
            
            sellCross = (order.direction==DIRECTION_SHORT and 
                         order.price<=sellCrossPrice and
                         sellCrossPrice > 0)    # 国内的tick行情在跌停时bidPrice1为0，此时卖无法成交
            '''
            ###任建军修改
            # 判断是否会成交
            buyCross = (order.direction==DIRECTION_LONG and 
                        buyCrossPrice > 0)      # 国内的tick行情在涨停时askPrice1为0，此时买无法成交
            
            sellCross = (order.direction==DIRECTION_SHORT and 
                         sellCrossPrice > 0)    # 国内的tick行情在跌停时bidPrice1为0，此时卖无法成交
            
            # 如果发生了成交
            if buyCross or sellCross:
                # 推送成交数据
                self.tradeCount += 1            # 成交编号自增1
                tradeID = str(self.tradeCount)
                trade = VtTradeData()
                trade.vtSymbol = order.vtSymbol
                trade.tradeID = tradeID
                trade.vtTradeID = tradeID
                trade.orderID = order.orderID
                trade.vtOrderID = order.orderID
                trade.direction = order.direction
                trade.offset = order.offset
                
                # 以买入为例：
                # 1. 假设当根K线的OHLC分别为：100, 125, 90, 110
                # 2. 假设在上一根K线结束(也是当前K线开始)的时刻，策略发出的委托为限价105
                # 3. 则在实际中的成交价会是100而不是105，因为委托发出时市场的最优价格是100
                if buyCross:
                    ### 原始程序
                    #trade.price = min(order.price, buyBestCrossPrice)
                    ### 任建军修改
                    trade.price = order.price
                    self.strategy.pos += order.totalVolume
                else:
                    ### 原始程序
                    #trade.price = max(order.price, sellBestCrossPrice)
                    ### 任建军修改
                    trade.price = order.price
                    self.strategy.pos -= order.totalVolume
                
                trade.volume = order.totalVolume
                ### 原始代码
                #trade.tradeTime = self.dt.strftime('%H:%M:%S')
                #trade.dt = self.dt
                ### 任建军修改
                trade.tradeTime = order.orderTime                
                trade.dt = datetime.strptime(order.orderTime, "%Y-%m-%d")  
                self.strategy.onTrade(trade)
                
                self.tradeDict[tradeID] = trade
                
                # 推送委托数据
                order.tradedVolume = order.totalVolume
                order.status = STATUS_ALLTRADED
                self.strategy.onOrder(order)
                
                # 从字典中删除该限价单
                if orderID in self.workingLimitOrderDict:
                    del self.workingLimitOrderDict[orderID]
                
    #----------------------------------------------------------------------
    def crossStopOrder(self):
        """基于最新数据撮合停止单"""
        # 先确定会撮合成交的价格，这里和限价单规则相反
        if self.mode == self.BAR_MODE:
            buyCrossPrice = self.bar.high    # 若买入方向停止单价格低于该价格，则会成交
            sellCrossPrice = self.bar.low    # 若卖出方向限价单价格高于该价格，则会成交
            bestCrossPrice = self.bar.open   # 最优成交价，买入停止单不能低于，卖出停止单不能高于
        else:
            buyCrossPrice = self.tick.lastPrice
            sellCrossPrice = self.tick.lastPrice
            bestCrossPrice = self.tick.lastPrice
        
        # 遍历停止单字典中的所有停止单
        for stopOrderID, so in self.workingStopOrderDict.items():
            # 判断是否会成交
            buyCross = so.direction==DIRECTION_LONG and so.price<=buyCrossPrice
            sellCross = so.direction==DIRECTION_SHORT and so.price>=sellCrossPrice
            
            # 如果发生了成交
            if buyCross or sellCross:
                # 更新停止单状态，并从字典中删除该停止单
                so.status = STOPORDER_TRIGGERED
                if stopOrderID in self.workingStopOrderDict:
                    del self.workingStopOrderDict[stopOrderID]                        

                # 推送成交数据
                self.tradeCount += 1            # 成交编号自增1
                tradeID = str(self.tradeCount)
                trade = VtTradeData()
                trade.vtSymbol = so.vtSymbol
                trade.tradeID = tradeID
                trade.vtTradeID = tradeID
                
                if buyCross:
                    self.strategy.pos += so.volume
                    trade.price = max(bestCrossPrice, so.price)
                else:
                    self.strategy.pos -= so.volume
                    trade.price = min(bestCrossPrice, so.price)                
                
                self.limitOrderCount += 1
                orderID = str(self.limitOrderCount)
                trade.orderID = orderID
                trade.vtOrderID = orderID
                trade.direction = so.direction
                trade.offset = so.offset
                trade.volume = so.volume
                trade.tradeTime = self.dt.strftime('%H:%M:%S')
                trade.dt = self.dt
                
                self.tradeDict[tradeID] = trade
                
                # 推送委托数据
                order = VtOrderData()
                order.vtSymbol = so.vtSymbol
                order.symbol = so.vtSymbol
                order.orderID = orderID
                order.vtOrderID = orderID
                order.direction = so.direction
                order.offset = so.offset
                order.price = so.price
                order.totalVolume = so.volume
                order.tradedVolume = so.volume
                order.status = STATUS_ALLTRADED
                order.orderTime = trade.tradeTime
                
                self.limitOrderDict[orderID] = order
                
                # 按照顺序推送数据
                self.strategy.onStopOrder(so)
                self.strategy.onOrder(order)
                self.strategy.onTrade(trade)
    
    #------------------------------------------------
    # 策略接口相关
    #------------------------------------------------      

    #----------------------------------------------------------------------
    def sendOrder(self, vtSymbol, orderType, price, volume, strategy):
        """发单"""
        self.limitOrderCount += 1
        orderID = str(self.limitOrderCount)
        
        order = VtOrderData()
        order.vtSymbol = vtSymbol
        order.price = self.roundToPriceTick(price)
        order.totalVolume = volume
        order.orderID = orderID
        order.vtOrderID = orderID
        # 原始程序
        #order.orderTime = self.dt.strftime('%H:%M:%S')
        # 任建军修改
        order.orderTime = self.dt.strftime('%Y-%m-%d')
        
        # CTA委托类型映射
        if orderType == CTAORDER_BUY:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_OPEN
        elif orderType == CTAORDER_SELL:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_CLOSE
        elif orderType == CTAORDER_SHORT:
            order.direction = DIRECTION_SHORT
            order.offset = OFFSET_OPEN
        elif orderType == CTAORDER_COVER:
            order.direction = DIRECTION_LONG
            order.offset = OFFSET_CLOSE     
        
        # 保存到限价单字典中
        self.workingLimitOrderDict[orderID] = order
        self.limitOrderDict[orderID] = order
        
        return [orderID]
    
    #----------------------------------------------------------------------
    def cancelOrder(self, vtOrderID):
        """撤单"""
        if vtOrderID in self.workingLimitOrderDict:
            order = self.workingLimitOrderDict[vtOrderID]
            
            order.status = STATUS_CANCELLED
            order.cancelTime = self.dt.strftime('%H:%M:%S')
            
            self.strategy.onOrder(order)
            
            del self.workingLimitOrderDict[vtOrderID]
        
    #----------------------------------------------------------------------
    def sendStopOrder(self, vtSymbol, orderType, price, volume, strategy):
        """发停止单（本地实现）"""
        self.stopOrderCount += 1
        stopOrderID = STOPORDERPREFIX + str(self.stopOrderCount)
        
        so = StopOrder()
        so.vtSymbol = vtSymbol
        so.price = self.roundToPriceTick(price)
        so.volume = volume
        so.strategy = strategy
        so.status = STOPORDER_WAITING
        so.stopOrderID = stopOrderID
        
        if orderType == CTAORDER_BUY:
            so.direction = DIRECTION_LONG
            so.offset = OFFSET_OPEN
        elif orderType == CTAORDER_SELL:
            so.direction = DIRECTION_SHORT
            so.offset = OFFSET_CLOSE
        elif orderType == CTAORDER_SHORT:
            so.direction = DIRECTION_SHORT
            so.offset = OFFSET_OPEN
        elif orderType == CTAORDER_COVER:
            so.direction = DIRECTION_LONG
            so.offset = OFFSET_CLOSE           
        
        # 保存stopOrder对象到字典中
        self.stopOrderDict[stopOrderID] = so
        self.workingStopOrderDict[stopOrderID] = so
        
        # 推送停止单初始更新
        self.strategy.onStopOrder(so)        
        
        return [stopOrderID]
    
    #----------------------------------------------------------------------
    def cancelStopOrder(self, stopOrderID):
        """撤销停止单"""
        # 检查停止单是否存在
        if stopOrderID in self.workingStopOrderDict:
            so = self.workingStopOrderDict[stopOrderID]
            so.status = STOPORDER_CANCELLED
            del self.workingStopOrderDict[stopOrderID]
            self.strategy.onStopOrder(so)
    
    #----------------------------------------------------------------------
    def putStrategyEvent(self, name):
        """发送策略更新事件，回测中忽略"""
        pass
     
    #----------------------------------------------------------------------
    def insertData(self, dbName, collectionName, data):
        """考虑到回测中不允许向数据库插入数据，防止实盘交易中的一些代码出错"""
        pass
    
    #----------------------------------------------------------------------
    def loadBar(self, dbName, collectionName, startDate):
        """直接返回初始化数据列表中的Bar"""
        return self.initData
    
    #----------------------------------------------------------------------
    def loadTick(self, dbName, collectionName, startDate):
        """直接返回初始化数据列表中的Tick"""
        return self.initData
    
    #----------------------------------------------------------------------
    def writeCtaLog(self, content):
        """记录日志"""
        log = str(self.dt) + ' ' + content 
        self.logList.append(log)
    
    #----------------------------------------------------------------------
    def cancelAll(self, name):
        """全部撤单"""
        # 撤销限价单
        for orderID in self.workingLimitOrderDict.keys():
            self.cancelOrder(orderID)
        
        # 撤销停止单
        for stopOrderID in self.workingStopOrderDict.keys():
            self.cancelStopOrder(stopOrderID)

    #----------------------------------------------------------------------
    def saveSyncData(self, strategy):
        """保存同步数据（无效）"""
        pass
    
    #----------------------------------------------------------------------
    def getPriceTick(self, strategy):
        """获取最小价格变动"""
        return self.priceTick
    
    #------------------------------------------------
    # 结果计算相关
    #------------------------------------------------      
    
    #----------------------------------------------------------------------
    def calculateBacktestingResult(self):
        """
        计算回测结果
        """
        self.output(u'计算回测结果')
        
        # 检查成交记录
        if not self.tradeDict:
            self.output(u'成交记录为空，无法计算回测结果')
            return {}
        
        # 首先基于回测后的成交记录，计算每笔交易的盈亏
        resultList = []             # 交易结果列表
        
        longTrade = []              # 未平仓的多头交易
        shortTrade = []             # 未平仓的空头交易
        
        tradeTimeList = []          # 每笔成交时间戳
        posList = [0]               # 每笔成交后的持仓情况        

        for trade in self.tradeDict.values():
            # 复制成交对象，因为下面的开平仓交易配对涉及到对成交数量的修改
            # 若不进行复制直接操作，则计算完后所有成交的数量会变成0
            trade = copy.copy(trade)
            
            # 多头交易
            if trade.direction == DIRECTION_LONG:
                # 如果尚无空头交易
                if not shortTrade:
                    longTrade.append(trade)
                # 当前多头交易为平空
                else:
                    while True:
                        entryTrade = shortTrade[0]
                        exitTrade = trade
                        
                        # 清算开平仓交易
                        closedVolume = min(exitTrade.volume, entryTrade.volume)
                        result = TradingResult(entryTrade.price, entryTrade.dt, 
                                               exitTrade.price, exitTrade.dt,
                                               -closedVolume, self.rate, self.slippage, self.size)
                        resultList.append(result)
                        
                        posList.extend([-1,0])
                        tradeTimeList.extend([result.entryDt, result.exitDt])
                        
                        # 计算未清算部分
                        entryTrade.volume -= closedVolume
                        exitTrade.volume -= closedVolume
                        
                        # 如果开仓交易已经全部清算，则从列表中移除
                        if not entryTrade.volume:
                            shortTrade.pop(0)
                        
                        # 如果平仓交易已经全部清算，则退出循环
                        if not exitTrade.volume:
                            break
                        
                        # 如果平仓交易未全部清算，
                        if exitTrade.volume:
                            # 且开仓交易已经全部清算完，则平仓交易剩余的部分
                            # 等于新的反向开仓交易，添加到队列中
                            if not shortTrade:
                                longTrade.append(exitTrade)
                                break
                            # 如果开仓交易还有剩余，则进入下一轮循环
                            else:
                                pass
                        
            # 空头交易        
            else:
                # 如果尚无多头交易
                if not longTrade:
                    shortTrade.append(trade)
                # 当前空头交易为平多
                else:                    
                    while True:
                        entryTrade = longTrade[0]
                        exitTrade = trade
                        
                        # 清算开平仓交易
                        closedVolume = min(exitTrade.volume, entryTrade.volume)
                        result = TradingResult(entryTrade.price, entryTrade.dt, 
                                               exitTrade.price, exitTrade.dt,
                                               closedVolume, self.rate, self.slippage, self.size)
                        resultList.append(result)
                        
                        posList.extend([1,0])
                        tradeTimeList.extend([result.entryDt, result.exitDt])

                        # 计算未清算部分
                        entryTrade.volume -= closedVolume
                        exitTrade.volume -= closedVolume
                        
                        # 如果开仓交易已经全部清算，则从列表中移除
                        if not entryTrade.volume:
                            longTrade.pop(0)
                        
                        # 如果平仓交易已经全部清算，则退出循环
                        if not exitTrade.volume:
                            break
                        
                        # 如果平仓交易未全部清算，
                        if exitTrade.volume:
                            # 且开仓交易已经全部清算完，则平仓交易剩余的部分
                            # 等于新的反向开仓交易，添加到队列中
                            if not longTrade:
                                shortTrade.append(exitTrade)
                                break
                            # 如果开仓交易还有剩余，则进入下一轮循环
                            else:
                                pass                    
        
        # 到最后交易日尚未平仓的交易，则以最后价格平仓
        if self.mode == self.BAR_MODE:
            endPrice = self.bar.close
        else:
            endPrice = self.tick.lastPrice
            
        for trade in longTrade:
            result = TradingResult(trade.price, trade.dt, endPrice, self.dt, 
                                   trade.volume, self.rate, self.slippage, self.size)
            resultList.append(result)
            
        for trade in shortTrade:
            result = TradingResult(trade.price, trade.dt, endPrice, self.dt, 
                                   -trade.volume, self.rate, self.slippage, self.size)
            resultList.append(result)            
        
        # 检查是否有交易
        if not resultList:
            self.output(u'无交易结果')
            return {}
        
        # 然后基于每笔交易的结果，我们可以计算具体的盈亏曲线和最大回撤等        
        capital = 0             # 资金
        maxCapital = 0          # 资金最高净值
        drawdown = 0            # 回撤
        
        totalResult = 0         # 总成交数量
        totalTurnover = 0       # 总成交金额（合约面值）
        totalCommission = 0     # 总手续费
        totalSlippage = 0       # 总滑点
        
        timeList = []           # 时间序列
        pnlList = []            # 每笔盈亏序列
        capitalList = []        # 盈亏汇总的时间序列
        drawdownList = []       # 回撤的时间序列
        
        winningResult = 0       # 盈利次数
        losingResult = 0        # 亏损次数		
        totalWinning = 0        # 总盈利金额		
        totalLosing = 0         # 总亏损金额   
        
        
        
        for result in resultList:
            capital += result.pnl
            maxCapital = max(capital, maxCapital)
            drawdown = capital - maxCapital
            
            pnlList.append(result.pnl)
            timeList.append(result.exitDt)      # 交易的时间戳使用平仓时间
            capitalList.append(capital)
            drawdownList.append(drawdown)
            
            totalResult += 1
            totalTurnover += result.turnover
            totalCommission += result.commission
            totalSlippage += result.slippage
            
            if result.pnl >= 0:
                winningResult += 1
                totalWinning += result.pnl
            else:
                losingResult += 1
                totalLosing += result.pnl
                
        # 计算盈亏相关数据
        winningRate = winningResult/totalResult*100         # 胜率
        
        averageWinning = 0                                  # 这里把数据都初始化为0
        averageLosing = 0
        profitLossRatio = 0

        ###任建军添加
        averagewininglosing = 0
        ###任建军添加        
        
        if winningResult:
            averageWinning = totalWinning/winningResult     # 平均每笔盈利
        if losingResult:
            averageLosing = totalLosing/losingResult        # 平均每笔亏损
        if averageLosing:
            profitLossRatio = -averageWinning/averageLosing # 盈亏比
        ###任建军添加
        if totalWinning+totalLosing:
            averagewininglosing = (totalWinning+totalLosing)/(winningResult+losingResult) #平均盈亏
        ###任建军添加

        # 返回回测结果
        d = {}
        d['capital'] = capital                    # 资金
        d['maxCapital'] = maxCapital              # 资金最高净值
        d['drawdown'] = drawdown                  # 回撤
        d['totalResult'] = totalResult            # 总成交数量
        d['totalTurnover'] = totalTurnover        # 总成交金额（合约面值）
        d['totalCommission'] = totalCommission    # 总手续费
        d['totalSlippage'] = totalSlippage        # 总滑点
        d['timeList'] = timeList                  # 时间序列
        d['pnlList'] = pnlList                    # 每笔盈亏序列
        d['capitalList'] = capitalList            # 盈亏汇总的时间序列
        d['drawdownList'] = drawdownList          # 回撤的时间序列
        d['winningRate'] = winningRate            # 胜率
        d['averageWinning'] = averageWinning      # 平均每笔盈利
        d['averageLosing'] = averageLosing        # 平均每笔亏损
        d['profitLossRatio'] = profitLossRatio    # 盈亏比
        d['posList'] = posList                    # 每笔成交后的持仓情况 
        d['tradeTimeList'] = tradeTimeList        # 每笔成交时间戳
        d['resultList'] = resultList              # 交易结果列表
        ###任建军添加
        d['averagewininglosing'] = averagewininglosing #平均盈亏
        ###任建军添加
        
        return d
        
    #----------------------------------------------------------------------
    def showBacktestingResult(self):
        """显示回测结果"""
        d = self.calculateBacktestingResult()
        if len(d) == 0:
            return
        # 输出
        self.output('-' * 30)
        self.output(u'第一笔交易：\t%s' % d['timeList'][0])
        self.output(u'最后一笔交易：\t%s' % d['timeList'][-1])
        
        self.output(u'总交易次数：\t%s' % formatNumber(d['totalResult']))        
        self.output(u'总盈亏：\t%s' % formatNumber(d['capital']))
        self.output(u'最大回撤: \t%s' % formatNumber(min(d['drawdownList'])))                
        
        self.output(u'平均每笔盈利：\t%s' %formatNumber(d['capital']/d['totalResult']))
        self.output(u'平均每笔滑点：\t%s' %formatNumber(d['totalSlippage']/d['totalResult']))
        self.output(u'平均每笔佣金：\t%s' %formatNumber(d['totalCommission']/d['totalResult']))
        
        self.output(u'胜率\t\t%s%%' %formatNumber(d['winningRate']))
        self.output(u'盈利交易平均值\t%s' %formatNumber(d['averageWinning']))
        self.output(u'亏损交易平均值\t%s' %formatNumber(d['averageLosing']))
        self.output(u'盈亏比：\t%s' %formatNumber(d['profitLossRatio']))
    
        
        # 绘图
        fig = plt.figure(figsize=(10, 16))
        
        pCapital = plt.subplot(4, 1, 1)
        pCapital.set_ylabel("capital")
        pCapital.plot(d['capitalList'], color='r', lw=0.8)
        
        pDD = plt.subplot(4, 1, 2)
        pDD.set_ylabel("DD")
        pDD.bar(range(len(d['drawdownList'])), d['drawdownList'], color='g')
        
        pPnl = plt.subplot(4, 1, 3)
        pPnl.set_ylabel("pnl")
        pPnl.hist(d['pnlList'], bins=50, color='c')

        pPos = plt.subplot(4, 1, 4)
        pPos.set_ylabel("Position")
        if d['posList'][-1] == 0:
            del d['posList'][-1]
        tradeTimeIndex = [item.strftime("%m/%d %H:%M:%S") for item in d['tradeTimeList']]
        if len(tradeTimeIndex)==0 or np.int(len(tradeTimeIndex)/10) == 0:
            return
        xindex = np.arange(0, len(tradeTimeIndex), np.int(len(tradeTimeIndex)/10))
        tradeTimeIndex = map(lambda i: tradeTimeIndex[i], xindex)
        pPos.plot(d['posList'], color='k', drawstyle='steps-pre')
        pPos.set_ylim(-1.2, 1.2)
        plt.sca(pPos)
        plt.tight_layout()
        plt.xticks(xindex, tradeTimeIndex, rotation=30)  # 旋转15
        
        plt.show()
        
    
    #----------------------------------------------------------------------
    def clearBacktestingResult(self):
        """清空之前回测的结果"""
        # 清空限价单相关
        self.limitOrderCount = 0
        self.limitOrderDict.clear()
        self.workingLimitOrderDict.clear()        
        
        # 清空停止单相关
        self.stopOrderCount = 0
        self.stopOrderDict.clear()
        self.workingStopOrderDict.clear()
        
        # 清空成交相关
        self.tradeCount = 0
        self.tradeDict.clear()
        
        # 清空多参数优化日线回测结果
        self.dailyResultDict.clear()
        
    #----------------------------------------------------------------------
    def runOptimization(self, strategyClass, optimizationSetting):
        """单进程优化参数"""
        # 获取优化设置        
        settingList = optimizationSetting.generateSetting()
        targetName = optimizationSetting.optimizeTarget
        
        # 检查参数设置问题
        if not settingList or not targetName:
            self.output(u'优化设置有问题，请检查')
        
        # 写入CSV文件 表头
        ###任建军添加
        Optimization_result_csv = pd.DataFrame(columns = ['参数组', '累计收益率', '平均盈亏', '胜率', '交易次数', '平均盈利/平均亏损', '权益最大回撤','权益最大回撤比'])
        ###任建军添加
        
        # 遍历优化
        resultList = []
        resultList_csv= []
        for setting in settingList:
            self.clearBacktestingResult()
            self.output('-' * 30)
            self.output('setting: %s' %str(setting))
            self.initStrategy(strategyClass, setting)
            self.runBacktesting()
                        
            df = self.calculateDailyResult()    
            df, d = self.calculateDailyStatistics(df) 
            try:
                targetValue = d[targetName]
            except KeyError:
                targetValue = 0
            resultList.append(([str(setting)], targetValue, d))
            
            
            ###任建军添加
            d1= self.calculateBacktestingResult()
            s = pd.Series(          [setting.values(),float('%.2f'%d['totalReturn']),float('%.2f'%d1['averagewininglosing']),float('%.2f'%d1['winningRate']),d['totalTradeCount'],float('%.2f'%d1['profitLossRatio']),float('%.2f'%d['maxDrawdown']),float('%.2f'%d['maxDdPercent'])],\
                          index =         ['参数组'  , '累计收益率'                  , '平均盈亏'                             , '胜率'                        , '交易次数'          , '平均盈利/平均亏损'                , '权益最大回撤'                ,'权益最大回撤比'])
            resultList_csv.append(s)            
            ###任建军添加
        
        # 写入CSV文件 内容
        ###任建军添加
        for i in range(len(resultList_csv)):
            Optimization_result_csv = Optimization_result_csv.append(resultList_csv[i],ignore_index=True)         
        Optimization_result_csv.to_csv(u'F:\\uiKLine\\data\\Optimization\\OptimizationResult.csv',encoding='utf_8_sig',mode='w',index=False)
        ###任建军添加
        
        
        # 显示结果
        resultList.sort(reverse=True, key=lambda result:result[1])
        self.output('-' * 30)
        self.output(u'优化结果：')
        for result in resultList:
            self.output(u'参数：%s，目标：%s' %(result[0], result[1]))    
        return resultList
            
    #----------------------------------------------------------------------
    def runParallelOptimization(self, strategyClass, optimizationSetting):
        """多进程并行优化参数"""
        # 获取优化设置        
        settingList = optimizationSetting.generateSetting()
        targetName = optimizationSetting.optimizeTarget
        
        self.poolscount[0] = len(settingList)
        for num in range(1,self.poolscount[0]+1):
            self.poolscount.append(num)
        mylist=multiprocessing.Manager().list(self.poolscount) 
        
        # 检查参数设置问题
        if not settingList or not targetName:
            self.output(u'优化设置有问题，请检查')
        
        # 多进程优化，启动一个对应CPU核心数量的进程池
        pool = multiprocessing.Pool(multiprocessing.cpu_count())
        l = []

        num=1
        for setting in settingList:
            # 任建军修改 添加了self.capital参数
            l.append(pool.apply_async(optimize, (strategyClass, setting,
                                                 targetName, self.mode, 
                                                 self.startDate, self.initDays, self.endDate,
                                                 self.slippage, self.rate, self.size, self.priceTick,
                                                 self.dbName, self.symbol,self.capital,mylist,num)))
            num+=1
        pool.close()
        pool.join()   
        
        ###任建军添加
        resultList_run_csv = [res.get() for res in l]   
        resultList_csv= []
        for result in resultList_run_csv:
            d      =result[2]
            d1     =result[3]              
            setting=result[4]
            if len(d) == 0 or len(d1) == 0:
                pass
                #s = pd.Series([setting.values(),            float(0)    ,  float(0) ,  float(0)    ,    0     ,           0          ,    float(0)        ,float(0)         ,float(0)      , float(0)],\
                #              index =         ['参数组'  , '累计收益率'  , '平均盈亏'  , '胜率'      , '交易次数', '平均盈利/平均亏损'   , '权益最大回撤'      ,'权益最大回撤比'  ,'损益最大回撤' ,'损益最大回撤比'])
            else:
                s = pd.Series([setting,'%02.2f'%float(d['totalReturn']),'%02.2f'%float(d1['averagewininglosing']),'%02.2f'%float(d1['winningRate']),d['totalTradeCount'],'%02.2f'%float(d1['profitLossRatio']),'%02.2f'%float(d['maxDrawdown']),'%02.2f'%float(d['maxDdPercent']),'%02.2f'%float(min(d1['drawdownList'])),'%02.2f'%float(min(d1['drawdownrateList']))],\
                              index =         ['参数组'  , '累计收益率'                  , '平均盈亏'                             , '胜率'                        , '交易次数'          , '平均盈利/平均亏损'                , '权益最大回撤'                ,'权益最大回撤比'                ,'损益最大回撤'                       ,'损益最大回撤比'])
                resultList_csv.append(s)    
                
        Optimization_result_csv = pd.DataFrame(columns = ['参数组', '累计收益率', '平均盈亏', '胜率', '交易次数', '平均盈利/平均亏损', '权益最大回撤','权益最大回撤比','损益最大回撤','损益最大回撤比'])
        for i in range(len(resultList_csv)):
            Optimization_result_csv = Optimization_result_csv.append(resultList_csv[i],ignore_index=True)         
        Optimization_result_csv.to_csv(r'F:\\uiKLine\\data\\Optimization\OptimizationResult.csv',encoding='utf_8_sig',mode='w',index=False)                
        ###任建军添加
        
        
        # 显示结果
        resultList = [res.get() for res in l]
        resultList.sort(reverse=True, key=lambda result:result[1])
        self.output('-' * 30)
        self.output(u'优化结果：')
        for result in resultList:
            self.output(u'参数：%s，目标：%s' %(result[0], result[1]))    
            
        return resultList

    #----------------------------------------------------------------------
    def runParallelOptimization_batch(self, strategyClass, optimizationSetting,settingList):
        """多进程分批并行优化参数"""
        # 获取优化设置        
        targetName = optimizationSetting.optimizeTarget
        
        self.poolscount= [0,0]
        self.poolscount[0] = len(settingList)
        for num in range(1,self.poolscount[0]+1):
            self.poolscount.append(num)
        mylist=multiprocessing.Manager().list(self.poolscount) 
        
        # 检查参数设置问题
        if not settingList or not targetName:
            self.output(u'优化设置有问题，请检查')
        
        # 多进程优化，启动一个对应CPU核心数量的进程池
        pool = multiprocessing.Pool(multiprocessing.cpu_count())
        l = []

        num=1
        for setting in settingList:
            # 任建军修改 添加了self.capital参数
            l.append(pool.apply_async(optimize, (strategyClass, setting,
                                                 targetName, self.mode, 
                                                 self.startDate, self.initDays, self.endDate,
                                                 self.slippage, self.rate, self.size, self.priceTick,
                                                 self.dbName, self.symbol,self.capital,mylist,num)))
            num+=1
        pool.close()
        pool.join()   
        
        ###任建军添加
        resultList_run_csv = [res.get() for res in l]   
        resultList_csv= []
        for result in resultList_run_csv:
            d      =result[2]
            d1     =result[3]              
            setting=result[4]
            if len(d) == 0 or len(d1) == 0:
                pass
                #s = pd.Series([setting.values(),            float(0)    ,  float(0) ,  float(0)    ,    0     ,           0          ,    float(0)        ,float(0)         ,float(0)      , float(0)],\
                #              index =         ['参数组'  , '累计收益率'  , '平均盈亏'  , '胜率'      , '交易次数', '平均盈利/平均亏损'   , '权益最大回撤'      ,'权益最大回撤比'  ,'损益最大回撤' ,'损益最大回撤比'])
            else:
                s = pd.Series([setting,'%02.2f'%float(d['totalReturn']),'%02.2f'%float(d1['averagewininglosing']),'%02.2f'%float(d1['winningRate']),d['totalTradeCount'],'%02.2f'%float(d1['profitLossRatio']),'%02.2f'%float(d['maxDrawdown']),'%02.2f'%float(d['maxDdPercent']),'%02.2f'%float(min(d1['drawdownList'])),'%02.2f'%float(min(d1['drawdownrateList']))],\
                              index =         ['参数组'  , '累计收益率'                  , '平均盈亏'                             , '胜率'                        , '交易次数'          , '平均盈利/平均亏损'                , '权益最大回撤'                ,'权益最大回撤比'                ,'损益最大回撤'                       ,'损益最大回撤比'])
                resultList_csv.append(s)            

            Optimization_result_csv = pd.DataFrame(columns = ['参数组', '累计收益率', '平均盈亏', '胜率', '交易次数', '平均盈利/平均亏损', '权益最大回撤','权益最大回撤比','损益最大回撤','损益最大回撤比'])
            for i in range(len(resultList_csv)):
                Optimization_result_csv = Optimization_result_csv.append(resultList_csv[i],ignore_index=True)         
            Optimization_result_csv.to_csv(r'F:\\uiKLine\\data\\Optimization\OptimizationResult.csv',encoding='utf_8_sig',mode='a+',index=False)                
        ###任建军添加
        
        
        # 显示结果
        resultList = [res.get() for res in l]
        resultList.sort(reverse=True, key=lambda result:result[1])
        self.output('-' * 30)
        self.output(u'优化结果：')
        for result in resultList:
            self.output(u'参数：%s，目标：%s' %(result[0], result[1]))    
            
        return resultList
        
    #----------------------------------------------------------------------
    def updateDailyClose(self, dt, price):
        """更新每日收盘价"""
        date = dt.date()
        
        if date not in self.dailyResultDict:
            self.dailyResultDict[date] = DailyResult(date, price)
        else:
            self.dailyResultDict[date].closePrice = price
            
    #----------------------------------------------------------------------
    def calculateDailyResult(self):
        """计算按日统计的交易结果"""
        self.output(u'计算按日统计结果')
        
        # 检查成交记录
        if not self.tradeDict:
            self.output(u'成交记录为空，无法计算回测结果')
            return {}
        
        # 将成交添加到每日交易结果中
        for trade in self.tradeDict.values():                
            date = trade.dt.date()
            dailyResult = self.dailyResultDict[date]
            dailyResult.addTrade(trade) 
          
        # 遍历计算每日结果
        previousClose = 0
        openPosition = 0
        for dailyResult in self.dailyResultDict.values():
            dailyResult.previousClose = previousClose
            previousClose = dailyResult.closePrice
            
            dailyResult.calculatePnl(openPosition, self.size, self.rate, self.slippage )
            openPosition = dailyResult.closePosition

            
            
            
        # 生成DataFrame
        resultDict = {k:[] for k in dailyResult.__dict__.keys()}
        for dailyResult in self.dailyResultDict.values():
            for k, v in dailyResult.__dict__.items():
                resultDict[k].append(v)
            
                
                
        resultDf = pd.DataFrame.from_dict(resultDict)
        
        # 计算衍生数据
        resultDf = resultDf.set_index('date')
        
                
        return resultDf      
    #----------------------------------------------------------------------
    def calculateDailyResult_to_CSV(self,filename):
        """计算按日统计的交易结果输出到csv文件，为K线图形信号显示使用"""
        self.output(u'计算按日统计结果')
        
        # 检查成交记录
        if not self.tradeDict:
            self.output(u'成交记录为空，无法计算回测结果')
            return {}
        
        # 将成交添加到每日交易结果中
        for trade in self.tradeDict.values():                
            date = trade.dt.date()
            dailyResult = self.dailyResultDict[date]
            dailyResult.addTrade(trade) 
            
        # 遍历计算每日结果
        previousClose = 0
        openPosition = 0
        for dailyResult in self.dailyResultDict.values():
            dailyResult.previousClose = previousClose
            previousClose = dailyResult.closePrice
            
            dailyResult.calculatePnl(openPosition, self.size, self.rate, self.slippage )
            openPosition = dailyResult.closePosition
            
        # 生成DataFrame
        resultDict = {k:[] for k in dailyResult.__dict__.keys()+['deal_DIRECTION']+['deal_OFFSET']}
        for dailyResult in self.dailyResultDict.values():
            
            if dailyResult.tradeCount > 0 :
                # 对于所有策略限定只允许每日最多交易一次 
                resultDict['deal_DIRECTION'].append(dailyResult.tradeList[0].direction )
                resultDict['deal_OFFSET'].append(dailyResult.tradeList[0].offset )
            else:  
                resultDict['deal_DIRECTION'].append(EMPTY_UNICODE)
                resultDict['deal_OFFSET'].append(EMPTY_UNICODE)
                
            for k, v in dailyResult.__dict__.items():
                
                resultDict[k].append(v)
                
        resultDf = pd.DataFrame.from_dict(resultDict)
        resultDf.drop(['tradeList'],axis=1,inplace=True)
        
        # 计算衍生数据
        #resultDf = resultDf.set_index('date')
        
        resultDf.to_csv(filename,encoding='utf_8_sig',mode='w',index=False) 
        self.output(u'计算结束已经输出到%s文件中'%filename)
        return resultDf
    
    #----------------------------------------------------------------------    
    def calculateDailyStatistics(self, df):
        """计算按日统计的结果"""
        df['balance'] = df['netPnl'].cumsum() + self.capital
        df['return'] = (np.log(df['balance']) - np.log(df['balance'].shift(1))).fillna(0)
        df['highlevel'] = df['balance'].rolling(min_periods=1,window=len(df),center=False).max()
        df['drawdown'] = df['balance'] - df['highlevel']        
        df['ddPercent'] = df['drawdown'] / df['highlevel'] * 100
        
        
        
        # 计算统计结果
        startDate = df.index[0]
        endDate = df.index[-1]

        totalDays = len(df)
        profitDays = len(df[df['netPnl']>0])
        lossDays = len(df[df['netPnl']<0])
        
        endBalance = df['balance'].iloc[-1]
        maxDrawdown = df['drawdown'].min()
        maxDdPercent = df['ddPercent'].min()
        
     
        totalNetPnl = df['netPnl'].sum()
        dailyNetPnl = totalNetPnl / totalDays
        
        totalCommission = df['commission'].sum()
        dailyCommission = totalCommission / totalDays
        
        totalSlippage = df['slippage'].sum()
        dailySlippage = totalSlippage / totalDays
        
        totalTurnover = df['turnover'].sum()
        dailyTurnover = totalTurnover / totalDays
        
        totalTradeCount = df['tradeCount'].sum()
        dailyTradeCount = totalTradeCount / totalDays
        
        totalReturn = (endBalance/self.capital - 1) * 100
        annualizedReturn = totalReturn / totalDays * 240
        dailyReturn = df['return'].mean() * 100
        returnStd = df['return'].std() * 100
             
        
        if returnStd:
            sharpeRatio = dailyReturn / returnStd * np.sqrt(240)
        else:
            sharpeRatio = 0
            
        # 返回结果
        result = {
            'startDate': startDate,              #首个交易日  
            'endDate': endDate,                  #结束交易日
            'totalDays': totalDays,              #总交易日
            'profitDays': profitDays,            #盈利交易日
            'lossDays': lossDays,                #亏损交易日
            'endBalance': endBalance,            #结束资金
            'maxDrawdown': maxDrawdown,          #最大回撤
            'maxDdPercent': maxDdPercent,        #百分比最大回撤
            'totalNetPnl': totalNetPnl,          #总盈亏
            'dailyNetPnl': dailyNetPnl,          #日均盈亏
            'totalCommission': totalCommission,  #总手续费
            'dailyCommission': dailyCommission,  #日均手续费
            'totalSlippage': totalSlippage,      #总滑点
            'dailySlippage': dailySlippage,      #日滑点
            'totalTurnover': totalTurnover,      #总成交金额
            'dailyTurnover': dailyTurnover,      #日均成交金额
            'totalTradeCount': totalTradeCount,  #总的交易次数
            'dailyTradeCount': dailyTradeCount,  #日均成交笔数
            'totalReturn': totalReturn,          #累计收益率
            'annualizedReturn': annualizedReturn,#年化收益
            'dailyReturn': dailyReturn,          #日均收益率
            'returnStd': returnStd,              #收益标准差
            'sharpeRatio': sharpeRatio,          #夏普比率 
        }
        
        return df, result
    #----------------------------------------------------------------------    
    def calculateDailyStatisticsForWH(self, df):
        """计算按日统计的结果，为了一些文华的输出指标"""
        df['balance'] = df['netPnl'].cumsum() + self.capital
        df['return'] = (np.log(df['balance']) - np.log(df['balance'].shift(1))).fillna(0)
        df['highlevel'] = df['balance'].rolling(min_periods=1,window=len(df),center=False).max()
        df['drawdown'] = df['balance'] - df['highlevel']        
        df['ddPercent'] = df['drawdown'] / df['highlevel'] * 100
        
        
        
        # 计算统计结果
        startDate = df.index[0]
        endDate = df.index[-1]

        totalDays = len(df)
        profitDays = len(df[df['netPnl']>0])
        lossDays = len(df[df['netPnl']<0])
        
        endBalance = df['balance'].iloc[-1]
        maxDrawdown = df['drawdown'].min()
        maxDrawdowndate = df[(df.drawdown == df['drawdown'].min())].index.tolist()[0]        
        maxDdPercent = df['ddPercent'].min()
        maxDdPercentdate = df[(df.ddPercent == df['ddPercent'].min())].index.tolist()[0]  
        
     
        totalNetPnl = df['netPnl'].sum()
        dailyNetPnl = totalNetPnl / totalDays
        
        totalCommission = df['commission'].sum()
        dailyCommission = totalCommission / totalDays
        
        totalSlippage = df['slippage'].sum()
        dailySlippage = totalSlippage / totalDays
        
        totalTurnover = df['turnover'].sum()
        dailyTurnover = totalTurnover / totalDays
        
        totalTradeCount = df['tradeCount'].sum()
        dailyTradeCount = totalTradeCount / totalDays
        
        totalReturn = (endBalance/self.capital - 1) * 100
        annualizedReturn = totalReturn / totalDays * 240
        dailyReturn = df['return'].mean() * 100
        returnStd = df['return'].std() * 100
             
        
        if returnStd:
            sharpeRatio = dailyReturn / returnStd * np.sqrt(240)
        else:
            sharpeRatio = 0
            
        # 返回结果
        result = {
            'startDate': startDate,              #首个交易日  
            'endDate': endDate,                  #结束交易日
            'totalDays': totalDays,              #总交易日
            'profitDays': profitDays,            #盈利交易日
            'lossDays': lossDays,                #亏损交易日
            'endBalance': endBalance,            #结束资金
            'maxDrawdown': maxDrawdown,          #权益最大回撤
            'maxDdPercent': maxDdPercent,        #权益百分比最大回撤
            'maxDrawdowndate': maxDrawdowndate,  #权益最大回撤日期
            'maxDdPercentdate': maxDdPercentdate,#权益百分比最大回撤日期
            'totalNetPnl': totalNetPnl,          #总盈亏
            'dailyNetPnl': dailyNetPnl,          #日均盈亏
            'totalCommission': totalCommission,  #总手续费
            'dailyCommission': dailyCommission,  #日均手续费
            'totalSlippage': totalSlippage,      #总滑点
            'dailySlippage': dailySlippage,      #日滑点
            'totalTurnover': totalTurnover,      #总成交金额
            'dailyTurnover': dailyTurnover,      #日均成交金额
            'totalTradeCount': totalTradeCount,  #总的交易次数
            'dailyTradeCount': dailyTradeCount,  #日均成交笔数
            'totalReturn': totalReturn,          #累计收益率
            'annualizedReturn': annualizedReturn,#年化收益
            'dailyReturn': dailyReturn,          #日均收益率
            'returnStd': returnStd,              #收益标准差
            'sharpeRatio': sharpeRatio,          #夏普比率 
        }
        return df, result
    #----------------------------------------------------------------------
    def showDailyResult(self, df=None, result=None):
        """显示按日统计的交易结果"""
        if df is None:
            df = self.calculateDailyResult()
            df, result = self.calculateDailyStatistics(df)
            
        # 输出统计结果
        self.output('-' * 30)
        self.output(u'首个交易日：\t%s' % result['startDate'])
        self.output(u'最后交易日：\t%s' % result['endDate'])
        
        self.output(u'总交易日：\t%s' % result['totalDays'])
        self.output(u'盈利交易日\t%s' % result['profitDays'])
        self.output(u'亏损交易日：\t%s' % result['lossDays'])
        
        self.output(u'起始资金：\t%s' % self.capital)
        self.output(u'结束资金：\t%s' % formatNumber(result['endBalance']))
    
        self.output(u'总收益率：\t%s%%' % formatNumber(result['totalReturn']))
        self.output(u'年化收益：\t%s%%' % formatNumber(result['annualizedReturn']))
        self.output(u'总盈亏：\t%s' % formatNumber(result['totalNetPnl']))
        self.output(u'最大回撤: \t%s' % formatNumber(result['maxDrawdown']))   
        self.output(u'百分比最大回撤: %s%%' % formatNumber(result['maxDdPercent']))   
        
        self.output(u'总手续费：\t%s' % formatNumber(result['totalCommission']))
        self.output(u'总滑点：\t%s' % formatNumber(result['totalSlippage']))
        self.output(u'总成交金额：\t%s' % formatNumber(result['totalTurnover']))
        self.output(u'总成交笔数：\t%s' % formatNumber(result['totalTradeCount']))
        
        self.output(u'日均盈亏：\t%s' % formatNumber(result['dailyNetPnl']))
        self.output(u'日均手续费：\t%s' % formatNumber(result['dailyCommission']))
        self.output(u'日均滑点：\t%s' % formatNumber(result['dailySlippage']))
        self.output(u'日均成交金额：\t%s' % formatNumber(result['dailyTurnover']))
        self.output(u'日均成交笔数：\t%s' % formatNumber(result['dailyTradeCount']))
        
        self.output(u'日均收益率：\t%s%%' % formatNumber(result['dailyReturn']))
        self.output(u'收益标准差：\t%s%%' % formatNumber(result['returnStd']))
        self.output(u'Sharpe Ratio：\t%s' % formatNumber(result['sharpeRatio']))
        
        # 绘图
        fig = plt.figure(figsize=(10, 16))
        
        pBalance = plt.subplot(4, 1, 1)
        pBalance.set_title('Balance')
        df['balance'].plot(legend=True)
        
        pDrawdown = plt.subplot(4, 1, 2)
        pDrawdown.set_title('Drawdown')
        pDrawdown.fill_between(range(len(df)), df['drawdown'].values)
        
        pPnl = plt.subplot(4, 1, 3)
        pPnl.set_title('Daily Pnl') 
        df['netPnl'].plot(kind='bar', legend=False, grid=False, xticks=[])

        pKDE = plt.subplot(4, 1, 4)
        pKDE.set_title('Daily Pnl Distribution')
        df['netPnl'].hist(bins=50)
        
        plt.show()
       
    #----------------------------------------------------------------------
    def calculateBacktestingResultForWH(self,LongOrShort = 2):
        """计算回测结果,为了文华那样的显示输出 LongOrShort:0 多，1 空，2 多空""" 
        if LongOrShort == 2:
            self.output(u'计算回测结果')
        elif LongOrShort == 0:
            self.output(u'计算回测结果_多')
        elif LongOrShort == 1:
            self.output(u'计算回测结果_空')
        
        # 检查成交记录
        if not self.tradeDict:
            self.output(u'成交记录为空，无法计算回测结果')
            return {}
        
        # 首先基于回测后的成交记录，计算每笔交易的盈亏
        resultList = []             # 交易结果列表
        
        longTrade = []              # 未平仓的多头交易
        shortTrade = []             # 未平仓的空头交易
        
        tradeTimeList = []          # 每笔成交时间戳
        posList = [0]               # 每笔成交后的持仓情况        
                    
        for trade in self.tradeDict.values():
            # 复制成交对象，因为下面的开平仓交易配对涉及到对成交数量的修改
            # 若不进行复制直接操作，则计算完后所有成交的数量会变成0
            trade = copy.copy(trade)
            
            # 多头交易
            if trade.direction == DIRECTION_LONG:
                           
                # 如果尚无空头交易
                if not shortTrade:
                    longTrade.append(trade)
                # 当前多头交易为平空
                else:
                    while True:
                        entryTrade = shortTrade[0]
                        exitTrade = trade
                        
                        # 清算开平仓交易
                        closedVolume = min(exitTrade.volume, entryTrade.volume)
                        result = TradingResult(entryTrade.price, entryTrade.dt, 
                                               exitTrade.price, exitTrade.dt,
                                               -closedVolume, self.rate, self.slippage, self.size)
                        resultList.append(result)
                        
                        posList.extend([-1,0])
                        tradeTimeList.extend([result.entryDt, result.exitDt])
                        
                        # 计算未清算部分
                        entryTrade.volume -= closedVolume
                        exitTrade.volume -= closedVolume
                        
                        # 如果开仓交易已经全部清算，则从列表中移除
                        if not entryTrade.volume:
                            shortTrade.pop(0)
                        
                        # 如果平仓交易已经全部清算，则退出循环
                        if not exitTrade.volume:
                            break
                        
                        # 如果平仓交易未全部清算，
                        if exitTrade.volume:
                            # 且开仓交易已经全部清算完，则平仓交易剩余的部分
                            # 等于新的反向开仓交易，添加到队列中
                            if not shortTrade:
                                longTrade.append(exitTrade)
                                break
                            # 如果开仓交易还有剩余，则进入下一轮循环
                            else:
                                pass
                        
            # 空头交易        
            else:           
                
                # 如果尚无多头交易
                if not longTrade:
                    shortTrade.append(trade)
                # 当前空头交易为平多
                else:                    
                    while True:
                        entryTrade = longTrade[0]
                        exitTrade = trade
                        
                        # 清算开平仓交易
                        closedVolume = min(exitTrade.volume, entryTrade.volume)
                        result = TradingResult(entryTrade.price, entryTrade.dt, 
                                               exitTrade.price, exitTrade.dt,
                                               closedVolume, self.rate, self.slippage, self.size)
                        resultList.append(result)
                        
                        posList.extend([1,0])
                        tradeTimeList.extend([result.entryDt, result.exitDt])

                        # 计算未清算部分
                        entryTrade.volume -= closedVolume
                        exitTrade.volume -= closedVolume
                        
                        # 如果开仓交易已经全部清算，则从列表中移除
                        if not entryTrade.volume:
                            longTrade.pop(0)
                        
                        # 如果平仓交易已经全部清算，则退出循环
                        if not exitTrade.volume:
                            break
                        
                        # 如果平仓交易未全部清算，
                        if exitTrade.volume:
                            # 且开仓交易已经全部清算完，则平仓交易剩余的部分
                            # 等于新的反向开仓交易，添加到队列中
                            if not longTrade:
                                shortTrade.append(exitTrade)
                                break
                            # 如果开仓交易还有剩余，则进入下一轮循环
                            else:
                                pass                    
        
        

        # 到最后交易日尚未平仓的交易，则以最后价格平仓
        if self.mode == self.BAR_MODE:
            endPrice = self.bar.close
        else:
            endPrice = self.tick.lastPrice
           
        for trade in longTrade:          
            result = TradingResult(trade.price, trade.dt, endPrice, self.dt, 
                                   trade.volume, self.rate, self.slippage, self.size)
            resultList.append(result)
            
        for trade in shortTrade:     
            result = TradingResult(trade.price, trade.dt, endPrice, self.dt, 
                                   -trade.volume, self.rate, self.slippage, self.size)
            resultList.append(result)   
        # 检查是否有交易
        if not resultList:
            self.output(u'无交易结果')
            return {}
        
        # 然后基于每笔交易的结果，我们可以计算具体的盈亏曲线和最大回撤等        
        capital = 0             # 总盈亏
        maxCapital = 0          # 总盈亏最高净值
        drawdown = 0            # 损益回撤
        drawdownrate = 0        # 损益回撤
        
        totalResult = 0         # 总成交数量
        totalTurnover = 0       # 总成交金额（合约面值）
        totalCommission = 0     # 总手续费
        totalSlippage = 0       # 总滑点
        
        timeList = []           # 时间序列
        pnlList = []            # 每笔盈亏序列
        capitalList = []        # 盈亏汇总的时间序列
        drawdownList = []       # 损益回撤的时间序列
        drawdownrateList = []   # 损益比回撤的时间序列        
        winloselist=[]          # 连续盈亏的时间序列      
        
        winningResult = 0       # 盈利次数
        losingResult = 0        # 亏损次数		
        totalWinning = 0        # 总盈利金额		
        totalLosing = 0         # 总亏损金额   
        wincount= 0
        losecount= 0
        
        
        for result in resultList:
            
            if LongOrShort == 0 and result.volume<0 :
                continue
            if LongOrShort == 1 and result.volume>0 :
                continue
            
            capital += result.pnl
            maxCapital = max(capital, maxCapital)
            drawdown = capital - maxCapital
            drawdownrate = drawdown / (maxCapital+self.capital)*100
            
            pnlList.append(result.pnl)
            timeList.append(result.exitDt)      # 交易的时间戳使用平仓时间
            capitalList.append(capital)
            drawdownList.append(drawdown)
            drawdownrateList.append(drawdownrate)
            
            totalResult += 1
            totalTurnover += result.turnover
            totalCommission += result.commission
            totalSlippage += result.slippage
            
            if result.pnl >= 0:
                winningResult += 1
                totalWinning += result.pnl
                losecount=0
                wincount+=1
                winloselist.append(wincount)
            else:
                losingResult += 1
                totalLosing += result.pnl
                wincount=0
                losecount-=1
                winloselist.append(losecount)
                
        # 计算盈亏相关数据
        winningRate = 0 
        if totalResult:
            winningRate = winningResult/totalResult*100         # 胜率
        
        averageWinning = 0                                  # 这里把数据都初始化为0
        averageLosing = 0
        profitLossRatio = 0

        ###任建军添加
        averagewininglosing = 0
        ###任建军添加        
        
        if winningResult:
            averageWinning = totalWinning/winningResult     # 平均每笔盈利
        if losingResult:
            averageLosing = totalLosing/losingResult        # 平均每笔亏损
        if averageLosing:
            profitLossRatio = -averageWinning/averageLosing # 盈亏比
        ###任建军添加
        if totalWinning+totalLosing:
            averagewininglosing = (totalWinning+totalLosing)/(winningResult+losingResult) #平均盈亏
        ###任建军添加

        # 返回回测结果
        d = {}
        d['capital'] = capital                    # 总盈亏
        d['maxCapital'] = maxCapital              # 总盈亏最高净值
        d['drawdown'] = drawdown                  # 损益回撤
        d['drawdownrate'] = drawdownrate          # 损益回撤比
        d['totalResult'] = totalResult            # 总成交数量（次数）
        d['totalTurnover'] = totalTurnover        # 总成交金额（合约面值）
        d['totalCommission'] = totalCommission    # 总手续费
        d['totalSlippage'] = totalSlippage        # 总滑点
        d['timeList'] = timeList                  # 时间序列
        d['pnlList'] = pnlList                    # 每笔盈亏序列
        d['capitalList'] = capitalList            # 盈亏汇总的时间序列
        d['drawdownList'] = drawdownList          # 损益回撤的时间序列
        d['drawdownrateList'] = drawdownrateList  # 损益回撤的时间序列
        d['winningRate'] = winningRate            # 胜率
        d['averageWinning'] = averageWinning      # 平均每笔盈利
        d['averageLosing'] = averageLosing        # 平均每笔亏损
        d['profitLossRatio'] = profitLossRatio    # 盈亏比
        d['posList'] = posList                    # 每笔成交后的持仓情况 
        d['tradeTimeList'] = tradeTimeList        # 每笔成交时间戳
        d['resultList'] = resultList              # 交易结果列表
        d['profitrate'] = (capital/self.capital) * 100    # 盈利率
        d['totalWinning'] = totalWinning          # 总盈利
        d['totalLosing']  = totalLosing           # 总亏损
        d['winningResult']  = winningResult       # 盈利次数
        d['losingResult']  = losingResult         # 亏损次数
        d['winloselist']  = winloselist           # 盈亏列表
        
        ###任建军添加
        d['averagewininglosing'] = averagewininglosing #平均盈亏
        ###任建军添加
        
        return d
    
    #----------------------------------------------------------------------
    def showBacktestingResultLikeWH(self, df=None, result=None):
        """"显示回测结果,类似文华"""
        d = self.calculateBacktestingResultForWH()
        if len(d) == 0:
            return
        # 输出        
        #权益的相关指标需要，按日统计每日的资金持有情况，不能按照交易结果统计.请注意损益的统计是按照交易结果统计的
        df = df.set_index('date')
        df, result = self.calculateDailyStatisticsForWH(df)                  
        
        tb1 = pt.PrettyTable(["animal", "ferocity"],encoding=sys.stdout.encoding)
        tb1.field_names = [u'项目']+[u'值']
        tb1.add_row([u'时间范围',df.index.tolist()[0].strftime("%Y-%m-%d") +' --- '+df.index.tolist()[-1].strftime("%Y-%m-%d") ])
        tb1.add_row([u'资金分配量',"%(xxx)s"%{'xxx':formatNumber(self.capital)}])
        tb1.add_row([u'最终权益',"%(xxx)s"%{'xxx':formatNumber(self.capital+d['capital'])}])
        tb1.add_row(['  ','  '])
        

        tb1.add_row([u'盈利率',"%(xxx)s%%"%{'xxx':formatNumber(d['profitrate'])}])
        tb1.add_row([u'总盈利',"%(xxx)s"%{'xxx':formatNumber(d['totalWinning'])}])
        tb1.add_row([u'总亏损',"%(xxx)s"%{'xxx':formatNumber(d['totalLosing'])}])
        tb1.add_row([u'净利润',"%(xxx)s"%{'xxx':formatNumber(d['capital'])}])
        if d['totalLosing'] == 0:
            tb1.add_row([u'总盈利/总亏损',"%(xxx)s"%{'xxx':formatNumber(0)}])
        else:
            tb1.add_row([u'总盈利/总亏损',"%(xxx)s"%{'xxx':formatNumber(d['totalWinning']/abs(d['totalLosing']))}])
            
        tb1.add_row([u'平均盈利',"%(xxx)s"%{'xxx':formatNumber(d['averageWinning'])}])
        tb1.add_row([u'平均亏损',"%(xxx)s"%{'xxx':formatNumber(d['averageLosing'])}])
        if d['averageLosing']==0:
            tb1.add_row([u'平均盈利/平均亏损',"%(xxx)s"%{'xxx':formatNumber(0)}])
        else:

            tb1.add_row([u'平均盈利/平均亏损',"%(xxx)s"%{'xxx':formatNumber(d['averageWinning']/abs(d['averageLosing']))}])            
        tb1.add_row(['  ','  '])
        
        tb1.add_row([u'交易次数',"%(xxx)s"%{'xxx':d['totalResult']}])
        tb1.add_row([u'盈利次数',"%(xxx)s"%{'xxx':d['winningResult']}])
        tb1.add_row([u'亏损次数',"%(xxx)s"%{'xxx':d['losingResult']}])
        tb1.add_row([u'胜率',"%(xxx)s%%"%{'xxx':formatNumber(d['winningRate'])}])
        tb1.add_row(['  ','  '])
        

        tb1.add_row([u'最大盈利',"%(xxx)s"%{'xxx':formatNumber(max(d['pnlList']))}])
        tb1.add_row([u'最大亏损',"%(xxx)s"%{'xxx':formatNumber(min(d['pnlList']))}])
        tb1.add_row([u'最大盈利时间',"%(xxx)s"%{'xxx':d['timeList'][d['pnlList'].index(max(d['pnlList']))].strftime("%Y-%m-%d")}])
        tb1.add_row([u'最大亏损时间',"%(xxx)s"%{'xxx':d['timeList'][d['pnlList'].index(min(d['pnlList']))].strftime("%Y-%m-%d")}])        
          
        if d['totalWinning'] == 0:
            tb1.add_row([u'最大盈利/总盈利',"%(xxx)s"%{'xxx':formatNumber(0)}])  
        else:
            tb1.add_row([u'最大盈利/总盈利',"%(xxx)s"%{'xxx':formatNumber(max(d['pnlList'])/abs(d['totalWinning']))}])    
            
            
        if d['totalLosing'] == 0:
            tb1.add_row([u'最大亏损/总亏损',"%(xxx)s"%{'xxx':formatNumber(0)}])  
        else:
            tb1.add_row([u'最大亏损/总亏损',"%(xxx)s"%{'xxx':formatNumber(min(d['pnlList'])/d['totalLosing'])}])  
            
        tb1.add_row([u'最大持续盈利次数',"%(xxx)s"%{'xxx':(max(d['winloselist']))}])        
        tb1.add_row([u'最大持续盈利时间',"%(xxx)s"%{'xxx':d['timeList'][d['winloselist'].index(max(d['winloselist']))-max(d['winloselist'])+1].strftime("%Y-%m-%d")+' --- '+d['timeList'][d['winloselist'].index(max(d['winloselist']))].strftime("%Y-%m-%d")}])    
        tb1.add_row([u'最大持续亏损次数',"%(xxx)s"%{'xxx':(abs(min(d['winloselist'])))}])            
        tb1.add_row([u'最大持续亏损时间',"%(xxx)s"%{'xxx':d['timeList'][d['winloselist'].index(min(d['winloselist']))-abs(min(d['winloselist']))+1].strftime("%Y-%m-%d")+' --- '+d['timeList'][d['winloselist'].index(min(d['winloselist']))].strftime("%Y-%m-%d")}])       
        tb1.add_row(['  ','  '])
        

        tb1.add_row([u'损益最大回撤',"%(xxx)s"%{'xxx':formatNumber(min(d['drawdownList']))}])     
        tb1.add_row([u'损益最大回撤时间',"%(xxx)s"%{'xxx':d['timeList'][d['drawdownList'].index(min(d['drawdownList']))].strftime("%Y-%m-%d")}])      
        tb1.add_row([u'损益最大回撤比',"%(xxx)s"%{'xxx':formatNumber(min(d['drawdownrateList']))}])  
        tb1.add_row([u'损益最大回撤比时间',"%(xxx)s"%{'xxx':d['timeList'][d['drawdownrateList'].index(min(d['drawdownrateList']))].strftime("%Y-%m-%d")}]) 
        tb1.add_row([u'权益最大回撤',"%(xxx)s"%{'xxx':formatNumber(result['maxDrawdown'])}])    
        tb1.add_row([u'权益最大回撤时间',"%(xxx)s"%{'xxx':result['maxDrawdowndate']}])            
        tb1.add_row([u'权益最大回撤比',"%(xxx)s"%{'xxx':formatNumber(result['maxDdPercent'])}])    
        tb1.add_row([u'权益最大回撤比时间',"%(xxx)s"%{'xxx':result['maxDdPercentdate']}])             
        
        
        tb1.reversesort = True        
        print(tb1)
        # 输出
        #self.output('-' * 30)
        #self.output(u'时间范围\t%s' %df.index.tolist()[0].strftime("%Y-%m-%d") +' --- '+df.index.tolist()[-1].strftime("%Y-%m-%d") )    
        #self.output(u'资金分配量\t%s' %formatNumber(self.capital))    
        #self.output(u'最终权益\t\t%s' % formatNumber(self.capital+d['capital'])) 
        #self.output(' ')     
        
        #self.output(u'盈利率\t\t%s%%' %formatNumber(d['profitrate']))    
        #self.output(u'总盈利\t\t%s' % formatNumber(d['totalWinning'])) 
        #self.output(u'总亏损\t\t%s' % formatNumber(d['totalLosing'])) 
        #self.output(u'净利润\t\t%s' % formatNumber(d['capital']))
        #self.output(u'总盈利/总亏损\t%s' %formatNumber(d['totalWinning']/abs(d['totalLosing'])))   
        #self.output(u'平均盈利\t\t%s' % formatNumber(d['averageWinning'])) 
        #self.output(u'平均亏损\t\t%s' % formatNumber(d['averageLosing'])) 
        #self.output(u'平均盈利/平均亏损%s' %formatNumber(d['averageWinning']/abs(d['averageLosing'])))  
        #self.output(' ')         
        
        #self.output(u'交易次数：\t%s' % formatNumber(d['totalResult']))     
        #self.output(u'盈利次数：\t%s' % formatNumber(d['winningResult']))   
        #self.output(u'亏损次数：\t%s' % formatNumber(d['losingResult']))   
        #self.output(u'胜率\t\t%s%%' %formatNumber(d['winningRate']))      
        #self.output(' ')                        
        
        #self.output(u'最大盈利：\t%s' % formatNumber(max(d['pnlList'])))  
        #self.output(u'最大亏损：\t%s' % formatNumber(min(d['pnlList'])))     
        #self.output(u'最大盈利时间\t%s'  % d['timeList'][d['pnlList'].index(max(d['pnlList']))].strftime("%Y-%m-%d"))
        #self.output(u'最大亏损时间\t%s'  % d['timeList'][d['pnlList'].index(min(d['pnlList']))].strftime("%Y-%m-%d"))
        #self.output(u'最大盈利/总盈利\t%s' %formatNumber(max(d['pnlList'])/abs(d['totalWinning']))) 
        #self.output(u'最大亏损/总亏损\t%s' %formatNumber(min(d['pnlList'])/d['totalLosing']))   
        #self.output(u'最大持续盈利次数\t%s' %formatNumber(max(d['winloselist'])))    
        #self.output(u'最大持续盈利时间\t%s'  % d['timeList'][d['winloselist'].index(max(d['winloselist']))-max(d['winloselist'])+1].strftime("%Y-%m-%d")+' --- '+d['timeList'][d['winloselist'].index(max(d['winloselist']))].strftime("%Y-%m-%d")) 
        #self.output(u'最大持续亏损次数\t%s' %formatNumber(abs(min(d['winloselist']))))     
        #self.output(u'最大持续亏损时间\t%s'  % d['timeList'][d['winloselist'].index(min(d['winloselist']))-abs(min(d['winloselist']))+1].strftime("%Y-%m-%d")+' --- '+d['timeList'][d['winloselist'].index(min(d['winloselist']))].strftime("%Y-%m-%d"))
        #self.output(' ')    
            
        #self.output(u'损益最大回撤: \t%s' % formatNumber(min(d['drawdownList'])))     
        #self.output(u'损益最大回撤时间\t%s'  % d['timeList'][d['drawdownList'].index(min(d['drawdownList']))].strftime("%Y-%m-%d"))
        #self.output(u'损益最大回撤比: \t%s%%' % formatNumber(min(d['drawdownrateList']))) 
        #self.output(u'损益最大回撤时间\t%s'  % d['timeList'][d['drawdownrateList'].index(min(d['drawdownrateList']))].strftime("%Y-%m-%d"))
        #self.output(u'权益最大回撤: \t%s' % formatNumber(result['maxDrawdown']))     
        #self.output(u'权益最大回撤时间\t%s'  % result['maxDrawdowndate'])
        #self.output(u'权益最大回撤比: \t%s%%' % formatNumber(result['maxDdPercent']))    
        #self.output(u'权益最大回撤时间\t%s'  % result['maxDdPercentdate'])      
        
        '''
        # 绘图
        fig = plt.figure(figsize=(10, 16))
        
        pCapital = plt.subplot(4, 1, 1)
        pCapital.set_ylabel("capital")
        pCapital.plot(d['capitalList'], color='r', lw=0.8)
        
        pDD = plt.subplot(4, 1, 2)
        pDD.set_ylabel("DD")
        pDD.bar(range(len(d['drawdownList'])), d['drawdownList'], color='g')
        
        pPnl = plt.subplot(4, 1, 3)
        pPnl.set_ylabel("pnl")
        pPnl.hist(d['pnlList'], bins=50, color='c')

        pPos = plt.subplot(4, 1, 4)
        pPos.set_ylabel("Position")
        if d['posList'][-1] == 0:
            del d['posList'][-1]
        tradeTimeIndex = [item.strftime("%m/%d %H:%M:%S") for item in d['tradeTimeList']]
        xindex = np.arange(0, len(tradeTimeIndex), np.int(len(tradeTimeIndex)/10))
        tradeTimeIndex = map(lambda i: tradeTimeIndex[i], xindex)
        pPos.plot(d['posList'], color='k', drawstyle='steps-pre')
        pPos.set_ylim(-1.2, 1.2)
        plt.sca(pPos)
        plt.tight_layout()
        plt.xticks(xindex, tradeTimeIndex, rotation=30)  # 旋转15
        
        plt.show()
        '''
    #----------------------------------------------------------------------
    def showBacktestingResultLikeWH_V1(self, df=None, result=None):
        """"显示回测结果,类似文华"""
        d = self.calculateBacktestingResultForWH()
        d_l = self.calculateBacktestingResultForWH(0)
        d_s = self.calculateBacktestingResultForWH(1)
        if len(d) == 0:
            return
        # 输出        
        #权益的相关指标需要，按日统计每日的资金持有情况，不能按照交易结果统计.请注意损益的统计是按照交易结果统计的
        df = df.set_index('date')
        df, result = self.calculateDailyStatisticsForWH(df)                  
        
        tb1 = pt.PrettyTable(["1", "2","3","4"],encoding=sys.stdout.encoding)
        tb1.field_names = [u'项目']+[u'值']+[u'值_多']+[u'值_空']
        tb1.add_row([u'时间范围',df.index.tolist()[0].strftime("%Y-%m-%d") +' --- '+df.index.tolist()[-1].strftime("%Y-%m-%d"),"",""])
        tb1.add_row([u'资金分配量',"%(xxx)s"%{'xxx':formatNumber(self.capital)},"",""])
        tb1.add_row([u'最终权益',"%(xxx)s"%{'xxx':formatNumber(self.capital+d['capital'])},"",""])
        tb1.add_row(['  ','  ',"",""])
        

        if d_l['totalResult'] >0 and d_s['totalResult']>0:
            tb1.add_row([u'盈利率',"%(xxx)s%%"%{'xxx':formatNumber(d['profitrate'])},"%(xxx)s%%"%{'xxx':formatNumber(d_l['profitrate'])},"%(xxx)s%%"%{'xxx':formatNumber(d_s['profitrate'])}])
            tb1.add_row([u'总盈利',"%(xxx)s"%{'xxx':formatNumber(d['totalWinning'])},"%(xxx)s"%{'xxx':formatNumber(d_l['totalWinning'])},"%(xxx)s"%{'xxx':formatNumber(d_s['totalWinning'])}])      
            tb1.add_row([u'总亏损',"%(xxx)s"%{'xxx':formatNumber(d['totalLosing'])},"%(xxx)s"%{'xxx':formatNumber(d_l['totalLosing'])},"%(xxx)s"%{'xxx':formatNumber(d_s['totalLosing'])}])
            tb1.add_row([u'净利润',"%(xxx)s"%{'xxx':formatNumber(d['capital'])},"%(xxx)s"%{'xxx':formatNumber(d_l['capital'])},"%(xxx)s"%{'xxx':formatNumber(d_s['capital'])}])
            tb1.add_row([u'总盈利/总亏损',"%(xxx)s"%{'xxx':formatNumber(d['totalWinning']/abs(d['totalLosing']))},"%(xxx)s"%{'xxx':formatNumber(d_l['totalWinning']/abs(d_l['totalLosing']))},"%(xxx)s"%{'xxx':formatNumber(d_s['totalWinning']/abs(d_s['totalLosing']))}])
            tb1.add_row([u'平均盈利',"%(xxx)s"%{'xxx':formatNumber(d['averageWinning'])},"%(xxx)s"%{'xxx':formatNumber(d_l['averageWinning'])},"%(xxx)s"%{'xxx':formatNumber(d_s['averageWinning'])}])
            tb1.add_row([u'平均亏损',"%(xxx)s"%{'xxx':formatNumber(d['averageLosing'])},"%(xxx)s"%{'xxx':formatNumber(d_l['averageLosing'])},"%(xxx)s"%{'xxx':formatNumber(d_s['averageLosing'])}])
            tb1.add_row([u'平均盈利/平均亏损',"%(xxx)s"%{'xxx':formatNumber(d['averageWinning']/abs(d['averageLosing']))},"%(xxx)s"%{'xxx':formatNumber(d_l['averageWinning']/abs(d_l['averageLosing']))},"%(xxx)s"%{'xxx':formatNumber(d_s['averageWinning']/abs(d_s['averageLosing']))}]) 
        if d_l['totalResult'] ==0:
            tb1.add_row([u'盈利率',"%(xxx)s%%"%{'xxx':formatNumber(d['profitrate'])},"%(xxx)s"%{'xxx':'---'},"%(xxx)s%%"%{'xxx':formatNumber(d_s['profitrate'])}])
            tb1.add_row([u'总盈利',"%(xxx)s"%{'xxx':formatNumber(d['totalWinning'])},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':formatNumber(d_s['totalWinning'])}])        
            tb1.add_row([u'总亏损',"%(xxx)s"%{'xxx':formatNumber(d['totalLosing'])},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':formatNumber(d_s['totalLosing'])}])
            tb1.add_row([u'净利润',"%(xxx)s"%{'xxx':formatNumber(d['capital'])},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':formatNumber(d_s['capital'])}])
            tb1.add_row([u'总盈利/总亏损',"%(xxx)s"%{'xxx':formatNumber(d['totalWinning']/abs(d['totalLosing']))},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':formatNumber(d_s['totalWinning']/abs(d_s['totalLosing']))}])
            tb1.add_row([u'平均盈利',"%(xxx)s"%{'xxx':formatNumber(d['averageWinning'])},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':formatNumber(d_s['averageWinning'])}])
            tb1.add_row([u'平均亏损',"%(xxx)s"%{'xxx':formatNumber(d['averageLosing'])},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':formatNumber(d_s['averageLosing'])}])
            tb1.add_row([u'平均盈利/平均亏损',"%(xxx)s"%{'xxx':formatNumber(d['averageWinning']/abs(d['averageLosing']))},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':formatNumber(d_s['averageWinning']/abs(d_s['averageLosing']))}]) 
        if d_s['totalResult'] ==0:
            tb1.add_row([u'盈利率',"%(xxx)s%%"%{'xxx':formatNumber(d['profitrate'])},"%(xxx)s%%"%{'xxx':formatNumber(d_l['profitrate'])},"%(xxx)s"%{'xxx':'---'}])
            tb1.add_row([u'总盈利',"%(xxx)s"%{'xxx':formatNumber(d['totalWinning'])},"%(xxx)s"%{'xxx':formatNumber(d_l['totalWinning'])},"%(xxx)s"%{'xxx':'---'}])             
            tb1.add_row([u'总亏损',"%(xxx)s"%{'xxx':formatNumber(d['totalLosing'])},"%(xxx)s"%{'xxx':formatNumber(d_l['totalLosing'])},"%(xxx)s"%{'xxx':'---'}])
            tb1.add_row([u'净利润',"%(xxx)s"%{'xxx':formatNumber(d['capital'])},"%(xxx)s"%{'xxx':formatNumber(d_l['capital'])},"%(xxx)s"%{'xxx':'---'}])
            tb1.add_row([u'总盈利/总亏损',"%(xxx)s"%{'xxx':formatNumber(d['totalWinning']/abs(d['totalLosing']))},"%(xxx)s"%{'xxx':formatNumber(d_l['totalWinning']/abs(d_l['totalLosing']))},"%(xxx)s"%{'xxx':'---'}])
            tb1.add_row([u'平均盈利',"%(xxx)s"%{'xxx':formatNumber(d['averageWinning'])},"%(xxx)s"%{'xxx':formatNumber(d_l['averageWinning'])},"%(xxx)s"%{'xxx':'---'}])
            tb1.add_row([u'平均亏损',"%(xxx)s"%{'xxx':formatNumber(d['averageLosing'])},"%(xxx)s"%{'xxx':formatNumber(d_l['averageLosing'])},"%(xxx)s"%{'xxx':'---'}])
            tb1.add_row([u'平均盈利/平均亏损',"%(xxx)s"%{'xxx':formatNumber(d['averageWinning']/abs(d['averageLosing']))},"%(xxx)s"%{'xxx':formatNumber(d_l['averageWinning']/abs(d_l['averageLosing']))},"%(xxx)s"%{'xxx':'---'}]) 

        
        tb1.add_row(['  ','  ','',''])
        
        if d_l['totalResult'] >0 and d_s['totalResult']>0:
            tb1.add_row([u'交易次数',"%(xxx)s"%{'xxx':d['totalResult']}  ,"%(xxx)s"%{'xxx':d_l['totalResult']},  "%(xxx)s"%{'xxx':d_s['totalResult']}])
            tb1.add_row([u'盈利次数',"%(xxx)s"%{'xxx':d['winningResult']},"%(xxx)s"%{'xxx':d_l['winningResult']},"%(xxx)s"%{'xxx':d_s['winningResult']}])
            tb1.add_row([u'亏损次数',"%(xxx)s"%{'xxx':d['losingResult']} ,"%(xxx)s"%{'xxx':d_l['losingResult']}, "%(xxx)s"%{'xxx':d_s['losingResult']}])
            tb1.add_row([u'胜率',"%(xxx)s%%"%{'xxx':formatNumber(d['winningRate'])},"%(xxx)s%%"%{'xxx':formatNumber(d_l['winningRate'])},"%(xxx)s%%"%{'xxx':formatNumber(d_s['winningRate'])}])
        if d_l['totalResult'] ==0:
            tb1.add_row([u'交易次数',"%(xxx)s"%{'xxx':d['totalResult']}  ,"%(xxx)s"%{'xxx':'---'},  "%(xxx)s"%{'xxx':d_s['totalResult']}])
            tb1.add_row([u'盈利次数',"%(xxx)s"%{'xxx':d['winningResult']},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':d_s['winningResult']}])
            tb1.add_row([u'亏损次数',"%(xxx)s"%{'xxx':d['losingResult']} ,"%(xxx)s"%{'xxx':'---'}, "%(xxx)s"%{'xxx':d_s['losingResult']}])
            tb1.add_row([u'胜率',"%(xxx)s%%"%{'xxx':formatNumber(d['winningRate'])},"%(xxx)s"%{'xxx':'---'},"%(xxx)s%%"%{'xxx':formatNumber(d_s['winningRate'])}])
        if d_s['totalResult'] ==0:
            tb1.add_row([u'交易次数',"%(xxx)s"%{'xxx':d['totalResult']}  ,"%(xxx)s"%{'xxx':d_l['totalResult']},  "%(xxx)s"%{'xxx':'---'}])
            tb1.add_row([u'盈利次数',"%(xxx)s"%{'xxx':d['winningResult']},"%(xxx)s"%{'xxx':d_l['winningResult']},"%(xxx)s"%{'xxx':'---'}])
            tb1.add_row([u'亏损次数',"%(xxx)s"%{'xxx':d['losingResult']} ,"%(xxx)s"%{'xxx':d_l['losingResult']}, "%(xxx)s"%{'xxx':'---'}])
            tb1.add_row([u'胜率',"%(xxx)s%%"%{'xxx':formatNumber(d['winningRate'])},"%(xxx)s%%"%{'xxx':formatNumber(d_l['winningRate'])},"%(xxx)s"%{'xxx':'---'}])
    
        
        tb1.add_row(['  ','  ','',''])
        
        if d_l['totalResult'] >0 and d_s['totalResult']>0:
            tb1.add_row([u'最大盈利',"%(xxx)s"%{'xxx':formatNumber(max(d['pnlList']))},"%(xxx)s"%{'xxx':formatNumber(max(d_l['pnlList']))},"%(xxx)s"%{'xxx':formatNumber(max(d_s['pnlList']))}])
            tb1.add_row([u'最大亏损',"%(xxx)s"%{'xxx':formatNumber(min(d['pnlList']))},"%(xxx)s"%{'xxx':formatNumber(min(d_l['pnlList']))},"%(xxx)s"%{'xxx':formatNumber(min(d_s['pnlList']))}])
            tb1.add_row([u'最大盈利时间',"%(xxx)s"%{'xxx':d['timeList'][d['pnlList'].index(max(d['pnlList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_l['timeList'][d_l['pnlList'].index(max(d_l['pnlList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_s['timeList'][d_s['pnlList'].index(max(d_s['pnlList']))].strftime("%Y-%m-%d")}])
            tb1.add_row([u'最大亏损时间',"%(xxx)s"%{'xxx':d['timeList'][d['pnlList'].index(min(d['pnlList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_l['timeList'][d_l['pnlList'].index(min(d_l['pnlList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_s['timeList'][d_s['pnlList'].index(min(d_s['pnlList']))].strftime("%Y-%m-%d")}])   
            if d_l['winningResult'] == 0:
                tb1.add_row([u'最大盈利/总盈利',"%(xxx)s"%{'xxx':formatNumber(max(d['pnlList'])/abs(d['totalWinning']))},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':formatNumber(max(d_s['pnlList'])/abs(d_s['totalWinning']))}]) 
            else:
                tb1.add_row([u'最大盈利/总盈利',"%(xxx)s"%{'xxx':formatNumber(max(d['pnlList'])/abs(d['totalWinning']))},"%(xxx)s"%{'xxx':formatNumber(max(d_l['pnlList'])/abs(d_l['totalWinning']))},"%(xxx)s"%{'xxx':formatNumber(max(d_s['pnlList'])/abs(d_s['totalWinning']))}])                 
            tb1.add_row([u'最大持续盈利次数',"%(xxx)s"%{'xxx':(max(d['winloselist']))},"%(xxx)s"%{'xxx':(max(d_l['winloselist']))},"%(xxx)s"%{'xxx':(max(d_s['winloselist']))}])                   
            if d_l['winningResult'] == 0:
                tb1.add_row([u'最大持续盈利时间',"%(xxx)s"%{'xxx':d['timeList'][d['winloselist'].index(max(d['winloselist']))-max(d['winloselist'])+1].strftime("%Y-%m-%d")+' --- '+d['timeList'][d['winloselist'].index(max(d['winloselist']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':d_s['timeList'][d_s['winloselist'].index(max(d_s['winloselist']))-max(d_s['winloselist'])+1].strftime("%Y-%m-%d")+' --- '+d_s['timeList'][d_s['winloselist'].index(max(d_s['winloselist']))].strftime("%Y-%m-%d")}]) 
            else:
                tb1.add_row([u'最大持续盈利时间',"%(xxx)s"%{'xxx':d['timeList'][d['winloselist'].index(max(d['winloselist']))-max(d['winloselist'])+1].strftime("%Y-%m-%d")+' --- '+d['timeList'][d['winloselist'].index(max(d['winloselist']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_l['timeList'][d_l['winloselist'].index(max(d_l['winloselist']))-max(d_l['winloselist'])+1].strftime("%Y-%m-%d")+' --- '+d_l['timeList'][d_l['winloselist'].index(max(d_l['winloselist']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_s['timeList'][d_s['winloselist'].index(max(d_s['winloselist']))-max(d_s['winloselist'])+1].strftime("%Y-%m-%d")+' --- '+d_s['timeList'][d_s['winloselist'].index(max(d_s['winloselist']))].strftime("%Y-%m-%d")}])         
            tb1.add_row([u'最大持续亏损次数',"%(xxx)s"%{'xxx':(abs(min(d['winloselist'])))},"%(xxx)s"%{'xxx':(abs(min(d_l['winloselist'])))},"%(xxx)s"%{'xxx':(abs(min(d_s['winloselist'])))}])            
            tb1.add_row([u'最大持续亏损时间',"%(xxx)s"%{'xxx':d['timeList'][d['winloselist'].index(min(d['winloselist']))-abs(min(d['winloselist']))+1].strftime("%Y-%m-%d")+' --- '+d['timeList'][d['winloselist'].index(min(d['winloselist']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_l['timeList'][d_l['winloselist'].index(min(d_l['winloselist']))-abs(min(d_l['winloselist']))+1].strftime("%Y-%m-%d")+' --- '+d_l['timeList'][d_l['winloselist'].index(min(d_l['winloselist']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_s['timeList'][d_s['winloselist'].index(min(d_s['winloselist']))-abs(min(d_s['winloselist']))+1].strftime("%Y-%m-%d")+' --- '+d_s['timeList'][d_s['winloselist'].index(min(d_s['winloselist']))].strftime("%Y-%m-%d")}])                                                                                  
        if d_l['totalResult'] ==0:
            tb1.add_row([u'最大盈利',"%(xxx)s"%{'xxx':formatNumber(max(d['pnlList']))},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':formatNumber(max(d_s['pnlList']))}])
            tb1.add_row([u'最大亏损',"%(xxx)s"%{'xxx':formatNumber(min(d['pnlList']))},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':formatNumber(min(d_s['pnlList']))}])
            tb1.add_row([u'最大盈利时间',"%(xxx)s"%{'xxx':d['timeList'][d['pnlList'].index(max(d['pnlList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':d_s['timeList'][d_s['pnlList'].index(max(d_s['pnlList']))].strftime("%Y-%m-%d")}])
            tb1.add_row([u'最大亏损时间',"%(xxx)s"%{'xxx':d['timeList'][d['pnlList'].index(min(d['pnlList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':d_s['timeList'][d_s['pnlList'].index(min(d_s['pnlList']))].strftime("%Y-%m-%d")}])  
            tb1.add_row([u'最大盈利/总盈利',"%(xxx)s"%{'xxx':formatNumber(max(d['pnlList'])/abs(d['totalWinning']))},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':formatNumber(max(d_s['pnlList'])/abs(d_s['totalWinning']))}]) 
            tb1.add_row([u'最大持续盈利次数',"%(xxx)s"%{'xxx':(max(d['winloselist']))},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':(max(d_s['winloselist']))}])      
            tb1.add_row([u'最大持续盈利时间',"%(xxx)s"%{'xxx':d['timeList'][d['winloselist'].index(max(d['winloselist']))-max(d['winloselist'])+1].strftime("%Y-%m-%d")+' --- '+d['timeList'][d['winloselist'].index(max(d['winloselist']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':d_s['timeList'][d_s['winloselist'].index(max(d_s['winloselist']))-max(d_s['winloselist'])+1].strftime("%Y-%m-%d")+' --- '+d_s['timeList'][d_s['winloselist'].index(max(d_s['winloselist']))].strftime("%Y-%m-%d")}])
            tb1.add_row([u'最大持续亏损次数',"%(xxx)s"%{'xxx':(abs(min(d['winloselist'])))},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':(abs(min(d_s['winloselist'])))}])            
            tb1.add_row([u'最大持续亏损时间',"%(xxx)s"%{'xxx':d['timeList'][d['winloselist'].index(min(d['winloselist']))-abs(min(d['winloselist']))+1].strftime("%Y-%m-%d")+' --- '+d['timeList'][d['winloselist'].index(min(d['winloselist']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':d_s['timeList'][d_s['winloselist'].index(min(d_s['winloselist']))-abs(min(d_s['winloselist']))+1].strftime("%Y-%m-%d")+' --- '+d_s['timeList'][d_s['winloselist'].index(min(d_s['winloselist']))].strftime("%Y-%m-%d")}]) 
        if d_s['totalResult'] ==0:    
            tb1.add_row([u'最大盈利',"%(xxx)s"%{'xxx':formatNumber(max(d['pnlList']))},"%(xxx)s"%{'xxx':formatNumber(max(d_l['pnlList']))},"%(xxx)s"%{'xxx':'---'}])
            tb1.add_row([u'最大亏损',"%(xxx)s"%{'xxx':formatNumber(min(d['pnlList']))},"%(xxx)s"%{'xxx':formatNumber(min(d_l['pnlList']))},"%(xxx)s"%{'xxx':'---'}])
            tb1.add_row([u'最大盈利时间',"%(xxx)s"%{'xxx':d['timeList'][d['pnlList'].index(max(d['pnlList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_l['timeList'][d_l['pnlList'].index(max(d_l['pnlList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':'---'}])
            tb1.add_row([u'最大亏损时间',"%(xxx)s"%{'xxx':d['timeList'][d['pnlList'].index(min(d['pnlList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_l['timeList'][d_l['pnlList'].index(min(d_l['pnlList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':'---'}])       
            tb1.add_row([u'最大盈利/总盈利',"%(xxx)s"%{'xxx':formatNumber(max(d['pnlList'])/abs(d['totalWinning']))},"%(xxx)s"%{'xxx':formatNumber(max(d_l['pnlList'])/abs(d_l['totalWinning']))},"%(xxx)s"%{'xxx':'---'}]) 
            tb1.add_row([u'最大持续盈利次数',"%(xxx)s"%{'xxx':(max(d['winloselist']))},"%(xxx)s"%{'xxx':(max(d_l['winloselist']))},"%(xxx)s"%{'xxx':'---'}])        
            tb1.add_row([u'最大持续盈利时间',"%(xxx)s"%{'xxx':d['timeList'][d['winloselist'].index(max(d['winloselist']))-max(d['winloselist'])+1].strftime("%Y-%m-%d")+' --- '+d['timeList'][d['winloselist'].index(max(d['winloselist']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_l['timeList'][d_l['winloselist'].index(max(d_l['winloselist']))-max(d_l['winloselist'])+1].strftime("%Y-%m-%d")+' --- '+d_l['timeList'][d_l['winloselist'].index(max(d_l['winloselist']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':'---'}])  
            tb1.add_row([u'最大持续亏损次数',"%(xxx)s"%{'xxx':(abs(min(d['winloselist'])))},"%(xxx)s"%{'xxx':(abs(min(d_l['winloselist'])))},"%(xxx)s"%{'xxx':'---'}])            
            tb1.add_row([u'最大持续亏损时间',"%(xxx)s"%{'xxx':d['timeList'][d['winloselist'].index(min(d['winloselist']))-abs(min(d['winloselist']))+1].strftime("%Y-%m-%d")+' --- '+d['timeList'][d['winloselist'].index(min(d['winloselist']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_l['timeList'][d_l['winloselist'].index(min(d_l['winloselist']))-abs(min(d_l['winloselist']))+1].strftime("%Y-%m-%d")+' --- '+d_l['timeList'][d_l['winloselist'].index(min(d_l['winloselist']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':'---'}])                                                                                  
           
     
        tb1.add_row(['  ','  ','',''])
        

        if d_l['totalResult'] >0 and d_s['totalResult']>0:
            tb1.add_row([u'损益最大回撤',"%(xxx)s"%{'xxx':formatNumber(min(d['drawdownList']))},"%(xxx)s"%{'xxx':formatNumber(min(d_l['drawdownList']))},"%(xxx)s"%{'xxx':formatNumber(min(d_s['drawdownList']))}])     
            tb1.add_row([u'损益最大回撤时间',"%(xxx)s"%{'xxx':d['timeList'][d['drawdownList'].index(min(d['drawdownList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_l['timeList'][d_l['drawdownList'].index(min(d_l['drawdownList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_s['timeList'][d_s['drawdownList'].index(min(d_s['drawdownList']))].strftime("%Y-%m-%d")}])      
            tb1.add_row([u'损益最大回撤比',"%(xxx)s"%{'xxx':formatNumber(min(d['drawdownrateList']))},"%(xxx)s"%{'xxx':formatNumber(min(d_l['drawdownrateList']))},"%(xxx)s"%{'xxx':formatNumber(min(d_s['drawdownrateList']))}])  
            tb1.add_row([u'损益最大回撤比时间',"%(xxx)s"%{'xxx':d['timeList'][d['drawdownrateList'].index(min(d['drawdownrateList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_l['timeList'][d_l['drawdownrateList'].index(min(d_l['drawdownrateList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_s['timeList'][d_s['drawdownrateList'].index(min(d_s['drawdownrateList']))].strftime("%Y-%m-%d")}])     
        if d_l['totalResult'] ==0:
            tb1.add_row([u'损益最大回撤',"%(xxx)s"%{'xxx':formatNumber(min(d['drawdownList']))},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':formatNumber(min(d_s['drawdownList']))}])     
            tb1.add_row([u'损益最大回撤时间',"%(xxx)s"%{'xxx':d['timeList'][d['drawdownList'].index(min(d['drawdownList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':d_s['timeList'][d_s['drawdownList'].index(min(d_s['drawdownList']))].strftime("%Y-%m-%d")}])   
            tb1.add_row([u'损益最大回撤比',"%(xxx)s"%{'xxx':formatNumber(min(d['drawdownrateList']))},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':formatNumber(min(d_s['drawdownrateList']))}])  
            tb1.add_row([u'损益最大回撤比时间',"%(xxx)s"%{'xxx':d['timeList'][d['drawdownrateList'].index(min(d['drawdownrateList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':'---'},"%(xxx)s"%{'xxx':d_s['timeList'][d_s['drawdownrateList'].index(min(d_s['drawdownrateList']))].strftime("%Y-%m-%d")}]) 
        if d_s['totalResult'] ==0:  
            tb1.add_row([u'损益最大回撤',"%(xxx)s"%{'xxx':formatNumber(min(d['drawdownList']))},"%(xxx)s"%{'xxx':formatNumber(min(d_l['drawdownList']))},"%(xxx)s"%{'xxx':'---'}])     
            tb1.add_row([u'损益最大回撤时间',"%(xxx)s"%{'xxx':d['timeList'][d['drawdownList'].index(min(d['drawdownList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_l['timeList'][d_l['drawdownList'].index(min(d_l['drawdownList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':'---'}])     
            tb1.add_row([u'损益最大回撤比',"%(xxx)s"%{'xxx':formatNumber(min(d['drawdownrateList']))},"%(xxx)s"%{'xxx':formatNumber(min(d_l['drawdownrateList']))},"%(xxx)s"%{'xxx':'---'}])  
            tb1.add_row([u'损益最大回撤比时间',"%(xxx)s"%{'xxx':d['timeList'][d['drawdownrateList'].index(min(d['drawdownrateList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':d_l['timeList'][d_l['drawdownrateList'].index(min(d_l['drawdownrateList']))].strftime("%Y-%m-%d")},"%(xxx)s"%{'xxx':'---'}]) 
        
        
        tb1.add_row([u'权益最大回撤',"%(xxx)s"%{'xxx':formatNumber(result['maxDrawdown'])},"",""])    
        tb1.add_row([u'权益最大回撤时间',"%(xxx)s"%{'xxx':result['maxDrawdowndate']},"",""])            
        tb1.add_row([u'权益最大回撤比',"%(xxx)s"%{'xxx':formatNumber(result['maxDdPercent'])},"",""])    
        tb1.add_row([u'权益最大回撤比时间',"%(xxx)s"%{'xxx':result['maxDdPercentdate']},"",""])              
        
        
        tb1.reversesort = True        
        print(tb1)
    #----------------------------------------------------------------------
       
            
########################################################################
class TradingResult(object):
    """每笔交易的结果"""

    #----------------------------------------------------------------------
    def __init__(self, entryPrice, entryDt, exitPrice, 
                 exitDt, volume, rate, slippage, size):
        """Constructor"""
        self.entryPrice = entryPrice    # 开仓价格
        self.exitPrice = exitPrice      # 平仓价格
        
        self.entryDt = entryDt          # 开仓时间datetime    
        self.exitDt = exitDt            # 平仓时间
        
        self.volume = volume    # 交易数量（+/-代表方向）
        
        self.turnover = (self.entryPrice+self.exitPrice)*size*abs(volume)   # 成交金额
        self.commission = self.turnover*rate                                # 手续费成本
        self.slippage = slippage*2*size*abs(volume)                         # 滑点成本
        self.pnl = ((self.exitPrice - self.entryPrice) * volume * size 
                    - self.commission - self.slippage)                      # 净盈亏


########################################################################
class DailyResult(object):
    """每日交易的结果"""

    #----------------------------------------------------------------------
    def __init__(self, date, closePrice):
        """Constructor"""
        self.date = date                # 日期
        self.closePrice = closePrice    # 当日收盘价
        self.previousClose = 0          # 昨日收盘价
        
        self.tradeList = []             # 成交列表
        self.tradeCount = 0             # 成交数量
        
        self.openPosition = 0           # 开盘时的持仓
        self.closePosition = 0          # 收盘时的持仓
        
        self.tradingPnl = 0             # 交易盈亏
        self.positionPnl = 0            # 持仓盈亏
        self.totalPnl = 0               # 总盈亏
        
        self.turnover = 0               # 成交量
        self.commission = 0             # 手续费
        self.slippage = 0               # 滑点
        self.netPnl = 0                 # 净盈亏
        
    #----------------------------------------------------------------------
    def addTrade(self, trade):
        """添加交易"""
        self.tradeList.append(trade)

    #----------------------------------------------------------------------
    def calculatePnl(self, openPosition=0, size=1, rate=0, slippage=0):
        """
        计算盈亏
        size: 合约乘数
        rate：手续费率
        slippage：滑点点数
        """
        # 持仓部分
        self.openPosition = openPosition
        self.positionPnl = self.openPosition * (self.closePrice - self.previousClose) * size
        self.closePosition = self.openPosition
        
        # 交易部分
        self.tradeCount = len(self.tradeList)
        
        for trade in self.tradeList:
            if trade.direction == DIRECTION_LONG:
                posChange = trade.volume
            else:
                posChange = -trade.volume
                
            self.tradingPnl += posChange * (self.closePrice - trade.price) * size
            self.closePosition += posChange
            self.turnover += trade.price * trade.volume * size
            self.commission += trade.price * trade.volume * size * rate
            self.slippage += trade.volume * size * slippage
        
        # 汇总
        self.totalPnl = self.tradingPnl + self.positionPnl
        self.netPnl = self.totalPnl - self.commission - self.slippage


########################################################################
class OptimizationSetting(object):
    """优化设置"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.paramDict = OrderedDict()
        
        self.optimizeTarget = ''        # 优化目标字段
        
        self.greater_than=[]        #[['x','y'],['a','b']]  'x' > 'y' , 'a' > 'b'
        self.less_than=[]           #[['x','y'],['a','b']]  'x' < 'y' , 'a' < 'b'
        self.greater_than_equal=[]  #[['x','y'],['a','b']]  'x' >= 'y' , 'a' >= 'b'
        self.less_than_equal=[]     #[['x','y'],['a','b']]  'x' <= 'y' , 'a' <= 'b'
        
    #----------------------------------------------------------------------
    def addParameter(self, name, start, end=None, step=None):
        """增加优化参数"""
        if end is None and step is None:
            self.paramDict[name] = [start]
            return 
        
        if end < start:
            print(u'参数起始点必须不大于终止点')
            return
        
        if step <= 0:
            print(u'参数布进必须大于0')
            return
        
        l = []
        param = start
        
        while param <= end:
            l.append(param)
            param += step
        
        self.paramDict[name] = l
        
    #----------------------------------------------------------------------
    def generateSetting(self):
        """生成优化参数组合"""
        # 参数名的列表
        nameList = self.paramDict.keys()
        paramList = self.paramDict.values()
        
        # 使用迭代工具生产参数对组合
        productList = list(product(*paramList))
        
        # 把参数对组合打包到一个个字典组成的列表中
        settingList = []
        for p in productList:
            d = dict(zip(nameList, p))
            
            ##### 任建军添加20181105#####################
            filter_pass=True
            for filter in self.greater_than:
                if not(d[filter[0]] > d[filter[1]]) :
                    filter_pass=False
                    break
            if filter_pass==False:
                continue
            
            filter_pass=True
            for filter in self.less_than:
                if not(d[filter[0]] < d[filter[1]]) :
                    filter_pass=False
                    break
            if filter_pass==False:
                continue        
            
            filter_pass=True
            for filter in self.greater_than_equal:
                if not(d[filter[0]] >= d[filter[1]]) :
                    filter_pass=False
                    break
            if filter_pass==False:
                continue   
            
            filter_pass=True
            for filter in self.less_than_equal:
                if not(d[filter[0]] <= d[filter[1]]) :
                    filter_pass=False
                    break
            if filter_pass==False:
                continue   
            ##### 任建军添加20181105#####################
            
            settingList.append(d)
    
        return settingList
    #----------------------------------------------------------------------
    def addfilter_greater_than(self, lists):
        """参数的大于关系，会成倍的优化运行效率"""
        self.greater_than =  lists
        pass
    def addfilter_less_than(self,lists):
        """参数的小于等于关系，会成倍的优化运行效率"""
        self.less_than =  lists
        pass
    def addfilter_greater_than_equal(self,lists):
        """参数的大于等于关系，会成倍的优化运行效率"""
        self.greater_than_equal =  lists
        pass
    def addfilter_less_than_equal(self,lists):
        """参数的小于等于关系，会成倍的优化运行效率"""
        self.less_than_equal =  lists
        pass
        
    
    #----------------------------------------------------------------------
    def setOptimizeTarget(self, target):
        """设置优化目标字段"""
        self.optimizeTarget = target


########################################################################
class HistoryDataServer(RpcServer):
    """历史数据缓存服务器"""

    #----------------------------------------------------------------------
    def __init__(self, repAddress, pubAddress):
        """Constructor"""
        super(HistoryDataServer, self).__init__(repAddress, pubAddress)
        
        self.dbClient = pymongo.MongoClient(globalSetting['mongoHost'], 
                                            globalSetting['mongoPort'])
        
        self.historyDict = {}
        
        self.register(self.loadHistoryData)
    
    #----------------------------------------------------------------------
    def loadHistoryData(self, dbName, symbol, start, end):
        """"""
        # 首先检查是否有缓存，如果有则直接返回
        history = self.historyDict.get((dbName, symbol, start, end), None)
        if history:
            print(u'找到内存缓存：%s %s %s %s' %(dbName, symbol, start, end))
            return history
        
        # 否则从数据库加载
        collection = self.dbClient[dbName][symbol]
        
        if end:
            flt = {'datetime':{'$gte':start, '$lt':end}}        
        else:
            flt = {'datetime':{'$gte':start}}        
            
        cx = collection.find(flt).sort('datetime')
        history = [d for d in cx]
        
        self.historyDict[(dbName, symbol, start, end)] = history
        print(u'从数据库加载：%s %s %s %s' %(dbName, symbol, start, end))
        return history
    
#----------------------------------------------------------------------
def runHistoryDataServer():
    """"""
    repAddress = 'tcp://*:5555'
    pubAddress = 'tcp://*:7777'

    hds = HistoryDataServer(repAddress, pubAddress)
    hds.start()

    print(u'按任意键退出')
    hds.stop()
    raw_input()

#----------------------------------------------------------------------
def formatNumber(n):
    """格式化数字到字符串"""
    rn = round(n, 2)        # 保留两位小数
    return format(rn, ',')  # 加上千分符
    

#----------------------------------------------------------------------
def optimize(strategyClass, setting, targetName,
             mode, startDate, initDays, endDate,
             slippage, rate, size, priceTick,
             dbName, symbol,capital,poolscount,num):
    """多进程优化时跑在每个进程中运行的函数"""
    engine = BacktestingEngine()
    engine.outputshow=False
    engine.setBacktestingMode(mode)
    engine.setStartDate(startDate, initDays)
    engine.setEndDate(endDate)
    engine.setSlippage(slippage)
    engine.setRate(rate)
    engine.setSize(size)
    engine.setPriceTick(priceTick)
    engine.setDatabase(dbName, symbol)
    engine.setCapital(capital)
    
    engine.initStrategy(strategyClass, setting)
    engine.runBacktesting()
    
    
    print('总次数：%d , 当前次数：%d , 执行进度%02.2f%%'%(poolscount[0],poolscount[num],float(poolscount[num]/poolscount[0]*100)))
    
    
    df = engine.calculateDailyResult()
    
    if len(df) == 0:
        return (str(setting), 0,{},{},setting)  
    df, d = engine.calculateDailyStatistics(df)
    
  
    ###任建军添加
    d1= engine.calculateBacktestingResultForWH()
    ###任建军添加
    try:
        targetValue = d[targetName]
    except KeyError:
        targetValue = 0          
    #原始代码    
    #return (str(setting), targetValue,d)    
    ###任建军添加
    return (str(setting), targetValue,d,d1,setting)    
    ###任建军添加
    