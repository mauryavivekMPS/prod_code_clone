from django.template.base import Library
from django.utils.safestring import mark_safe
from ivweb.app import constants

register = Library()


@register.filter(is_safe=True)
def pipeline_name(pipeline_id):
    return constants.PIPELINE_LOOKUP[pipeline_id]

@register.filter(is_safe=True)
def nullable(s):
    if s:
        return s
    else:
        return mark_safe('<span class="null-value">&ndash;</span>')

