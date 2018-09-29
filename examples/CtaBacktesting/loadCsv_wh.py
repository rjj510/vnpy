# encoding: UTF-8

"""
导入wh导出的CSV历史数据到MongoDB中
"""

from vnpy.trader.app.ctaStrategy.ctaBase import DAILY_DB_NAME
from vnpy.trader.app.ctaStrategy.ctaHistoryData_wh import loadWhCsv


if __name__ == '__main__':
    loadWhCsv('RB9999_1day.csv', DAILY_DB_NAME, 'RB9999')