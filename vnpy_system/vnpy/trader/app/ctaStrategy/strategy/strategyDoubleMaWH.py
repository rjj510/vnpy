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
    A_LONG        = 25       #{做多交易均线天数       默认 }   
    E_LONG        = 93       #{做多趋势均线天数}                                      
    A_DAYS_BK     = 0        #{交易线开仓穿越天数 用于买开  默认2 }  
    A_DAYS_SP     = 2        #{交易线平仓穿越天数 用于卖平  默认2 }                              
    E_DAYS_LONG   = 2        #{做多从下到上的天数}                       
    A_RATE_BK_MIN = 0.1      #{交易线开仓穿越幅度 用于买开  默认2 }    
    A_RATE_BK_MAX = 1.8      #{交易线开仓穿越幅度 用于买开  默认2 }     
    A_RATE_SP     = 0.94     #{交易线平仓穿越幅度 用于卖平  默认1.2}    
    A_LOSS_SP     = 0.08     #{保证金亏损幅度     用于卖平  默认0.45}    
    A_DAY_LOSS    = 1.7      #{达到当日最大跌幅   用于卖平  默认2.3}    
    A_FLAOT_PROFIT= 2900     #{最大浮盈           用于卖平  默认}  
    '''
    
    A_LONG        = 19       #{做多交易均线天数       默认 }   
    E_LONG        = 115       #{做多趋势均线天数}                                      
    A_DAYS_BK     = 0        #{交易线开仓穿越天数 用于买开  默认2 }  
    A_DAYS_SP     = 2        #{交易线平仓穿越天数 用于卖平  默认2 }                              
    E_DAYS_LONG   = 1        #{做多从下到上的天数}                       
    A_RATE_BK_MIN = 0.3      #{交易线开仓穿越幅度 用于买开  默认2 }    
    A_RATE_BK_MAX = 2.38     #{交易线开仓穿越幅度 用于买开  默认2 }     
    A_RATE_SP     = 0.1      #{交易线平仓穿越幅度 用于卖平  默认1.2}    
    A_LOSS_SP     = 0.15     #{保证金亏损幅度     用于卖平  默认0.45}    
    A_DAY_LOSS    = 2.4      #{达到当日最大跌幅   用于卖平  默认2.3}    
    A_FLAOT_PROFIT= 3800     #{最大浮盈           用于卖平  默认}  
    
    
    # 策略变量
    A_ma0   = EMPTY_FLOAT
    A_ma1   = EMPTY_FLOAT
    A_close1= EMPTY_FLOAT    
    BARSLAST_CR_UP_LONG = EMPTY_INT_WH
    BARSLAST_CR_DOWN_LONG = EMPTY_INT_WH
    BKPRICE = EMPTY_FLOAT_WH
    E_ma0   = EMPTY_FLOAT
    E_ma1   = EMPTY_FLOAT    
    initDays= E_LONG+E_DAYS_LONG            # 初始化数据所用的天数
    
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'A_LONG',
                 'A_DAYS_BK',
                 'A_RATE_BK_MIN',
                 'A_RATE_BK_MAX',
                 'A_DAYS_SP',
                 'A_RATE_SP',
                 'A_LOSS_SP',
                 'A_DAY_LOSS',
                 'A_FLAOT_PROFIT',
                 'E_LONG',
                 'E_DAYS_LONG']    
    
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
        
        self.initDays= self.E_LONG+self.E_DAYS_LONG
        
        self.bg = BarGenerator(self.onBar)
        self.am = ArrayManager(self.initDays)
        
        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）
        
        
        self.A_ma0   = EMPTY_FLOAT
        self.A_ma1   = EMPTY_FLOAT
        self.A_close1= EMPTY_FLOAT    
        self.BARSLAST_CR_UP_LONG = EMPTY_INT_WH
        self.BARSLAST_CR_DOWN_LONG = EMPTY_INT_WH
        self.BKPRICE = EMPTY_FLOAT_WH
        self.E_ma0   = EMPTY_FLOAT
        self.E_ma1   = EMPTY_FLOAT     
        
        
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'双EMA演示策略初始化')
        
        #initData = self.loadBar(self.ctaEngine.initDays)
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
        am = self.am        
        am.updateBar(bar)
        if not am.inited:
            return
                        
        #/*用CLOSE上下穿越交易均线，来确定买入或者卖出时机*/
        #//A=TRADE 交易
        #//E=TREND 趋势      
        A_ma  = am.sma(self.A_LONG,array=True)  
        self.A_ma0 = A_ma[-1]  
        self.A_ma1 = A_ma[-2]
        self.A_close1 = am.closeArray[-2]
        #-------------------------买开条件-----------------------------------------------
        #{上穿交易线       买开}           
        if self.BARSLAST_CR_UP_LONG == EMPTY_INT_WH:
            CR_UP_LONG   = bar.close>self.A_ma0 and self.A_close1<self.A_ma1
            if CR_UP_LONG:
                self.BARSLAST_CR_UP_LONG = 0  
                self.BARSLAST_CR_DOWN_LONG = EMPTY_INT_WH
            else:
                pass
        else:
            self.BARSLAST_CR_UP_LONG = self.BARSLAST_CR_UP_LONG + 1               
        #{上穿交易线  A_DAYS_BK   买开1}        
        EL1          = self.BARSLAST_CR_UP_LONG>=self.A_DAYS_BK
        #{上穿交易线幅度A_RATE_BK 买开2}        
        EL2_MIN      = bar.close>(self.A_ma0*(1+self.A_RATE_BK_MIN/100));
        #{上穿交易线幅度A_RATE_BK 买开2}        
        EL2_MAX      = bar.close<(self.A_ma0*(1+self.A_RATE_BK_MAX/100));   
        
        #-------------------------卖平条件-----------------------------------------------
        #{下穿交易线       卖平}                               
        if self.BARSLAST_CR_DOWN_LONG == EMPTY_INT_WH:
            CR_DOWN_LONG = bar.close<self.A_ma0 and self.A_close1>self.A_ma1
            if CR_DOWN_LONG:
                self.BARSLAST_CR_DOWN_LONG = 0  
                self.BARSLAST_CR_UP_LONG = EMPTY_INT_WH
            else:
                pass
        else:
            self.BARSLAST_CR_DOWN_LONG = self.BARSLAST_CR_DOWN_LONG + 1            
        #{下穿交易线  A_DAYS_SP     卖平1}        
        SP1          = self.BARSLAST_CR_DOWN_LONG>=self.A_DAYS_SP
        #{下穿交易线幅度A_RATE_SP   卖平2}        
        SP2          = self.A_ma0>(bar.close*(1+self.A_RATE_SP/100))
        #{保证金亏损幅度            卖平3}    
        SP3          = False
        if self.pos == 1:
            A_PRICE_SP   = self.BKPRICE*self.A_WEIGHT*self.A_BZJ      #{最近买开价位总费用 用于卖平} 
            SP3          = (self.BKPRICE-bar.close)*self.A_WEIGHT > (A_PRICE_SP*self.A_LOSS_SP)
        #{当日最大跌幅度           卖平4}        
        SP4              = (am.closeArray[-2]-am.closeArray[-1])/am.closeArray[-1]*100 > self.A_DAY_LOSS
        #{最佳浮盈                卖平5}        
        SP5              = (bar.close-self.BKPRICE)*self.A_WEIGHT >= self.A_FLAOT_PROFIT
        
        #{买开条件成立}                            
        GOING_BK         = EL1 and EL2_MAX and EL2_MIN 
        #{卖平条件成立}         
        GOING_SP        = (SP1 and SP2) or SP3 or SP4 or SP5         
        
        #-------------------------做多条件-----------------------------------------------
        #/*用CLOSE在趋势线的上方或者下方，来判断是做多还是做空*/
        E_ma  = am.sma(self.E_LONG,array=True)  
        self.E_ma0 = E_ma[-1]          
        #// 趋势线         
        #{上穿趋势线，做多}     
        MA_UP           = bar.close > self.E_ma0    
        #// 做多行情
        #{MA_UP形态持续了E_DAYS天 做多}
        GOING_LONG   = min(map(lambda x, y: x - y, am.closeArray.tolist()[(0-self.E_DAYS_LONG):], E_ma.tolist()[(0-self.E_DAYS_LONG):]))>0
        
        #-------------------------交易-----------------------------------------------
        if GOING_LONG and GOING_BK and self.pos == 0: 
            self.buy(bar.close, 1)
        if GOING_SP and self.pos == 1:
            self.sell(bar.close, 1)
                
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
        if trade.direction == DIRECTION_LONG and trade.offset == OFFSET_OPEN :
            self.BKPRICE = trade.price
        if trade.direction == DIRECTION_SHORT and trade.offset == OFFSET_CLOSE :
            self.BKPRICE = EMPTY_FLOAT_WH 
    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass    
