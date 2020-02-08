# encoding: UTF-8

"""
这里的策略是根据《短线交易秘诀（原书第2版）》第四章动能穿透的内容编写而成
1 、测量波幅的方式：
    今日的最高价和收盘价之间的差值。
    前一日的最高价和收盘价之间的差值。
    过去X天的平均范围。
    
2、进场方式
    当天的开盘价加上波幅的比例作为买入点， 当天的开盘价减去波幅的比例作为卖出点（1）
    将第二天的开盘价加上波幅的比例作为买入点， 第二天的开盘价减去波幅的比例作为卖出点（2）
    根据前一天波幅的某个百分比加上前一天的最高价作为买人信号，或者前一天最低点减去波幅的百分比处卖出。（3）
    今日收盘价加上今日波幅的某个比例，作为第二日买入的价格点。（4）
    
3、出场方式
    保护性止损
    入场点位减去前日价格波幅的50%作为我们的保护性止损点
    在第一个可以获利的开盘价获利离场。
    最佳浮盈
    
4、周交易日

5、更多的思考
    在行情看涨的日子里买入时用比较小的波动率放大参数，在行情看不太清楚时使用50%的波动率扩大系数来形成离市价点更远的入场点呢？
    那么我们对离场点又能做些什么呢？在上涨/下跌更明确的日子里，持仓时间更长能否带来更好的结果呢？”
    
6、深入研究
   把一个波动率系数分别加到：（1）今天的收盘价上；（2）昨天的开盘价上；（3）今天的最低价上；（4）今天的中间价上（最高价与最低价的平均值）来观察。
   测试经历了所有的低收日，即今日收盘比开盘价低，也比前日收盘价低的情况；也经历了所有的高收日，情形刚好与低收日的相反，今日的收盘价比开盘价高，也
   高于前日的收盘价。以及作为波动率系数在系统中表现最好的三天的平均真值范围的测试结果。这些数值是经过高度优化的
   低收日且收盘价低于开盘价时，在次日开盘价上涨达到过去三天平均真实波动的60%时买入，
   在今日收盘价上涨达到三天（表现最好的三天）平均真实波动的60%时买入
   
7、趋势的定义
   如何机械性地定义一个上涨趋势呢？我最喜欢的点子就是看今天的20日收盘价移动均线是不是比昨天的值高，
   
8、趋势结合的思考
   趋势系数滤掉了很多盈利的交易机会，所以看上去似乎形态是高收日的情况下，我们就希望可以不那么关注趋势。
   而对低收日，我们当然想更注意趋势变化。简而言之，低收日产生的上涨机会更好。

"""

from __future__ import division

from vnpy.trader.vtConstant import EMPTY_STRING, EMPTY_FLOAT,DIRECTION_LONG,OFFSET_OPEN,DIRECTION_SHORT,OFFSET_CLOSE
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator,
                                                     ArrayManager)
from datetime import datetime ,timedelta
import time
import Queue
import numpy as np

