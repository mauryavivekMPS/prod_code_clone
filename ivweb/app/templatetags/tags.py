import json
import markdown
from django import template
from django.utils.safestring import SafeText
from ivetl.models import ContentBlock

register = template.Library()


@register.simple_tag
def status_icon(status_item=None):
    if type(status_item) == bool:
        if status_item:
            return '<span class="status-icon status-success"></span>'
        else:
            return '<span class="status-icon status-empty"></span>'

    if type(status_item) == SafeText or type(status_item) == str:
        if status_item == 'in-progress':
            return '<span class="status-icon status-warning status-pulse"></span>'

    if status_item:
        if status_item.status == 'started':
            return '<span class="status-icon status-empty"></span>'
        elif status_item.status == 'in-progress':
            return '<span class="status-icon status-warning status-pulse"></span>'
        elif status_item.status == 'completed':
            return '<span class="status-icon status-success"></span>'
        elif status_item.status == 'error':
            return '<span class="status-icon status-danger"></span>'
        else:
            return '<span class="status-icon status-empty"></span>'
    else:
        return '<span class="status-icon status-empty"></span>'


@register.simple_tag
def checkmark(thing):
    if thing:
        return '<span class="lnr lnr-check checkmark"></span>'
    else:
        return ''


@register.simple_tag
def checkmark_or_cross(thing):
    if thing:
        return '<span class="lnr lnr-check checkmark"></span>'
    else:
        return '<span class="lnr lnr-cross cross"></span>'


@register.simple_tag
def sort_column(column_label, field_name, sort_key, sort_descending, use_status_icon=False):
    if field_name == sort_key:
        if sort_descending:
            icon = 'fa-sort-asc'  # these icons make more sense reversed
            next_sort_order = ''
        else:
            icon = 'fa-sort-desc'
            next_sort_order = '-'
    else:
        icon = 'fa-sort'
        next_sort_order = ''

    return '<a href=".?sort=%s%s" class="sort">%s <i class="fa %s"></i></a>' % (
        next_sort_order,
        field_name,
        column_label if not use_status_icon else status_icon(),
        icon,
    )


@register.simple_tag
def get_alert_param_value(alert, param_name):
    params = json.loads(alert.check_params)
    return params.get(param_name, '')


@register.simple_tag
def get_alert_filter_value(alert, filter_name):
    filters = json.loads(alert.filter_params)
    return filters.get(filter_name, '')


@register.simple_tag
def content_block(block_id):
    try:
        block = ContentBlock.objects.get(block_id=str(block_id))
        return markdown.markdown(block.markdown)
    except ContentBlock.DoesNotExist:
        return ''
