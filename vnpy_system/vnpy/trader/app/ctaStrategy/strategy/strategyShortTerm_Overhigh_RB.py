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

加仓有两种量化策略
第1种
在原来策略的基础上进行构建，只优化浮盈加仓点
优点:
缺点：

第二种
作为新的量化策略，优化全部的参数
优点：
缺点：
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
########################################################################
class ShortTermStrategy_Overhigh(CtaTemplate):
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
    strategyStartpos=1890      
    strategyEndpos=  2289
    # 策略 做多策略还是做空策略，BOOL值  True=Long False=Short
    # 注意：多参数优化时直接修改该值
    # 直接回测时候也需要直接修改该值
    LongOrShort     =True                
    
    all_bar=[]                           # 存放所以bar  
    short_term_list=[]                   # 存放UIkline生成好的短期指标结果
    short_term_last_three_index=[]       # 存放最近3个短期指标index 下标 
    short_term_open_last_three_index=[]  # 存放上一次开仓的最近3个短期指标index 下标 
    can_overhigh = True                  # 能否加仓，控制只能加仓一次，不允许多次。
    
    ###--20090327优化参数(strategyStartpos = 0000 20090327)开多-----#####
    ###E_LONG        = 14                 # 做多趋势均线天数 # 
    ###A_LOSS_SP     = 0.26               # 保证金亏损幅度   #
    ###A_FLAOT_PROFIT= 3600               # 最佳浮盈         #           
    ###---------------------------------------------------#####
   
    ####--20170103优化参数(strategStartpos = 1890 20170103)开多------#####            
    E_LONG        = 15                   # 做多趋势均线天数     #
    A_LOSS_SP_1   = 0.19                  # 当只有1手时候保证金亏损幅度   #
    A_LOSS_SP_2   = 0.01                  # 当只有2手时候保证金亏损幅度   #
    A_FLAOT_PROFIT_1= 2550               # 最佳浮盈             # 
    A_FLAOT_PROFIT_2= 1600               # 最佳浮盈             # 
    Float_Profit_Over_High = 500        # 浮盈加仓点           #
    ###-----------------------------------------------------#####         
    
    
    ###--20090327优化参数(strategyStartpos = 0000 20090327)开空-----#####
    ###SK_E_LONG        = 6                 # 做多趋势均线天数 # 
    ###SK_A_LOSS_SP     = 0.15               # 保证金亏损幅度  #
    ###SK_A_FLAOT_PROFIT= 3250               # 最佳浮盈        #           
    ###---------------------------------------------------#####
    
    ###--20090327优化参数(strategyStartpos = 1890 20170103)开空-----#####
    SK_E_LONG        = 5                  # 做多趋势均线天数 # 
    SK_A_LOSS_SP     = 0.35               # 保证金亏损幅度   #
    SK_A_FLAOT_PROFIT= 3000               # 最佳浮盈         #           
    ###---------------------------------------------------#####
    
    BKPRICE = [EMPTY_FLOAT_WH,EMPTY_FLOAT_WH]
    SKPRICE = EMPTY_FLOAT_WH
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'E_LONG',
                 'A_LOSS_SP_1',
                 'A_LOSS_SP_2',
                 'A_FLAOT_PROFIT_1',
                 'A_FLAOT_PROFIT_2',
                 'SK_A_LOSS_SP',
                 'SK_A_FLAOT_PROFIT',
                 'SK_E_LONG',
                 'LongOrShort',
                 'Float_Profit_Over_High'
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
        super(ShortTermStrategy_Overhigh, self).__init__(ctaEngine, setting)
        
        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）
        self.short_term_list                 =[] 
        self.short_term_last_three_index     =[]
        self.short_term_open_last_three_index=[]
        self.all_bar                         =[]   
        self.BKPRICE                         =[EMPTY_FLOAT_WH,EMPTY_FLOAT_WH]
        self.SKPRICE                         =EMPTY_FLOAT_WH
        self.initDays                        =self.E_LONG if self.LongOrShort==True else self.SK_E_LONG
        self.strategyStartpos                =1890     
        self.strategyEndpos                  =2289 
        self.can_overhigh                    =True
        
        self.bg = BarGenerator(self.onBar)
        self.am = ArrayManager(self.initDays)  
        
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""        
        self.writeCtaLog(u'短期市场结构策略初始化')
        
        index_settings = self.load_Index_Setting()
        if len(index_settings)==0 :
            print("检查F:\uiKLine\json\uiKLine_index.json路径是否正确")
            return
        for setting in index_settings:
            self.short_term_list = setting[u'SHORT_TERM_INDEX']     
        if len(self.short_term_list) == 0:
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
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        self.all_bar.append(bar)      
        am = self.am        
        am.updateBar(bar)
        if not am.inited:
            return  
        
        if len(self.all_bar) > self.strategyEndpos+1 :   
            if self.pos > 0:
                self.sell(bar.close, self.pos)
                self.putEvent()              
            if self.pos < 0:
                self.cover(bar.close, abs(self.pos)) 
                self.putEvent()                          
            return
        
        # 更新最近三次短期列表的值 低1 高2 低1-->做多买入 /  高2 低1 高2-->(做多卖平 or 做空卖出)
        if len(self.short_term_last_three_index) < 3 :
            if self.short_term_list[len(self.all_bar)-1] != 0 :
                self.short_term_last_three_index.append(len(self.all_bar)-1)
            self.putEvent()
            return
        else:
            if self.short_term_list[len(self.all_bar)-1] != 0 :
                del self.short_term_last_three_index[0]
                self.short_term_last_three_index.append(len(self.all_bar)-1)                          

        if len(self.all_bar) < self.strategyStartpos :
            self.putEvent()            
            return
        
        
        #------------------------- 1 、做多买开条件----------------------------------------------        
        # 条件1：短期市场结构是否满足要求 满足为TRUE 不满足为FALSE
        BK_Condition_1 = False 
        # 首先：满足做多的基本要求形态-->低1 高2 低1
        if  self.short_term_list[self.short_term_last_three_index[0]] == 1 and \
            self.short_term_list[self.short_term_last_three_index[1]] == 2 and \
            self.short_term_list[self.short_term_last_three_index[2]] == 1  :
            # 其次：低点是上升的形态 高点高于两边的低点
            if  (self.all_bar[self.short_term_last_three_index[0]].low  < self.all_bar[self.short_term_last_three_index[2]].low) and \
                (self.all_bar[self.short_term_last_three_index[1]].high > self.all_bar[self.short_term_last_three_index[2]].low) and \
                (self.all_bar[self.short_term_last_three_index[1]].high > self.all_bar[self.short_term_last_three_index[0]].low): 
                # 然后: close大于高点
                if self.all_bar[self.short_term_last_three_index[1]].high < bar.close:
                    # 接着： 如果指标没有被使用过
                    if  cmp(self.short_term_open_last_three_index , self.short_term_last_three_index) != 0:
                        # 最后： 这是第1手开仓
                        if  self.BKPRICE[0] == EMPTY_FLOAT_WH:                        
                            BK_Condition_1 = True     
                        
        # 条件2：考察趋势
        BK_Condition_2 = False   
        A_ma  = am.sma(self.E_LONG,array=True)  
        if  A_ma[-1] < bar.close and self.BKPRICE[0] == EMPTY_FLOAT_WH:
            # close大于趋势线，并且这是第1手开仓
            BK_Condition_2 = True    
        #--------------------------2 、做多加仓条件-----------------------------------------------          
        BK_OH_Condition_1 = False
        # 条件1：首先处于持多仓一手,并且没有加仓过
        if self.pos == 1 and  self.can_overhigh  and self.BKPRICE[0] != EMPTY_FLOAT_WH and self.BKPRICE[1] == EMPTY_FLOAT_WH: 
            BK_OH_Condition_1 = (bar.close - self.BKPRICE[0])*self.A_WEIGHT>self.Float_Profit_Over_High
        #--------------------------3 、做多卖平条件-----------------------------------------------          
        #条件1：保证金亏损幅度         
        SP_Condition_1_1  = False   
        SP_Condition_1_2  = False             
        if   self.pos == 1 and self.BKPRICE[0] != EMPTY_FLOAT_WH and self.BKPRICE[1] == EMPTY_FLOAT_WH: #卖平第1仓
            A_PRICE_SP              = self.BKPRICE[0]*self.A_WEIGHT*self.A_BZJ       
            SP_Condition_1_1        = (self.BKPRICE[0]-bar.close)*self.A_WEIGHT > (A_PRICE_SP*self.A_LOSS_SP_1)
        if   self.pos == 1 and self.BKPRICE[0] == EMPTY_FLOAT_WH and self.BKPRICE[1] != EMPTY_FLOAT_WH: #第1仓已平，现在卖平第2仓
            A_PRICE_SP              = self.BKPRICE[0]*self.A_WEIGHT*self.A_BZJ       
            SP_Condition_1_1        = (self.BKPRICE[0]-bar.close)*self.A_WEIGHT > (A_PRICE_SP*self.A_LOSS_SP_1)   
        elif self.pos == 2 and self.BKPRICE[0] != EMPTY_FLOAT_WH and self.BKPRICE[1] != EMPTY_FLOAT_WH:  
            A_PRICE_SP              = self.BKPRICE[0]*self.A_WEIGHT*self.A_BZJ       
            SP_Condition_1_1        = (self.BKPRICE[0]-bar.close)*self.A_WEIGHT > (A_PRICE_SP*self.A_LOSS_SP_1)   
            A_PRICE_SP              = self.BKPRICE[1]*self.A_WEIGHT*self.A_BZJ      
            SP_Condition_1_2        = (self.BKPRICE[1]-bar.close)*self.A_WEIGHT > (A_PRICE_SP*self.A_LOSS_SP_2)        
        
        #条件2：最佳浮盈  
        SP_Condition_2_1  = False   
        SP_Condition_2_2  = False  
        if self.pos == 1 and self.BKPRICE[0] != EMPTY_FLOAT_WH and self.BKPRICE[1] == EMPTY_FLOAT_WH: #卖平第1仓:
            SP_Condition_2_1        = (bar.close-self.BKPRICE[0])*self.A_WEIGHT >= self.A_FLAOT_PROFIT_1  
        if self.pos == 1 and self.BKPRICE[0] == EMPTY_FLOAT_WH and self.BKPRICE[1] != EMPTY_FLOAT_WH: #卖平第1仓，现在卖平第2仓
            SP_Condition_2_2        = (bar.close-self.BKPRICE[1])*self.A_WEIGHT >= self.A_FLAOT_PROFIT_1  
        if self.pos == 2 and self.BKPRICE[0] != EMPTY_FLOAT_WH and self.BKPRICE[1] != EMPTY_FLOAT_WH: 
            SP_Condition_2_1        = (bar.close-self.BKPRICE[0])*self.A_WEIGHT >= self.A_FLAOT_PROFIT_1  
            SP_Condition_2_2        = (bar.close-self.BKPRICE[1])*self.A_WEIGHT >= self.A_FLAOT_PROFIT_2              
        #条件3：卖空形态  
        SP_Condition_3  = False   
        if self.pos == 1 or self.pos == 2:
            # 首先：满足做空卖开的基本要求形态-->高2 低1 高2
            if  self.short_term_list[self.short_term_last_three_index[0]] == 2 and \
                self.short_term_list[self.short_term_last_three_index[1]] == 1 and \
                self.short_term_list[self.short_term_last_three_index[2]] == 2  :
                # 其次：高点是下降的形态 低点高于两边的高点
                if  (self.all_bar[self.short_term_last_three_index[0]].high > self.all_bar[self.short_term_last_three_index[2]].high) and \
                    (self.all_bar[self.short_term_last_three_index[1]].low  < self.all_bar[self.short_term_last_three_index[2]].high) and \
                    (self.all_bar[self.short_term_last_three_index[1]].low  < self.all_bar[self.short_term_last_three_index[0]].high): 
                    # 然后: close小于低点
                    if self.all_bar[self.short_term_last_three_index[1]].low > bar.close:   
                        SP_Condition_3  = True               
        #-------------------------4 、做空卖开条件-----------------------------------------------       
        # 条件1：短期市场结构是否满足要求 满足为TRUE 不满足为FALSE
        SK_Condition_1 = False 
        # 首先：满足做空的基本要求形态-->高2 低1 高2
        if  self.short_term_list[self.short_term_last_three_index[0]] == 2 and \
            self.short_term_list[self.short_term_last_three_index[1]] == 1 and \
            self.short_term_list[self.short_term_last_three_index[2]] == 2  :
            # 其次：高点是下降的形态 低点高于两边的高点
            if  (self.all_bar[self.short_term_last_three_index[0]].high > self.all_bar[self.short_term_last_three_index[2]].high) and \
                (self.all_bar[self.short_term_last_three_index[1]].low  < self.all_bar[self.short_term_last_three_index[2]].high) and \
                (self.all_bar[self.short_term_last_three_index[1]].low  < self.all_bar[self.short_term_last_three_index[0]].high): 
                # 然后: close小于低点
                if self.all_bar[self.short_term_last_three_index[1]].low > bar.close:   
                    SK_Condition_1 = True   
                        
        # 条件2：考察趋势
        SK_Condition_2 = False   
        A_ma  = am.sma(self.SK_E_LONG,array=True)  
        if  A_ma[-1] > bar.close:
            # close大于趋势线
            SK_Condition_2 = True                         
        #-------------------------5 、 做空买平条件-----------------------------------------------         
        #条件1：保证金亏损幅度         
        BP_Condition_1  = False            
        if self.pos == -1:
            A_PRICE_SP              = self.BKPRICE*self.A_WEIGHT*self.A_BZJ      #{最近买开价位总费用} 
            BP_Condition_1          = (bar.close-self.BKPRICE)*self.A_WEIGHT > (A_PRICE_SP*self.SK_A_LOSS_SP)    
        
        #条件2：最佳浮盈  
        BP_Condition_2  = False   
        if self.pos == -1:
            BP_Condition_2          = (self.BKPRICE-bar.close)*self.A_WEIGHT >= self.SK_A_FLAOT_PROFIT  
            
        #条件3：买多形态  
        BP_Condition_3  = False   
        if self.pos == -1:
            # 首先：满足做多买开的基本要求形态-->低1 高2 低1
            if  self.short_term_list[self.short_term_last_three_index[0]] == 1 and \
                self.short_term_list[self.short_term_last_three_index[1]] == 2 and \
                self.short_term_list[self.short_term_last_three_index[2]] == 1  :
                # 其次：低点是上升的形态 高点高于两边的低点
                if  (self.all_bar[self.short_term_last_three_index[0]].low  < self.all_bar[self.short_term_last_three_index[2]].low) and \
                    (self.all_bar[self.short_term_last_three_index[1]].high > self.all_bar[self.short_term_last_three_index[2]].low) and \
                    (self.all_bar[self.short_term_last_three_index[1]].high > self.all_bar[self.short_term_last_three_index[0]].low): 
                    # 然后: close大于高点
                    if self.all_bar[self.short_term_last_three_index[1]].high < bar.close:
                        BP_Condition_3 = True
            
        #-------------------------6 、 执行交易---------------------------------------------------        
        # 做多建仓
        if BK_Condition_1  and BK_Condition_2 and self.pos == 0 and self.LongOrShort==True: 
            self.buy(bar.close, 1)
            self.MAXCLOSE_AFTER_OPEN= bar.close
            self.short_term_open_last_three_index  = []
            self.short_term_open_last_three_index  = copy.deepcopy(self.short_term_last_three_index)
            self.can_overhigh  = True
            self.putEvent()
            #print(bar.date,'K')
            return
        # 做多加仓
        if BK_OH_Condition_1  and self.LongOrShort==True and self.pos == 1: 
            self.buy(bar.close, 1)
            self.can_overhigh  = False
            self.putEvent()
            #print(bar.date,'J')
            return
        # 做多平仓 
        if ((self.pos == 1) and (self.BKPRICE[0]!=EMPTY_FLOAT_WH and self.BKPRICE[1] == EMPTY_FLOAT_WH) and ((SP_Condition_1_1 or SP_Condition_2_1 or SP_Condition_3))) or \
           ((self.pos == 1) and (self.BKPRICE[0]==EMPTY_FLOAT_WH and self.BKPRICE[1] != EMPTY_FLOAT_WH) and ((SP_Condition_1_2 or SP_Condition_2_2 or SP_Condition_3))) or \
           ((self.pos == 2) and (self.BKPRICE[0]!=EMPTY_FLOAT_WH and self.BKPRICE[1] != EMPTY_FLOAT_WH) and ((SP_Condition_1_1 or SP_Condition_2_1 or SP_Condition_3))) or \
           ((self.pos == 2) and (self.BKPRICE[0]!=EMPTY_FLOAT_WH and self.BKPRICE[1] != EMPTY_FLOAT_WH) and ((SP_Condition_1_2 or SP_Condition_2_2 or SP_Condition_3)))    :
            #做多平仓 只有1手   并且                   是开仓第1手                                                              三个条件任意成立一个
            if (self.pos == 1) and (self.BKPRICE[0]!=EMPTY_FLOAT_WH and self.BKPRICE[1] == EMPTY_FLOAT_WH) and ((SP_Condition_1_1 or SP_Condition_2_1 or SP_Condition_3)):
                self.BKPRICE[0]=EMPTY_FLOAT_WH
                self.sell(bar.close, 1)  
                #print(bar.date,'PK')
            #做多平仓 只有1手   并且                   是加仓的1手                                                              三个条件任意成立一个
            if (self.pos == 1) and (self.BKPRICE[0]==EMPTY_FLOAT_WH and self.BKPRICE[1] != EMPTY_FLOAT_WH) and ((SP_Condition_1_2 or SP_Condition_2_2 or SP_Condition_3)):
                self.BKPRICE[1]=EMPTY_FLOAT_WH
                self.sell(bar.close, 1)  
                #print(bar.date,'PJ')
            #做多平仓 有2手     并且                    确认是2手                                                             第一手 三个条件任意成立一个
            if (self.pos == 2) and (self.BKPRICE[0]!=EMPTY_FLOAT_WH and self.BKPRICE[1] != EMPTY_FLOAT_WH) and ((SP_Condition_1_1 or SP_Condition_2_1 or SP_Condition_3)):
                self.BKPRICE[0]=EMPTY_FLOAT_WH
                self.sell(bar.close, 1)  
                #print(bar.date,'PK')
            #做多平仓 有2手     并且                    确认是2手                                                              第二手 三个条件任意成立一个
            if (self.pos == 2) and (self.BKPRICE[0]!=EMPTY_FLOAT_WH and self.BKPRICE[1] != EMPTY_FLOAT_WH) and ((SP_Condition_1_2 or SP_Condition_2_2 or SP_Condition_3)):
                self.BKPRICE[1]=EMPTY_FLOAT_WH
                self.sell(bar.close, 1)  
                #print(bar.date,'PJ')
            self.putEvent()
            return    
        
        
        
        if SK_Condition_1  and SK_Condition_2 and self.pos == 0 and self.LongOrShort==False: 
            self.short(bar.close, 1)
            self.short_term_open_last_three_index  = []
            self.short_term_open_last_three_index  = copy.deepcopy(self.short_term_last_three_index)
        if (BP_Condition_1 or BP_Condition_2 or BP_Condition_3) and self.pos == -1:
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
        if trade.direction == DIRECTION_LONG and trade.offset == OFFSET_OPEN  :    #做多买开
            self.BKPRICE.append(trade.price)
            if   self.pos == 1 and self.BKPRICE[0]==EMPTY_FLOAT_WH and self.BKPRICE[1]==EMPTY_FLOAT_WH : #开仓
                self.BKPRICE[0]=trade.price
            elif   self.pos == 1 and self.BKPRICE[0]!=EMPTY_FLOAT_WH and self.BKPRICE[1]==EMPTY_FLOAT_WH : 
                print(u"策略错误")
            elif   self.pos == 1 and self.BKPRICE[0]==EMPTY_FLOAT_WH and self.BKPRICE[1]!=EMPTY_FLOAT_WH : 
                print(u"策略错误")
            elif self.pos == 1 and self.BKPRICE[0]!=EMPTY_FLOAT_WH and self.BKPRICE[1]!=EMPTY_FLOAT_WH : 
                print(u"策略错误")
            elif   self.pos == 2 and self.BKPRICE[0]==EMPTY_FLOAT_WH and self.BKPRICE[1]==EMPTY_FLOAT_WH : 
                print(u"策略错误")
            elif   self.pos == 2 and self.BKPRICE[0]!=EMPTY_FLOAT_WH and self.BKPRICE[1]==EMPTY_FLOAT_WH : 
                self.BKPRICE[1]=trade.price
            elif   self.pos == 2 and self.BKPRICE[0]==EMPTY_FLOAT_WH and self.BKPRICE[1]!=EMPTY_FLOAT_WH : 
                self.BKPRICE[0]=trade.price
            elif self.pos == 2 and self.BKPRICE[0]!=EMPTY_FLOAT_WH and self.BKPRICE[1]!=EMPTY_FLOAT_WH : 
                print(u"策略错误")
            
        if trade.direction == DIRECTION_SHORT and trade.offset == OFFSET_CLOSE:    #做多卖平
            pass
            
        if trade.direction == DIRECTION_SHORT and trade.offset == OFFSET_OPEN  :   #做空卖开
            self.BKPRICE = trade.price
        if trade.direction == DIRECTION_LONG and trade.offset == OFFSET_CLOSE:     #做空买平
            self.BKPRICE = EMPTY_FLOAT_WH     
    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass    
    #----------------------------------------------------------------------
    def load_Index_Setting(self):
        """把相关指标从json文件读取"""
        try:
            with open(u'F:\\uiKLine\\json\\uiKLine_index.json') as f:
                index_settings= json.load(f)
                f.close()      
        except:
            print ("读取失败，检查F:\\uiKLine\\json\\uiKLine_index.json路径是否正确")
            return {}
        return index_settings
    