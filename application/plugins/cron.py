"""
CronJobs
"""
#pylint: disable=too-many-arguments
import os
from datetime import datetime, timedelta
import click
from mongoengine.errors import DoesNotExist

from application import app, cron_register
from application.modules.debug import ColorCodes as CC
from application.models.cron import CronStats, CronGroup

@app.cli.group(name='cron')
def _cli_cron():
    """Cron Jobs"""

def get_stats(group):
    """
    Return Stats Object
    """
    try:
        return CronStats.objects.get(group=group)
    except DoesNotExist:
        new = CronStats()
        new.group = group
        new.next_run = None
        new.last_start = None
        return new


def calc_next_run(job, last_start):
    """
    Calculate next run of Job
    """
    now = datetime.now()
    current_hour = now.hour

    t_from = int(job.timerange_from)
    t_to = int(job.timerange_to)


    if not last_start and  t_from <= current_hour <= t_to:
        # Job is currently and range, but was never started
        return now - timedelta(minutes=1)


    if t_from <= current_hour <= t_to:
        # We are in Timerange, but job was running already,
        # so add minutes to the next interval
        minutes = False
        hours = False
        days = False
        interval = job.interval
        if interval == '10min':
            minutes = 10
        elif interval == 'hour':
            hours = 1
        elif interval == 'daily':
            days = 1

        if minutes:
            return last_start + timedelta(minutes=minutes)
        if days:
            return last_start + timedelta(days=days)
        if hours:
            return last_start + timedelta(hours=hours)
    return now

def in_timerange(job):
    """
    Check if Job is in timerange to run
    """
    now = datetime.now()
    current_hour = now.hour
    t_from = int(job.timerange_from)
    t_to = int(job.timerange_to)
    if t_from <= current_hour <= t_to:
        return True
    return False

def calc_next_possible_run(job):
    """
    Return the next full time in allowd timerange
    """
    now = datetime.now()
    current_hour = now.hour
    t_from = int(job.timerange_from)
    if current_hour >= t_from:
        # Next is tomorrw
        return datetime.strptime(f"{now.day+1:02d}.{now.month:02d}.{now.year} {t_from:02d}:00", "%d.%m.%Y %H:%M")
    else:
        # Still today
        return datetime.strptime(f"{now.day:02d}.{now.month:02d}.{now.year} {t_from:02d}:00", "%d.%m.%Y %H:%M")



@_cli_cron.command('run_jobs')
def run_jobs(): #pylint: disable=invalid-name
    """
    Run all configured Jobs
    """
    now = datetime.now()
    for job in CronGroup.objects(enabled=True):
        stats = get_stats(job.name)

        if not stats.next_run:
            stats.next_run = calc_next_run(job, stats.last_start)
            stats.save()
        if not stats.is_running and stats.next_run <= now + timedelta(minutes=1):
            if not in_timerange(job):
                stats.next_run = calc_next_possible_run(job)
                stats.save()
                continue
            print('-------------------------------------------------------------')
            print(f"{CC.HEADER} Running Group {job.name} {CC.ENDC}")
            stats.is_running = True
            stats.last_start = now
            stats.failure = False
            stats.save()
            for task in job.jobs:
                print(f"{CC.UNDERLINE}{CC.OKBLUE}Task: {task.name} {CC.ENDC}")
                stats.last_message = f"{now}: Started {task.name} (PID: {os.getpid()})"
                stats.save()
                try:
                    if task.account:
                        account_name = task.account.name
                        cron_register[task.command](account=account_name)
                    else:
                        cron_register[task.command]()
                except Exception as exp:
                    stats.is_running = False
                    stats.failure = True
                    stats.last_ended = None
                    stats.last_message = str(exp)
                    stats.save()
                    # Don't Catch any exceptions. If for example the Import breaks,
                    # there should no export of deletion of hosts
                    raise

            stats.last_ended = datetime.now()
            stats.next_run = calc_next_run(job, stats.last_start)
            stats.is_running = False
            stats.save()
