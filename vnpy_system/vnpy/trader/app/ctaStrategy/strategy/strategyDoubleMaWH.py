# encoding: UTF-8

"""
这里的Demo是一个MA_螺纹_多_PLUS_2017策略实现
"""

from __future__ import division

from vnpy.trader.vtConstant import EMPTY_STRING, EMPTY_FLOAT,DIRECTION_LONG,OFFSET_OPEN,DIRECTION_SHORT,OFFSET_CLOSE
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator,
                                                     ArrayManager)

EMPTY_INT_WH = -1
EMPTY_FLOAT_WH = -1.0
########################################################################
class DoubleMaStrategyWh(CtaTemplate):
    """双指数均线策略Demo"""
    className = 'DoubleMaStrategyWh'
    author = u'任建军'
    
    # 策略参数                   
    A_WEIGHT      = 10       #{每手吨数                }                 
    A_BZJ         = 0.14     #{保证金参数              }
    #--------------以下是可以优化的策略----------------------------
    '''
    SK_A_LONG        = 17       #{做空交易均线天数}                           
    SK_A_DAYS_OPEN   = 1        #{交易线开仓穿越天数 用于卖开}              
    SK_A_RATE_MIN    = 0.76     #{交易线开仓穿越幅度 用于卖开}    
    SK_A_RATE_MAX    = 3.70     #{交易线开仓穿越幅度 用于卖开}   
    SK_A_DAYS_CLOSE  = 1        #{交易线平仓穿越天数 用于买平}              
    SK_A_RATE_SP     = 0.6      #{交易线平仓穿越幅度 用于买平}  
    SK_A_LOSS_SP     = 0.06     #{保证金亏损幅度     用于买平}    
    SK_A_DAY_LOSS    = 2.74     #{达到当日最大涨幅   用于买平}    
    SK_A_FLAOT_PROFIT= 2550     #{最大浮盈          用于买平}   
    SK_E_LONG        = 64       #{做空趋势均线天数   用于判断是否做空}                                        
    SK_E_DAYS_LONG   = 2        #{做空趋势线的天数   用于判断是否做空}    
    '''
    SK_A_LONG        = 13       #{做空交易均线天数}                           
    SK_A_DAYS_OPEN   = 5        #{交易线开仓穿越天数 用于卖开}              
    SK_A_RATE_MIN    = 0.65     #{交易线开仓穿越幅度 用于卖开}    
    SK_A_RATE_MAX    = 3.70     #{交易线开仓穿越幅度 用于卖开}   
    SK_A_DAYS_CLOSE  = 1        #{交易线平仓穿越天数 用于买平}              
    SK_A_RATE_SP     = 3.1      #{交易线平仓穿越幅度 用于买平}  
    SK_A_LOSS_SP     = 0.08     #{保证金亏损幅度     用于买平}    
    SK_A_DAY_LOSS    = 1.7      #{达到当日最大涨幅   用于买平}    
    SK_A_FLAOT_PROFIT= 2900     #{最大浮盈          用于买平}   
    SK_E_LONG        = 69       #{做空趋势均线天数   用于判断是否做空}                                        
    SK_E_DAYS_LONG   = 6        #{做空趋势线的天数   用于判断是否做空}   
    
    
    # 策略变量
    SK_A_ma0   = EMPTY_FLOAT
    SK_A_ma1   = EMPTY_FLOAT
    SK_A_close1= EMPTY_FLOAT    
    BARSLAST_CR_UP_SK_A_LONG    = EMPTY_INT_WH
    BARSLAST_CR_DOWN_SK_A_LONG  = EMPTY_INT_WH
    BARSLAST_CR_UP_SK_E_LONG    = EMPTY_INT_WH
    BARSLAST_CR_DOWN_SK_E_LONG  = EMPTY_INT_WH
    BKPRICE = EMPTY_FLOAT_WH 
    SKPRICE = EMPTY_FLOAT_WH 
    initDays= SK_E_LONG+SK_E_DAYS_LONG            # 初始化数据所用的天数
    
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'SK_A_LONG',
                 'SK_A_DAYS_OPEN',
                 'SK_A_RATE_MIN',
                 'SK_A_RATE_MAX',
                 'SK_A_DAYS_CLOSE',
                 'SK_A_RATE_SP',
                 'SK_A_LOSS_SP',
                 'SK_A_DAY_LOSS',
                 'SK_A_FLAOT_PROFIT',
                 'SK_E_LONG',
                 'SK_E_DAYS_LONG']    
    
    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos']  
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(DoubleMaStrategyWh, self).__init__(ctaEngine, setting)
        
        self.initDays= self.SK_E_LONG+self.SK_E_DAYS_LONG
        
        self.bg = BarGenerator(self.onBar)
        self.am = ArrayManager(self.initDays)
        
        self.strategyStartpos                =1891      
        self.strategyEndpos                  =2344        
        self.all_bar                         =[]       
        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）
        
        
        self.SK_A_ma0   = EMPTY_FLOAT
        self.SK_A_ma1   = EMPTY_FLOAT
        self.SK_A_close1= EMPTY_FLOAT    
        self.BARSLAST_CR_UP_SK_A_LONG   = EMPTY_INT_WH
        self.BARSLAST_CR_DOWN_SK_A_LONG = EMPTY_INT_WH
        self.BARSLAST_CR_UP_SK_E_LONG   = EMPTY_INT_WH
        self.BARSLAST_CR_DOWN_SK_E_LONG = EMPTY_INT_WH
        self.BKPRICE    = EMPTY_FLOAT_WH
        self.SKPRICE    = EMPTY_FLOAT_WH 
        self.SK_E_ma0   = EMPTY_FLOAT
        self.SK_E_ma1   = EMPTY_FLOAT     
        self.BP_style   = 0000        
        
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'双EMA演示策略初始化')
        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)
            self.ctaEngine.updateDailyClose(bar.datetime, bar.close)
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'双EMA演示策略启动')
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'双EMA演示策略停止')
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        self.bg.updateTick(tick)
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        self.all_bar.append(bar)  
        am = self.am        
        am.updateBar(bar)
        if not am.inited:
            return
        
        if len(self.all_bar) > self.strategyEndpos :   
            '''
            if self.pos > 0:
                self.sell(bar.close, self.pos)
                self.putEvent()              
            if self.pos < 0:
                self.cover(bar.close, abs(self.pos)) 
                self.putEvent()                         
            '''
            return
        
        #/*用CLOSE上下穿越交易均线，来确定买入或者卖出时机*/
        #//A=TRADE 交易
        #//E=TREND 趋势      
        A_ma             = am.sma(self.SK_A_LONG,array=True)  
        self.SK_A_ma0    = A_ma[-1]  
        self.SK_A_ma1    = A_ma[-2]
        self.SK_A_close1 = am.closeArray[-2]        
        if self.BARSLAST_CR_UP_SK_A_LONG   == EMPTY_INT_WH:
            CR_UP_LONG   = bar.close>self.SK_A_ma0 and self.SK_A_close1<self.SK_A_ma1
            if CR_UP_LONG:
                self.BARSLAST_CR_UP_SK_A_LONG = 0  
                self.BARSLAST_CR_DOWN_SK_A_LONG = EMPTY_INT_WH
        else:
            self.BARSLAST_CR_UP_SK_A_LONG = self.BARSLAST_CR_UP_SK_A_LONG + 1                    
        if self.BARSLAST_CR_DOWN_SK_A_LONG == EMPTY_INT_WH:
            CR_DOWN_LONG = bar.close<self.SK_A_ma0 and self.SK_A_close1>self.SK_A_ma1
            if CR_DOWN_LONG:
                self.BARSLAST_CR_DOWN_SK_A_LONG = 0  
                self.BARSLAST_CR_UP_SK_A_LONG = EMPTY_INT_WH
        else:
            self.BARSLAST_CR_DOWN_SK_A_LONG = self.BARSLAST_CR_DOWN_SK_A_LONG + 1           
      
        if len(self.all_bar) < self.strategyStartpos :
            self.putEvent()            
            return            
            
        #-------------------------1、做空卖开条件-----------------------------------------
        #条件1：向下突破开仓均线（SK_A_LONG）达到天数（SK_A_DAYS_OPEN）与幅度（SK_A_RATE_MIN...SK_A_RATE_MAX）
        SK_Condition_1 = False 
        if self.BARSLAST_CR_DOWN_SK_A_LONG >= self.SK_A_DAYS_OPEN and \
           bar.close < (self.SK_A_ma0*(1-self.SK_A_RATE_MIN/100))    and \
           bar.close > (self.SK_A_ma0*(1-self.SK_A_RATE_MAX/100))    :
            SK_Condition_1 = True 
        
        #条件2：在过去周期（SK_E_DAYS_LONG）天数，CLOSE保持在均线（SK_E_LONG）下方
        E_ma  = am.sma(self.SK_E_LONG,array=True)  
        SK_Condition_2 = max(map(lambda x, y: x - y, am.closeArray.tolist()[(0-self.SK_E_DAYS_LONG):], E_ma.tolist()[(0-self.SK_E_DAYS_LONG):]))<0                         
        #-------------------------2、做空买平条件-----------------------------------------
        self.BP_style   = 0000            
        #条件1：保证金亏损 
        BP_Condition_1   = False
        if self.pos == -1:
            A_PRICE_SP        = self.SKPRICE*self.A_WEIGHT*self.A_BZJ
            BP_Condition_1    = (bar.close - self.SKPRICE)*self.A_WEIGHT > (A_PRICE_SP*self.SK_A_LOSS_SP)   
            if BP_Condition_1:
                self.BP_style     = self.BP_style | 8 #1000            
        #条件2：最佳浮盈
        BP_Condition_2  = False            
        if self.pos == -1:
            BP_Condition_2    = (self.SKPRICE - bar.close)*self.A_WEIGHT >= self.SK_A_FLAOT_PROFIT
            if BP_Condition_2:
                self.BP_style     = self.BP_style | 4 #0100      
        #条件3：当日最大涨幅
        BP_Condition_3  = False            
        if self.pos == -1:
            BP_Condition_3    = (am.closeArray[-1]-am.closeArray[-2])/am.closeArray[-2]*100 > self.SK_A_DAY_LOSS  
            if BP_Condition_3:
                self.BP_style     = self.BP_style | 2 #0010                            
        #条件4：向上突破平仓均线（SK_A_LONG）达到天数（SK_A_DAYS_CLOSE）与幅度（SK_A_RATE_SP）
        BP_Condition_4  = False           
        if self.pos == -1:
            if self.BARSLAST_CR_UP_SK_A_LONG >= self.SK_A_DAYS_CLOSE and\
               self.SK_A_ma0>(bar.close*(1+self.SK_A_RATE_SP/100)):
                BP_Condition_4  = True  
                self.BP_style     = self.BP_style | 1 #0001                     
        #-------------------------3 、 做空执行交易-----------------------------------------------  
        if SK_Condition_1 and self.pos == 0 and SK_Condition_2:               
            self.short(bar.close, 1)   
        if (BP_Condition_1 or BP_Condition_2 or BP_Condition_3 or BP_Condition_4) and self.pos == -1 :  
            self.cover(bar.close, 1)     
        
        # 发出状态更新事件
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder              
        if trade.direction == DIRECTION_SHORT and trade.offset == OFFSET_OPEN  :          
            self.SKPRICE = trade.price
            print('SELL :',trade.tradeTime,trade.price)
        if trade.direction == DIRECTION_LONG and trade.offset == OFFSET_CLOSE: 
            print('COVER:',trade.tradeTime,trade.price,(self.SKPRICE- trade.price)*self.A_WEIGHT,'{:08b}'.format(self.BP_style)[-4:]) 
            self.SKPRICE = EMPTY_FLOAT_WH   
    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass    
