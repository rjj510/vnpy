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
 
 --------------------------------测试时间：20181129 、 测试周期：全部数据 、测试方向：做多-----------------------
 1、找出全部最优参数
    1-1 
    输入：
    setting.addParameter('BK_A_LOSS_SP'            ,100  ,1500 ,300) 
    setting.addParameter('BK_Volatility'           ,0.1  ,1.5  ,0.3) 
    setting.addParameter('SP_Volatility'           ,0.1  ,1.5  ,0.3)  
    setting.addParameter('BK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,100  ,1500 ,300)     
    输出：	
    {u'BK_Volatility': 0.7, u'BK_A_LOSS_SP': 700, u'SP_Volatility': 0.7, u'BK_A_FLAOT_PROFIT_ALL': 400, u'BK_BEFORE_DAY': 1}	
    134.73	102.59	52.79	788	1.23	-9580.00	-25.09	-9580.00	-25.09	

    1-2
    输入：
    setting.addParameter('BK_A_LOSS_SP'            ,400  ,1000 ,100) 
    setting.addParameter('BK_Volatility'           ,0.5  ,0.9  ,0.1) 
    setting.addParameter('SP_Volatility'           ,0.5  ,0.9  ,0.1) 
    setting.addParameter('BK_BEFORE_DAY'           , 1             ) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,100  ,700 ,100) 
    输出：
    {u'BK_Volatility': 0.7, u'BK_A_LOSS_SP': 700, u'SP_Volatility': 0.7, u'BK_A_FLAOT_PROFIT_ALL': 500, u'BK_BEFORE_DAY': 1}	
    143.87	116.65	51.08	740	1.34	-10870.00	-26.92	-10800.00	-26.79	
    
    1-3
    输入：
    setting.addParameter('BK_A_LOSS_SP'            ,600  ,800 ,50) 
    setting.addParameter('BK_Volatility'           ,0.6  ,0.8  ,0.05) 
    setting.addParameter('SP_Volatility'           ,0.6  ,0.8  ,0.05) 
    setting.addParameter('BK_BEFORE_DAY'           , 1             ) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,400  ,600 ,50)     
    输出：
    {u'BK_Volatility': 0.75, u'BK_A_LOSS_SP': 750, u'SP_Volatility': 0.75, u'BK_A_FLAOT_PROFIT_ALL': 500, u'BK_BEFORE_DAY': 1}	
    154.47	134.32	52.75	690	1.32	-9170.00	-21.48	-8930.00	-20.92	  
    
    1-4
    最优：
    setting.addParameter('BK_A_LOSS_SP'            ,750) 
    setting.addParameter('BK_Volatility'           ,0.75) 
    setting.addParameter('SP_Volatility'           ,0.75) 
    setting.addParameter('BK_BEFORE_DAY'           , 1) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,500)     
    
2、 确定周交易（1-3）
3、 确定周交易后找出全部最优参数：
    3-1 
    输入：
    setting.addParameter('BK_A_LOSS_SP'            ,300  ,1500 ,300) 
    setting.addParameter('BK_Volatility'           ,0.1  ,1.5  ,0.3) 
    setting.addParameter('SP_Volatility'           ,0.1  ,1.5  ,0.3)  
    setting.addParameter('BK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,300  ,1500 ,300)  
    输出：
    {u'BK_Volatility': 0.7, u'BK_A_LOSS_SP': 1200, u'SP_Volatility': 0.7, u'BK_A_FLAOT_PROFIT_ALL': 600, u'BK_BEFORE_DAY': 1}	
    111.23	165.20	50.00	404	1.58	-8020.00	-21.42	-7870.00	-21.10	
    
    3-2 
    输入：
    setting.addParameter('BK_A_LOSS_SP'            ,900  ,1500 ,100) 
    setting.addParameter('BK_Volatility'           ,0.5  ,1.0  ,0.1) 
    setting.addParameter('SP_Volatility'           ,0.5  ,1.0  ,0.1)  
    setting.addParameter('BK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,400  ,800 ,100)       
    输出：
    {u'BK_Volatility': 0.7, u'BK_A_LOSS_SP': 1400, u'SP_Volatility': 1.0, u'BK_A_FLAOT_PROFIT_ALL': 500, u'BK_BEFORE_DAY': 1}	
    129.13	200.73	62.18	386	1.06	-4010.00	-10.56	-3770.00	-9.87	
    
    3-3
    输入:
    setting.addParameter('BK_A_LOSS_SP'            ,1300  ,1500,50  ) 
    setting.addParameter('BK_Volatility'           ,0.6  ,0.8  ,0.05) 
    setting.addParameter('SP_Volatility'           ,0.9  ,1.2  ,0.05)  
    setting.addParameter('BK_BEFORE_DAY'           ,1               ) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,400  ,600  ,50  )       
    输出：
    {u'BK_Volatility': 0.7, u'BK_A_LOSS_SP': 1450, u'SP_Volatility': 1.0, u'BK_A_FLAOT_PROFIT_ALL': 500, u'BK_BEFORE_DAY': 1}	
    129.13	200.73	62.18	386	1.06	-4010.00	-10.56	-3770.00	-9.87	

    3-4
    最优：
    setting.addParameter('BK_A_LOSS_SP'            ,1400) 
    setting.addParameter('BK_Volatility'           ,0.7 ) 
    setting.addParameter('SP_Volatility'           ,1.0 )  
    setting.addParameter('BK_BEFORE_DAY'           ,1   ) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,500 )    
    
