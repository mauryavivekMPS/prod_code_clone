import logging
import json
import requests
from operator import attrgetter
from dateutil.parser import parse
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from ivetl.models import NotificationSummary, Alert
from ivetl.alerts import CHECKS, get_check_params_display_string, get_filter_params_display_string
from ivweb.app.views import utils as view_utils
from ivetl.common import common

log = logging.getLogger(__name__)


@login_required
def list_notifications(request):
    filter_param = request.GET.get('filter', request.COOKIES.get('notification-list-filter', 'active'))
    show_dismissed = filter_param == 'dismissed'

    single_publisher_user = False
    if request.user.is_superuser:
        filtered_notifications = NotificationSummary.objects.filter(dismissed=show_dismissed)
        alerts_by_alert_id = {a.alert_id: a for a in Alert.objects.all()}
    else:
        accessible_publisher_ids = [p.publisher_id for p in request.user.get_accessible_publishers()]

        # need to do this the long way because cassandra does not support IN for partition keys in certain situations
        filtered_notifications = []
        for publisher_id in accessible_publisher_ids:
            for notification in NotificationSummary.objects.filter(publisher_id=publisher_id, dismissed=show_dismissed):
                filtered_notifications.append(notification)

        alerts_by_alert_id = {a.alert_id: a for a in Alert.objects.filter(publisher_id__in=accessible_publisher_ids)}

        if len(accessible_publisher_ids) == 1:
            single_publisher_user = True

    for notification in filtered_notifications:
        setattr(notification, 'alert_name', alerts_by_alert_id[notification.alert_id].name)

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('notification-list-sort', 'alert_name'))
    sorted_notifications = sorted(filtered_notifications, key=attrgetter(sort_key), reverse=sort_descending)

    open_notification = request.GET.get('notification_summary_id')

    response = render(request, 'notifications/list.html', {
        'notifications': sorted_notifications,
        'reset_url': reverse('notifications.list') + '?sort=' + sort_param + '&filter=' + filter_param,
        'filter_param': filter_param,
        'sort_key': sort_key,
        'sort_descending': sort_descending,
        'single_publisher_user': single_publisher_user,
        'open_notification': open_notification,
    })

    response.set_cookie('notification-list-sort', value=sort_param, max_age=30*24*60*60)
    response.set_cookie('notification-list-filter', value=filter_param, max_age=30*24*60*60)

    return response


@login_required
def include_notification_details(request):
    notification_summary_id = request.GET['notification_summary_id']
    publisher_id = request.GET['publisher_id']
    notification_summary = NotificationSummary.objects.get(publisher_id=publisher_id, notification_summary_id=notification_summary_id)
    alert = Alert.objects.get(alert_id=notification_summary.alert_id)
    check = CHECKS[alert.check_id]
    values_list = json.loads(notification_summary.values_list_json)

    ordered_values_list = []
    for values in values_list:
        row = []
        for col in check['table_order']:

            value_type = col.get('type', 'raw')
            if value_type == 'article-link':
                article_title = values.get('article_title')
                if article_title:
                    article_title = article_title[:44]
                else:
                    article_title = 'Untitled'
                rendered_value = '<a href="http://dx.doi.org/%s" target="_blank">%s</a>' % (
                    values['doi'],
                    article_title
                )
            elif value_type == 'check-link':
                check_name = values.get('check_name')
                if check_name:
                    check_name = check_name[:44]
                else:
                    check_name = 'Untitled'
                from_timestamp = int(parse(values['from_date']).timestamp())
                to_timestamp = int(parse(values['to_date']).timestamp())
                rendered_value = '<a href="https://my.pingdom.com/reports/responsetime#check=%s&daterange=%s-%s&tab=result_tab" target="_blank">%s</a>' % (
                    values['check_id'],
                    from_timestamp,
                    to_timestamp,
                    check_name
                )
            else:
                rendered_value = values[col['key']]

            row.append({
                'value': rendered_value,
                'key': col['key'],
                'type': value_type,
                'align': col.get('align', 'left'),
                'width': col.get('width', 'normal'),
            })
        ordered_values_list.append(row)

    setattr(alert, 'param_display_string', get_check_params_display_string(alert))
    setattr(alert, 'filter_display_string', get_filter_params_display_string(alert))

    return render(request, 'notifications/include/details.html', {
        'notification': notification_summary,
        'values_list': ordered_values_list,
        'alert': alert,
        'check': check,
        'product': common.PRODUCT_BY_ID[notification_summary.product_id],
        'is_include': True,
    })


@login_required
def dismiss_notification(request):
    notification_summary_id = request.POST['notification_summary_id']
    publisher_id = request.POST['publisher_id']
    notification_summary = NotificationSummary.objects.get(publisher_id=publisher_id, notification_summary_id=notification_summary_id)
    notification_summary.dismissed = True
    notification_summary.save()
    return HttpResponse('ok')
