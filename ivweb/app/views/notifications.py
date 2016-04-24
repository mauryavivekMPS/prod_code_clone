import logging
import json
from operator import attrgetter
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from ivetl.models import Notification_Summary, Alert
from ivetl.alerts import checks
from ivweb.app.views import utils as view_utils
from ivetl.common import common

log = logging.getLogger(__name__)


@login_required
def list_notifications(request, publisher_id=None):
    if publisher_id:
        all_notifications = Notification_Summary.objects.filter(publisher_id=publisher_id)
        alerts_by_alert_id = {a.alert_id: a for a in Alert.objects.filter(publisher_id=publisher_id)}
    else:
        all_notifications = Notification_Summary.objects.all()
        alerts_by_alert_id = {a.alert_id: a for a in Alert.objects.all()}

    filter_param = request.GET.get('filter', request.COOKIES.get('notification-list-filter', 'active'))

    show_dismissed = filter_param == 'dismissed'
    filtered_notifications = all_notifications.filter(dismissed=show_dismissed)

    for notification in filtered_notifications:
        setattr(notification, 'alert_name', alerts_by_alert_id[notification.alert_id].name)

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('notification-list-sort', 'publisher_id'))
    sorted_notifications = sorted(filtered_notifications, key=attrgetter(sort_key), reverse=sort_descending)

    response = render(request, 'notifications/list.html', {
        'notifications': sorted_notifications,
        'reset_url': reverse('notifications.list') + '?sort=' + sort_param + '&filter=' + filter_param,
        'filter_param': filter_param,
        'sort_key': sort_key,
        'sort_descending': sort_descending,
    })

    response.set_cookie('notification-list-sort', value=sort_param, max_age=30*24*60*60)
    response.set_cookie('notification-list-filter', value=filter_param, max_age=30*24*60*60)

    return response


@login_required
def include_notification_details(request):
    notification_summary_id = request.GET['notification_summary_id']
    publisher_id = request.GET['publisher_id']
    notification_summary = Notification_Summary.objects.get(publisher_id=publisher_id, notification_summary_id=notification_summary_id)
    alert = Alert.objects.get(alert_id=notification_summary.alert_id)
    check = checks[alert.check_id]
    values_list = json.loads(notification_summary.values_list_json)

    ordered_values_list = []
    for values in values_list:
        row = []
        for col in check['table_order']:
            row.append({
                'value': values[col['key']],
                'key': col['key'],

            })
        ordered_values_list.append(row)

    return render(request, 'notifications/include/details.html', {
        'notification': notification_summary,
        'values_list': ordered_values_list,
        'check': check,
        'product': common.PRODUCT_BY_ID[notification_summary.product_id],
        'is_include': True,
    })


@login_required
def dismiss_notification(request):
    notification_summary_id = request.POST['notification_summary_id']
    publisher_id = request.POST['publisher_id']
    notification_summary = Notification_Summary.objects.get(publisher_id=publisher_id, notification_summary_id=notification_summary_id)
    notification_summary.dismissed = True
    notification_summary.save()
    return HttpResponse('ok')