EMPTY_INT_WH = -1
EMPTY_FLOAT_WH = -1.0
########################################################################
class strategy_Volatility_RB_V1(CtaTemplate):
    """双指数均线策略Demo"""
    className = 'strategy_Volatility_RB_V1'
    author = u'任建军'
    
    # 策略参数Trend_DAYS                   
    A_WEIGHT      = 10       #{每手吨数                }                 
    A_BZJ         = 0.14     #{保证金参数              }
    #--------------以下是可以优化的策略----------------------------    
    #方案二：不同时间段用不同参数体系。
    '''
    # self.TEMP == 1  2011年01月	---  2012年12月
    # 做多的优化参数优化期全部数据星期[0,1,2,3,4]
    BK_A_LOSS_SP     = 600      #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 1.0      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.1      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{买开N日中最高价-买开N日中的最低价 买开N=1代表当日} 
    SP_BEFORE_DAY    = 2        #{卖平M日中最高价-卖平M日中的最低价 卖平M=1代表当日} 
    BK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  } 
    # 做空的优化参数优化期全部数据星期[0,1,2,3,4]
    SK_A_LOSS_SP     = 600      #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.7      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 0.4      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 4        #{卖开N日中最高价-卖开N日中的最低价 卖开N=1代表当日} 
    BP_BEFORE_DAY    = 2        #{买平M日中最高价-买平M日中的最低价 买平M=1代表当日} 
    SK_A_FLAOT_PROFIT_ALL=800   #{最佳浮盈                  }       
    # 多空判断
    Trend_DAYS       = 130         #{做多：当前CLOSE大于Trend_DAYS天前的CLOSE ; 做空：当前CLOSE小于Trend_DAYS天前的CLOSE }
    ma               = 31
    # 多参数系数
    BK_A_LOSS_SP_RATIO = 1      #{当CLOSE<MA均线的时候，缩小}xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    BK_Volatility_RATIO= 1      #{当CLOSE>MA均线的时候, 缩小}xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    SP_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    BK_A_FLAOT_PROFIT_ALL_RATIO= 0.85#{当CLOSE>MA均线的时候, 放大}
    # 空参数系数
    SK_A_LOSS_SP_RATIO = 1      #{当CLOSE>MA均线的时候，缩小}xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    SK_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  
    BP_Volatility_RATIO= 1      #{当CLOSE>MA均线的时候, 缩小}
    SK_A_FLAOT_PROFIT_ALL_RATIO= 1.9#{当CLOSE<MA均线的时候, 放大}
    '''
    
    
    '''
    #self.TEMP == 2 2011年07月	2013年06月
    # 做多的优化参数优化期全部数据 星期[0,1,2,3,4]
    BK_A_LOSS_SP     = 800     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 1.0      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.6      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{买开N日中最高价-买开N日中的最低价 买开N=1代表当日} 
    SP_BEFORE_DAY    = 2        #{卖平M日中最高价-卖平M日中的最低价 卖平M=1代表当日} 
    BK_A_FLAOT_PROFIT_ALL=800   #{最佳浮盈                  } 
    # 做空的优化参数优化期最近数据 星期[0,1,2,3,4]
    SK_A_LOSS_SP     = 1000     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.7      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 0.2      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 4        #{卖开N日中最高价-卖开N日中的最低价 卖开N=1代表当日} 
    BP_BEFORE_DAY    = 3        #{买平M日中最高价-买平M日中的最低价 买平M=1代表当日} 
    SK_A_FLAOT_PROFIT_ALL=900   #{最佳浮盈                  }       
    # 多空判断
    Trend_DAYS       = 175      #{做多：当前CLOSE大于Trend_DAYS天前的CLOSE ; 做空：当前CLOSE小于Trend_DAYS天前的CLOSE }
    ma               = 23
    # 多参数系数
    BK_A_LOSS_SP_RATIO = 1      #{当CLOSE<MA均线的时候，缩小}
    BK_Volatility_RATIO= 1      #{当CLOSE>MA均线的时候, 缩小}  
    SP_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}
    BK_A_FLAOT_PROFIT_ALL_RATIO= 0.85#{当CLOSE>MA均线的时候, 放大}
    # 空参数系数
    SK_A_LOSS_SP_RATIO = 1      #{当CLOSE>MA均线的时候，缩小}
    SK_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}  
    BP_Volatility_RATIO= 0.45      #{当CLOSE>MA均线的时候, 缩小}
    SK_A_FLAOT_PROFIT_ALL_RATIO= 1.9#{当CLOSE<MA均线的时候, 放大}
    '''
    
    '''
    #self.TEMP == 3 2012年01月	2013年12月
    # 做多的优化参数优化期全部数据 星期[0,1,2,3]
    BK_A_LOSS_SP     = 1400     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.7      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.9      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{买开N日中最高价-买开N日中的最低价 买开N=1代表当日} 
    SP_BEFORE_DAY    = 1        #{卖平M日中最高价-卖平M日中的最低价 卖平M=1代表当日} 
    BK_A_FLAOT_PROFIT_ALL=600   #{最佳浮盈                  } 
    # 做空的优化参数优化期最近数据 星期[1,2,3,4]
    SK_A_LOSS_SP     = 900     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.7      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 0.3      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 4        #{卖开N日中最高价-卖开N日中的最低价 卖开N=1代表当日} 
    BP_BEFORE_DAY    = 3        #{买平M日中最高价-买平M日中的最低价 买平M=1代表当日} 
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }       
    # 多空判断
    Trend_DAYS       = 380         #{做多：当前CLOSE大于Trend_DAYS天前的CLOSE ; 做空：当前CLOSE小于Trend_DAYS天前的CLOSE }
    ma               = 16
    # 多参数系数
    BK_A_LOSS_SP_RATIO = 1      #{当CLOSE<MA均线的时候，缩小}
    BK_Volatility_RATIO= 1      #{当CLOSE>MA均线的时候, 缩小}  
    SP_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}
    BK_A_FLAOT_PROFIT_ALL_RATIO= 0.85#{当CLOSE>MA均线的时候, 放大}
    # 空参数系数
    SK_A_LOSS_SP_RATIO = 1      #{当CLOSE>MA均线的时候，缩小}
    SK_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}  
    BP_Volatility_RATIO= 0.45      #{当CLOSE>MA均线的时候, 缩小}
    SK_A_FLAOT_PROFIT_ALL_RATIO= 1.9#{当CLOSE<MA均线的时候, 放大}
    '''
    
    
    '''
    # self.TEMP == 4 2012年07月	2014年06月
    # 做多的优化参数优化期全部数据 星期[0,1,2,3]
    BK_A_LOSS_SP     = 1400     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.7      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.9      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{买开N日中最高价-买开N日中的最低价 买开N=1代表当日} 
    SP_BEFORE_DAY    = 1        #{卖平M日中最高价-卖平M日中的最低价 卖平M=1代表当日} 
    BK_A_FLAOT_PROFIT_ALL=600   #{最佳浮盈                  } 
    # 做空的优化参数优化期最近数据 星期[1,2,3,4]
    SK_A_LOSS_SP     = 900     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.8      #{卖开的开盘价波幅   用于卖开}  ###################
    BP_Volatility    = 0.4      #{买平的成交价波幅   用于买平}  ###################
    SK_BEFORE_DAY    = 4        #{卖开N日中最高价-卖开N日中的最低价 卖开N=1代表当日} 
    BP_BEFORE_DAY    = 3        #{买平M日中最高价-买平M日中的最低价 买平M=1代表当日} 
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }       
    # 多空判断
    Trend_DAYS       = 320      #{做多：当前CLOSE大于Trend_DAYS天前的CLOSE ; 做空：当前CLOSE小于Trend_DAYS天前的CLOSE } ######################
    ma               = 15       # #############################
    # 多参数系数
    BK_A_LOSS_SP_RATIO = 1      #{当CLOSE<MA均线的时候，缩小}
    BK_Volatility_RATIO= 1      #{当CLOSE>MA均线的时候, 缩小}  
    SP_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}
    BK_A_FLAOT_PROFIT_ALL_RATIO= 0.85#{当CLOSE>MA均线的时候, 放大}
    # 空参数系数
    SK_A_LOSS_SP_RATIO = 1      #{当CLOSE>MA均线的时候，缩小}
    SK_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}  
    BP_Volatility_RATIO= 0.45      #{当CLOSE>MA均线的时候, 缩小}
    SK_A_FLAOT_PROFIT_ALL_RATIO= 1.9#{当CLOSE<MA均线的时候, 放大}
    '''
    
    '''
    # self.TEMP == 5 2013年01月	2014年12月
    # 做多的优化参数优化期全部数据 星期[0,1,2,3]
    BK_A_LOSS_SP     = 1400     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.7      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.9      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{买开N日中最高价-买开N日中的最低价 买开N=1代表当日} 
    SP_BEFORE_DAY    = 1        #{卖平M日中最高价-卖平M日中的最低价 卖平M=1代表当日} 
    BK_A_FLAOT_PROFIT_ALL=600   #{最佳浮盈                  } 
    # 做空的优化参数优化期最近数据 星期[1,2,3,4]
    SK_A_LOSS_SP     = 900     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.5      #{卖开的开盘价波幅   用于卖开}  ###################
    BP_Volatility    = 1.1      #{买平的成交价波幅   用于买平}  ###################
    SK_BEFORE_DAY    = 4        #{卖开N日中最高价-卖开N日中的最低价 卖开N=1代表当日} 
    BP_BEFORE_DAY    = 3        #{买平M日中最高价-买平M日中的最低价 买平M=1代表当日} 
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }       
    # 多空判断
    Trend_DAYS       = 320      #{做多：当前CLOSE大于Trend_DAYS天前的CLOSE ; 做空：当前CLOSE小于Trend_DAYS天前的CLOSE } ######################
    ma               = 15       # #############################
    # 多参数系数
    BK_A_LOSS_SP_RATIO = 1      #{当CLOSE<MA均线的时候，缩小}
    BK_Volatility_RATIO= 1      #{当CLOSE>MA均线的时候, 缩小}  
    SP_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}
    BK_A_FLAOT_PROFIT_ALL_RATIO= 0.85#{当CLOSE>MA均线的时候, 放大}
    # 空参数系数
    SK_A_LOSS_SP_RATIO = 1      #{当CLOSE>MA均线的时候，缩小}
    SK_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}  
    BP_Volatility_RATIO= 0.45      #{当CLOSE>MA均线的时候, 缩小}
    SK_A_FLAOT_PROFIT_ALL_RATIO= 1.9#{当CLOSE<MA均线的时候, 放大}    
    '''
    
    '''
    # self.TEMP == 6 2013年07月	2015年06月
    # 做多的优化参数优化期全部数据 星期[0,1,2,3]
    BK_A_LOSS_SP     = 1400     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.7      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.9      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{买开N日中最高价-买开N日中的最低价 买开N=1代表当日} 
    SP_BEFORE_DAY    = 1        #{卖平M日中最高价-卖平M日中的最低价 卖平M=1代表当日} 
    BK_A_FLAOT_PROFIT_ALL=600   #{最佳浮盈                  } 
    # 做空的优化参数优化期最近数据 星期[1,2,3,4]
    SK_A_LOSS_SP     = 900     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.6      #{卖开的开盘价波幅   用于卖开}###########################
    BP_Volatility    = 0.5      #{买平的成交价波幅   用于买平}###########################  
    SK_BEFORE_DAY    = 4        #{卖开N日中最高价-卖开N日中的最低价 卖开N=1代表当日} 
    BP_BEFORE_DAY    = 3        #{买平M日中最高价-买平M日中的最低价 买平M=1代表当日} 
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }       
    # 多空判断
    Trend_DAYS       = 320         #{做多：当前CLOSE大于Trend_DAYS天前的CLOSE ; 做空：当前CLOSE小于Trend_DAYS天前的CLOSE }
    ma               = 16
    # 多参数系数
    BK_A_LOSS_SP_RATIO = 1      #{当CLOSE<MA均线的时候，缩小}
    BK_Volatility_RATIO= 1      #{当CLOSE>MA均线的时候, 缩小}  
    SP_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}
    BK_A_FLAOT_PROFIT_ALL_RATIO= 0.85#{当CLOSE>MA均线的时候, 放大}
    # 空参数系数
    SK_A_LOSS_SP_RATIO = 1      #{当CLOSE>MA均线的时候，缩小}
    SK_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}  
    BP_Volatility_RATIO= 0.45      #{当CLOSE>MA均线的时候, 缩小}
    SK_A_FLAOT_PROFIT_ALL_RATIO= 1.9#{当CLOSE<MA均线的时候, 放大}
    '''
    
    '''
    # self.TEMP == 7 2014年01月	2015年12月
    # 做多的优化参数优化期全部数据 星期[0,1,2,3]
    BK_A_LOSS_SP     = 1400     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.7      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.9      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{买开N日中最高价-买开N日中的最低价 买开N=1代表当日} 
    SP_BEFORE_DAY    = 1        #{卖平M日中最高价-卖平M日中的最低价 卖平M=1代表当日} 
    BK_A_FLAOT_PROFIT_ALL=600   #{最佳浮盈                  } 
    # 做空的优化参数优化期最近数据 星期[1,2,3,4]
    SK_A_LOSS_SP     = 900     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.3      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 0.9      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 1        #{卖开N日中最高价-卖开N日中的最低价 卖开N=1代表当日} ###########4
    BP_BEFORE_DAY    = 4        #{买平M日中最高价-买平M日中的最低价 买平M=1代表当日} ###########3
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }       
    # 多空判断
    Trend_DAYS       = 380         #{做多：当前CLOSE大于Trend_DAYS天前的CLOSE ; 做空：当前CLOSE小于Trend_DAYS天前的CLOSE }
    ma               = 16
    # 多参数系数
    BK_A_LOSS_SP_RATIO = 1      #{当CLOSE<MA均线的时候，缩小}
    BK_Volatility_RATIO= 1      #{当CLOSE>MA均线的时候, 缩小}  
    SP_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}
    BK_A_FLAOT_PROFIT_ALL_RATIO= 0.85#{当CLOSE>MA均线的时候, 放大}
    # 空参数系数
    SK_A_LOSS_SP_RATIO = 1      #{当CLOSE>MA均线的时候，缩小}
    SK_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}  ##################
    BP_Volatility_RATIO= 0.45      #{当CLOSE>MA均线的时候, 缩小}    ##################
    SK_A_FLAOT_PROFIT_ALL_RATIO= 1.9#{当CLOSE<MA均线的时候, 放大}
    '''
    
    '''
    # self.TEMP == 8 2014年07月	2016年06月
    # 做多的优化参数优化期全部数据 星期[0,1,2,3]
    BK_A_LOSS_SP     = 1400     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.7      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.9      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{买开N日中最高价-买开N日中的最低价 买开N=1代表当日} 
    SP_BEFORE_DAY    = 1        #{卖平M日中最高价-卖平M日中的最低价 卖平M=1代表当日} 
    BK_A_FLAOT_PROFIT_ALL=600   #{最佳浮盈                  } 
    # 做空的优化参数优化期最近数据 星期[1,2,3,4]
    SK_A_LOSS_SP     = 900     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.9      #{卖开的开盘价波幅   用于卖开} ######################0.3
    BP_Volatility    = 0.5      #{买平的成交价波幅   用于买平} ######################0.9
    SK_BEFORE_DAY    = 4        #{卖开N日中最高价-卖开N日中的最低价 卖开N=1代表当日} 
    BP_BEFORE_DAY    = 3        #{买平M日中最高价-买平M日中的最低价 买平M=1代表当日} 
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }       
    # 多空判断
    Trend_DAYS       = 380         #{做多：当前CLOSE大于Trend_DAYS天前的CLOSE ; 做空：当前CLOSE小于Trend_DAYS天前的CLOSE }
    ma               = 16
    # 多参数系数
    BK_A_LOSS_SP_RATIO = 1      #{当CLOSE<MA均线的时候，缩小}
    BK_Volatility_RATIO= 1      #{当CLOSE>MA均线的时候, 缩小}  
    SP_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}
    BK_A_FLAOT_PROFIT_ALL_RATIO= 0.85#{当CLOSE>MA均线的时候, 放大}
    # 空参数系数
    SK_A_LOSS_SP_RATIO = 1      #{当CLOSE>MA均线的时候，缩小}
    SK_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}  
    BP_Volatility_RATIO= 0.45      #{当CLOSE>MA均线的时候, 缩小}
    SK_A_FLAOT_PROFIT_ALL_RATIO= 1.9#{当CLOSE<MA均线的时候, 放大}
    '''
    
    '''
    # self.TEMP == 9 2015年01月	2016年12月
    # 做多的优化参数优化期全部数据 星期[0,1,2,3]
    BK_A_LOSS_SP     = 1400     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.7      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.9      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{买开N日中最高价-买开N日中的最低价 买开N=1代表当日} 
    SP_BEFORE_DAY    = 1        #{卖平M日中最高价-卖平M日中的最低价 卖平M=1代表当日} 
    BK_A_FLAOT_PROFIT_ALL=500   #{最佳浮盈                  } ###########600
    # 做空的优化参数优化期最近数据 星期[1,2,3,4]
    SK_A_LOSS_SP     = 900     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.3      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 0.9      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 4        #{卖开N日中最高价-卖开N日中的最低价 卖开N=1代表当日}
    BP_BEFORE_DAY    = 3        #{买平M日中最高价-买平M日中的最低价 买平M=1代表当日}
    SK_A_FLAOT_PROFIT_ALL=1200  #{最佳浮盈                  }   ##############1000       
    # 多空判断
    Trend_DAYS       = 300         #{做多：当前CLOSE大于Trend_DAYS天前的CLOSE ; 做空：当前CLOSE小于Trend_DAYS天前的CLOSE }380
    ma               = 15       #16
    # 多参数系数
    BK_A_LOSS_SP_RATIO = 1      #{当CLOSE<MA均线的时候，缩小}
    BK_Volatility_RATIO= 1      #{当CLOSE>MA均线的时候, 缩小}  
    SP_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}
    BK_A_FLAOT_PROFIT_ALL_RATIO= 1.1#{当CLOSE>MA均线的时候, 放大}############0.85
    # 空参数系数
    SK_A_LOSS_SP_RATIO = 0.5    #{当CLOSE>MA均线的时候，缩小} ###############1
    SK_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}  
    BP_Volatility_RATIO= 0.45   #{当CLOSE>MA均线的时候, 缩小}
    SK_A_FLAOT_PROFIT_ALL_RATIO= 1.9#{当CLOSE<MA均线的时候, 放大}
    '''
     
    '''   
    #self.TEMP == 10 2015年07月	2017年06月
    # 做多的优化参数优化期全部数据 星期[0,1,2,3]
    BK_A_LOSS_SP     = 1400     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.7      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.9      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{买开N日中最高价-买开N日中的最低价 买开N=1代表当日} 
    SP_BEFORE_DAY    = 1        #{卖平M日中最高价-卖平M日中的最低价 卖平M=1代表当日} 
    BK_A_FLAOT_PROFIT_ALL=600   #{最佳浮盈                  } 
    # 做空的优化参数优化期最近数据 星期[1,2,3,4]
    SK_A_LOSS_SP     = 900     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.3      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 0.9      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 4        #{卖开N日中最高价-卖开N日中的最低价 卖开N=1代表当日}  #####4
    BP_BEFORE_DAY    = 2        #{买平M日中最高价-买平M日中的最低价 买平M=1代表当日}  #####3
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }       
    # 多空判断
    Trend_DAYS       = 380         #{做多：当前CLOSE大于Trend_DAYS天前的CLOSE ; 做空：当前CLOSE小于Trend_DAYS天前的CLOSE }
    ma               = 16
    # 多参数系数
    BK_A_LOSS_SP_RATIO = 1      #{当CLOSE<MA均线的时候，缩小}
    BK_Volatility_RATIO= 1      #{当CLOSE>MA均线的时候, 缩小}  
    SP_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}
    BK_A_FLAOT_PROFIT_ALL_RATIO= 0.9#{当CLOSE>MA均线的时候, 放大}#########0.85
    # 空参数系数
    SK_A_LOSS_SP_RATIO = 1      #{当CLOSE>MA均线的时候，缩小}
    SK_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}  
    BP_Volatility_RATIO= 0.45      #{当CLOSE>MA均线的时候, 缩小}
    SK_A_FLAOT_PROFIT_ALL_RATIO= 1.8#{当CLOSE<MA均线的时候, 放大}#########1.9
    '''
    
    '''
    #self.TEMP == 11 2016年01月	2017年12月
    # 做多的优化参数优化期全部数据 星期[0,1,2,3]
    BK_A_LOSS_SP     = 1400     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.7      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.9      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{买开N日中最高价-买开N日中的最低价 买开N=1代表当日} 
    SP_BEFORE_DAY    = 1        #{卖平M日中最高价-卖平M日中的最低价 卖平M=1代表当日} 
    BK_A_FLAOT_PROFIT_ALL=600   #{最佳浮盈                  } 
    # 做空的优化参数优化期最近数据 星期[1,2,3,4]
    SK_A_LOSS_SP     = 900     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.3      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 0.9      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 4        #{卖开N日中最高价-卖开N日中的最低价 卖开N=1代表当日} 
    BP_BEFORE_DAY    = 2        #{买平M日中最高价-买平M日中的最低价 买平M=1代表当日} ###################3
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }       
    # 多空判断
    Trend_DAYS       = 200         #{做多：当前CLOSE大于Trend_DAYS天前的CLOSE ; 做空：当前CLOSE小于Trend_DAYS天前的CLOSE }#380
    ma               = 33           #16
    # 多参数系数
    BK_A_LOSS_SP_RATIO = 1      #{当CLOSE<MA均线的时候，缩小}
    BK_Volatility_RATIO= 1      #{当CLOSE>MA均线的时候, 缩小}  
    SP_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}
    BK_A_FLAOT_PROFIT_ALL_RATIO= 0.7#{当CLOSE>MA均线的时候, 放大}#########0.85
    # 空参数系数
    SK_A_LOSS_SP_RATIO = 0.5      #{当CLOSE>MA均线的时候，缩小}  ######1
    SK_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}  
    BP_Volatility_RATIO= 0.45      #{当CLOSE>MA均线的时候, 缩小}
    SK_A_FLAOT_PROFIT_ALL_RATIO= 1.9#{当CLOSE<MA均线的时候, 放大}   
    '''
    
    '''
    #self.TEMP == 12 2016年07月	2018年06月
    # 做多的优化参数优化期全部数据 星期[0,1,2,3]
    BK_A_LOSS_SP     = 1400     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.7      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.9      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{买开N日中最高价-买开N日中的最低价 买开N=1代表当日} 
    SP_BEFORE_DAY    = 1        #{卖平M日中最高价-卖平M日中的最低价 卖平M=1代表当日} 
    BK_A_FLAOT_PROFIT_ALL=600   #{最佳浮盈                  } 
    # 做空的优化参数优化期最近数据 星期[1,2,3,4]
    SK_A_LOSS_SP     = 900     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.3      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 0.9      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 3        #{卖开N日中最高价-卖开N日中的最低价 卖开N=1代表当日} ########4
    BP_BEFORE_DAY    = 1        #{买平M日中最高价-买平M日中的最低价 买平M=1代表当日} ########3
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }       
    # 多空判断
    Trend_DAYS       = 380         #{做多：当前CLOSE大于Trend_DAYS天前的CLOSE ; 做空：当前CLOSE小于Trend_DAYS天前的CLOSE }
    ma               = 16
    # 多参数系数
    BK_A_LOSS_SP_RATIO = 1      #{当CLOSE<MA均线的时候，缩小}
    BK_Volatility_RATIO= 1      #{当CLOSE>MA均线的时候, 缩小}  
    SP_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}
    BK_A_FLAOT_PROFIT_ALL_RATIO= 0.85#{当CLOSE>MA均线的时候, 放大}
    # 空参数系数
    SK_A_LOSS_SP_RATIO = 1      #{当CLOSE>MA均线的时候，缩小}
    SK_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}  
    BP_Volatility_RATIO= 0.45      #{当CLOSE>MA均线的时候, 缩小}
    SK_A_FLAOT_PROFIT_ALL_RATIO= 1.9#{当CLOSE<MA均线的时候, 放大}
    '''
    
    
    '''
    #self.TEMP == 13 2017年01月	2018年12月
    # 做多的优化参数优化期全部数据 星期[0,1,2,3]
    BK_A_LOSS_SP     = 1400     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.7      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.9      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{买开N日中最高价-买开N日中的最低价 买开N=1代表当日} 
    SP_BEFORE_DAY    = 1        #{卖平M日中最高价-卖平M日中的最低价 卖平M=1代表当日} 
    BK_A_FLAOT_PROFIT_ALL=600   #{最佳浮盈                  } 
    # 做空的优化参数优化期最近数据 星期[1,2,3,4]
    SK_A_LOSS_SP     = 900     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.3      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 0.9      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 4        #{卖开N日中最高价-卖开N日中的最低价 卖开N=1代表当日} 
    BP_BEFORE_DAY    = 3        #{买平M日中最高价-买平M日中的最低价 买平M=1代表当日} 
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }       
    # 多空判断
    Trend_DAYS       = 380         #{做多：当前CLOSE大于Trend_DAYS天前的CLOSE ; 做空：当前CLOSE小于Trend_DAYS天前的CLOSE }
    ma               = 16
    # 多参数系数
    BK_A_LOSS_SP_RATIO = 1      #{当CLOSE<MA均线的时候，缩小}
    BK_Volatility_RATIO= 1      #{当CLOSE>MA均线的时候, 缩小}  
    SP_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}
    BK_A_FLAOT_PROFIT_ALL_RATIO= 0.85#{当CLOSE>MA均线的时候, 放大}
    # 空参数系数
    SK_A_LOSS_SP_RATIO = 1      #{当CLOSE>MA均线的时候，缩小}
    SK_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}  
    BP_Volatility_RATIO= 0.45      #{当CLOSE>MA均线的时候, 缩小}
    SK_A_FLAOT_PROFIT_ALL_RATIO= 1.9#{当CLOSE<MA均线的时候, 放大}
    '''
    
    '''    
    #self.TEMP == 14 2017年07月	2019年06月
    # 做多的优化参数优化期全部数据 星期[0,1,2,3]
    BK_A_LOSS_SP     = 1400     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.7      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.9      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{买开N日中最高价-买开N日中的最低价 买开N=1代表当日} 
    SP_BEFORE_DAY    = 1        #{卖平M日中最高价-卖平M日中的最低价 卖平M=1代表当日} 
    BK_A_FLAOT_PROFIT_ALL=400   #{最佳浮盈                  } ########400
    # 做空的优化参数优化期最近数据 星期[1,2,3,4]
    SK_A_LOSS_SP     = 900     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.3      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 0.9      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 2        #{卖开N日中最高价-卖开N日中的最低价 卖开N=1代表当日} #######4
    BP_BEFORE_DAY    = 3        #{买平M日中最高价-买平M日中的最低价 买平M=1代表当日} #######3
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }       
    # 多空判断
    Trend_DAYS       = 380         #{做多：当前CLOSE大于Trend_DAYS天前的CLOSE ; 做空：当前CLOSE小于Trend_DAYS天前的CLOSE }
    ma               = 16
    # 多参数系数
    BK_A_LOSS_SP_RATIO = 1      #{当CLOSE<MA均线的时候，缩小}
    BK_Volatility_RATIO= 0.9      #{当CLOSE>MA均线的时候, 缩小}  #############1
    SP_Volatility_RATIO= 1.3     #{当CLOSE<MA均线的时候, 缩小} #####################1
    BK_A_FLAOT_PROFIT_ALL_RATIO= 0.85#{当CLOSE>MA均线的时候, 放大}
    # 空参数系数
    SK_A_LOSS_SP_RATIO = 1      #{当CLOSE>MA均线的时候，缩小}
    SK_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小} 
    BP_Volatility_RATIO= 0.45      #{当CLOSE>MA均线的时候, 缩小}
    SK_A_FLAOT_PROFIT_ALL_RATIO= 1.9#{当CLOSE<MA均线的时候, 放大}
    '''
    
    #'''
    #self.TEMP == 29 2018年01月	2019年12月
    # 做多的优化参数优化期全部数据 星期[0,1,2,3]
    BK_A_LOSS_SP     = 1200     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.4      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.8      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 2        #{买开N日中最高价-买开N日中的最低价 买开N=1代表当日} 
    SP_BEFORE_DAY    = 1        #{卖平M日中最高价-卖平M日中的最低价 卖平M=1代表当日} 
    BK_A_FLAOT_PROFIT_ALL=700   #{最佳浮盈                  } 
    # 做空的优化参数优化期最近数据 星期[1,2,3,4]
    SK_A_LOSS_SP     = 500     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.7      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 0.8      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 3        #{卖开N日中最高价-卖开N日中的最低价 卖开N=1代表当日} 
    BP_BEFORE_DAY    = 1        #{买平M日中最高价-买平M日中的最低价 买平M=1代表当日} 
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }       
    # 多空判断
    Trend_DAYS       = 380         #{做多：当前CLOSE大于Trend_DAYS天前的CLOSE ; 做空：当前CLOSE小于Trend_DAYS天前的CLOSE }
    ma               = 13
    # 多参数系数
    BK_A_LOSS_SP_RATIO = 1      #{当CLOSE<MA均线的时候，缩小}
    BK_Volatility_RATIO= 0.8      #{当CLOSE>MA均线的时候, 缩小}  
    SP_Volatility_RATIO= 0.9      #{当CLOSE<MA均线的时候, 缩小}
    BK_A_FLAOT_PROFIT_ALL_RATIO= 0.85#{当CLOSE>MA均线的时候, 放大}
    # 空参数系数
    SK_A_LOSS_SP_RATIO = 1      #{当CLOSE>MA均线的时候，缩小}
    SK_Volatility_RATIO= 1.3    #{当CLOSE<MA均线的时候, 缩小}  
    BP_Volatility_RATIO= 0.5    #{当CLOSE>MA均线的时候, 缩小}
    SK_A_FLAOT_PROFIT_ALL_RATIO= 1.9#{当CLOSE<MA均线的时候, 放大}
    #'''
        
    #方案一：全部时间段用一套参数体系
    '''
    # 做多的优化参数优化期全部数据 星期[0,1,2,3]
    BK_A_LOSS_SP     = 1400     #{保证金亏损金额     用于卖平}  
    BK_Volatility    = 0.7      #{买开的开盘价波幅   用于买开}  
    SP_Volatility    = 0.9      #{卖平的成交价波幅   用于卖平}  
    BK_BEFORE_DAY    = 1        #{买开N日中最高价-买开N日中的最低价 买开N=1代表当日} 
    SP_BEFORE_DAY    = 1        #{卖平M日中最高价-卖平M日中的最低价 卖平M=1代表当日} 
    BK_A_FLAOT_PROFIT_ALL=600   #{最佳浮盈                  } 
    # 做空的优化参数优化期最近数据 星期[1,2,3,4]
    SK_A_LOSS_SP     = 900     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.3      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 0.9      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 4        #{卖开N日中最高价-卖开N日中的最低价 卖开N=1代表当日} 
    BP_BEFORE_DAY    = 3        #{买平M日中最高价-买平M日中的最低价 买平M=1代表当日} 
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }       
    # 多空判断
    Trend_DAYS       = 380         #{做多：当前CLOSE大于Trend_DAYS天前的CLOSE ; 做空：当前CLOSE小于Trend_DAYS天前的CLOSE }
    ma               = 16
    # 多参数系数
    BK_A_LOSS_SP_RATIO = 1      #{当CLOSE<MA均线的时候，缩小}
    BK_Volatility_RATIO= 1      #{当CLOSE>MA均线的时候, 缩小}  
    SP_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}
    BK_A_FLAOT_PROFIT_ALL_RATIO= 0.85#{当CLOSE>MA均线的时候, 放大}
    # 空参数系数
    SK_A_LOSS_SP_RATIO = 1      #{当CLOSE>MA均线的时候，缩小}
    SK_Volatility_RATIO= 1      #{当CLOSE<MA均线的时候, 缩小}  
    BP_Volatility_RATIO= 0.45      #{当CLOSE>MA均线的时候, 缩小}
    SK_A_FLAOT_PROFIT_ALL_RATIO= 1.9#{当CLOSE<MA均线的时候, 放大}
    '''
    
    
    TEMP      = 0 
    
    # 策略变量
    showtrade        = False  
    #LongOrShort      = True                
    # 参数列表，保存了参数的名称
    paramList = ['name'         ,
                 'className'    ,
                 'author'       ,
                 'vtSymbol'     ,
                 'BK_A_LOSS_SP' ,
                 'BK_Volatility',
                 'SP_Volatility',
                 'BK_BEFORE_DAY',
                 'SP_BEFORE_DAY',
                 'BK_A_FLAOT_PROFIT_ALL',
                 'SK_A_LOSS_SP' ,
                 'SK_Volatility',
                 'BP_Volatility',
                 'SK_BEFORE_DAY',
                 'BP_BEFORE_DAY',
                 'SK_A_FLAOT_PROFIT_ALL',
                 'Trend_DAYS',
                 'ma',
                 'BK_A_LOSS_SP_RATIO',
                 'BK_Volatility_RATIO',
                 'SP_Volatility_RATIO',
                 'BK_A_FLAOT_PROFIT_ALL_RATIO',
                 'SK_A_LOSS_SP_RATIO',
                 'SK_Volatility_RATIO',
                 'BP_Volatility_RATIO',
                 'SK_A_FLAOT_PROFIT_ALL_RATIO',
                 'TEMP']    
    
    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos']  
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos']

    #----------------------------------------------------------------------
    def setparalist(self,paralist):
        """"""            
        self.BK_A_LOSS_SP     = paralist[0]     
        self.BK_Volatility    = paralist[1]     
        self.SP_Volatility    = paralist[2]     
        self.BK_BEFORE_DAY    = paralist[3]        
        self.SP_BEFORE_DAY    = paralist[4]      
        self.BK_A_FLAOT_PROFIT_ALL=paralist[5]
    
        self.SK_A_LOSS_SP     = paralist[6]
        self.SK_Volatility    = paralist[7]     
        self.BP_Volatility    = paralist[8]     
        self.SK_BEFORE_DAY    = paralist[9]        
        self.BP_BEFORE_DAY    = paralist[10]  
        self.SK_A_FLAOT_PROFIT_ALL=paralist[11]  
        
        self.Trend_DAYS      = paralist[12]      
        self.Trend_DAYS_Before=paralist[13]          
    
    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(strategy_Volatility_RB_V1, self).__init__(ctaEngine, setting)
          
        self.initDays         = max(self.BK_BEFORE_DAY,self.SK_BEFORE_DAY)           # 初始化数据所用的天数        
        self.bg = BarGenerator(self.onBar)
        self.am = ArrayManager(self.initDays)
        
        
        if self.TEMP == 1:
            self.strategyStartpos                =432      
            self.strategyEndpos                  =918        
        elif self.TEMP == 2:
            self.strategyStartpos                =551      
            self.strategyEndpos                  =1031     
        elif self.TEMP == 3:
            self.strategyStartpos                =676      
            self.strategyEndpos                  =1157      
        elif self.TEMP == 4:
            self.strategyStartpos                =793      
            self.strategyEndpos                  =1276      
        elif self.TEMP == 5:
            self.strategyStartpos                =919      
            self.strategyEndpos                  =1401      
        elif self.TEMP == 6:
            self.strategyStartpos                =1032      
            self.strategyEndpos                  =1520      
        elif self.TEMP == 7:
            self.strategyStartpos                =1157      
            self.strategyEndpos                  =1645      
        elif self.TEMP == 8:
            self.strategyStartpos                =1276      
            self.strategyEndpos                  =1765   
        elif self.TEMP == 9:
            self.strategyStartpos                =1402      
            self.strategyEndpos                  =1889   
        elif self.TEMP == 10:
            self.strategyStartpos                =1521      
            self.strategyEndpos                  =2008   
        elif self.TEMP == 11:
            self.strategyStartpos                =1646      
            self.strategyEndpos                  =2134   
        elif self.TEMP == 12:
            self.strategyStartpos                =1766      
            self.strategyEndpos                  =2252   
        elif self.TEMP == 13:
            self.strategyStartpos                =1890      
            self.strategyEndpos                  =2376   
        elif self.TEMP == 14:
            self.strategyStartpos                =2009      
            self.strategyEndpos                  =2494   
        elif self.TEMP == 15:
            self.strategyStartpos                =919      
            self.strategyEndpos                  =1031   
        elif self.TEMP == 16:
            self.strategyStartpos                =1032      
            self.strategyEndpos                  =1156   
        elif self.TEMP == 17:
            self.strategyStartpos                =1157      
            self.strategyEndpos                  =1275   
        elif self.TEMP == 18:
            self.strategyStartpos                =1276      
            self.strategyEndpos                  =1401   
        elif self.TEMP == 19:
            self.strategyStartpos                =1402      
            self.strategyEndpos                  =1520   
        elif self.TEMP == 20:
            self.strategyStartpos                =1521      
            self.strategyEndpos                  =1645   
        elif self.TEMP == 21:
            self.strategyStartpos                =1646      
            self.strategyEndpos                  =1765   
        elif self.TEMP == 22:
            self.strategyStartpos                =1766      
            self.strategyEndpos                  =1889   
        elif self.TEMP == 23:
            self.strategyStartpos                =1890      
            self.strategyEndpos                  =2008   
        elif self.TEMP == 24:
            self.strategyStartpos                =2009      
            self.strategyEndpos                  =2133   
        elif self.TEMP == 25:
            self.strategyStartpos                =2134      
            self.strategyEndpos                  =2252   
        elif self.TEMP == 26:
            self.strategyStartpos                =2253      
            self.strategyEndpos                  =2376   
        elif self.TEMP == 27:
            self.strategyStartpos                =2377      
            self.strategyEndpos                  =2494   
        elif self.TEMP == 28:
            self.strategyStartpos                =2495      
            self.strategyEndpos                  =2620   
        elif self.TEMP == 29:
            self.strategyStartpos                =2134      
            self.strategyEndpos                  =2620   
        else:
            self.strategyStartpos                =1889      
            self.strategyEndpos                  =2497   
        
        
            
        self.all_bar                         =[]     
        self.SP_style                        =0000 
        self.BP_style                        =0000 
        self.BKPRICE                         =EMPTY_FLOAT_WH  
        self.BKDATE                          =EMPTY_FLOAT_WH  
        self.SKPRICE                         =EMPTY_FLOAT_WH  
        self.SKDATE                          =EMPTY_FLOAT_WH  
        self.tradeday                        =0
        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）
        self.BKWeekProfit                    =[0,0,0,0,0,0,0]
        self.SKWeekProfit                    =[0,0,0,0,0,0,0]        
        
        self.LongBestday                     =[0,1,2,3,4]#[0,1,2,3]
        self.ShortBestday                    =[0,1,2,3,4]#[1,2,3,4]
        
        self.TrendStatus                     =2 # 0-做多 1-做空 2-数据收集期
        self.BK_virtual_trade_day            =False #虚拟交易日
        self.SK_virtual_trade_day            =False #虚拟交易日
        self.BK_Q_HIGH                            =Queue.Queue()
        self.BK_Q_HIGH.maxsize                    =self.BK_BEFORE_DAY       
        self.BK_Q_LOW                             =Queue.Queue()
        self.BK_Q_LOW.maxsize                     =self.BK_BEFORE_DAY      
        self.BK_Q_OPEN                            =Queue.Queue()
        self.BK_Q_OPEN.maxsize                    =self.BK_BEFORE_DAY     
        self.SP_Q_HIGH                            =Queue.Queue()
        self.SP_Q_HIGH.maxsize                    =self.SP_BEFORE_DAY       
        self.SP_Q_LOW                             =Queue.Queue()
        self.SP_Q_LOW.maxsize                     =self.SP_BEFORE_DAY      


        self.SK_Q_HIGH                            =Queue.Queue()
        self.SK_Q_HIGH.maxsize                    =self.SK_BEFORE_DAY       
        self.SK_Q_LOW                             =Queue.Queue()
        self.SK_Q_LOW.maxsize                     =self.SK_BEFORE_DAY      
        self.SK_Q_OPEN                            =Queue.Queue()
        self.SK_Q_OPEN.maxsize                    =self.SK_BEFORE_DAY     
        self.BP_Q_HIGH                            =Queue.Queue()
        self.BP_Q_HIGH.maxsize                    =self.BP_BEFORE_DAY       
        self.BP_Q_LOW                             =Queue.Queue()
        self.BP_Q_LOW.maxsize                     =self.BP_BEFORE_DAY              
             
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
    def strategy_4(self,bar):
        """主力策略 今日收盘价加上今日波幅的某个比例，作为第二日买入的价格点。（4）"""
        self.all_bar.append(bar)  
        
        am = self.am        
        am.updateBar(bar)
        if not am.inited:
            return
        
        
        #if bar.date=='20200114':
        #    print bar.date
        #    print bar.close
        
        
        if len(self.all_bar)-1 > self.strategyEndpos :  
            if self.pos == 1 and self.BK_virtual_trade_day == False:
                self.sell(bar.close,1)
            elif self.pos == -1 and self.SK_virtual_trade_day == False:
                self.cover(bar.close,1)
            return
        
        if len(self.all_bar)-1 < self.strategyStartpos :
            self.putEvent()            
            return              
                
        if  self.BK_Q_HIGH.qsize() < self.BK_Q_HIGH.maxsize:
            self.BK_Q_HIGH.put(self.all_bar[-1].high)
        else:
            self.BK_Q_HIGH.get()
            self.BK_Q_HIGH.put(self.all_bar[-1].high)  
        if self.BK_Q_LOW.qsize() < self.BK_Q_LOW.maxsize:
            self.BK_Q_LOW.put(self.all_bar[-1].low)
        else:
            self.BK_Q_LOW.get()
            self.BK_Q_LOW.put(self.all_bar[-1].low)  
        if self.BK_Q_OPEN.qsize() < self.BK_Q_OPEN.maxsize:
            self.BK_Q_OPEN.put(self.all_bar[-1].open)
        else:
            self.BK_Q_OPEN.get()
            self.BK_Q_OPEN.put(self.all_bar[-1].open) 
        if self.SP_Q_HIGH.qsize() < self.SP_Q_HIGH.maxsize:
            self.SP_Q_HIGH.put(self.all_bar[-1].high)
        else:
            self.SP_Q_HIGH.get()
            self.SP_Q_HIGH.put(self.all_bar[-1].high)  
        if self.SP_Q_LOW.qsize() < self.SP_Q_LOW.maxsize:
            self.SP_Q_LOW.put(self.all_bar[-1].low)
        else:
            self.SP_Q_LOW.get()
            self.SP_Q_LOW.put(self.all_bar[-1].low)      
            
        
        if  self.SK_Q_HIGH.qsize() < self.SK_Q_HIGH.maxsize:
            self.SK_Q_HIGH.put(self.all_bar[-1].high)
        else:
            self.SK_Q_HIGH.get()
            self.SK_Q_HIGH.put(self.all_bar[-1].high)  
        if self.SK_Q_LOW.qsize() < self.SK_Q_LOW.maxsize:
            self.SK_Q_LOW.put(self.all_bar[-1].low)
        else:
            self.SK_Q_LOW.get()
            self.SK_Q_LOW.put(self.all_bar[-1].low)  
        if self.SK_Q_OPEN.qsize() < self.SK_Q_OPEN.maxsize:
            self.SK_Q_OPEN.put(self.all_bar[-1].open)
        else:
            self.SK_Q_OPEN.get()
            self.SK_Q_OPEN.put(self.all_bar[-1].open) 
        if self.BP_Q_HIGH.qsize() < self.BP_Q_HIGH.maxsize:
            self.BP_Q_HIGH.put(self.all_bar[-1].high)
        else:
            self.BP_Q_HIGH.get()
            self.BP_Q_HIGH.put(self.all_bar[-1].high)  
        if self.BP_Q_LOW.qsize() < self.BP_Q_LOW.maxsize:
            self.BP_Q_LOW.put(self.all_bar[-1].low)
        else:
            self.BP_Q_LOW.get()
            self.BP_Q_LOW.put(self.all_bar[-1].low)             
            

        

        
            
        # 这个出了一个大问题 -1代表的是取今天的数据，-2代表取前一天的数据
        # 根据书中内容本意是取-2前一天的数据，结果错写成-1.所有测试结果也是按照取值-1计算。
        # 万幸的是取值-1的结果也不错，暂时以取值-1位置。
        # 代表的逻辑是：
        # 下影线长 上影线短 ，open+BK_CURDAYRANGE*self.BK_Volatility 容易冲出范围
        # 光头光脚          ，open+BK_CURDAYRANGE*self.BK_Volatility 不易冲出范围
        # 下影线短 上影线长 ，open+BK_CURDAYRANGE*self.BK_Volatility 不易冲出范围
        # 总之，从K线上看 BK_Condition_1是一个倒锤阳线才可以，或者接近光头光脚阳线
        BK_CURDAYRANGE  = max(list(self.BK_Q_HIGH.queue)) - min(list(self.BK_Q_LOW.queue))  
        SP_CURDAYRANGE  = max(list(self.SP_Q_HIGH.queue)) - min(list(self.SP_Q_LOW.queue))    
             
        SK_CURDAYRANGE  = max(list(self.SK_Q_HIGH.queue)) - min(list(self.SK_Q_LOW.queue))  
        BP_CURDAYRANGE  = max(list(self.BP_Q_HIGH.queue)) - min(list(self.BP_Q_LOW.queue))    
                
        
            
        if self.tradeday!=0:
            self.tradeday = self.tradeday+1
            
        now_price_ma= bar.close
        if len(self.all_bar) > self.Trend_DAYS+self.ma: 
            now_price=[]
            Trend_DAYS_Before_price=[]
            for index in range(self.ma,0,-1) :
                now_price.append(self.all_bar[0-index].close)
                Trend_DAYS_Before_price.append(self.all_bar[0-index-self.Trend_DAYS].close)   
                
            now_price_ma = np.mean(np.mat( np.array(now_price)))
            if  np.mean(np.mat( np.array(now_price)))  > np.mean(np.mat( np.array(Trend_DAYS_Before_price))):
                self.TrendStatus = 0
            else:
                self.TrendStatus = 1 
        
        if self.TrendStatus == 0 and bar.close < now_price_ma:
            self.BK_Volatility_RATIO_           = 1
            self.BK_A_FLAOT_PROFIT_ALL_RATIO_   = 1
            self.BK_A_LOSS_SP_RATIO_            = self.BK_A_LOSS_SP_RATIO
            self.SP_Volatility_RATIO_           = self.SP_Volatility_RATIO
        else:
            self.BK_Volatility_RATIO_         = self.BK_Volatility_RATIO
            self.BK_A_FLAOT_PROFIT_ALL_RATIO_ = self.BK_A_FLAOT_PROFIT_ALL_RATIO
            self.BK_A_LOSS_SP_RATIO_          = 1
            self.SP_Volatility_RATIO_         = 1
    
        if self.TrendStatus == 1 and bar.close > now_price_ma:
            self.SK_Volatility_RATIO_           = 1
            self.SK_A_FLAOT_PROFIT_ALL_RATIO_   = 1
            self.SK_A_LOSS_SP_RATIO_            = self.SK_A_LOSS_SP_RATIO
            self.BP_Volatility_RATIO_           = self.BP_Volatility_RATIO
        else:
            self.SK_Volatility_RATIO_           = self.SK_Volatility_RATIO
            self.SK_A_FLAOT_PROFIT_ALL_RATIO_   = self.SK_A_FLAOT_PROFIT_ALL_RATIO
            self.SK_A_LOSS_SP_RATIO_            = 1
            self.BP_Volatility_RATIO_           = 1


        #-------------------------1、做多买开条件-----------------------------------------
        #条件1：收盘价高于开盘价，达到前日波幅买入；没有办法确认价格是收阳还是收阴，只能在当天价格确实有高于开盘价格幅度或低于开盘幅度的那一刹那成交openorclose
        BK_Condition_1 = False     
        if min(list(self.BK_Q_LOW.queue))  <= list(self.BK_Q_OPEN.queue)[0]  +  (BK_CURDAYRANGE*self.BK_Volatility*self.BK_Volatility_RATIO_) and  \
           max(list(self.BK_Q_HIGH.queue)) >= list(self.BK_Q_OPEN.queue)[0]  +  (BK_CURDAYRANGE*self.BK_Volatility*self.BK_Volatility_RATIO_) and  \
           bar.close>=list(self.BK_Q_OPEN.queue)[0] :
            BK_Condition_1 = True   
                  
        #-------------------------2、做多卖平条件-----------------------------------------   
        self.SP_style=0000
        #条件1：保证金亏损 保证金亏损只能在第二天进行确认，也不能在当天确认，但是当天可能超过了保证金的亏损。
        SP_Condition_1   = False
        if self.pos == 1:
            A_PRICE_SP         =  self.BKPRICE-(self.BK_A_LOSS_SP*self.BK_A_LOSS_SP_RATIO_)/self.A_WEIGHT
            SP_Condition_1     =  bar.close<A_PRICE_SP    
            if SP_Condition_1:
                self.SP_style     = self.SP_style | 8 #1000   
        #条件2：买开价格减去波幅的一定比率 由于价格的震荡，当天可能做多后又做空
        SP_Condition_2  = False            
        if self.pos == 1:
            SP_Condition_2    =  bar.close < self.BKPRICE  -  (SP_CURDAYRANGE*self.SP_Volatility*self.SP_Volatility_RATIO_)
            if SP_Condition_2:
                self.SP_style     = self.SP_style | 4 #0100   
        #条件3：最佳浮盈
        SP_Condition_3  = False            
        if self.pos == 1:
            SP_Condition_3     = int((bar.close-self.BKPRICE)*self.A_WEIGHT) >= int(self.BK_A_FLAOT_PROFIT_ALL*self.BK_A_FLAOT_PROFIT_ALL_RATIO_)    
            if SP_Condition_3:
                self.SP_style     = self.SP_style | 2 #0010                                          
        #-------------------------3 、 做多执行交易-----------------------------------------------  
        #if BK_Condition_1 and self.pos==0 and self.LongOrShort == True and self.TrendStatus == 0:    
        if BK_Condition_1 and self.pos==0 and self.TrendStatus == 0:     
            #0 '星期一',1 :'星期二',2  '星期三',3 '星期四',4  '星期五',5  '星期六',6 '星期天', 
            if (datetime.strptime(bar.date, "%Y%m%d").weekday() in self.LongBestday) :            
                self.buy(bar.close, 1)
                self.tradeday = 1
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
                self.BK_virtual_trade_day =True
                return 
            
        if (SP_Condition_1 or SP_Condition_2 or SP_Condition_3 ) and self.pos == 1 :    
            #0 '星期一',1 :'星期二',2  '星期三',3 '星期四',4  '星期五',5  '星期六',6 '星期天', 
            if (self.BKDATE.weekday() in self.LongBestday):              
                self.sell(bar.close, 1) 
            else:
                self.BKWeekProfit[self.BKDATE.weekday()]=self.BKWeekProfit[self.BKDATE.weekday()]+(bar.close- self.BKPRICE)*self.A_WEIGHT 
                self.pos = self.pos-1
                self.BKDATE = EMPTY_FLOAT_WH
                self.BK_virtual_trade_day =False
                '''
                if self.showtrade: 
                    for each in self.BKWeekProfit:
                        print each,',',  
                    print '\r',          
                '''
                return 
                            
        #-------------------------4、做空卖开条件-----------------------------------------
        #条件4：价格低于开盘价，达到前日波幅卖开；为什么是SK_CURDAYRANGE1而不是SK_CURDAYRANGE？
        SK_Condition_1 = False 
        if min(list(self.SK_Q_LOW.queue))  <= list(self.SK_Q_OPEN.queue)[0]   -  (SK_CURDAYRANGE*self.SK_Volatility*self.SK_Volatility_RATIO_) and  \
           max(list(self.SK_Q_HIGH.queue)) >= list(self.SK_Q_OPEN.queue)[0]   -  (SK_CURDAYRANGE*self.SK_Volatility*self.SK_Volatility_RATIO_) and  \
           bar.close<list(self.SK_Q_OPEN.queue)[0] :
            SK_Condition_1 = True             
        
        #-------------------------5、做空买平条件-----------------------------------------   
        self.BP_style=0000
        #条件1：保证金亏损 
        BP_Condition_1   = False
        if self.pos == -1:
            A_PRICE_SP         =  self.SKPRICE+(self.SK_A_LOSS_SP*self.SK_A_LOSS_SP_RATIO_)/self.A_WEIGHT         
            BP_Condition_1     =  bar.close>A_PRICE_SP  
            if BP_Condition_1:
                self.BP_style  = self.BP_style | 8 #1000   
        #条件2：卖开价格减去波幅的一定比率
        BP_Condition_2  = False            
        if self.pos == -1:
            BP_Condition_2    =  bar.close > self.SKPRICE  +  (BP_CURDAYRANGE*self.BP_Volatility*self.BP_Volatility_RATIO_)
            if BP_Condition_2:
                self.BP_style     = self.BP_style | 4 #0100  
        #条件3：最佳浮盈
        BP_Condition_3  = False            
        if self.pos == -1:       
            BP_Condition_3    = int((self.SKPRICE - bar.close)*self.A_WEIGHT) >= int(self.SK_A_FLAOT_PROFIT_ALL*self.SK_A_FLAOT_PROFIT_ALL_RATIO_)  
            if BP_Condition_3:
                self.BP_style     = self.BP_style | 2 #0010    
            
        #-------------------------6 、 做空执行交易-----------------------------------------------        
        #if SK_Condition_1 and self.pos==0 and self.LongOrShort == False and self.TrendStatus == 1:           
        if SK_Condition_1 and self.pos==0 and self.TrendStatus == 1:      
            #0 '星期一',1 :'星期二',2  '星期三',3 '星期四',4  '星期五',5  '星期六',6 '星期天', 
            if (datetime.strptime(bar.date, "%Y%m%d").weekday() in self.ShortBestday) :            
                self.short(bar.close, 1)  
                self.tradeday = 1
            else:
                # 注释参见做多的注释
                self.pos = self.pos-1
                self.SKDATE = datetime.strptime(bar.date, "%Y%m%d") 
                self.SKPRICE = bar.close
                self.SK_virtual_trade_day =True
                return         
            
        if (BP_Condition_1 or BP_Condition_2 or BP_Condition_3 ) and self.pos == -1 :    
            #0 '星期一',1 :'星期二',2  '星期三',3 '星期四',4  '星期五',5  '星期六',6 '星期天', 
            if (self.SKDATE.weekday() in self.ShortBestday):              
                self.cover(bar.close, 1) 
            else:
                self.SKWeekProfit[self.SKDATE.weekday()]=self.SKWeekProfit[self.SKDATE.weekday()]+(self.SKPRICE - bar.close)*self.A_WEIGHT 
                self.pos = self.pos+1
                self.SKDATE = EMPTY_FLOAT_WH
                self.SK_virtual_trade_day =False
                
                if self.showtrade: 
                    for each in self.SKWeekProfit:
                        print each,',',  
                    print '\r',          
                return  
        
        # 发出状态更新事件
        self.putEvent()        
        
    #----------------------------------------------------------------------
    def strategy_2(self,bar):
        """备选策略 将第二天的开盘价加上波幅的比例作为买入点， 第二天的开盘价减去波幅的比例作为卖出点（2）"""
        self.all_bar.append(bar)  
        
        if  self.BK_Q_HIGH.qsize() < self.BK_Q_HIGH.maxsize:
            self.BK_Q_HIGH.put(self.all_bar[-1].high)
        else:
            self.BK_Q_HIGH.get()
            self.BK_Q_HIGH.put(self.all_bar[-1].high)  
        if self.BK_Q_LOW.qsize() < self.BK_Q_LOW.maxsize:
            self.BK_Q_LOW.put(self.all_bar[-1].low)
        else:
            self.BK_Q_LOW.get()
            self.BK_Q_LOW.put(self.all_bar[-1].low)  
        if self.BK_Q_OPEN.qsize() < self.BK_Q_OPEN.maxsize:
            self.BK_Q_OPEN.put(self.all_bar[-1].open)
        else:
            self.BK_Q_OPEN.get()
            self.BK_Q_OPEN.put(self.all_bar[-1].open) 
        if self.SP_Q_HIGH.qsize() < self.SP_Q_HIGH.maxsize:
            self.SP_Q_HIGH.put(self.all_bar[-1].high)
        else:
            self.SP_Q_HIGH.get()
            self.SP_Q_HIGH.put(self.all_bar[-1].high)  
        if self.SP_Q_LOW.qsize() < self.SP_Q_LOW.maxsize:
            self.SP_Q_LOW.put(self.all_bar[-1].low)
        else:
            self.SP_Q_LOW.get()
            self.SP_Q_LOW.put(self.all_bar[-1].low)      
            
        
        if  self.SK_Q_HIGH.qsize() < self.SK_Q_HIGH.maxsize:
            self.SK_Q_HIGH.put(self.all_bar[-1].high)
        else:
            self.SK_Q_HIGH.get()
            self.SK_Q_HIGH.put(self.all_bar[-1].high)  
        if self.SK_Q_LOW.qsize() < self.SK_Q_LOW.maxsize:
            self.SK_Q_LOW.put(self.all_bar[-1].low)
        else:
            self.SK_Q_LOW.get()
            self.SK_Q_LOW.put(self.all_bar[-1].low)  
        if self.SK_Q_OPEN.qsize() < self.SK_Q_OPEN.maxsize:
            self.SK_Q_OPEN.put(self.all_bar[-1].open)
        else:
            self.SK_Q_OPEN.get()
            self.SK_Q_OPEN.put(self.all_bar[-1].open) 
        if self.BP_Q_HIGH.qsize() < self.BP_Q_HIGH.maxsize:
            self.BP_Q_HIGH.put(self.all_bar[-1].high)
        else:
            self.BP_Q_HIGH.get()
            self.BP_Q_HIGH.put(self.all_bar[-1].high)  
        if self.BP_Q_LOW.qsize() < self.BP_Q_LOW.maxsize:
            self.BP_Q_LOW.put(self.all_bar[-1].low)
        else:
            self.BP_Q_LOW.get()
            self.BP_Q_LOW.put(self.all_bar[-1].low)             
            

        
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
        BK_CURDAYRANGE  = self.all_bar[-2].high - self.all_bar[-2].low
        SP_CURDAYRANGE  = max(list(self.SP_Q_HIGH.queue)) - min(list(self.SP_Q_LOW.queue))    
             
        SK_CURDAYRANGE  = self.all_bar[-2].high - self.all_bar[-2].low 
        BP_CURDAYRANGE  = max(list(self.BP_Q_HIGH.queue)) - min(list(self.BP_Q_LOW.queue))    
                
        if len(self.all_bar) < self.strategyStartpos :
            self.putEvent()            
            return            
        
        #if bar.date=='20170317':
         #   print bar.date
         #   print bar.close
            
        if self.tradeday!=0:
            self.tradeday = self.tradeday+1
            
        #  当前连续n天的均值大于Trend_DAYS天前的连续n天的均值
        if len(self.all_bar) > self.Trend_DAYS+self.ma: 
            now_price=[]
            Trend_DAYS_Before_price=[]
            for index in range(self.ma,0,-1) :
                now_price.append(self.all_bar[0-index].close)
                Trend_DAYS_Before_price.append(self.all_bar[0-index-self.Trend_DAYS].close)   
                
            if  np.mean(np.mat( np.array(now_price)))  > np.mean(np.mat( np.array(Trend_DAYS_Before_price))):
                self.TrendStatus = 0
            else:
                self.TrendStatus = 1 
                    
        #-------------------------1、做多买开条件-----------------------------------------
        #条件1：收盘价高于开盘价，达到前日波幅买入；没有办法确认价格是收阳还是收阴，只能在当天价格确实有高于开盘价格幅度或低于开盘幅度的那一刹那成交openorclose
        BK_Condition_1 = False     
        if (bar.high > bar.open + BK_CURDAYRANGE*self.BK_Volatility) and \
           (bar.low  < bar.open + BK_CURDAYRANGE*self.BK_Volatility) :
            BK_Condition_1 = True   
                  
        #-------------------------2、做多卖平条件-----------------------------------------   
        self.SP_style=0000
        #条件1：保证金亏损 保证金亏损只能在第二天进行确认，也不能在当天确认，但是当天可能超过了保证金的亏损。
        SP_Condition_1   = False
        if self.pos == 1:
            A_PRICE_SP         =  self.BKPRICE-self.BK_A_LOSS_SP/self.A_WEIGHT
            SP_Condition_1     = (bar.high > A_PRICE_SP) and  (bar.low  < A_PRICE_SP)       
            if SP_Condition_1:
                self.SP_style  = self.SP_style | 8 #1000   
        #条件2：最佳浮盈
        SP_Condition_2  = False            
        if self.pos == 1:
            SP_Condition_2     = (bar.open-self.BKPRICE)*self.A_WEIGHT >= self.BK_A_FLAOT_PROFIT_ALL     
            if SP_Condition_2:
                self.SP_style     = self.SP_style | 2 #0010                                          
        #-------------------------3 、 做多执行交易-----------------------------------------------  
        #if BK_Condition_1 and self.pos==0 and self.LongOrShort == True and self.TrendStatus == 0:    
        if BK_Condition_1 and self.pos==0 and self.TrendStatus == 0:     
            #0 '星期一',1 :'星期二',2  '星期三',3 '星期四',4  '星期五',5  '星期六',6 '星期天', 
            if (datetime.strptime(bar.date, "%Y%m%d").weekday() in self.LongBestday) :            
                self.buy(bar.open + BK_CURDAYRANGE*self.BK_Volatility, 1)
                self.tradeday = 1
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
            
        if (SP_Condition_1 or SP_Condition_2 ) and self.pos == 1 :    
            #0 '星期一',1 :'星期二',2  '星期三',3 '星期四',4  '星期五',5  '星期六',6 '星期天', 
            if (self.BKDATE.weekday() in self.LongBestday):              
                if SP_Condition_1:
                    self.sell(A_PRICE_SP,1)
                else:
                    self.sell(bar.open, 1) 
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
        #条件4：价格低于开盘价，达到前日波幅卖开；为什么是SK_CURDAYRANGE1而不是SK_CURDAYRANGE？
        SK_Condition_1 = False 
        if bar.high > bar.open - SK_CURDAYRANGE*self.SK_Volatility and \
           bar.low  < bar.open - SK_CURDAYRANGE*self.SK_Volatility :
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
            BP_Condition_2    =  bar.close > self.SKPRICE  +  (BP_CURDAYRANGE*self.BP_Volatility)
            if BP_Condition_2:
                self.BP_style     = self.BP_style | 4 #0100  
        #条件3：最佳浮盈
        BP_Condition_3  = False            
        if self.pos == -1:       
            BP_Condition_3    = (self.SKPRICE - bar.close)*self.A_WEIGHT >self.SK_A_FLAOT_PROFIT_ALL    
            if BP_Condition_3:
                self.BP_style     = self.BP_style | 2 #0010    
            
        #-------------------------6 、 做空执行交易-----------------------------------------------        
        #if SK_Condition_1 and self.pos==0 and self.LongOrShort == False and self.TrendStatus == 1:           
        if SK_Condition_1 and self.pos==0 and self.TrendStatus == 1:      
            #0 '星期一',1 :'星期二',2  '星期三',3 '星期四',4  '星期五',5  '星期六',6 '星期天', 
            if (datetime.strptime(bar.date, "%Y%m%d").weekday() in self.ShortBestday) :            
                self.short(bar.close, 1)  
                self.tradeday = 1
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
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        self.strategy_4(bar)
        
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder              
        if trade.direction == DIRECTION_LONG and trade.offset == OFFSET_OPEN  :    #做多买开
            if self.showtrade : 
                print 'L , K',',',trade.tradeTime,',',int(trade.price),',','%06d'%(self.ctaEngine.interest),',','     ',',','    ',',','  ',',','%03d'%(trade.volume) 
                pass
            self.BKPRICE = trade.price
            self.BKDATE  = datetime.strptime(trade.tradeTime, "%Y-%m-%d")  
        if trade.direction == DIRECTION_SHORT and trade.offset == OFFSET_CLOSE:    #做多卖平
            self.ctaEngine.interest =int((trade.price- self.BKPRICE)*self.A_WEIGHT)*trade.volume+self.ctaEngine.interest 
            if self.showtrade: 
                #0 '星期一',1 :'星期二',2  '星期三',3 '星期四',4  '星期五',5  '星期六',6 '星期天', 
                self.BKWeekProfit[self.BKDATE.weekday()]=self.BKWeekProfit[self.BKDATE.weekday()]+(trade.price- self.BKPRICE)*self.A_WEIGHT 
                if int((trade.price- self.BKPRICE)*self.A_WEIGHT) >= 0:
                    print 'L , P',',',trade.tradeTime,',',int(trade.price),',','%06d'%(self.ctaEngine.interest),',','\033[0;31m%05d\033[0m'%(int((trade.price- self.BKPRICE)*self.A_WEIGHT)) ,',','{:08b}'.format(self.SP_style)[-4:],',','%02d'%(self.tradeday),',','%03d'%(0-trade.volume)              
                else:
                    print 'L , P',',',trade.tradeTime,',',int(trade.price),',','%06d'%(self.ctaEngine.interest),',','\033[0;32m%05d\033[0m'%(int((trade.price- self.BKPRICE)*self.A_WEIGHT)) ,',','{:08b}'.format(self.SP_style)[-4:],',','%02d'%(self.tradeday),',','%03d'%(0-trade.volume)              
                     
                #for each in self.BKWeekProfit:
                #    print each,',',  
                #print '\r',                
            self.BKPRICE = EMPTY_FLOAT_WH   
            self.BKDATE  = EMPTY_FLOAT_WH
            self.tradeday= 0
            
        if trade.direction == DIRECTION_SHORT and trade.offset == OFFSET_OPEN  :   #做空卖开
            if self.showtrade : 
                print 'S , K',',',trade.tradeTime,',',int(trade.price),',','%06d'%(self.ctaEngine.interest),',','     ',',','    ',',','  ',',','%03d'%(trade.volume)     
                pass
            self.SKPRICE = trade.price
            self.SKDATE  = datetime.strptime(trade.tradeTime, "%Y-%m-%d")  
        if trade.direction == DIRECTION_LONG and trade.offset == OFFSET_CLOSE:     #做空买平
            self.ctaEngine.interest =int((self.SKPRICE- trade.price)*self.A_WEIGHT)*abs(trade.volume)+self.ctaEngine.interest 
            if self.showtrade : 
                self.SKWeekProfit[self.SKDATE.weekday()]=self.SKWeekProfit[self.SKDATE.weekday()]+(self.SKPRICE - trade.price)*self.A_WEIGHT 
                if int((self.SKPRICE- trade.price)*self.A_WEIGHT) >= 0 :
                    print 'S , P',',',trade.tradeTime,',',int(trade.price),',','%06d'%(self.ctaEngine.interest),',','\033[0;31m%05d\033[0m'%(int((self.SKPRICE- trade.price)*self.A_WEIGHT)) ,',','{:08b}'.format(self.BP_style)[-4:],',','%02d'%(self.tradeday),',','%03d'%(0-trade.volume) 
                else:
                    print 'S , P',',',trade.tradeTime,',',int(trade.price),',','%06d'%(self.ctaEngine.interest),',','\033[0;32m%05d\033[0m'%(int((self.SKPRICE- trade.price)*self.A_WEIGHT)) ,',','{:08b}'.format(self.BP_style)[-4:],',','%02d'%(self.tradeday),',','%03d'%(0-trade.volume) 
                    
                    
                #for each in self.SKWeekProfit:
                #    print each,',',  
                #print '\r',                 
            self.SKPRICE = EMPTY_FLOAT_WH   
            self.SKDATE  = EMPTY_FLOAT_WH
            self.tradeday= 0
    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass    