4、 测试有否过度拟合

-----------------------------------------------------------------------------------------------------------
--------------------------------测试时间：20181130 、 测试周期：20170103-20181130 、测试方向：做多------------
 1、找出全部最优参数
    1-1 
    输入：
    setting.addParameter('BK_A_LOSS_SP'            ,100  ,1500 ,300) 
    setting.addParameter('BK_Volatility'           ,0.1  ,1.5  ,0.3) 
    setting.addParameter('SP_Volatility'           ,0.1  ,1.5  ,0.3)  
    setting.addParameter('BK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,100  ,1500 ,300)   
    输出：	
    {u'BK_Volatility': 0.7, u'BK_A_LOSS_SP': 1000, u'SP_Volatility': 0.7, u'BK_A_FLAOT_PROFIT_ALL': 400, u'BK_BEFORE_DAY': 1}	
    83.53	301.93	71.08	165	0.86	-3930.00	-8.11	-3530.00	-8.11	


    1-2
    输入：
    setting.addParameter('BK_A_LOSS_SP'            ,700  ,1300 ,200  ) 
    setting.addParameter('BK_Volatility'           ,0.5  ,1.2  ,0.1  ) 
    setting.addParameter('SP_Volatility'           ,0.5  ,1.2  ,0.1  )  
    setting.addParameter('BK_BEFORE_DAY'           ,1                ) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,100  ,700  ,200  )  
    输出：
    {u'BK_Volatility': 0.7, u'BK_A_LOSS_SP': 1300, u'SP_Volatility': 0.9, u'BK_A_FLAOT_PROFIT_ALL': 500, u'BK_BEFORE_DAY': 1}	
    92.87	361.82	72.73	153	0.86	-4760.00	-12.37	-4760.00	-12.37	

    
    1-3
    输入：
    setting.addParameter('BK_A_LOSS_SP'            ,1100  ,1500 ,100  ) 
    setting.addParameter('BK_Volatility'           ,0.6  ,0.8  ,0.05  ) 
    setting.addParameter('SP_Volatility'           ,0.8  ,1.0  ,0.05  )  
    setting.addParameter('BK_BEFORE_DAY'           ,1                ) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,300  ,700  ,100  )    
    输出： 
    {u'BK_Volatility': 0.75, u'BK_A_LOSS_SP': 1300, u'SP_Volatility': 0.9, u'BK_A_FLAOT_PROFIT_ALL': 500, u'BK_BEFORE_DAY': 1}	
    96.10	389.59	72.97	147	0.94	-4760.00	-12.41	-4760.00	-12.41	

    1-4:
    输入：
    setting.addParameter('BK_A_LOSS_SP'            ,1200  ,1400 ,50  ) 
    setting.addParameter('BK_Volatility'           ,0.75 ) 
    setting.addParameter('SP_Volatility'           ,0.9  )  
    setting.addParameter('BK_BEFORE_DAY'           ,1                ) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,400  ,600  ,50  )     
    输出：
    {u'BK_Volatility': 0.75, u'BK_A_LOSS_SP': 1350, u'SP_Volatility': 0.9, u'BK_A_FLAOT_PROFIT_ALL': 550, u'BK_BEFORE_DAY': 1}	
    97.40	400.27	72.60	145	0.97	-4760.00	-12.41	-4760.00	-12.41	

    1-5
    最优：
    setting.addParameter('BK_A_LOSS_SP'            ,1350 ) 
    setting.addParameter('BK_Volatility'           ,0.75 ) 
    setting.addParameter('SP_Volatility'           ,0.9  )  
    setting.addParameter('BK_BEFORE_DAY'           ,1    ) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,550  )     
    
