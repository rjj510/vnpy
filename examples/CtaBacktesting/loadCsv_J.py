# encoding: UTF-8

"""
导入wh导出的CSV历史数据到MongoDB中
"""

from vnpy.trader.app.ctaStrategy.ctaBase import DAILY_DB_NAME
from vnpy.trader.app.ctaStrategy.ctaHistoryData_wh import loadWhCsv


if __name__ == '__main__':
    loadWhCsv(u'F:\\uiKLine\\data\\dailydata\\J9999_increment.csv', DAILY_DB_NAME, 'J9999')
    #loadWhCsv(u'F:\\uiKLine\\data\\dailydata\\J9999.csv', DAILY_DB_NAME, 'J9999')