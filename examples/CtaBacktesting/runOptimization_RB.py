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
 测试周期：2017年1月3日-2018年11月16日
 1、
    1-1 
    输入：
    setting.addParameter('SK_A_LONG'            , 13    ,34 ,       5) 
    setting.addParameter('SK_A_DAYS_OPEN'       , 0     ,5   ,      2) 
    setting.addParameter('SK_E_LONG'            , 60    ,120 ,      5) 
    setting.addParameter('SK_E_DAYS_LONG'       , 0     ,10   ,     3) 
    输出：	
    {u'SK_A_DAYS_OPEN': 4, u'SK_E_LONG': 70, u'SK_A_LONG': 13, u'SK_E_DAYS_LONG': 6}	
    18.50	504.55	36.36	22	4.08	-2480.00	-7.08	-1700.00	-4.90	

    1-2
    输入：
    setting.addParameter('SK_A_LONG'            , 13    ,20  ,      2) 
    setting.addParameter('SK_A_DAYS_OPEN'       , 3     ,5   ,      1) 
    setting.addParameter('SK_E_LONG'            , 60    ,80  ,      2) 
    setting.addParameter('SK_E_DAYS_LONG'       , 4     ,8  ,       2) 
    输出：
    {u'SK_A_DAYS_OPEN': 5, u'SK_E_LONG': 70, u'SK_A_LONG': 13, u'SK_E_DAYS_LONG': 6}	
    20.90	627.00	40.00	20	4.23	-2680.00	-7.37	-1900.00	-5.34	


    1-3
    输入：
    setting.addParameter('SK_A_LONG'            , 13    ,17  ,      1) 
    setting.addParameter('SK_A_DAYS_OPEN'       , 3     ,5   ,      1) 
    setting.addParameter('SK_E_LONG'            , 68    ,72  ,      1) 
    setting.addParameter('SK_E_DAYS_LONG'       , 5     ,8  ,       1)  
    输出：
    {u'SK_A_DAYS_OPEN': 5, u'SK_E_LONG': 69, u'SK_A_LONG': 13, u'SK_E_DAYS_LONG': 6}	
    20.90	627.00	40.00	20	4.23	-2680.00	-7.37	-1900.00	-5.34	


    1-4
    输入：
    setting.addParameter('SK_A_LONG'            , 13) 
    setting.addParameter('SK_A_DAYS_OPEN'       , 5) 
    setting.addParameter('SK_E_LONG'            , 69) 
    setting.addParameter('SK_E_DAYS_LONG'       , 6) 
    setting.addParameter('SK_A_RATE_MIN'        , 0.1,0.9,0.3) 
    setting.addParameter('SK_A_RATE_MAX'        , 1.2,5.0,0.6) 
    setting.addParameter('SK_A_RATE_SP'         , 0.1,4.0,0.6) 
    输出：
    {u'SK_A_RATE_MAX': 4.8, u'SK_A_LONG': 13, u'SK_A_DAYS_OPEN': 5, u'SK_E_LONG': 69, u'SK_A_RATE_MIN': 0.7, u'SK_A_RATE_SP': 3.7, u'SK_E_DAYS_LONG': 6}	
    18.70	510.00	36.36	22	4.19	-2470.00	-7.27	-2470.00	-6.96	


    1-5
    输入：
    setting.addParameter('SK_A_LONG'            , 13) 
    setting.addParameter('SK_A_DAYS_OPEN'       , 5) 
    setting.addParameter('SK_E_LONG'            , 69) 
    setting.addParameter('SK_E_DAYS_LONG'       , 6) 
    setting.addParameter('SK_A_RATE_MIN'        , 0.5,0.8,0.1) 
    setting.addParameter('SK_A_RATE_MAX'        , 3.0,5.0,0.1) 
    setting.addParameter('SK_A_RATE_SP'         , 3.0,4.0,0.1) 
    输出：
    {u'SK_A_RATE_MAX': 3.7, u'SK_A_LONG': 13, u'SK_A_DAYS_OPEN': 5, u'SK_E_LONG': 69, u'SK_A_RATE_MIN': 0.6, u'SK_A_RATE_SP': 3.0, u'SK_E_DAYS_LONG': 6}	
    20.90	627.00	40.00	20	4.23	-2680.00	-7.37	-1900.00	-5.34	


    1-6
    输入：
    setting.addParameter('SK_A_LONG'            , 13) 
    setting.addParameter('SK_A_DAYS_OPEN'       , 5) 
    setting.addParameter('SK_E_LONG'            , 69) 
    setting.addParameter('SK_E_DAYS_LONG'       , 6) 
    setting.addParameter('SK_A_RATE_MIN'        , 0.5,0.7,0.03) 
    setting.addParameter('SK_A_RATE_MAX'        , 3.6,3.8,0.03) 
    setting.addParameter('SK_A_RATE_SP'         , 2.8,3.2,0.05) 
    输出：
    {u'SK_A_RATE_MAX': 3.78, u'SK_A_LONG': 13, u'SK_A_DAYS_OPEN': 5, u'SK_E_LONG': 69, u'SK_A_RATE_MIN': 0.68, u'SK_A_RATE_SP': 3.2, u'SK_E_DAYS_LONG': 6}	
    20.90	627.00	40.00	20	4.23	-2680.00	-7.37	-1900.00	-5.34	

    1-7
    输入：
    setting.addParameter('SK_A_LONG'            , 13) 
    setting.addParameter('SK_A_DAYS_OPEN'       , 5) 
    setting.addParameter('SK_E_LONG'            , 69) 
    setting.addParameter('SK_E_DAYS_LONG'       , 6) 
    setting.addParameter('SK_A_RATE_MIN'        , 0.65) 
    setting.addParameter('SK_A_RATE_MAX'        , 3.7) 
    setting.addParameter('SK_A_RATE_SP'         , 3.1) 
    setting.addParameter('SK_A_LOSS_SP'         , 0.05,0.45,0.05) 
    setting.addParameter('SK_A_DAY_LOSS'        , 1.0,4.0,1.0) 
    setting.addParameter('SK_A_FLAOT_PROFIT'    , 1000,3000,500) 
    输出：
    {u'SK_A_RATE_MAX': 3.7, u'SK_A_FLAOT_PROFIT': 3000, u'SK_A_LONG': 13, u'SK_A_DAY_LOSS': 2.0, u'SK_A_LOSS_SP': 0.05, u'SK_A_DAYS_OPEN': 5, u'SK_E_DAYS_LONG': 6, u'SK_E_LONG': 69, u'SK_A_RATE_SP': 3.1, u'SK_A_RATE_MIN': 0.65}	
    25.63	769.00	50.00	19	3.86	-1890.00	-5.08	-1140.00	-3.13	

    
    1-8
    输入：
    setting.addParameter('SK_A_LONG'            , 13) 
    setting.addParameter('SK_A_DAYS_OPEN'       , 5) 
    setting.addParameter('SK_E_LONG'            , 69) 
    setting.addParameter('SK_E_DAYS_LONG'       , 6) 
    setting.addParameter('SK_A_RATE_MIN'        , 0.65) 
    setting.addParameter('SK_A_RATE_MAX'        , 3.7) 
    setting.addParameter('SK_A_RATE_SP'         , 3.1) 
    setting.addParameter('SK_A_LOSS_SP'         , 0.05,0.1,0.01) 
    setting.addParameter('SK_A_DAY_LOSS'        , 1.8,2.2,0.1) 
    setting.addParameter('SK_A_FLAOT_PROFIT'    , 2000,4000,500) 
    输出：
    {u'SK_A_RATE_MAX': 3.7, u'SK_A_FLAOT_PROFIT': 3500, u'SK_A_LONG': 13, u'SK_A_DAY_LOSS': 2.2, u'SK_A_LOSS_SP': 0.08, u'SK_A_DAYS_OPEN': 5, u'SK_E_DAYS_LONG': 6, u'SK_E_LONG': 69, u'SK_A_RATE_SP': 3.1, u'SK_A_RATE_MIN': 0.65}	
    25.63	769.00	50.00	19	3.86	-1890.00	-5.08	-1140.00	-3.13	

    
    1-9
    输入：
    setting.addParameter('SK_A_LONG'            , 13) 
    setting.addParameter('SK_A_DAYS_OPEN'       , 5) 
    setting.addParameter('SK_E_LONG'            , 69) 
    setting.addParameter('SK_E_DAYS_LONG'       , 6) 
    setting.addParameter('SK_A_RATE_MIN'        , 0.65) 
    setting.addParameter('SK_A_RATE_MAX'        , 3.7) 
    setting.addParameter('SK_A_RATE_SP'         , 3.1) 
    setting.addParameter('SK_A_LOSS_SP'         , 0.08) 
    setting.addParameter('SK_A_DAY_LOSS'        , 1.7,2.0,05) 
    setting.addParameter('SK_A_FLAOT_PROFIT'    , 2800,3200,100) 
    输出：
    {u'SK_A_RATE_MAX': 3.7, u'SK_A_FLAOT_PROFIT': 2900, u'SK_A_LONG': 13, u'SK_A_DAY_LOSS': 1.7, u'SK_A_LOSS_SP': 0.08, u'SK_A_DAYS_OPEN': 5, u'SK_E_DAYS_LONG': 6, u'SK_E_LONG': 69, u'SK_A_RATE_SP': 3.1, u'SK_A_RATE_MIN': 0.65}	
    25.63	769.00	50.00	19	3.86	-1890.00	-5.08	-1140.00	-3.13	

    
    1-10
    输入：
    setting.addParameter('SK_A_LONG'            , 13) 
    setting.addParameter('SK_A_DAYS_OPEN'       , 5) 
    setting.addParameter('SK_E_LONG'            , 69) 
    setting.addParameter('SK_E_DAYS_LONG'       , 6) 
    setting.addParameter('SK_A_RATE_MIN'        , 0.65) 
    setting.addParameter('SK_A_RATE_MAX'        , 3.7) 
    setting.addParameter('SK_A_RATE_SP'         , 3.1) 
    setting.addParameter('SK_A_LOSS_SP'         , 0.08) 
    setting.addParameter('SK_A_DAY_LOSS'        , 1.7) 
    setting.addParameter('SK_A_FLAOT_PROFIT'    , 2900) 
    setting.addParameter('SK_A_DAYS_CLOSE'      , 0,5,1) 
    输出：
    {u'SK_A_RATE_MAX': 3.7, u'SK_A_FLAOT_PROFIT': 2900, u'SK_A_LONG': 13, u'SK_A_DAY_LOSS': 1.7, u'SK_A_LOSS_SP': 0.08, u'SK_A_DAYS_OPEN': 5, u'SK_E_DAYS_LONG': 6, u'SK_E_LONG': 69, u'SK_A_RATE_SP': 3.1, u'SK_A_DAYS_CLOSE': 0, u'SK_A_RATE_MIN': 0.65}	
    25.63	769.00	50.00	19	3.86	-1890.00	-5.08	-1140.00	-3.13	
    
