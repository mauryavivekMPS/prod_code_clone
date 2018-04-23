import codecs
import os
import uuid
import humanize
import datetime
import boto3
import chardet
import itertools
from operator import attrgetter
from dateutil.rrule import rrule, MONTHLY
from ivetl.models import SystemGlobal, PipelineStatus, PipelineTaskStatus, AuditLogByUser, AuditLogByPublisher, AuditLogByTime
from ivetl.common import common


def day_range(from_date, to_date):
    """Generates an inclusive range of days. Will use the hour, minute, second from the from_date."""
    for n in range(int((to_date - from_date).days) + 1):
        yield from_date + datetime.timedelta(n)


def month_range(from_date, to_date):
    """Generates an inclusive range of months. Will use day, hour, minute, second from the from_date."""
    return rrule(MONTHLY, dtstart=from_date, until=to_date)


def start_of_quarter(date):
    if date.month < 4:
        return datetime.datetime(date.year, 1, 1)
    elif date.month < 7:
        return datetime.datetime(date.year, 4, 1)
    elif date.month < 10:
        return datetime.datetime(date.year, 7, 1)
    else:
        return datetime.datetime(date.year, 10, 1)


def start_of_previous_quarter(date):
    if date.month < 4:
        return datetime.datetime(date.year - 1, 10, 1)
    elif date.month < 7:
        return datetime.datetime(date.year, 1, 1)
    elif date.month < 10:
        return datetime.datetime(date.year, 4, 1)
    else:
        return datetime.datetime(date.year, 7, 1)


def _get_high_water_key_name(product_id, pipeline_id, publisher_id):
    return '_'.join([product_id, pipeline_id, publisher_id, 'high_water'])


def get_high_water(product_id, pipeline_id, publisher_id):
    try:
        key = _get_high_water_key_name(product_id, pipeline_id, publisher_id)
        return SystemGlobal.objects.get(name=key).date_value
    except SystemGlobal.DoesNotExist:
        return None


def get_from_to_dates_with_high_water(product_id, pipeline_id, publisher_id, from_date, to_date):
    today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)

    if from_date:
        from_date = datetime.datetime.combine(from_date, datetime.time.min)

    if to_date:
        to_date = datetime.datetime.combine(to_date, datetime.time.min)

    if not from_date:
        last_uptime_day_processed = get_high_water(product_id, pipeline_id, publisher_id)
        if not last_uptime_day_processed:
            last_uptime_day_processed = today - datetime.timedelta(2)

        from_date = last_uptime_day_processed

    if from_date > today - datetime.timedelta(1):
        raise ValueError('Invalid date range: The from date must be before yesterday.')

    if not to_date:
        to_date = today - datetime.timedelta(1)

    if to_date < from_date:
        raise ValueError('Invalid date range: The date range must be at least one day.')

    return from_date, to_date


def update_high_water(product_id, pipeline_id, publisher_id, new_high_water_date):
    key = _get_high_water_key_name(product_id, pipeline_id, publisher_id)
    try:
        current_high_water = SystemGlobal.objects(name=key).date_value
    except:
        current_high_water = datetime.datetime.min

    if type(new_high_water_date) is datetime.date:
        new_high_water_date = datetime.datetime.combine(new_high_water_date, datetime.time.min)

    # only update if the new data is more recent
    if new_high_water_date > current_high_water:
        SystemGlobal.objects(name=key).update(date_value=new_high_water_date)


def file_len(file_path, encoding='utf-8'):
    i = 0
    with open(file_path, encoding=encoding) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def list_dir(path, with_lines_and_sizes=False, ignore=[]):
    files = [{'file_name': n} for n in os.listdir(path) if not ignore or ignore and n not in ignore]
    if with_lines_and_sizes:
        for file in files:
            file_path = os.path.join(path, file['file_name'])
            i = 0
            line_count = 0
            encoding = guess_encoding(file_path)
            with codecs.open(file_path, encoding=encoding) as f:
                for i, l in enumerate(f):
                    pass
                line_count = i + 1
            file['line_count'] = line_count
            file['file_size'] = humanize.naturalsize(os.stat(file_path).st_size)
            file['file_id'] = uuid.uuid4()
    return files