2、 确定周交易（1、2、4、5）
3、 确定周交易后找出全部最优参数：
    3-1 
    输入：
    setting.addParameter('BK_A_LOSS_SP'            ,100  ,1500 ,300) 
    setting.addParameter('BK_Volatility'           ,0.1  ,1.5  ,0.3) 
    setting.addParameter('SP_Volatility'           ,0.1  ,1.5  ,0.3)  
    setting.addParameter('BK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,100  ,1500 ,300)       
    输出：
    {u'BK_Volatility': 0.7, u'BK_A_LOSS_SP': 1300, u'SP_Volatility': 1.3, u'BK_A_FLAOT_PROFIT_ALL': 1300, u'BK_BEFORE_DAY': 1}	
    61.77	500.81	59.46	73	1.41	-3380.00	-7.84	-3070.00	-6.58	

    3-2 
    输入：
    setting.addParameter('BK_A_LOSS_SP'            ,1000  ,1600 ,200) 
    setting.addParameter('BK_Volatility'           ,0.4  ,1.0  ,0.2) 
    setting.addParameter('SP_Volatility'           ,1.0  ,1.6  ,0.2)  
    setting.addParameter('BK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,1000  ,1600 ,200)  
    输出：
    {u'BK_Volatility': 0.6, u'BK_A_LOSS_SP': 1400, u'SP_Volatility': 1.2, u'BK_A_FLAOT_PROFIT_ALL': 1400, u'BK_BEFORE_DAY': 1}	
    79.13	552.09	60.47	85	1.42	-3660.00	-7.17	-3340.00	-5.85	

    
    3-3
    输入:
    setting.addParameter('BK_A_LOSS_SP'            ,1300  ,1500 ,50) 
    setting.addParameter('BK_Volatility'           ,0.6) 
    setting.addParameter('SP_Volatility'           ,1.2)  
    setting.addParameter('BK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,1300  ,1500 ,50)   
    输出：
    {u'BK_Volatility': 0.6, u'BK_A_LOSS_SP': 1300, u'SP_Volatility': 1.2, u'BK_A_FLAOT_PROFIT_ALL': 1400, u'BK_BEFORE_DAY': 1}	
    79.13	552.09	60.47	85	1.42	-3660.00	-7.17	-3340.00	-5.85	

    3-4
    最优：
    setting.addParameter('BK_A_LOSS_SP'            ,1300) 
    setting.addParameter('BK_Volatility'           ,0.6) 
    setting.addParameter('SP_Volatility'           ,1.2)  
    setting.addParameter('BK_BEFORE_DAY'           ,1  ) 
    setting.addParameter('BK_A_FLAOT_PROFIT_ALL'   ,1400) 
    
4、 测试有否过度拟合
    3-4，有严重过度拟合。
    1-5，有轻微过度拟合。
    1-5（只在周1245交易），有轻微过度拟合。

-----------------------------------------------------------------------------------------------------------
-------------------------------测试时间：20181127 、 测试周期：全部数据 、测试方向：做空-----------------------
 1、找出全部最优参数
    1-1 
    输入：
    setting.addParameter('SK_A_LOSS_SP'            ,100  ,1500 ,300) 
    setting.addParameter('SK_Volatility'           ,0.1  ,1.5  ,0.3) 
    setting.addParameter('BP_Volatility'           ,0.1  ,1.5  ,0.3)  
    setting.addParameter('SK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('SK_A_FLAOT_PROFIT_ALL'   ,100  ,1500 ,300)   
    输出：	
    {u'BP_Volatility': 1.3, u'SK_A_LOSS_SP': 1300, u'SK_Volatility': 0.7, u'SK_BEFORE_DAY': 1, u'SK_A_FLAOT_PROFIT_ALL': 1000}	
    104.40	128.36	45.49	487	1.54	-12930.00	-19.21	-12040.00	-18.13	
    
    1-2
    输入：
    setting.addParameter('SK_A_LOSS_SP'            ,1200 ,1800 ,200) 
    setting.addParameter('SK_Volatility'           ,0.4  ,1.1  ,0.2) 
    setting.addParameter('BP_Volatility'           ,1.0  ,1.6  ,0.2)  
    setting.addParameter('SK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('SK_A_FLAOT_PROFIT_ALL'   ,700  ,1300 ,200)  
    输出：
    {u'BP_Volatility': 1.2, u'SK_A_LOSS_SP': 1800, u'SK_Volatility': 0.8, u'SK_BEFORE_DAY': 1, u'SK_A_FLAOT_PROFIT_ALL': 900}	
    86.43	115.76	47.77	448	1.38	-13470.00	-21.06	-12580.00	-20.18	

    1-3
    输入： 
    setting.addParameter('SK_A_LOSS_SP'            ,1100  ,1500 ,100) 
    setting.addParameter('SK_Volatility'           ,0.7  ,1.0  ,0.1) 
    setting.addParameter('BP_Volatility'           ,1.2  ,1.5  ,0.1)  
    setting.addParameter('SK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('SK_A_FLAOT_PROFIT_ALL'   ,700  ,1100 ,100)   
    输出：   
    {u'BP_Volatility': 1.3, u'SK_A_LOSS_SP': 1500, u'SK_Volatility': 0.7, u'SK_BEFORE_DAY': 1, u'SK_A_FLAOT_PROFIT_ALL': 1000}	
    108.70	133.65	45.49	487	1.55	-12930.00	-18.85	-12040.00	-17.78	

    1-4
    输入： 
    setting.addParameter('SK_A_LOSS_SP'            ,1500  ,1800 ,100) 
    setting.addParameter('SK_Volatility'           ,0.5  ,0.7  ,0.1) 
    setting.addParameter('BP_Volatility'           ,1.2  ,1.5  ,0.1)  
    setting.addParameter('SK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('SK_A_FLAOT_PROFIT_ALL'   ,900  ,1100 ,50)   
    输出：   
    {u'BP_Volatility': 1.3, u'SK_A_LOSS_SP': 1500, u'SK_Volatility': 0.7, u'SK_BEFORE_DAY': 1, u'SK_A_FLAOT_PROFIT_ALL': 1000}	
    108.70	133.65	45.49	487	1.55	-12930.00	-18.85	-12040.00	-17.78	
    
    1-5最优
    SK_A_LOSS_SP     = 1500     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.7      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 1.3      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 1        #{波幅的天数                } 
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }  

2、 确定周交易（1、2、3、4）
3、 确定周交易后找出全部最优参数：
    3-1 
    输入：
    setting.addParameter('SK_A_LOSS_SP'            ,100  ,1500 ,300) 
    setting.addParameter('SK_Volatility'           ,0.1  ,1.5  ,0.3) 
    setting.addParameter('BP_Volatility'           ,0.1  ,1.5  ,0.3)  
    setting.addParameter('SK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('SK_A_FLAOT_PROFIT_ALL'   ,100  ,1500 ,300)   
    输出：
    {u'BP_Volatility': 0.4, u'SK_A_LOSS_SP': 400, u'SK_Volatility': 0.4, u'SK_BEFORE_DAY': 1, u'SK_A_FLAOT_PROFIT_ALL': 1000}	
    119.53	107.69	31.83	666	2.89	-10690.00	-17.02	-10690.00	-17.02	
    
    3-2 
    输入：
    setting.addParameter('SK_A_LOSS_SP'            ,100  ,700  ,200) 
    setting.addParameter('SK_Volatility'           ,0.1  ,0.8  ,0.2) 
    setting.addParameter('BP_Volatility'           ,0.1  ,0.7  ,0.2)  
    setting.addParameter('SK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('SK_A_FLAOT_PROFIT_ALL'   ,700  ,1300 ,200)   
    输出：
    {u'BP_Volatility': 0.7, u'SK_A_LOSS_SP': 700, u'SK_Volatility': 0.7, u'SK_BEFORE_DAY': 1, u'SK_A_FLAOT_PROFIT_ALL': 900}	
    114.07	132.12	40.54	518	2.00	-7510.00	-16.11	-6680.00	-16.11
    
    3-3 
    输入：
    setting.addParameter('SK_A_LOSS_SP'            ,300  ,500  ,100) 
    setting.addParameter('SK_Volatility'           ,0.3  ,0.5  ,0.1) 
    setting.addParameter('BP_Volatility'           ,0.3  ,0.5  ,0.1)  
    setting.addParameter('SK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('SK_A_FLAOT_PROFIT_ALL'   ,900  ,1100 ,50) 
    输出：
    {u'BP_Volatility': 0.4, u'SK_A_LOSS_SP': 400, u'SK_Volatility': 0.5, u'SK_BEFORE_DAY': 1, u'SK_A_FLAOT_PROFIT_ALL': 1000}	
    127.10	117.32	32.31	650	2.90	-9240.00	-14.40	-9240.00	-14.40	

    3-4 
    最优：
    SK_A_LOSS_SP     = 400     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.5      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 0.4      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 1        #{波幅的天数                } 
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }     
    
4、 测试有否过度拟合
    3-4 回撤太大,胜率太低。 （在所有、单调上升、单调下降、最近区域内回测）
-----------------------------------------------------------------------------------------------------------
-------------------------------测试时间：20181205 、 测试周期：2017-1-3 --- 20181205  、测试方向：做空-----------------------
 1、找出全部最优参数
    1-1 
    输入：
    setting.addParameter('SK_A_LOSS_SP'            ,100  ,1500 ,300) 
    setting.addParameter('SK_Volatility'           ,0.1  ,1.5  ,0.3) 
    setting.addParameter('BP_Volatility'           ,0.1  ,1.5  ,0.3)  
    setting.addParameter('SK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('SK_A_FLAOT_PROFIT_ALL'   ,100  ,1500 ,300)   
    输出：	
    {u'BP_Volatility': 1.3, u'SK_A_LOSS_SP': 700, u'SK_Volatility': 0.7, u'SK_BEFORE_DAY': 1, u'SK_A_FLAOT_PROFIT_ALL': 400}	
    20.17	75.62	57.50	160	0.87	-10130.00	-24.79	-9430.00	-23.07	

    
    1-2
    输入：
    setting.addParameter('SK_A_LOSS_SP'            ,400  ,1000 ,200) 
    setting.addParameter('SK_Volatility'           ,0.4  ,1.0  ,0.2) 
    setting.addParameter('BP_Volatility'           ,1.0  ,1.6  ,0.2)  
    setting.addParameter('SK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('SK_A_FLAOT_PROFIT_ALL'   ,100  ,700 , 200)   
    输出：
    {u'BP_Volatility': 1.6, u'SK_A_LOSS_SP': 600, u'SK_Volatility': 0.8, u'SK_BEFORE_DAY': 1, u'SK_A_FLAOT_PROFIT_ALL': 100}	
    15.53	62.13	66.67	150	0.60	-6510.00	-17.78	-6510.00	-17.78	


    1-3
    输入： 
    setting.addParameter('SK_A_LOSS_SP'            ,500  ,800 ,100) 
    setting.addParameter('SK_Volatility'           ,0.4  ,1.0  ,0.1) 
    setting.addParameter('BP_Volatility'           ,1.0  ,1.6  ,0.1)  
    setting.addParameter('SK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('SK_A_FLAOT_PROFIT_ALL'   ,100  ,500 , 100)   
    输出：
    {u'BP_Volatility': 1.0, u'SK_A_LOSS_SP': 700, u'SK_Volatility': 0.7, u'SK_BEFORE_DAY': 1, u'SK_A_FLAOT_PROFIT_ALL': 500}	
    22.73	88.57	51.95	154	1.11	-9480.00	-23.29	-8780.00	-21.57	
      
    1-4最优:
    SK_A_LOSS_SP     = 700      #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.7      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 1.0      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 1        #{波幅的天数                } 
    SK_A_FLAOT_PROFIT_ALL=500   #{最佳浮盈                  }  

2、 确定周交易（星期2、3、4）
3、 确定周交易后找出全部最优参数：
    3-1 
    输入：
    setting.addParameter('SK_A_LOSS_SP'            ,100  ,1500 ,300) 
    setting.addParameter('SK_Volatility'           ,0.1  ,1.5  ,0.3) 
    setting.addParameter('BP_Volatility'           ,0.1  ,1.5  ,0.3)  
    setting.addParameter('SK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('SK_A_FLAOT_PROFIT_ALL'   ,100  ,1500 ,300)  
    输出：
    {u'BP_Volatility': 1.0, u'SK_A_LOSS_SP': 700, u'SK_Volatility': 0.1, u'SK_BEFORE_DAY': 1, u'SK_A_FLAOT_PROFIT_ALL': 1000}	
    45.20	276.73	53.06	98	1.39	-5880.00	-15.59	-5880.00	-15.59	

    3-2 
    输入：
    setting.addParameter('SK_A_LOSS_SP'            ,400  ,1000 ,200) 
    setting.addParameter('SK_Volatility'           ,0.1  ,0.4  ,0.1) 
    setting.addParameter('BP_Volatility'           ,0.8  ,1.4  ,0.1)  
    setting.addParameter('SK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('SK_A_FLAOT_PROFIT_ALL'   ,700  ,1300 ,200)  
    输出：
    {u'BP_Volatility': 0.9, u'SK_A_LOSS_SP': 1000, u'SK_Volatility': 0.3, u'SK_BEFORE_DAY': 1, u'SK_A_FLAOT_PROFIT_ALL': 900}	
    43.47	266.12	55.10	98	1.27	-4470.00	-11.58	-4020.00	-10.41	
    
    3-3 
    输入：    
    setting.addParameter('SK_A_LOSS_SP'            ,1000  ,1300 ,50) 
    setting.addParameter('SK_Volatility'           ,0.3) 
    setting.addParameter('BP_Volatility'           ,0.9)  
    setting.addParameter('SK_BEFORE_DAY'           ,1              ) 
    setting.addParameter('SK_A_FLAOT_PROFIT_ALL'   ,800  ,1100 ,50)  
    输出：
    {u'BP_Volatility': 0.9, u'SK_A_LOSS_SP': 1050, u'SK_Volatility': 0.3, u'SK_BEFORE_DAY': 1, u'SK_A_FLAOT_PROFIT_ALL': 1000}	
    51.13	326.38	57.45	94	1.25	-4720.00	-12.22	-4720.00	-12.22	

    3-4 
    最优：  
    SK_A_LOSS_SP     = 1050     #{保证金亏损金额     用于买平}  
    SK_Volatility    = 0.3      #{卖开的开盘价波幅   用于卖开}  
    BP_Volatility    = 0.9      #{买平的成交价波幅   用于买平}  
    SK_BEFORE_DAY    = 1        #{波幅的天数                } 
    SK_A_FLAOT_PROFIT_ALL=1000  #{最佳浮盈                  }     
    
4、 测试有否过度拟合
    3-4 只在测试期内表现不错 ，其他时间回撤太大,胜率太低，收益率太低。 （在所有、单调上升、单调下降、最近区域内回测）
---------------------------------------------------------------------------------------------------------------
"""


from __future__ import division
from __future__ import print_function
from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME, OptimizationSetting,DAILY_DB_NAME
if __name__ == '__main__':
    from vnpy.trader.app.ctaStrategy.strategy.strategy_Volatility_RB import strategy_Volatility_RB
          
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
                
    
    setting.addParameter('SK_A_LOSS_SP'            ,1050) 
    setting.addParameter('SK_Volatility'           ,0.3 ) 
    setting.addParameter('BP_Volatility'           ,0.9 )  
    setting.addParameter('SK_BEFORE_DAY'           ,1   ) 
    setting.addParameter('SK_A_FLAOT_PROFIT_ALL'   ,1000)  
    
            
    # 性能测试环境：I7-3770，主频3.4G, 8核心，内存16G，Windows 7 专业版
    # 测试时还跑着一堆其他的程序，性能仅供参考
    import time    
    start = time.time()
    
    # 运行单进程优化函数，自动输出结果，耗时：359秒
    #engine.runOptimization(DoubleMaStrategyWh, setting)            
    
    # 多进程优化，耗时：89秒
    engine.runParallelOptimization(strategy_Volatility_RB, setting)
    
    print(u'耗时：%s' %(time.time()-start))