from operator import attrgetter
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.template import loader, RequestContext
from ivetl.common import common
from ivetl.tasks import update_report_item
from ivetl.models import SingletonTaskStatus


def _get_items_with_status():
    report_items = []  # type: list[dict]

    datasource_ids = set()
    for product_group in common.PRODUCT_GROUPS:
        for datasource_id in product_group['tableau_datasources']:
            datasource_ids.add(datasource_id)

    report_items.extend([{'id': id, 'type': 'datasource'} for id in datasource_ids])

    for workbook in common.TABLEAU_WORKBOOKS:
        report_items.append({'id': workbook['id'], 'type': 'workbook'})

    for item in report_items:
        try:
            status = SingletonTaskStatus.objects.get(
                task_type='%s-update' % item['type'],
                task_id=item['id'],
            )
            item['status'] = status.status
        except SingletonTaskStatus.DoesNotExist:
            item['status'] = ''

    return report_items


@login_required
def update_reports(request):
    report_items = _get_items_with_status()
    sorted_report_items = sorted(report_items, key=lambda x: (x['type'], x['id']))
    sorted_publishers = sorted(request.user.get_accessible_publishers(), key=attrgetter('name'))

    return render(request, 'reports/update_reports.html', {
        'report_items': sorted_report_items,
        'publishers': sorted_publishers,
    })


@login_required
def update_item(request):
    if request.POST:
        item_type = request.POST['item_type']
        item_id = request.POST['item_id']
        publisher_id = request.POST.get('publisher_id')

        if publisher_id:
            publisher_id_list = [publisher_id]
            skip_demo_publishers = False
        else:
            publisher_id_list = []
            skip_demo_publishers = True

        update_report_item.s(
            item_type,
            item_id,
            request.user.user_id,
            publisher_id_list=publisher_id_list,
            skip_demo_publishers=skip_demo_publishers
        ).delay()

    return HttpResponse('ok')


@login_required
def include_item_statuses(request):
    report_items = _get_items_with_status()

    for item in report_items:
        template = loader.get_template('reports/include/item_status_row.html')
        context = RequestContext(request, {
            'item': item,
        })
        item['html'] = template.render(context)

    return JsonResponse({
        'report_items': report_items,
    })
