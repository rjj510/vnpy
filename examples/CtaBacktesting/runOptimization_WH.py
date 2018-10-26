# encoding: UTF-8

"""
展示如何执行参数优化。
"""

from __future__ import division
from __future__ import print_function


from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME, OptimizationSetting,DAILY_DB_NAME



if __name__ == '__main__':
    from vnpy.trader.app.ctaStrategy.strategy.strategyDoubleMaWH import DoubleMaStrategyWh
          
    # 创建回测引擎
    engine = BacktestingEngine()
    
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)
    engine.outputshow=False

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
    
    # 跑优化
    setting = OptimizationSetting()                 # 新建一个优化任务设置对象
    setting.setOptimizeTarget('maxDdPercent')     
  
    
    #setting.addParameter('A_LONG'            , 13    ,34  ,     1)         #{  做多交易均线天数           默认 }  (34-13+1)*(3-1)
    #setting.addParameter('A_DAYS_BK'         , 0     ,3   ,     1)          #{交易线开仓穿越天数 用于买开  默认2 }   
    setting.addParameter('E_LONG'            , 90    ,120 ,      5)          #{   做多趋势均线天数}    115
    setting.addParameter('E_DAYS_LONG'       , 0     ,10   ,     1)          #{ 做多从下到上的天数}    1
    #setting.addParameter('A_DAYS_SP'         , 0     ,3   ,     1)          #{交易线平仓穿越天数 用于卖平   默认2 }         
    #setting.addParameter('A_RATE_BK_MIN'     , 0.1   ,   0.5,   0.2)        #{交易线开仓穿越幅度 用于买开  默认2 }    
    #setting.addParameter('A_RATE_BK_MAX'     , 1.5   ,   3.0,   0.4)        #{交易线开仓穿越幅度 用于买开  默认2 }  
    #setting.addParameter('A_RATE_SP'         , 0.1   ,   1.0,   0.3)        #{交易线平仓穿越幅度 用于卖平  默认1.2}  
    #setting.addParameter('A_LOSS_SP'         , 0.05  ,   0.45,  0.2)        #{    保证金亏损幅度 用于卖平  默认0.45} 
    #setting.addParameter('A_DAY_LOSS'        , 0.5   ,   3.0,   0.5)        #{达到当日最大跌幅度 用于卖平  默认2.3} 
    #setting.addParameter('A_FLAOT_PROFIT'    , 1500  ,  5000,   800)        #{     最大浮盈幅度 用于卖平  默认3200}
    
    
    
    # 性能测试环境：I7-3770，主频3.4G, 8核心，内存16G，Windows 7 专业版
    # 测试时还跑着一堆其他的程序，性能仅供参考
    import time    
    start = time.time()
    
    # 运行单进程优化函数，自动输出结果，耗时：359秒
    #engine.runOptimization(DoubleMaStrategyWh, setting)            
    
    # 多进程优化，耗时：89秒
    engine.runParallelOptimization(DoubleMaStrategyWh, setting)
    
    print(u'耗时：%s' %(time.time()-start))