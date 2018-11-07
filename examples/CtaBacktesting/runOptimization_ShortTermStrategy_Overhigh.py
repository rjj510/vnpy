# encoding: UTF-8

"""
展示如何执行参数优化。
"""

from __future__ import division
from __future__ import print_function


from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME, OptimizationSetting,DAILY_DB_NAME

"""
 测试流程
 1、 粗粒度参数筛选（次数控制在1000次以内）
     目的：根据累计收益率、（权益回撤、损益回撤）、胜率，选出1-3个指标最好的参数。参数的顺序代表优先级的由大到小。
 2、 中粒度参数筛选（在第一步的基础上，修改参数范围和步进长度）
     目的：缩小参数范围
 3、 细粒度参数筛选（在第二步的基础上，修改参数范围和步进长度）
     目的：缩小参数范围
 4、 固定一个参数，测试其他的参数. (测试到这个步骤，优化参数可以作为备选方案了)
 5、 测试是否有过度拟合，用strategyShortTerm_Overhigh.py文件中第22行中提到的方法
 20181107
 测试周期：2017年1月4日-2018年11月7日
 1、输入：
    setting.addParameter('Float_Profit_Over_High',500,1500,500)  
    setting.addParameter('A_FLAOT_PROFIT_1',2500,3000,100)  
    setting.addParameter('A_FLAOT_PROFIT_2',3000,4000,100)  
    setting.addParameter('A_LOSS_SP_1'     ,0.1 ,0.3,0.1)   
    setting.addParameter('A_LOSS_SP_2'     ,0.1 ,0.3,0.1)  
    setting.addfilter_greater_than([
                                    ['A_LOSS_SP_1'     ,'A_LOSS_SP_2'],
                                    ['A_FLAOT_PROFIT_1','A_FLAOT_PROFIT_2'],
                                    ['A_FLAOT_PROFIT_1','Float_Profit_Over_High']
                                    ])      
    输出：
    {u'A_FLAOT_PROFIT_2': 2000, u'A_LOSS_SP_2': 0.1, u'A_LOSS_SP_1': 0.2, u'A_FLAOT_PROFIT_1': 2500, u'Float_Profit_Over_High': 500}	
    66.13	1044.21	63.16	38	1.83	-5890.00	-13.07	-2740.00	-5.96	
    
 2、输入：
    setting.addParameter('Float_Profit_Over_High',100,800,200)  
    setting.addParameter('A_FLAOT_PROFIT_1',2000,3000,300)  
    setting.addParameter('A_FLAOT_PROFIT_2',1000,3000,300)  
    setting.addParameter('A_LOSS_SP_1'     ,0.15 ,0.25,0.03)   
    setting.addParameter('A_LOSS_SP_2'     ,0.05 ,0.15,0.03)  
    setting.addfilter_greater_than([
                                    ['A_LOSS_SP_1'     ,'A_LOSS_SP_2'],
                                    ['A_FLAOT_PROFIT_1','A_FLAOT_PROFIT_2'],
                                    ['A_FLAOT_PROFIT_1','Float_Profit_Over_High']
                                    ])      
    输出：
    {u'A_FLAOT_PROFIT_2': 1600, u'A_LOSS_SP_2': 0.05, u'A_LOSS_SP_1': 0.21, u'A_FLAOT_PROFIT_1': 2600, u'Float_Profit_Over_High': 500}	
    74.33	1173.68	68.42	38	1.64	-4240.00	-9.24	-2740.00	-4.98	
    
 3、输入：
    setting.addParameter('Float_Profit_Over_High',100,600,50)  
    setting.addParameter('A_FLAOT_PROFIT_1',2500,2800,50)  
    setting.addParameter('A_FLAOT_PROFIT_2',1500,1800,50)  
    setting.addParameter('A_LOSS_SP_1'     ,0.2)   
    setting.addParameter('A_LOSS_SP_2'     ,0.03)   
    setting.addfilter_greater_than([
                                    ['A_LOSS_SP_1'     ,'A_LOSS_SP_2'],
                                    ['A_FLAOT_PROFIT_1','A_FLAOT_PROFIT_2'],
                                    ['A_FLAOT_PROFIT_1','Float_Profit_Over_High']
                                    ])      
    输出：    
    {u'A_FLAOT_PROFIT_2': 1600, u'A_LOSS_SP_2': 0.03, u'A_LOSS_SP_1': 0.2, u'A_FLAOT_PROFIT_1': 2550, u'Float_Profit_Over_High': 500}	
    76.10	1201.58	68.42	38	1.74	-4240.00	-9.24	-2210.00	-4.79	


 4、
    4-1输入：
    setting.addParameter('Float_Profit_Over_High',500)  
    setting.addParameter('A_FLAOT_PROFIT_1',2550)  
    setting.addParameter('A_FLAOT_PROFIT_2',1600)  
    setting.addParameter('A_LOSS_SP_1'     ,0.15,0.25,0.01)   
    setting.addParameter('A_LOSS_SP_2'     ,0.01,0.08,0.01)     
    setting.addfilter_greater_than([
                                    ['A_LOSS_SP_1'     ,'A_LOSS_SP_2'],
                                    ['A_FLAOT_PROFIT_1','A_FLAOT_PROFIT_2'],
                                    ['A_FLAOT_PROFIT_1','Float_Profit_Over_High']
                                    ])      
    4-1输出： 
    {u'A_FLAOT_PROFIT_2': 1600, u'A_LOSS_SP_2': 0.01, u'A_LOSS_SP_1': 0.19, u'A_FLAOT_PROFIT_1': 2550, u'Float_Profit_Over_High': 500}	
    76.73	1211.58	68.42	38	1.75	-4100.00	-8.93	-2210.00	-4.77	

 
    4-2输入：
    setting.addParameter('E_LONG'     ,5,20,1)       
    setting.addParameter('Float_Profit_Over_High',500)  
    setting.addParameter('A_FLAOT_PROFIT_1',2550)  
    setting.addParameter('A_FLAOT_PROFIT_2',1600)  
    setting.addParameter('A_LOSS_SP_1'     ,0.19)   
    setting.addParameter('A_LOSS_SP_2'     ,0.01)   
    setting.addfilter_greater_than([
                                    ['A_LOSS_SP_1'     ,'A_LOSS_SP_2'],
                                    ['A_FLAOT_PROFIT_1','A_FLAOT_PROFIT_2'],
                                    ['A_FLAOT_PROFIT_1','Float_Profit_Over_High']
                                    ])         
    4-2输出：    
    {u'A_FLAOT_PROFIT_2': 1600, u'A_LOSS_SP_2': 0.01, u'A_LOSS_SP_1': 0.19, u'A_FLAOT_PROFIT_1': 2550, u'Float_Profit_Over_High': 500, u'E_LONG': 15}	
    76.73	1211.58	68.42	38	1.75	-4100.00	-8.93	-2210.00	-4.77	




5、 测试有否过度拟合   

6、  使用中
    setting.addParameter('Float_Profit_Over_High',500)  
    setting.addParameter('A_FLAOT_PROFIT_1',2550)  
    setting.addParameter('A_FLAOT_PROFIT_2',1600)  
    setting.addParameter('A_LOSS_SP_1'     ,0.19)   
    setting.addParameter('A_LOSS_SP_2'     ,0.01)   
    setting.addParameter('E_LONG'          ,15)   
    

"""


