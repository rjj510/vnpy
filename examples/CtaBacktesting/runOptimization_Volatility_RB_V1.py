# encoding: UTF-8

from __future__ import division
from __future__ import print_function
from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME, OptimizationSetting,DAILY_DB_NAME
if __name__ == '__main__':
    from vnpy.trader.app.ctaStrategy.strategy.strategy_Volatility_RB_V1 import strategy_Volatility_RB_V1
          
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
                
    setting.addParameter('TEMP',1,29,1)     
    
    #setting.addParameter('BK_A_LOSS_SP',500,1800,100)     
    #setting.addParameter('SK_A_LOSS_SP',500,1800,100)  
    
    #setting.addParameter('BK_BEFORE_DAY',1,4,1)     
    #setting.addParameter('SP_BEFORE_DAY',1,4,1)   
    
    #setting.addParameter('SK_BEFORE_DAY',1,4,1)     
    #setting.addParameter('BP_BEFORE_DAY',1,4,1)     
    
    #setting.addParameter('BK_Volatility',0.1,1.5,0.1)     
    #setting.addParameter('SP_Volatility',0.1,1.5,0.1)  
    
    #setting.addParameter('SK_Volatility',0.1,1.5,0.1)      
    #setting.addParameter('BP_Volatility',0.1,1.5,0.1)  

    #setting.addParameter('BK_A_FLAOT_PROFIT_ALL',300,1800,100)     
    #setting.addParameter('SK_A_FLAOT_PROFIT_ALL',300,1800,100)      
    
    #setting.addParameter('Trend_DAYS',100,400,10)      
    #setting.addParameter('ma',13,34,2)        
    
    #setting.addParameter('BK_A_LOSS_SP_RATIO',0.3,1.3,0.1)      
    #setting.addParameter('SK_A_LOSS_SP_RATIO',0.3,1.3,0.1)      

    #setting.addParameter('BK_Volatility_RATIO',0.3,1.3,0.1)         
    #setting.addParameter('SP_Volatility_RATIO',0.3,1.3,0.1)      
    
    #setting.addParameter('SK_Volatility_RATIO',0.3,1.3,0.1)        
    #setting.addParameter('BP_Volatility_RATIO',0.3,1.3,0.1)     
    
    #setting.addParameter('BK_A_FLAOT_PROFIT_ALL_RATIO',0.7,2,0.1)      
    #setting.addParameter('SK_A_FLAOT_PROFIT_ALL_RATIO',0.7,2,0.1)      
            
            
    # 性能测试环境：I7-3770，主频3.4G, 8核心，内存16G，Windows 7 专业版
    # 测试时还跑着一堆其他的程序，性能仅供参考
    import time    
    start = time.time()
    
    # 运行单进程优化函数，自动输出结果，耗时：359秒
    #engine.runOptimization(DoubleMaStrategyWh, setting)            
    
    # 多进程优化，耗时：89秒
    engine.runParallelOptimization(strategy_Volatility_RB_V1, setting)
    
    print(u'耗时：%s' %(time.time()-start))
'''
from __future__ import division
from __future__ import print_function
from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME, OptimizationSetting_GA,DAILY_DB_NAME
from vnpy.trader.app.ctaStrategy.strategy.strategy_Volatility_RB_V1 import strategy_Volatility_RB_V1
from datetime import datetime

if __name__ == "__main__":
    engine = BacktestingEngine()
    
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)
    engine.outputshow=True


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
    
    engine.add_strategy(strategy_Volatility_RB_V1, {})

    setting = OptimizationSetting_GA()
    setting.set_target('profitrate') 
    
    #setting.add_parameter('BK_A_LOSS_SP'   ,1400) 
    setting.add_parameter('BK_Volatility'   ,0.5,1.0,0.1) 
    setting.add_parameter('SP_Volatility'   ,0.5,1.0,0.1) 
    #setting.add_parameter('BK_A_FLAOT_PROFIT_ALL'   ,600) 
    
    #setting.add_parameter('SK_A_LOSS_SP'   ,900) 
    setting.add_parameter('SK_Volatility'   ,0.3,1.5,0.1) 
    setting.add_parameter('BP_Volatility'   ,0.3,1.5,0.1) 
    setting.add_parameter('SK_BEFORE_DAY'   ,3,5,1) 
    setting.add_parameter('BP_BEFORE_DAY'   ,3,5,1) 
    #setting.add_parameter('SK_A_FLAOT_PROFIT_ALL'   ,1000)   
    

    #setting.add_parameter('Trend_DAYS'      ,380) 
    #setting.add_parameter('ma'              ,16)     
    

    setting.add_parameter('SK_A_FLAOT_PROFIT_ALL_RATIO' ,1,2.5,0.1)        

    print (engine.run_ga_optimization(setting))
'''