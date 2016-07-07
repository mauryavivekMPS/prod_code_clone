import datetime
from ivetl.models import SystemGlobal


def date_range(from_date, to_date):
    for n in range(int((to_date - from_date).days) + 1):
        yield from_date + datetime.timedelta(n)


def get_from_to_dates_with_high_water(from_date, to_date, pipeline_id):
    today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)

    if from_date:
        from_date = datetime.datetime.combine(from_date, datetime.time.min)

    if to_date:
        to_date = datetime.datetime.combine(to_date, datetime.time.min)

    if not from_date:
        try:
            # get last processed day
            last_uptime_day_processed = SystemGlobal.objects.get(name=pipeline_id + '_high_water').date_value
        except SystemGlobal.DoesNotExist:
            # default to two days ago
            last_uptime_day_processed = today - datetime.timedelta(2)

        from_date = last_uptime_day_processed

    if from_date > today - datetime.timedelta(1):
        raise ValueError('Invalid date range: The from date must be before yesterday.')

    if not to_date:
        to_date = today - datetime.timedelta(1)

    if to_date < from_date:
        raise ValueError('Invalid date range: The date range must be at least one day.')

    return from_date, to_date


def update_high_water(pipeline_id, new_high_water_date):
    try:
        current_high_water = SystemGlobal.objects(name=pipeline_id + '_high_water').date_value
    except:
        current_high_water = datetime.datetime.min

    if type(new_high_water_date) is datetime.date:
        new_high_water_date = datetime.datetime.combine(new_high_water_date, datetime.time.min)

    # only update if the new data is more recent
    if new_high_water_date > current_high_water:
        SystemGlobal.objects(name=pipeline_id + '_high_water').update(date_value=new_high_water_date)


def file_len(file_path, encoding='utf-8'):
    i = 0
    with open(file_path, encoding=encoding) as f:
        for i, l in enumerate(f):
            pass
    return i + 1
