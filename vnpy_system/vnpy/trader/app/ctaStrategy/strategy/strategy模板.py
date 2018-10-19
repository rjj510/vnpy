# encoding: UTF-8

"""
这里的策略是根据《短线交易秘诀（原书第2版）》第一章1.4认识市场结构的内容编写而成。
"""

from __future__ import division

from vnpy.trader.vtConstant import EMPTY_STRING, EMPTY_FLOAT,DIRECTION_LONG,OFFSET_OPEN,DIRECTION_SHORT,OFFSET_CLOSE
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator,
                                                     ArrayManager)

EMPTY_INT_WH = -1
EMPTY_FLOAT_WH = -1.0
########################################################################
class ShortTermStrategy(CtaTemplate):
    """短期市场结构策略"""
    className = 'ShortTermStrategy'
    author = u'任建军'
    
    # 策略参数                   
    A_WEIGHT      = 10       #{每手吨数                }                 
    A_BZJ         = 0.14     #{保证金参数              }
    #--------------以下是可以优化的策略----------------------------     
        
    # 策略变量
    initDays= 0            # 初始化数据所用的天数
    
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol']    
    
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
        
        #self.initDays= 
        
        self.bg = BarGenerator(self.onBar)
        self.am = ArrayManager(self.initDays)
        
        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）        
        
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        
        self.writeCtaLog(u'短期市场结构策略初始化')
        
        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)
            self.ctaEngine.updateDailyClose(bar.datetime, bar.close)
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'短期市场结构策略启动')
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'短期市场结构策略停止')
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        self.bg.updateTick(tick)
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        am = self.am        
        am.updateBar(bar)
        if not am.inited:
            return
                           
        #-------------------------买开条件-----------------------------------------------
        pass        
        #-------------------------卖平条件-----------------------------------------------  
        pass
        #-------------------------做多条件-----------------------------------------------
        pass
        #-------------------------做空条件-----------------------------------------------
        pass
        #-------------------------执行交易---------------------------------------------------
 
                
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
    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass    
