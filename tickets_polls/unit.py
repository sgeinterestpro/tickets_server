"""
filename: unit.py
datetime: 2019-04-23
author: muumlover
"""

from datetime import timedelta, datetime


def get_this_week_start():
    now = datetime.now()
    return now - timedelta(days=now.weekday())


def get_this_week_end():
    now = datetime.now()
    return now + timedelta(days=6 - now.weekday())
