import time
from apscheduler.schedulers.blocking import BlockingScheduler
from smap import downTools


def job():
    d = downTools()
    d.getFileName()


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    # 在每天22和23点的25分，运行一次 job 方法
    scheduler.add_job(job, 'cron', hour='20-22', minute='34')
    scheduler.start()
