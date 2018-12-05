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
 20181107 
 测试周期：2017年1月4日-2018年11月7日
 1、输入：
    setting.addParameter('A_LOSS_SP'         ,  0.1,0.5,0.2)     #{    保证金亏损幅度 用于卖平  默认0.45} 
    setting.addParameter('A_FLAOT_PROFIT'    ,  2000,4000,500)      #{    最大浮盈幅度 用于卖平  默认3200  }
    setting.addParameter('E_LONG'            ,  5  ,13  , 4)      #{    做多趋势均线天数}    115  
    输出：	
    1-1 {u'E_LONG': 13, u'A_LOSS_SP': 0.1, u'A_FLAOT_PROFIT': 3000}	
    37.23	930.83	41.67	24	4.32	-3710.00	-10.17	-2530.00	-7.09	

    1-2 {u'E_LONG': 13, u'A_LOSS_SP': 0.3, u'A_FLAOT_PROFIT': 2000}	
    35.83	1075.00	70.00	20	1.28	-3790.00	-9.44	-1910.00	-4.60	

    1-3 {u'E_LONG': 13, u'A_LOSS_SP': 0.1, u'A_FLAOT_PROFIT': 2000}	
    34.60	865.00	50.00	24	3.32	-2640.00	-7.15	-1310.00	-3.57	

 2、输入：
    setting.addParameter('A_LOSS_SP'         ,  0.1,0.3,0.1)     #{    保证金亏损幅度 用于卖平  默认0.45} 
    setting.addParameter('A_FLAOT_PROFIT'    ,  2000,3000,100)      #{    最大浮盈幅度 用于卖平  默认3200  }
    setting.addParameter('E_LONG'            ,  10  ,13  , 1)      #{    做多趋势均线天数}    115  
    
    输出：
    {u'E_LONG': 13, u'A_LOSS_SP': 0.2, u'A_FLAOT_PROFIT': 2900}	
    42.37	1271.00	60.00	20	2.11	-3550.00	-8.92	-1910.00	-4.28	

    
 3、输入：
    setting.addParameter('A_LOSS_SP'         ,  0.15,0.25,0.01)     #{    保证金亏损幅度 用于卖平  默认0.45} 
    setting.addParameter('A_FLAOT_PROFIT'    ,  2800,3000,50)      #{    最大浮盈幅度 用于卖平  默认3200  }
    setting.addParameter('E_LONG'            ,  10  ,13  , 1)      #{    做多趋势均线天数}    115  
    输出：    
    {u'E_LONG': 13, u'A_LOSS_SP': 0.19, u'A_FLAOT_PROFIT': 2950}	
    50.47	1514.00	60.00	20	2.39	-3550.00	-8.55	-1910.00	-4.06	
    
5、 测试有否过度拟合

6、 使用中
    setting.addParameter('A_LOSS_SP'         ,  0.19)      #{    保证金亏损幅度 用于卖平  默认0.45} 
    setting.addParameter('A_FLAOT_PROFIT'    ,  2950)      #{    最大浮盈幅度 用于卖平  默认3200  }
    setting.addParameter('E_LONG'            ,  13  )      #{    做多趋势均线天数}    115  
"""

from __future__ import division
from __future__ import print_function


from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME, OptimizationSetting,DAILY_DB_NAME



if __name__ == '__main__':
    from vnpy.trader.app.ctaStrategy.strategy.strategyShortTerm import ShortTermStrategy
          
    # 创建回测引擎
    engine = BacktestingEngine()
    
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)

    # 设置回测用的数据起始日期，注意：strategyShortTerm策略该值设置为第一天计算的日期，
    # 需要根据日期直接修改strategyShortTerm.py中class ShortTermStrategy的strategyStartpos值
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
  
    
#    setting.addParameter('A_LOSS_SP_ALL'         ,  0.1,0.5,0.1)    
#    setting.addParameter('A_FLAOT_PROFIT_ALL'    ,  1900,3000,300)     
#    setting.addParameter('A_MIN_UP_ALL'           ,  0.9,1.5,0.01)      

        


    setting.addParameter('SK_A_LOSS_SP_ALL'         ,  0.37)    
    setting.addParameter('SK_A_FLAOT_PROFIT_ALL'    ,  1450)     
    setting.addParameter('A_MIN_DOWN_ALL'           ,  0.9)   
        


    
    # 性能测试环境：I7-3770，主频3.4G, 8核心，内存16G，Windows 7 专业版
    # 测试时还跑着一堆其他的程序，性能仅供参考
    import time    
    start = time.time()
    
    # 运行单进程优化函数，自动输出结果，耗时：359秒
    #engine.runOptimization(DoubleMaStrategyWh, setting)            
    
    # 多进程优化，耗时：89秒
    engine.runParallelOptimization(ShortTermStrategy, setting)
    
    print(u'耗时：%s' %(time.time()-start))