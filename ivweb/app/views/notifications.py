import logging
import json
from operator import attrgetter
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ivetl.models import Notification_Summary, Alert
from ivetl.alerts import checks
from ivweb.app.views import utils as view_utils
from ivetl.common import common

log = logging.getLogger(__name__)


@login_required
def list_notifications(request, publisher_id=None):
    if publisher_id:
        notifications = Notification_Summary.objects.filter(publisher_id=publisher_id)
        alerts_by_alert_id = {a.alert_id: a for a in Alert.objects.filter(publisher_id=publisher_id)}
    else:
        notifications = Notification_Summary.objects.all()
        alerts_by_alert_id = {a.alert_id: a for a in Alert.objects.all()}

    for notification in notifications:
        setattr(notification, 'alert_name', alerts_by_alert_id[notification.alert_id].name)

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('notification-list-sort', 'publisher_id'))
    sorted_notifications = sorted(notifications, key=attrgetter(sort_key), reverse=sort_descending)

    response = render(request, 'notifications/list.html', {
        'notifications': sorted_notifications,
        'sort_key': sort_key,
        'sort_descending': sort_descending,
    })

    response.set_cookie('notification-list-sort', value=sort_param, max_age=30*24*60*60)

    return response


@login_required
def include_notification_details(request):
    notification_summary_id = request.GET['notification_summary_id']
    publisher_id = request.GET['publisher_id']
    notification_summary = Notification_Summary.objects.get(publisher_id=publisher_id, notification_summary_id=notification_summary_id)
    alert = Alert.objects.get(alert_id=notification_summary.alert_id)
    check = checks[alert.check_id]

    # render the notification summary content
    results = []
    for values in json.loads(notification_summary.values_list_json):
        results.append(check['format_string'] % values)

    return render(request, 'notifications/include/details.html', {
        'notification': notification_summary,
        'results': results,
        'check': check,
        'product': common.PRODUCT_BY_ID[notification_summary.product_id],
        'is_include': True,
    })
