"""
filename: unit.py
datetime: 2019-04-23
author: muumlover
"""

from datetime import timedelta, datetime


def date_week_start(date=None):
    """
    给定日期所在结算周的第一天
    :return:
    """
    if date is None:
        date = datetime.now()
    return date - timedelta(days=date.weekday())


def date_week_end(date=None):
    """
    给定日期所在结算周的最后一天
    :return:
    """
    if date is None:
        date = datetime.now()
    return date + timedelta(days=6 - date.weekday())


def date_month_start(date=None):
    """
    给定日期所在结算周的所属月开始的第一天
    :return:
    """
    if date is None:
        date = datetime.now()
    week_end = date_week_end(date)
    if date.month != week_end.month:
        return date_week_start(date)
    first_sunday = date + timedelta(days=7 - (35 + 1 + date.weekday() - date.day) % 7 - date.day)
    return date_week_start(first_sunday)


def date_month_end(date=None):
    """
    给定日期所在结算周的所属月结束的最后一天
    :return:
    """
    if date is None:
        date = datetime.now()
    next_month = datetime(year=date.year, month=date.month + 1, day=date.day)
    return date_month_start(next_month) + timedelta(days=-1)