if __name__ == '__main__':
    from vnpy.trader.app.ctaStrategy.strategy.strategyShortTerm_Overhigh import ShortTermStrategy_Overhigh
          
    # 创建回测引擎
    engine = BacktestingEngine()
    
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)

    # 设置回测用的数据起始日期，注意：strategyShortTerm_Overhigh策略该值设置为第一天计算的日期，
    # 需要根据日期直接修改strategyShortTerm_Overhigh.py中class ShortTermStrategy_Overhigh的strategyStartpos值
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
  

    setting.addParameter('E_LONG'     ,5,20,1)       
    setting.addParameter('Float_Profit_Over_High',500)  
    setting.addParameter('A_FLAOT_PROFIT_1',2550)  
    setting.addParameter('A_FLAOT_PROFIT_2',1600)  
    setting.addParameter('A_LOSS_SP_1'     ,0.19)   
    setting.addParameter('A_LOSS_SP_2'     ,0.01)   
    setting.addfilter_greater_than([\
                                    ['A_LOSS_SP_1'     ,'A_LOSS_SP_2'],\
                                    ['A_FLAOT_PROFIT_1','A_FLAOT_PROFIT_2'],\
                                    ['A_FLAOT_PROFIT_1','Float_Profit_Over_High']\
                                    ])   
    
        
#    setting.addParameter('A_LOSS_SP'         ,  0.26)      #{    保证金亏损幅度 用于卖平  默认0.45} 
#    setting.addParameter('A_FLAOT_PROFIT'    ,  2400)      #{    最大浮盈幅度 用于卖平  默认3200  }
#    setting.addParameter('Float_Profit_Over_High'            ,  500)        #{   做多趋势均线天数}    115  
#    setting.addParameter('E_LONG'            ,  13) 

#    setting.addParameter('SK_A_LOSS_SP'         ,  0.1,0.5,0.2)     #{    保证金亏损幅度 用于卖平  默认0.45} 
#    setting.addParameter('SK_A_FLAOT_PROFIT'    ,  2000,4000,1000)      #{    最大浮盈幅度 用于卖平  默认3200  }
#    setting.addParameter('SK_E_LONG'            ,  5  ,15  , 4)      #{    做多趋势均线天数}    115  
        
#    setting.addParameter('SK_A_LOSS_SP'         ,  0.35)     #{    保证金亏损幅度 用于卖平  默认0.45} 
#    setting.addParameter('SK_A_FLAOT_PROFIT'    ,  3000)      #{    最大浮盈幅度 用于卖平  默认3200  }
#    setting.addParameter('SK_E_LONG'            ,  5)      #{    做多趋势均线天数}    115  

    
    # 性能测试环境：I7-3770，主频3.4G, 8核心，内存16G，Windows 7 专业版
    # 测试时还跑着一堆其他的程序，性能仅供参考
    import time    
    start = time.time()
    
    # 运行单进程优化函数，自动输出结果，耗时：359秒
    #engine.runOptimization(ShortTermStrategy_Overhigh, setting)            
    
    # 多进程优化，耗时：89秒
    engine.runParallelOptimization(ShortTermStrategy_Overhigh, setting)
    
    print(u'耗时：%s' %(time.time()-start))