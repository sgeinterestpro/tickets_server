"""
filename: u_task.py
datetime: 2019-05-29
author: muumlover
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tasks import expiry


def setup_task(app):
    scheduler = AsyncIOScheduler({
        'apscheduler.jobstores.mongo': {
            'type': 'mongodb'
        }
    })
    scheduler.start()
    app['task'] = scheduler
    app['tasks'] = {}
    expiry_job = scheduler.add_job(expiry, 'cron', hour='0,1', args=[app], id='expiry')  # 每天0点处理1点处理遗漏
    app['tasks'].update({'expiry': expiry_job})
