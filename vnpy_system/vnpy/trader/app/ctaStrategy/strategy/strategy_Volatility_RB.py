# encoding: UTF-8

"""
这里的策略是根据《短线交易秘诀（原书第2版）》第四章动能穿透的内容编写而成
"""

from __future__ import division

from vnpy.trader.vtConstant import EMPTY_STRING, EMPTY_FLOAT,DIRECTION_LONG,OFFSET_OPEN,DIRECTION_SHORT,OFFSET_CLOSE
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator,
                                                     ArrayManager)
from datetime import datetime ,timedelta
import time

EMPTY_INT_WH = -1
EMPTY_FLOAT_WH = -1.0
########################################################################
class strategy_Volatility_RB(CtaTemplate):
    """双指数均线策略Demo"""
    className = 'strategy_Volatility_RB'
    author = u'任建军'
    
    # 策略参数                   
    A_WEIGHT      = 10       #{每手吨数                }                 
    A_BZJ         = 0.14     #{保证金参数              }
    #--------------以下是可以优化的策略----------------------------
    #20181129 做多的优化参数优化期全部数据 [星期1,2,3,4,5]
    ''' 
    BK_A_LOSS_SP     = 750      #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.75     #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.75     #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{波幅的天数                } 
    BK_A_FLAOT_PROFIT_ALL=500   #{最佳浮盈                  }    
    '''
    #20181129 做多的优化参数优化期全部数据 [星期1,2,3]
    BK_A_LOSS_SP     = 1400     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.7      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.9      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{波幅的天数                } 
    BK_A_FLAOT_PROFIT_ALL=500   #{最佳浮盈                  } 
    #20181129 做多的优化参数优化期20170103-20181130 [星期1,2,3,4,5]
    ''' 
    BK_A_LOSS_SP     = 1350     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.75      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.9      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{波幅的天数                } 
    BK_A_FLAOT_PROFIT_ALL=550   #{最佳浮盈                  }  
    '''
    
    #20181204 做空的优化参数优化期全部数据 [星期1,2,3,4,5]
    '''
    SK_A_LOSS_SP     = 1500     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.7      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 1.3      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 1        #{波幅的天数                } 
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }  
    
    
    #20181204 做空的优化参数优化期全部数据 [星期1,2,3,4]
    SK_A_LOSS_SP     = 400     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.5      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 0.4      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 1        #{波幅的天数                } 
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }      
    '''    
    #20181204 做空的优化参数优化期最近数据 [星期1,2,3,4,5]
    '''
    SK_A_LOSS_SP     = 700      #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.7      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 1.0      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 1        #{波幅的天数                } 
    SK_A_FLAOT_PROFIT_ALL=500   #{最佳浮盈                  }       
    '''
    #20181204 做空的优化参数优化期最近数据 [星期2,3,4]
    SK_A_LOSS_SP     = 1050     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.3      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 0.9      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 1        #{波幅的天数                } 
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }       
    
    
    # 策略变量
    showtrade        = False  
    LongOrShort      = True                
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'BK_A_LOSS_SP',
                 'BK_Volatility',
                 'SP_Volatility',
                 'BK_BEFORE_DAY',
                 'BK_A_FLAOT_PROFIT_ALL',
                 'SK_A_LOSS_SP',
                 'SK_Volatility',
                 'BP_Volatility',
                 'SK_BEFORE_DAY',
                 'SK_A_FLAOT_PROFIT_ALL']    
    
    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos']  
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(strategy_Volatility_RB, self).__init__(ctaEngine, setting)
    
        self.initDays         = max(self.BK_BEFORE_DAY,self.SK_BEFORE_DAY)           # 初始化数据所用的天数        
        self.bg = BarGenerator(self.onBar)
        self.am = ArrayManager(self.initDays)
        
        self.strategyStartpos                =1890      
        self.strategyEndpos                  =2358        
        self.all_bar                         =[]     
        self.SP_style                        =0000 
        self.BP_style                        =0000 
        self.BKPRICE                         =EMPTY_FLOAT_WH  
        self.BKDATE                          =EMPTY_FLOAT_WH  
        self.SKPRICE                         =EMPTY_FLOAT_WH  
        self.SKDATE                          =EMPTY_FLOAT_WH  
        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）
        self.BKWeekProfit                    =[0,0,0,0,0,0,0]
        self.SKWeekProfit                    =[0,0,0,0,0,0,0]
        self.LongBestday                     =[0,1,2]
        self.ShortBestday                    =[1,2,3]
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'波幅率演示策略初始化')
        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)
            self.ctaEngine.updateDailyClose(bar.datetime, bar.close)
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'波幅率演示策略启动')
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'波幅率演示策略停止')
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
            '''
            if self.pos == 1:
                self.sell(bar.close,1)
            elif self.pos == -1:
                self.cover(bar.close,1)
            '''
            return
        
        # 这个出了一个大问题 -1代表的是取今天的数据，-2代表取前一天的数据
        # 根据书中内容本意是取-2前一天的数据，结果错写成-1.所有测试结果也是按照取值-1计算。
        # 万幸的是取值-1的结果也不错，暂时以取值-1位置。
        # 代表的逻辑是：
        # 下影线长 上影线短 ，open+BK_CURDAYRANGE*self.BK_Volatility 容易冲出范围
        # 光头光脚          ，open+BK_CURDAYRANGE*self.BK_Volatility 不易冲出范围
        # 下影线短 上影线长 ，open+BK_CURDAYRANGE*self.BK_Volatility 不易冲出范围
        # 总之，从K线上看 BK_Condition_1是一个倒锤阳线才可以，或者接近光头光脚阳线
        BK_CURDAYRANGE1 = self.all_bar[-self.BK_BEFORE_DAY].high - self.all_bar[-1].low
        BK_CURDAYRANGE2 = self.all_bar[-1].high - self.all_bar[-self.BK_BEFORE_DAY].low
        BK_CURDAYRANGE  = max(BK_CURDAYRANGE1,BK_CURDAYRANGE2)     
        
        SK_CURDAYRANGE1 = self.all_bar[-self.BK_BEFORE_DAY].high - self.all_bar[-1].low
        SK_CURDAYRANGE2 = self.all_bar[-1].high - self.all_bar[-self.SK_BEFORE_DAY].low
        SK_CURDAYRANGE  = max(SK_CURDAYRANGE1,SK_CURDAYRANGE2)   
        
        if len(self.all_bar) < self.strategyStartpos :
            self.putEvent()            
            return            
        
        if bar.date == u'20180523':
            print bar.date 
        #-------------------------1、做多买开条件-----------------------------------------
        #条件1：价格高于开盘价，达到前日波幅买入；没有办法确认价格是收阳还是收阴，只能在当天价格确实有高于开盘价格幅度或低于开盘幅度的那一刹那成交openorclose
        BK_Condition_1 = False     
        if bar.low <= bar.open  +  (BK_CURDAYRANGE*self.BK_Volatility) and  \
           bar.high>= bar.open  +  (BK_CURDAYRANGE*self.BK_Volatility) and  \
           bar.close>=bar.open:
            BK_Condition_1 = True   
                  
        #-------------------------2、做多卖平条件-----------------------------------------   
        self.SP_style=0000
        #条件1：保证金亏损 保证金亏损只能在第二天进行确认，也不能在当天确认，但是当天可能超过了保证金的亏损。
        SP_Condition_1   = False
        if self.pos == 1:
            A_PRICE_SP         =  self.BKPRICE-self.BK_A_LOSS_SP/self.A_WEIGHT
            SP_Condition_1     =  bar.close<A_PRICE_SP  # bar.low <= A_PRICE_SP and  bar.high>=A_PRICE_SP  
            if SP_Condition_1:
                self.SP_style     = self.SP_style | 8 #1000   
        #条件2：买开价格减去波幅的一定比率 由于价格的震荡，当天可能做多后又做空
        SP_Condition_2  = False            
        if self.pos == 1:
            SP_Condition_2    =  bar.close < self.BKPRICE  -  (BK_CURDAYRANGE*self.SP_Volatility)
            if SP_Condition_2:
                self.SP_style     = self.SP_style | 4 #0100   
        #条件3：最佳浮盈
        SP_Condition_3  = False            
        if self.pos == 1:
            SP_Condition_3     = (bar.close-self.BKPRICE)*self.A_WEIGHT >= self.BK_A_FLAOT_PROFIT_ALL    
            if SP_Condition_3:
                self.SP_style     = self.SP_style | 2 #0010                                          
        #-------------------------3 、 做多执行交易-----------------------------------------------  
        if BK_Condition_1 and self.pos==0 and self.LongOrShort == True:      
            #0 '星期一',1 :'星期二',2  '星期三',3 '星期四',4  '星期五',5  '星期六',6 '星期天', 
            if (datetime.strptime(bar.date, "%Y%m%d").weekday() in self.LongBestday) :            
                self.buy(bar.close, 1)
            else:
                '''
                假设周1，2，3交易，周4，5不交易，但周4、5的BK_Condition_1为TRUE（称为虚拟交易买入信号）,需要将周4、5的pos置为大于1，
                这样即便是下周1（程为虚拟下周1）出现交易信号，系统也不能发出交易信号，因为对于虚拟交易买入信号的虚拟卖出信号还没有发出来，直到虚拟卖出
                信号发出后才可继续进行交易。
                只有只有才符合从周1到周5找出的最佳交易日子，所达成的结果。否则虚拟下周1的出现会打乱它后面的所有交易信号。
                '''
                self.pos = self.pos+1
                self.BKDATE = datetime.strptime(bar.date, "%Y%m%d") 
                self.BKPRICE = bar.close
                return 
            
        if (SP_Condition_1 or SP_Condition_2 or SP_Condition_3 ) and self.pos == 1 :    
            #0 '星期一',1 :'星期二',2  '星期三',3 '星期四',4  '星期五',5  '星期六',6 '星期天', 
            if (self.BKDATE.weekday() in self.LongBestday):              
                self.sell(bar.close, 1) 
            else:
                self.BKWeekProfit[self.BKDATE.weekday()]=self.BKWeekProfit[self.BKDATE.weekday()]+(bar.close- self.BKPRICE)*self.A_WEIGHT 
                self.pos = self.pos-1
                self.BKDATE = EMPTY_FLOAT_WH
                '''
                if self.showtrade: 
                    for each in self.BKWeekProfit:
                        print each,',',  
                    print '\r',          
                '''
                return 
                            
        #-------------------------4、做空卖开条件-----------------------------------------
        #条件4：价格低于开盘价，达到前日波幅卖开；
        SK_Condition_1 = False 
        if bar.low <= bar.open  -  (SK_CURDAYRANGE1*self.SK_Volatility) and  \
           bar.high>= bar.open  -  (SK_CURDAYRANGE1*self.SK_Volatility) and  \
           bar.close<bar.open:
            SK_Condition_1 = True             
        
        #-------------------------5、做空买平条件-----------------------------------------   
        self.BP_style=0000
        #条件1：保证金亏损 
        BP_Condition_1   = False
        if self.pos == -1:
            A_PRICE_SP         =  self.SKPRICE+self.SK_A_LOSS_SP/self.A_WEIGHT         
            BP_Condition_1     =  bar.close>A_PRICE_SP  
            if BP_Condition_1:
                self.BP_style  = self.BP_style | 8 #1000   
        #条件2：卖开价格减去波幅的一定比率
        BP_Condition_2  = False            
        if self.pos == -1:
            BP_Condition_2    =  bar.close > self.SKPRICE  +  (SK_CURDAYRANGE1*self.BP_Volatility)
            if BP_Condition_2:
                self.BP_style     = self.BP_style | 4 #0100  
        #条件3：最佳浮盈
        BP_Condition_3  = False            
        if self.pos == -1:       
            BP_Condition_3    = (self.SKPRICE - bar.close)*self.A_WEIGHT >= self.SK_A_FLAOT_PROFIT_ALL    
            if BP_Condition_3:
                self.BP_style     = self.BP_style | 2 #0010    
            
        #-------------------------6 、 做空执行交易-----------------------------------------------          
        if SK_Condition_1 and self.pos==0 and self.LongOrShort == False:      
            #0 '星期一',1 :'星期二',2  '星期三',3 '星期四',4  '星期五',5  '星期六',6 '星期天', 
            if (datetime.strptime(bar.date, "%Y%m%d").weekday() in self.ShortBestday) :            
                self.short(bar.close, 1)  
            else:
                # 注释参见做多的注释
                self.pos = self.pos-1
                self.SKDATE = datetime.strptime(bar.date, "%Y%m%d") 
                self.SKPRICE = bar.close
                return         
            
        if (BP_Condition_1 or BP_Condition_2 or BP_Condition_3 ) and self.pos == -1 :    
            #0 '星期一',1 :'星期二',2  '星期三',3 '星期四',4  '星期五',5  '星期六',6 '星期天', 
            if (self.SKDATE.weekday() in self.ShortBestday):              
                self.cover(bar.close, 1) 
            else:
                self.SKWeekProfit[self.SKDATE.weekday()]=self.SKWeekProfit[self.SKDATE.weekday()]+(self.SKPRICE - bar.close)*self.A_WEIGHT 
                self.pos = self.pos+1
                self.SKDATE = EMPTY_FLOAT_WH
                
                if self.showtrade: 
                    for each in self.SKWeekProfit:
                        print each,',',  
                    print '\r',          
                return  
            
        
        
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
            if self.showtrade: 
                print 'VRB BUY :',',',trade.tradeTime,',',trade.price 
                pass
            self.BKPRICE = trade.price
            self.BKDATE  = datetime.strptime(trade.tradeTime, "%Y-%m-%d")  
        if trade.direction == DIRECTION_SHORT and trade.offset == OFFSET_CLOSE:    #做多卖平
            if self.showtrade: 
                #0 '星期一',1 :'星期二',2  '星期三',3 '星期四',4  '星期五',5  '星期六',6 '星期天', 
                self.BKWeekProfit[self.BKDATE.weekday()]=self.BKWeekProfit[self.BKDATE.weekday()]+(trade.price- self.BKPRICE)*self.A_WEIGHT 
                print 'VRB SELL:',',',trade.tradeTime,',',trade.price,',',(trade.price- self.BKPRICE)*self.A_WEIGHT ,',','{:08b}'.format(self.SP_style)[-4:]                
                #for each in self.BKWeekProfit:
                #    print each,',',  
                #print '\r',                
            self.BKPRICE = EMPTY_FLOAT_WH   
            self.BKDATE  = EMPTY_FLOAT_WH
            
        if trade.direction == DIRECTION_SHORT and trade.offset == OFFSET_OPEN  :   #做空卖开
            if self.showtrade: 
                #print 'VRB SELL  :',',',trade.tradeTime,',',trade.price        
                pass
            self.SKPRICE = trade.price
            self.SKDATE  = datetime.strptime(trade.tradeTime, "%Y-%m-%d")  
        if trade.direction == DIRECTION_LONG and trade.offset == OFFSET_CLOSE:     #做空买平
            if self.showtrade: 
                self.SKWeekProfit[self.SKDATE.weekday()]=self.SKWeekProfit[self.SKDATE.weekday()]+(self.SKPRICE - trade.price)*self.A_WEIGHT 
                #print 'VRB COVER:',',',trade.tradeTime,',',trade.price,',',(self.SKPRICE- trade.price)*self.A_WEIGHT ,',','{:08b}'.format(self.BP_style)[-4:]
                for each in self.SKWeekProfit:
                    print each,',',  
                print '\r',                 
            self.SKPRICE = EMPTY_FLOAT_WH   
            self.SKDATE  = EMPTY_FLOAT_WH
    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass    
