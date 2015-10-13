from django.template.base import Library
from django.utils.safestring import mark_safe

register = Library()


@register.filter(is_safe=True)
def nullable_date(s):
    if s:
        return s
    else:
        return mark_safe('<span class="null-value">&ndash;</span>')


@register.filter(is_safe=True)
def nullable_duration(s):
    if s:
        return '%ss' % s
    elif s == 0:
        return mark_safe('<span class="lt">&lt;</span>1s')
    else:
        return mark_safe('<span class="null-value">&ndash;</span>')

