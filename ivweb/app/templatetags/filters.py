from django.template.base import Library
from ivweb.app import constants

register = Library()


@register.filter(is_safe=True)
def pipeline_name(pipeline_id):
    return constants.PIPELINE_LOOKUP[pipeline_id]