def get_most_recent_run(publisher_id, product_id, pipeline_id, status=None):
    all_runs = PipelineStatus.objects.filter(
        publisher_id=publisher_id,
        product_id=product_id,
        pipeline_id=pipeline_id,
    )

    most_recent_run = None
    if all_runs:

        if status:
            filtered_runs = [run for run in all_runs if run.status == status]
        else:
            filtered_runs = all_runs

        date_sorted_runs = sorted(filtered_runs, key=lambda r: r.start_time or datetime.datetime.min, reverse=True)
        most_recent_run = date_sorted_runs[0]

    return most_recent_run


def get_record_count_estimate(publisher_id, product_id, pipeline_id, task_id, default=100000):
    all_tasks = PipelineTaskStatus.objects.filter(publisher_id=publisher_id, product_id=product_id, pipeline_id=pipeline_id)
    all_tasks = [t for t in all_tasks if t.status == 'completed' and t.task_id == task_id]
    if all_tasks:
        sorted_tasks = sorted(all_tasks, key=attrgetter('start_time'), reverse=True)
        recent_task = sorted_tasks[0]
        return recent_task.current_record_count
    else:
        return default


def download_file_from_s3(bucket, key):
    session = boto3.Session(aws_access_key_id=common.AWS_ACCESS_KEY_ID, aws_secret_access_key=common.AWS_SECRET_ACCESS_KEY)
    s3_resource = session.resource('s3')
    if '/' in key:
        local_dir = os.path.join(common.TMP_DIR, bucket, key[:key.rindex('/')])
    else:
        local_dir = os.path.join(common.TMP_DIR, bucket)
    os.makedirs(local_dir, exist_ok=True)
    local_file = os.path.join(common.TMP_DIR, bucket, key)
    s3_resource.meta.client.download_file(bucket, key, local_file)
    return local_file


def download_files_from_s3_dir(bucket, dir_path):
    session = boto3.Session(aws_access_key_id=common.AWS_ACCESS_KEY_ID, aws_secret_access_key=common.AWS_SECRET_ACCESS_KEY)
    s3_resource = session.resource('s3')
    all_keys = [f.key for f in s3_resource.Bucket(bucket).objects.filter(Prefix=dir_path) if f.key != dir_path]
    local_files = []
    for key in all_keys:
        local_file = download_file_from_s3(bucket, key)
        local_files.append(local_file)
    return local_files


def add_audit_log(user_id='system', publisher_id='system', action='', description=''):
    event_time = datetime.datetime.now()

    AuditLogByUser.objects.create(
        user_id=user_id,
        event_time=event_time,
        action=action,
        publisher_id=publisher_id,
        description=description,
    )

    AuditLogByPublisher.objects.create(
        publisher_id=publisher_id,
        event_time=event_time,
        action=action,
        user_id=user_id,
        description=description,
    )

    AuditLogByTime.objects.create(
        month=event_time.strftime('%Y%m'),
        event_time=event_time,
        action=action,
        publisher_id=publisher_id,
        user_id=user_id,
        description=description,
    )


def trim_and_strip_doublequotes(s):
    s = s.strip()
    if s and s[0] == '"' and s[-1] == '"':
        return s[1:-1].strip()
    else:
        return s


def guess_encoding(file_path):
    # this is not a generalized function, it just guesses between UTF-8 and ISO-8859-2
    guess = chardet.detect(open(file_path, 'rb').read()[:100000])['encoding'].lower()
    if guess in ('utf-8', 'ascii', 'iso-8859-1', 'iso-8859-2'):
        return guess
    else:
        raise UnicodeDecodeError(guess, b'', 0, 1, 'Unsupported encoding, must be UTF-8 or ISO-8859-2.')


def lower_first_line(iterator):
    return itertools.chain([next(iterator).lower()], iterator)
