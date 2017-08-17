import logging
import datetime
from operator import attrgetter
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ivetl.models import AuditLogByTime, AuditLogByPublisher, AuditLogByUser, User, PublisherMetadata
from ivetl import utils

log = logging.getLogger(__name__)

TIME_FILTER_CHOICES = [
    ('last-90-days', 'Last 90 days'),
    ('this-year', 'This year'),
    ('last-year', 'Last year'),
    ('all-time', 'All time'),
]


@login_required
def show(request):
    selected_time = request.GET.get('time', 'last-90-days')
    selected_publisher = request.GET.get('publisher')
    selected_user = request.GET.get('user')

    now = datetime.datetime.now()

    if selected_time == 'last-90-days':
        end_date = now
        start_date = end_date - datetime.timedelta(days=90)
    elif selected_time == 'this-year':
        end_date = now
        start_date = datetime.datetime(end_date.year, 1, 1)
    elif selected_time == 'last-year':
        end_date = datetime.datetime(now.year - 1, 12, 31)
        start_date = datetime.datetime(end_date.year, 1, 1)
    else:
        end_date = now
        start_date = datetime.datetime(2016, 1, 1)  # audit logging epoch

    if selected_publisher:
        audit_logs = list(AuditLogByPublisher.objects.filter(
            publisher_id=selected_publisher,
            event_time__gte=start_date,
            event_time__lte=end_date,
        ).fetch_size(1000).limit(100000))

        # do a manual filter if both user and publisher are selected
        if selected_user:
            audit_logs = [a for a in audit_logs if str(a.user_id) == selected_user]

    elif selected_user:
        audit_logs = list(AuditLogByUser.objects.filter(
            user_id=selected_user,
            event_time__gte=start_date,
            event_time__lte=end_date,
        ).fetch_size(1000).limit(100000))

    else:
        start_of_start_date_month = datetime.datetime(start_date.year, start_date.month, 1)
        months = [m.strftime('%Y%m') for m in utils.month_range(start_of_start_date_month, end_date)]
        months.reverse()

        audit_logs = []
        for month in months:
            audit_logs.extend(list(AuditLogByTime.objects.filter(
                month=month,
                event_time__gte=start_date,
                event_time__lte=end_date,
            ).fetch_size(1000).limit(100000)))

    # add user display names to each entry
    user_id_to_display_name = {str(u.user_id): u.display_name for u in User.objects.all()}
    for log_entry in audit_logs:
        setattr(log_entry, 'user_display_name', user_id_to_display_name[str(log_entry.user_id)])

    all_publisher_filter_choices = [(p.publisher_id, p.name) for p in PublisherMetadata.objects.all()]
    all_publisher_filter_choices.append(('system', '(system) System'))
    all_publisher_filter_choices.append(('unknown', '(unknown) Unknown'))
    sorted_publisher_filter_choices = sorted(all_publisher_filter_choices, key=lambda c: c[1])

    sorted_users = sorted(User.objects.all(), key=attrgetter('display_name'))
    sorted_user_filter_choices = [(str(u.user_id), '%s (%s)' % (u.display_name, u.email)) for u in sorted_users]

    return render(request, 'audit_log.html', {
        'audit_logs': audit_logs,
        'time_filter_choices': TIME_FILTER_CHOICES,
        'publisher_filter_choices': sorted_publisher_filter_choices,
        'user_filter_choices': sorted_user_filter_choices,
        'selected_time': selected_time,
        'selected_publisher': selected_publisher,
        'selected_user': selected_user,
    })
