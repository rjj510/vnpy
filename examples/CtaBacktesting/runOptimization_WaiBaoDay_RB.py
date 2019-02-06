# encoding: UTF-8

"""
展示如何执行参数优化。

 测试流程
 1、 粗粒度参数筛选（次数控制在1000次以内）
     目的：根据累计收益率、（权益回撤、损益回撤）、胜率，选出1-3个指标最好的参数。参数的顺序代表优先级的由大到小。
 2、 中粒度参数筛选（在第一步的基础上，修改参数范围和步进长度）
     目的：缩小参数范围
 3、 细粒度参数筛选（在第二步的基础上，修改参数范围和步进长度）
     目的：缩小参数范围
 4、 固定一个参数，测试其他的参数. (测试到这个步骤，优化参数可以作为备选方案了)
 5、 测试是否有过度拟合，用strategyShortTerm.py文件中第22行中提到的方法
 
---------------------------------------------------------------------------------------------------------------
"""


from __future__ import division
from __future__ import print_function
from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME, OptimizationSetting,DAILY_DB_NAME
if __name__ == '__main__':
    from vnpy.trader.app.ctaStrategy.strategy.strategy_WaiBaoDay_RB import strategy_WaiBaoDay_RB
          
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
    setting = OptimizationSetting()                 # 新一个优化任务设置对象
    setting.setOptimizeTarget('maxDdPercent')     
                
    

    setting.addParameter('A_LOSS_SP_ALL'           ,0.1,0.4,0.02 )  
    setting.addParameter('A_FLAOT_PROFIT_ALL   '   ,500,3000,100 ) 
            
    # 性能测试环境：I7-3770，主频3.4G, 8核心，内存16G，Windows 7 专业版
    # 测试时还跑着一堆其他的程序，性能仅供参考
    import time    
    start = time.time()
    
    # 运行单进程优化函数，自动输出结果，耗时：359秒
    #engine.runOptimization(DoubleMaStrategyWh, setting)            
    
    # 多进程优化，耗时：89秒
    engine.runParallelOptimization(strategy_WaiBaoDay_RB, setting)
    
    print(u'耗时：%s' %(time.time()-start))