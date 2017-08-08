import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ivetl.models import AuditLogByTime, User


@login_required
def show(request):

    # get all of the logs for the previous 3 months
    now = datetime.datetime.now()
    month_minus_1 = datetime.datetime(now.year, now.month, 1) - datetime.timedelta(days=1)
    month_minus_2 = datetime.datetime(month_minus_1.year, month_minus_1.month, 1) - datetime.timedelta(days=1)

    # this requires some gymnastics to generate the month partition key
    months = [
        now.strftime('%Y%m'),
        month_minus_1.strftime('%Y%m'),
        month_minus_2.strftime('%Y%m'),
    ]

    # note that these are implicitly ordered by event_time desc
    audit_logs = list(AuditLogByTime.objects.filter(month=months[0]).fetch_size(1000).limit(100000))
    audit_logs.extend(list(AuditLogByTime.objects.filter(month=months[1]).fetch_size(1000).limit(100000)))
    audit_logs.extend(list(AuditLogByTime.objects.filter(month=months[2]).fetch_size(1000).limit(100000)))

    user_id_to_email = {str(u.user_id): u.email for u in User.objects.all()}
    for log in audit_logs:
        setattr(log, 'user_email', user_id_to_email[str(log.user_id)])

    return render(request, 'audit_log.html', {'audit_logs': audit_logs})
