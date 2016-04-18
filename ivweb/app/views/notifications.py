import logging
from operator import attrgetter
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ivetl.models import Notification_Summary
from ivweb.app.views import utils as view_utils

log = logging.getLogger(__name__)


@login_required
def list_notifications(request, publisher_id=None):
    if publisher_id:
        notifications = Notification_Summary.objects.filter(publisher_id=publisher_id)
    else:
        notifications = Notification_Summary.objects.all()

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('notification-list-sort', 'publisher_id'))
    sorted_notifications = sorted(notifications, key=attrgetter(sort_key), reverse=sort_descending)

    response = render(request, 'notifications/list.html', {
        'notifications': sorted_notifications,
        'sort_key': sort_key,
        'sort_descending': sort_descending,
    })

    response.set_cookie('notification-list-sort', value=sort_param, max_age=30*24*60*60)

    return response


