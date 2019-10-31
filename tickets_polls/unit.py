"""
filename: unit.py
datetime: 2019-04-23
author: muumlover
"""

from datetime import timedelta, datetime

sport_list = {
    'badminton': [1, 3, 4],
    'basketball': [1, 3],
    'football': list(range(1, 8)),
    'swim': [3, 5],
    'yoga': [4],
}


def get_sport():
    # Todo 修改为系统设置存到数据库
    weekday = datetime.now().isoweekday()
    return {
        k: {
            'enable': weekday in v,
            'message': '' if weekday in v else f'仅限每周{"、".join([str(x) for x in v])}使用'
        }
        for k, v in sport_list.items()
    }


def date_show(date, fmt):
    return datetime.strptime(date, "%Y-%m-%d").strftime(fmt)


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
