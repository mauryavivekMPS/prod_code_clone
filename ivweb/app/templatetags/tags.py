from django import template

register = template.Library()


@register.simple_tag
def status_icon(status_item=None):
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
