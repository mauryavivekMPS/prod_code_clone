from django.template.base import Library
from django.utils.safestring import mark_safe

register = Library()


@register.filter(is_safe=True)
def nullable(s):
    if s:
        return s
    else:
        return mark_safe('<span class="null-value">&ndash;</span>')

