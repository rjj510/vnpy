# encoding: UTF-8

"""
展示如何执行策略回测。
"""

from __future__ import division

import os

import vnpy.trader.app.ctaStrategy.ctaBacktesting as cta
#from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME,DAILY_DB_NAME
import vnpy.trader.app.ctaStrategy.strategy.strategy_Volatility_RB_V1 as VRB1
#----------------------------------------------------------------------
#def calculateDailyResult_init(showtrade,long_or_short):
def calculateDailyResult_init(showtrade,capital,size,paralist):
    """主函数，供其他python程序进行模块化程序初始化调用"""
    reload(VRB1)
    reload(cta)
    # 创建回测引擎
    engine = cta.BacktestingEngine()
    
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)
    
    # 设置产品相关参数
    engine.setSlippage(0)      # 股指1跳
    engine.setRate(0)          # 万0.3
    engine.setSize(10)         # 股指合约大小 
    engine.setPriceTick(1)     # 股指最小价格变动
    engine.setCapital(capital)
    
    
    # 在引擎中创建策略对象
    d = {}
    engine.initStrategy(VRB1.strategy_Volatility_RB_V1, d)
    engine.strategy.showtrade=showtrade
    engine.strategy.A_WEIGHT=size
    #engine.strategy.setparalist(paralist)
    #engine.strategy.LongOrShort=long_or_short
    return engine

#----------------------------------------------------------------------
'''根据计算每日结果，输出到CSV中'''
def calculateDailyResult_to_CSV(engine,start_date,start_pos,end_date,end_pos,csvfile,HYNAME,HYSTARTDATE):
    """主函数，供其他python程序进行模块化程序调用"""    
    # 设置回测用的数据起始日期
    engine.setStartDate(HYSTARTDATE)
    engine.strategy.strategyStartpos = start_pos
    engine.strategy.strategyEndpos   = end_pos
    
    # 设置使用的历史数据库
    engine.setDatabase(cta.DAILY_DB_NAME, HYNAME)
    
    os.system('cls')
    # 开始跑回测
    engine.runBacktesting()
    
    # 显示回测结果到CSV中 用于在K线上显示交易信号
    df= engine.calculateDailyResult_to_CSV(csvfile)    
  
    # 显示回测结果  用于文华的ctrl+G的快捷键功能
    print(HYNAME+u" 波幅率交易系统")
    print('start date:'+start_date)
    print('end   date:'+end_date)      
    engine.showBacktestingResultLikeWH_V1(df)
#----------------------------------------------------------------------
'''获得策略需要的初始化时间'''
def get_strategy_init_days(engine):
    return engine.strategy.BK_BEFORE_DAY
        
#----------------------------------------------------------------------
'''获得策略SK_E_LONG'''
def get_strategy_SK_E_LONG(engine):
    return engine.strategy.SK_E_LONG    

#----------------------------------------------------------------------
'''获得策略SK_A_LONG'''
def get_strategy_SK_A_LONG(engine):
    return engine.strategy.SK_A_LONG    

if __name__ == '__main__' :
    #or  __name__ == 'runBacktesting_WH':
    reload(VRB1)
    # 创建回测引擎
    engine = cta.BacktestingEngine()
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)

    # 设置回测用的数据起始日期
    engine.setStartDate('20090327')
    
    # 设置产品相关参数
    engine.setSlippage(0)      # 股指1跳
    engine.setRate(0)          # 万0.3
    engine.setSize(10)         # 股指合约大小 
    engine.setPriceTick(1)     # 股指最小价格变动
    engine.setCapital(30000)
    
    # 设置使用的历史数据库
    engine.setDatabase(DAILY_DB_NAME, 'RB9999')
    
    # 在引擎中创建策略对象
    d = {}
    engine.initStrategy(VRB1.strategy_Volatility_RB_V1, d)
    # 开始跑回测
    engine.runBacktesting()
    
    # 计算回测结果
    engine.calculateBacktestingResult()
    # 显示回测结果  
    engine.showBacktestingResult()