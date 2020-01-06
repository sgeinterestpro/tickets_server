"""
filename: unit.py
datetime: 2019-04-23
author: muumlover
"""

from datetime import timedelta, datetime

sport_list = {
    'badminton': [2, 4, 5],
    'basketball': [2, 4],
    'football': [1, 2, 3, 4, 5],
    'swim': [3, 5],
    'yoga': [4],
}


def get_sport():
    # Todo 修改为系统设置存到数据库
    weekday = datetime.now().isoweekday()
    return {
        k: {
            'enable': weekday in v,
            'message': '今日可使用' if weekday in v else f'仅限每周{",".join([str(x) for x in v])}使用'
        }
        for k, v in sport_list.items()
    }


def date_fmt_conv(date, fmt_from="%Y-%m-%d", fmt_to="%Y-%m-%d"):
    return datetime.strptime(date, fmt_from).strftime(fmt_to)


def date_week_start(date=None):
    """
    给定日期所在结算周的第一天
    :return:
    """
    if date is None:
        date = datetime.now()
    return date - timedelta(
        days=date.weekday(),
        hours=date.hour,
        minutes=date.minute,
        seconds=date.second,
        microseconds=date.microsecond
    )


def date_week_end(date=None):
    """
    给定日期所在结算周的最后一天
    :return:
    """
    if date is None:
        date = datetime.now()
    return date + timedelta(
        days=6 - date.weekday(),
        hours=23 - date.hour,
        minutes=59 - date.minute,
        seconds=59 - date.second,
        microseconds=-date.microsecond
    )


def date_month_start(date=None):
    """
    给定日期所在结算周的所属月开始的第一天
    某周日所在自然月即认定为某周所在的自然月
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
    date = date_week_end(date)
    if date.month < 12:
        next_month = datetime(year=date.year, month=date.month + 1, day=15)
    else:
        next_month = datetime(year=date.year + 1, month=1, day=15)
    return date_month_start(next_month) + timedelta(days=-1, hours=23, minutes=59, seconds=59)


if __name__ == '__main__':
    date_test = None
    date_test = datetime(year=2019, month=12, day=20)
    print(date_week_start(date_test))
    print(date_week_end(date_test))
    print(date_month_start(date_test))
    print(date_month_end(date_test))
