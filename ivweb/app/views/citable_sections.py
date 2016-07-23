import logging
from operator import attrgetter
from django.shortcuts import render, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import PublisherJournal
from ivweb.app.views import utils as view_utils

log = logging.getLogger(__name__)


@login_required
def list_journals(request):

    # messages = []
    # if 'from' in request.GET:
    #     from_value = request.GET['from']
    #     if from_value == 'save-success':
    #         messages.append("Changes to your alert have been saved.")
    #     elif from_value == 'new-success':
    #         messages.append("Your new alert is created and ready to go.")

    single_publisher_user = False
    if request.user.superuser:
        unsorted_journals = PublisherJournal.objects.all()
    else:
        accessible_publisher_ids = [p.publisher_id for p in request.user.get_accessible_publishers()]
        unsorted_journals = PublisherJournal.objects.filter(publisher_id__in=accessible_publisher_ids)
        if len(accessible_publisher_ids) == 1:
            single_publisher_user = True

    # filtered_alerts = []
    # if filter_param == 'active':
    #     for alert in alerts:
    #         if not alert.archived:
    #             filtered_alerts.append(alert)
    # elif filter_param == 'archived':
    #     for alert in alerts:
    #         if alert.archived:
    #             filtered_alerts.append(alert)

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('journal-list-sort', 'publisher_id'))
    sorted_journals = sorted(unsorted_journals, key=attrgetter(sort_key), reverse=sort_descending)

    # for alert in sorted_alerts:
    #     check = CHECKS[alert.check_id]
    #     setattr(alert, 'check_name', check['name'])
    #     setattr(alert, 'param_display_string', get_check_params_display_string(alert))
    #     setattr(alert, 'filter_display_string', get_filter_params_display_string(alert))

    response = render(request, 'citable_sections/list.html', {
        # 'alerts': sorted_alerts,
        # 'messages': messages,
        'journals': sorted_journals,
        'reset_url': reverse('citable_sections.list') + '?sort=' + sort_param,
        'sort_key': sort_key,
        'sort_descending': sort_descending,
        'single_publisher_user': single_publisher_user,
    })

    response.set_cookie('journal-list-sort', value=sort_param, max_age=30*24*60*60)

    return response


@login_required
def choose_citable_sections(request, uid=None):
    return HttpResponse('ok')
