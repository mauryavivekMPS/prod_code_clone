import datetime
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
        if s == 0:
            s = 1
        return str(datetime.timedelta(seconds=s))
    else:
        return mark_safe('<span class="null-value">&ndash;</span>')