5、 测试有否过度拟合

6、 使用中
    setting.addParameter('SK_A_LONG'            , 13) 
    setting.addParameter('SK_A_DAYS_OPEN'       , 5) 
    setting.addParameter('SK_E_LONG'            , 69) 
    setting.addParameter('SK_E_DAYS_LONG'       , 6) 
    setting.addParameter('SK_A_RATE_MIN'        , 0.65) 
    setting.addParameter('SK_A_RATE_MAX'        , 3.7) 
    setting.addParameter('SK_A_RATE_SP'         , 3.1) 
    setting.addParameter('SK_A_LOSS_SP'         , 0.08) 
    setting.addParameter('SK_A_DAY_LOSS'        , 1.7) 
    setting.addParameter('SK_A_FLAOT_PROFIT'    , 2900) 
    setting.addParameter('SK_A_DAYS_CLOSE'      , 1) 
"""



from __future__ import division
from __future__ import print_function
from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME, OptimizationSetting,DAILY_DB_NAME
if __name__ == '__main__':
    from vnpy.trader.app.ctaStrategy.strategy.strategyDoubleMaRB import DoubleMaStrategyWh
          
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
  
    setting.addParameter('SK_A_LONG'            , 13) 
    setting.addParameter('SK_A_DAYS_OPEN'       , 5) 
    setting.addParameter('SK_E_LONG'            , 69) 
    setting.addParameter('SK_E_DAYS_LONG'       , 6) 
    setting.addParameter('SK_A_RATE_MIN'        , 0.65) 
    setting.addParameter('SK_A_RATE_MAX'        , 3.7) 
    setting.addParameter('SK_A_RATE_SP'         , 3.1) 
    setting.addParameter('SK_A_LOSS_SP'         , 0.08) 
    setting.addParameter('SK_A_DAY_LOSS'        , 1.7) 
    setting.addParameter('SK_A_FLAOT_PROFIT'    , 2900) 
    setting.addParameter('SK_A_DAYS_CLOSE'      , 1) 

    
    
    
    # 性能测试环境：I7-3770，主频3.4G, 8核心，内存16G，Windows 7 专业版
    # 测试时还跑着一堆其他的程序，性能仅供参考
    import time    
    start = time.time()
    
    # 运行单进程优化函数，自动输出结果，耗时：359秒
    #engine.runOptimization(DoubleMaStrategyWh, setting)            
    
    # 多进程优化，耗时：89秒
    engine.runParallelOptimization(DoubleMaStrategyWh, setting)
    
    print(u'耗时：%s' %(time.time()-start))