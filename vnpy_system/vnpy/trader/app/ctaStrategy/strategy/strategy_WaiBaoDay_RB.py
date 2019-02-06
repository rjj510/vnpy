# encoding: UTF-8

"""
这里的策略是根据《短线交易秘诀（原书第2版）》第7.3章节内容编写而成。
"""

from __future__ import division

from vnpy.trader.vtConstant import EMPTY_STRING, EMPTY_FLOAT,DIRECTION_LONG,OFFSET_OPEN,DIRECTION_SHORT,OFFSET_CLOSE
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator,
                                                     ArrayManager)

EMPTY_INT_WH = -1
EMPTY_FLOAT_WH = -1.0
########################################################################
class strategy_WaiBaoDay_RB(CtaTemplate):
    """短期市场结构策略"""
    className = 'strategy_WaiBaoDay_RB'
    author = u'任建军'
    
    # 策略参数                   
    A_WEIGHT            = 10       #{每手吨数                }                 
    A_BZJ               = 0.14     #{保证金参数              }
    BKPRICE             = EMPTY_FLOAT_WH
    A_LOSS_SP_ALL       = 0.14               # 保证金亏损幅度     #
    A_FLAOT_PROFIT_ALL  = 1700               # 最佳浮盈           #     
    #--------------以下是可以优化的策略----------------------------     
        
    # 策略变量
    initDays= 10            # 初始化数据所用的天数
    
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'A_LOSS_SP_ALL',
                 'A_FLAOT_PROFIT_ALL']    
    
    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos']  
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(strategy_WaiBaoDay_RB, self).__init__(ctaEngine, setting)
        
        #self.initDays= 
     
        self.strategyStartpos                =1891      
        self.strategyEndpos                  =2394     
        self.all_bar                         =[]            
        self.bg = BarGenerator(self.onBar)
        self.am = ArrayManager(self.initDays)
        
        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）        
        
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        
        self.writeCtaLog(u'攻击日交易策略初始化')
        
        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)
            self.ctaEngine.updateDailyClose(bar.datetime, bar.close)
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'攻击日交易结构策略启动')
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'攻击日交易结构策略停止')
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
        
        if len(self.all_bar) > self.strategyEndpos+1 :  
                return
                        
        if len(self.all_bar) < self.strategyStartpos :
            self.putEvent()            
            return  
        
                           
        #-------------------------做多买开条件-----------------------------------------------
        
        # 上一个交易日是外包日的形态K线   
        BK_Condition_1 = False 
        if    (self.all_bar[-2].low    <  self.all_bar[-3].low  and \
               self.all_bar[-2].high   >  self.all_bar[-3].high and \
               self.all_bar[-2].close  <  self.all_bar[-3].low):
            BK_Condition_1 = True
        
        #外包日第二天开盘价的方向,书上说第二天开盘价的方向低于外包日收盘价之下，以开盘价买入。（个人建议还是以收盘价买入）
        BK_Condition_2 = False 
        if self.all_bar[-1].open <  self.all_bar[-2].close:
            BK_Condition_2 =True
                
        #-------------------------做多卖平条件-----------------------------------------------  
        #条件1：保证金亏损幅度         
        SP_Condition_1  = False            
        if self.pos == 1:
            A_PRICE_SP              = self.BKPRICE*self.A_WEIGHT*self.A_BZJ      #{最近买开价位总费用} 
            SP_Condition_1          = (self.BKPRICE-bar.close)*self.A_WEIGHT > (A_PRICE_SP*self.A_LOSS_SP_ALL)    


        #条件2：最佳浮盈  
        SP_Condition_2  = False   
        if self.pos == 1:
            SP_Condition_2          = (bar.close-self.BKPRICE)*self.A_WEIGHT >= self.A_FLAOT_PROFIT_ALL  
            
        #-------------------------做多执行交易---------------------------------------------------
        if BK_Condition_1 and BK_Condition_2 and self.pos == 0:    
            self.buy(bar.close, 1)
        if (SP_Condition_1 or SP_Condition_2 ) and self.pos == 1 :
            self.sell(bar.close, 1)     
    
        #-------------------------做多条件-----------------------------------------------
        pass
        #-------------------------做空条件-----------------------------------------------
        pass
 
                
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
        if trade.direction == DIRECTION_LONG and trade.offset == OFFSET_OPEN  :    #做多买开
            self.BKPRICE = trade.price
        if trade.direction == DIRECTION_SHORT and trade.offset == OFFSET_CLOSE:    #做多卖平
            self.BKPRICE = EMPTY_FLOAT_WH   
            
    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass    
