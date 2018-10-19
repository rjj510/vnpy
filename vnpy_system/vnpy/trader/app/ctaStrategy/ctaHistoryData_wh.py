# encoding: UTF-8

"""
本模块中主要包含：
1. 将文华财经导出的历史数据载入到MongoDB中用的函数
"""
from __future__ import print_function

import csv
from datetime import datetime, timedelta
from time import time
from struct import unpack

import pymongo

from vnpy.trader.vtGlobal import globalSetting
from vnpy.trader.vtConstant import *
from vnpy.trader.vtObject import VtBarData
from .ctaBase import SETTING_DB_NAME, TICK_DB_NAME, MINUTE_DB_NAME, DAILY_DB_NAME

#----------------------------------------------------------------------
def loadWhCsv(fileName, dbName, symbol):
    """将WH导出的csv格式的历史数据插入到Mongo数据库中"""
    start = time()
    print(u'开始读取CSV文件%s中的数据插入到%s的%s中' %(fileName, dbName, symbol))
    
    # 锁定集合，并创建索引
    print(globalSetting)
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort']) 
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)   
    
    # 读取数据和插入到数据库
    with open(fileName, 'r') as f:
        reader = csv.DictReader(f)
        for d in reader:
            print(d)
            bar = VtBarData()
            bar.vtSymbol = symbol
            bar.symbol = symbol
            bar.open = float(d['open'])
            bar.high = float(d['high'])
            bar.low = float(d['low'])
            bar.close = float(d['close'])
            bar.date = datetime.strptime(d['datetime'], '%Y-%m-%d').strftime('%Y%m%d')
            bar.time = ''
            bar.datetime = datetime.strptime(bar.date, '%Y%m%d')
            bar.volume = d['volume']
    
            flt = {'datetime': bar.datetime}
            collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)  
            print(bar.date, bar.time)
    
    print(u'插入完毕，耗时：%s' % (time()-start))
