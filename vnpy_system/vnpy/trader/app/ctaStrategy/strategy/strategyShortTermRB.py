# encoding: UTF-8

"""
这里的策略是根据《短线交易秘诀（原书第2版）》第一章1.4认识市场结构的内容编写而成。
中英对照
买开 BK
卖平 SP
卖开 SK
卖平 BP 


策略原则：
1、 务必力求简单 （优化参数不超过5个，选取合适的参数的指标权重：收益率>最大回撤>胜率）
    参数1: E_LONG              趋势确定参数 
    参数2: A_LOSS_SP           保证金亏损幅度
    参数3: A_FLAOT_PROFIT      最佳浮盈
    参数4:
    参数5:    
2、 顺势而为           （使用MA指标进行趋势判定）
3、 保住本金，减小亏损  （保证金亏损幅度）
4、 保护利润，合理止盈  （最佳浮盈）
5、 避免过度拟合（用2017年的做样本，用2016做测试）


"""

from __future__ import division

from vnpy.trader.vtConstant import EMPTY_STRING, EMPTY_FLOAT,DIRECTION_LONG,OFFSET_OPEN,DIRECTION_SHORT,OFFSET_CLOSE
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator,
                                                     ArrayManager)
import json
import numpy as np
import copy

EMPTY_INT_WH = -1
EMPTY_FLOAT_WH = -1.0
EMPTY_DATE_WH = ''
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
    initDays= 1                          # 初始化数据所用的天数
    # 策略启动日期位置（即前面的数据用于初始化），int值  
    # 注意：这个值决定了回测开始时刻的index值,
    # 多参数优化时根据F:\uiKLine\json\uiKLine_startpara中的STARTPOS值直接修改该值
    # 直接回测时候也需要直接修改该值
    # 同时修改__init__中的这个值
    #strategyStartpos=1890              
    #strategyEndpos=2340           
    strategyStartpos=1  #   20141010           
    strategyEndpos=2353    #   20160927
    
    # 策略 做多策略还是做空策略，BOOL值  True=Long False=Short
    # 注意：多参数优化时直接修改该值
    # 直接回测时候也需要直接修改该值
    LongOrShort     =False                
    
    all_bar=[]                           # 存放所以bar  
    ####--20170103优化参数(strategyStartpos = 1890 20170103)开多------#####       
    A_LOSS_SP_ALL       = 0.16               # 保证金亏损幅度     #
    A_FLAOT_PROFIT_ALL  = 1900               # 最佳浮盈           # 
    A_MIN_UP_ALL        = 0.9                # close超过short_term_last_two_high_all_index[1]幅度# 
    E_LONG_ALL          = 34       
    
    ###--20090327优化参数(strategyStartpos = 1890 20170103)开空-----#####
    SK_A_LOSS_SP_ALL     = 0.37               # 保证金亏损幅度   #
    SK_A_FLAOT_PROFIT_ALL= 1450               # 最佳浮盈         #   
    SK_E_LONG_ALL        = 34   
    A_MIN_DOWN_ALL       = 0.9                 # close超过short_term_last_two_low_all_index[1]幅度 #    
    ###---------------------------------------------------#####
    
    BKPRICE = EMPTY_FLOAT_WH
    SKPRICE = EMPTY_FLOAT_WH
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'A_LOSS_SP_FIRST',
                 'A_FLAOT_PROFIT_FIRST ',
                 'E_LONG_FIRST',
                 'A_LOSS_SP_ALL',
                 'A_FLAOT_PROFIT_ALL',
                 'A_MIN_UP_ALL',
                 'A_MIN_DOWN_ALL',
                 'SK_A_LOSS_SP_ALL',
                 'SK_A_FLAOT_PROFIT_ALL',
                 'SK_E_LONG',
                 'LongOrShort',
                 ]    
    
    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos']  
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(ShortTermStrategy, self).__init__(ctaEngine, setting)
        
        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）
        self.short_term_list_first           =[] 
        self.short_term_list_all             =[] 
        self.short_term_last_three_first_index=[]
        self.short_term_last_two_low_all_index=[]
        self.short_term_last_two_high_all_index=[]
        self.short_term_open_last_three_first_index=[]
        self.short_term_open_last_two_all_index=[]
        self.all_bar                         =[]   
        self.BK_style                        =EMPTY_INT_WH    # 2-->所有的低点 21利用低点 22利用高点
        self.SK_style                        =EMPTY_INT_WH    # 2-->所有的高点 21利用高点 22利用低点
        self.BKPRICE                         =EMPTY_FLOAT_WH   
        self.SKPRICE                         =EMPTY_FLOAT_WH
        self.initDays                        =self.E_LONG_ALL if self.LongOrShort==True else self.SK_E_LONG_ALL
        self.MAXCLOSE_AFTER_OPEN             =EMPTY_FLOAT_WH #建仓后close的最大值
        self.strategyStartpos                =1343      
        self.strategyEndpos                  =1826        
        self.SP_style   = 0000          
        self.tradeday                        =0        
        self.bg = BarGenerator(self.onBar)
        self.am = ArrayManager(self.initDays)  
        
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""        
        self.writeCtaLog(u'短期市场结构策略初始化')
             
        index_settings = self.load_All_Index_Setting()
        if len(index_settings)==0 :
            print("检查F:\uiKLine\json\uiKLine_all_index.json路径是否正确")
            return
        for setting in index_settings:
            self.short_term_list_all = setting[u'SHORT_TERM_INDEX']     
        if len(self.short_term_list_all) == 0:
            print("short term数据为空")
            return
        
        
        initData = self.loadBar(self.initDays)        
        for bar in initData:
            self.ctaEngine.updateDailyClose(bar.datetime, bar.close)
            self.onBar(bar)
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
    def short_term_all_index(self,bar,am):
        """
        利用short term(all)作为策略进行交易  
        1、做多买开：
        1-1、2个连续的低点呈现上升趋势买开
        1-2、2个连续的高点呈现上升趋势，且当日的close高于第二个高点的最高值A_MIN_UP_ALL%买开
        2、做多卖平
        2-1、保证金亏损幅度
        2-2、最佳浮盈
        2-3、对于1-1 closed低于用于开仓的第二个低点日的low值 
        2-4、对于1-2 closed低于用于开仓的第一个高点日的high值 
        """
        ########################################################################################
        # 更新最近两次短期列表的值 低1 < 低1 -->做多买入 
        if len(self.short_term_last_two_low_all_index) < 2 :
            if (self.short_term_list_all[len(self.all_bar)-1] != 0 and self.short_term_list_all[len(self.all_bar)-1] != 2) :
                self.short_term_last_two_low_all_index.append(len(self.all_bar)-1)
            return
        else:
            if (self.short_term_list_all[len(self.all_bar)-1] != 0 and self.short_term_list_all[len(self.all_bar)-1] != 2) :
                del self.short_term_last_two_low_all_index[0] 
                self.short_term_last_two_low_all_index.append(len(self.all_bar)-1)      
                
        # 更新最近两次短期列表的值 高2 < 高2 -->做多买入 , 高2 >  高2 -->做多卖平 
        if len(self.short_term_last_two_high_all_index) < 2 :
            if (self.short_term_list_all[len(self.all_bar)-1] != 0 and self.short_term_list_all[len(self.all_bar)-1] != 1) :
                self.short_term_last_two_high_all_index.append(len(self.all_bar)-1)
            return
        else:
            if (self.short_term_list_all[len(self.all_bar)-1] != 0 and self.short_term_list_all[len(self.all_bar)-1] != 1) :
                del self.short_term_last_two_high_all_index[0] 
                self.short_term_last_two_high_all_index.append(len(self.all_bar)-1)      
                
        if len(self.all_bar) < self.strategyStartpos :          
            return
        
        if self.tradeday > 0:
            self.tradeday = self.tradeday + 1
            
        #if bar.date=='20190408':
        #    print bar.date        
        ########################################################################################       
        #------------------------ 1 、 做多买开条件-----------------------------------------------        
        # 条件1：短期市场结构是否满足要求 满足为TRUE 不满足为FALSE
        BK_Condition_1 = False 
        # 首先：满足做多的基本要求形态-->低1 < 低1
        if  self.short_term_list_all[self.short_term_last_two_low_all_index[0]] == 1 and \
            self.short_term_list_all[self.short_term_last_two_low_all_index[1]] == 1  :
            # 其次：低点是上升的形态 后面的低点高于前面的低点 并且 最后面的低1的那个k日线全部走完（确定一个高、低点需要3个K线）
            if  (self.all_bar[self.short_term_last_two_low_all_index[0]].low  < self.all_bar[self.short_term_last_two_low_all_index[1]].low)  and \
                (len(self.all_bar)                                          == self.short_term_last_two_low_all_index[1]+2) :    
                # 最后： 如果指标没有被使用过
                if  cmp(self.short_term_open_last_two_all_index , self.short_term_last_two_low_all_index) != 0:
                    BK_Condition_1 = True     
                    
        # 条件2：短期市场结构是否满足要求 满足为TRUE 不满足为FALSE
        BK_Condition_2 = False 
        # 首先：满足做多的基本要求形态-->高2  <  高2
        if  self.short_term_list_all[self.short_term_last_two_high_all_index[0]] == 2 and \
            self.short_term_list_all[self.short_term_last_two_high_all_index[1]] == 2  :
            # 其次：高点是上升的形态 后面的高点高于前面的高点 并且 最后面的高2的那个k日线全部走完（确定一个高、低点需要3个K线）
            if  (self.all_bar[self.short_term_last_two_high_all_index[0]].high  < self.all_bar[self.short_term_last_two_high_all_index[1]].high)  and \
                (len(self.all_bar)                                          >= self.short_term_last_two_high_all_index[1]+2) :
                # 然后：高2后面的某个交易日的close高于第二个高点的最高值一定百分比
                if bar.close > self.all_bar[self.short_term_last_two_high_all_index[1]].high*(1+self.A_MIN_UP_ALL/100.0):
                    # 最后： 如果指标没有被使用过
                    if  cmp(self.short_term_open_last_two_all_index , self.short_term_last_two_high_all_index) != 0:
                        BK_Condition_2 = True                             
        #--------------------------2 、做多卖平条件-----------------------------------------------  
        self.SP_style   = 0000             
        #条件1：保证金亏损幅度         
        SP_Condition_1  = False            
        if self.pos == 1:
            A_PRICE_SP              = self.BKPRICE*self.A_WEIGHT*self.A_BZJ      #{最近买开价位总费用} 
            SP_Condition_1          = (self.BKPRICE-bar.close)*self.A_WEIGHT > (A_PRICE_SP*self.A_LOSS_SP_ALL)    
            if SP_Condition_1:
                self.SP_style     = self.SP_style | 8 #1000   
        
        #条件2：最佳浮盈  
        SP_Condition_2  = False   
        if self.pos == 1:
            SP_Condition_2          = (bar.close-self.BKPRICE)*self.A_WEIGHT >= self.A_FLAOT_PROFIT_ALL  
            if SP_Condition_2:
                self.SP_style     = self.SP_style | 4 #1000   
            
        #条件3：closed低于用于开仓的第二个低点日的low值  
        SP_Condition_3  = False   
        if self.pos == 1 and self.BK_style==21:
            SP_Condition_3          = bar.close < self.all_bar[self.short_term_open_last_two_all_index[1]].low   
            if SP_Condition_3:
                self.SP_style     = self.SP_style | 2 #0010   
            
        #条件4：closed低于用于开仓的第一个高点日的high值  
        SP_Condition_4  = False   
        if self.pos == 1 and self.BK_style==22:
            SP_Condition_4          = bar.close < self.all_bar[self.short_term_open_last_two_all_index[0]].high   
            if SP_Condition_4:
                self.SP_style     = self.SP_style | 1 #0001                       
            
        #-------------------------3 、 做多执行交易---------------------------------------------------        
        if BK_Condition_1 and self.pos == 0 and self.BK_style==EMPTY_INT_WH and self.LongOrShort==True:    
            self.buy(bar.close, 1)
            self.short_term_open_last_two_all_index  = []
            self.short_term_open_last_two_all_index  = copy.deepcopy(self.short_term_last_two_low_all_index)
            self.BK_style                          = 21
            self.tradeday                          = 1
        elif BK_Condition_2 and self.pos == 0  and self.BK_style==EMPTY_INT_WH and self.LongOrShort==True: 
            self.buy(bar.close, 1)
            self.short_term_open_last_two_all_index  = []
            self.short_term_open_last_two_all_index  = copy.deepcopy(self.short_term_last_two_high_all_index)
            self.BK_style                          = 22
            self.tradeday                          = 1
        if (SP_Condition_1 or SP_Condition_2 or SP_Condition_3) and self.pos == 1 and self.BK_style==21:
            self.sell(bar.close, 1)     
            self.BK_style                          = EMPTY_INT_WH  
        elif (SP_Condition_1 or SP_Condition_2 or SP_Condition_4) and self.pos == 1 and self.BK_style==22:
            self.sell(bar.close, 1)     
            self.BK_style                          = EMPTY_INT_WH     
        #################################################################################################
        #------------------------ 4 、 做空卖开条件-----------------------------------------------        
        # 条件1：短期市场结构是否满足要求 满足为TRUE 不满足为FALSE
        SK_Condition_1 = False 
        # 首先：满足做空的基本要求形态-->高2 > 高2
        if  self.short_term_list_all[self.short_term_last_two_high_all_index[0]] == 2 and \
            self.short_term_list_all[self.short_term_last_two_high_all_index[1]] == 2  :
            # 其次：高点是下降的形态 后面的高点点低于前面的高点 最后面的高2全部走完（确定一个高、低点需要3个K线）
            if  (self.all_bar[self.short_term_last_two_high_all_index[0]].high  > self.all_bar[self.short_term_last_two_high_all_index[1]].high)  and \
                (len(self.all_bar)                                          == self.short_term_last_two_high_all_index[1]+2) :    
                # 最后： 如果指标没有被使用过
                if  cmp(self.short_term_open_last_two_all_index , self.short_term_last_two_high_all_index) != 0:
                    SK_Condition_1 = True     
                    
        # 条件2：短期市场结构是否满足要求 满足为TRUE 不满足为FALSE
        SK_Condition_2 = False 
        # 首先：满足做空的基本要求形态-->低1 >  低1
        if  self.short_term_list_all[self.short_term_last_two_low_all_index[0]] == 1 and \
            self.short_term_list_all[self.short_term_last_two_low_all_index[1]] == 1  :
            # 其次：低点是下降的形态 后面的低点低于前面的低点 最后面的低1全部走完（确定一个高、低点需要3个K线）
            if  (self.all_bar[self.short_term_last_two_low_all_index[0]].low > self.all_bar[self.short_term_last_two_low_all_index[1]].low)  and \
                (len(self.all_bar)                                          >= self.short_term_last_two_low_all_index[1]+2) :
                # 然后：当日的close低于第二个低点的最低值
                if bar.close < self.all_bar[self.short_term_last_two_low_all_index[1]].low*(1-self.A_MIN_DOWN_ALL/100.0):
                    # 最后： 如果指标没有被使用过
                    if  cmp(self.short_term_open_last_two_all_index , self.short_term_last_two_low_all_index) != 0:
                        SK_Condition_2 = True                            
        #--------------------------5 、做空买平条件-----------------------------------------------          
        #条件1：保证金亏损幅度         
        BP_Condition_1  = False            
        if self.pos == -1:
            A_PRICE_SP              = self.SKPRICE*self.A_WEIGHT*self.A_BZJ      #{最近买开价位总费用} 
            BP_Condition_1          = (bar.close-self.SKPRICE)*self.A_WEIGHT > (A_PRICE_SP*self.SK_A_LOSS_SP_ALL)  
        
        #条件2：最佳浮盈  
        BP_Condition_2  = False   
        if self.pos == -1:
            BP_Condition_2          = (self.SKPRICE-bar.close)*self.A_WEIGHT >= self.SK_A_FLAOT_PROFIT_ALL 
            
        #条件3：closed高于用于开仓的第二个高点日的high值  
        BP_Condition_3  = False   
        if self.pos == -1 and self.SK_style==21:
            BP_Condition_3          = bar.close > self.all_bar[self.short_term_open_last_two_all_index[1]].high   
            
        #条件4：closed高于用于开仓的第一个低点日的low值  
        BP_Condition_4  = False   
        if self.pos == -1 and self.SK_style==22:
            BP_Condition_4          = bar.close > self.all_bar[self.short_term_open_last_two_all_index[0]].low          
  
        #-------------------------6 、 做空执行交易-----------------------------------------------        
        if SK_Condition_1 and self.pos == 0 and self.SK_style==EMPTY_INT_WH and self.LongOrShort==False:               
            self.short(bar.close, 1)
            self.short_term_open_last_two_all_index  = []
            self.short_term_open_last_two_all_index  = copy.deepcopy(self.short_term_last_two_high_all_index)
            self.SK_style                          = 21            
        elif SK_Condition_2 and self.pos == 0  and self.SK_style==EMPTY_INT_WH and self.LongOrShort==False: 
            self.short(bar.close, 1)
            self.short_term_open_last_two_all_index  = []
            self.short_term_open_last_two_all_index  = copy.deepcopy(self.short_term_last_two_low_all_index)
            self.SK_style                          = 22
        if (BP_Condition_1 or BP_Condition_2 or BP_Condition_3) and self.pos == -1 and self.SK_style==21:
            self.cover(bar.close, 1)     
            self.SK_style                          = EMPTY_INT_WH  
        elif (BP_Condition_1 or BP_Condition_2 or BP_Condition_4) and self.pos == -1 and self.SK_style==22:
            self.cover(bar.close, 1)     
            self.SK_style                          = EMPTY_INT_WH                                     
        self.putEvent()
 
    
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
            if self.pos > 0:
                self.sell(bar.close, self.pos)
                self.putEvent()              
            if self.pos < 0:
                self.cover(bar.close, abs(self.pos)) 
                self.putEvent()             
            '''
            return
        
        self.short_term_all_index(bar,am)              
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
            print 'STRB BUY :',',',trade.tradeTime,',',trade.price ,',',',',self.BK_style 
            self.BKPRICE = trade.price
        if trade.direction == DIRECTION_SHORT and trade.offset == OFFSET_CLOSE:    #做多卖平
            print 'STRB SELL:',',',trade.tradeTime,',',trade.price,',',(trade.price- self.BKPRICE)*self.A_WEIGHT,',' ,'{:08b}'.format(self.SP_style)[-4:],',',self.tradeday
            self.BKPRICE = EMPTY_FLOAT_WH   
            self.tradeday=0 
            
        if trade.direction == DIRECTION_SHORT and trade.offset == OFFSET_OPEN  :   #做空卖开
            print 'STRB SELL  :',',',trade.tradeTime,',',trade.price ,',',self.SK_style             
            self.SKPRICE = trade.price
        if trade.direction == DIRECTION_LONG and trade.offset == OFFSET_CLOSE:     #做空买平
            print 'STRB COVER:',',',trade.tradeTime,',',trade.price,',',(self.SKPRICE- trade.price)*self.A_WEIGHT 
            self.SKPRICE = EMPTY_FLOAT_WH     
    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass    
    #----------------------------------------------------------------------   
    def load_All_Index_Setting(self):
        """把相关指标从json文件读取"""
        try:
            with open(u'F:\\uiKLine\\json\\uiKLine_all_index.json') as f:
                index_settings= json.load(f)
                f.close()      
        except:
            print ("读取失败，检查F:\\uiKLine\\json\\uiKLine_all_index.json路径是否正确")
            return {}
        return index_settings    