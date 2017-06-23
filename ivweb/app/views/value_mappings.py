import logging
from operator import attrgetter
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.value_mappings import MAPPING_TYPES
from ivetl.models import ValueMapping, ValueMappingDisplay

log = logging.getLogger(__name__)


@login_required
def list_mappings(request):

    mappings_by_publisher = []
    for publisher in request.user.get_accessible_publishers():
        for mapping_type in MAPPING_TYPES:
            mappings_by_publisher.append({
                'publisher_id': publisher.publisher_id,
                'publisher_name': publisher.name,
                'mapping_type': mapping_type,
            })

    sorted_mappings_by_publisher = sorted(mappings_by_publisher, key=lambda m: m['publisher_name'])

    response = render(request, 'value_mappings/list.html', {
        'mappings_by_publisher': sorted_mappings_by_publisher,
    })

    return response


@login_required
def edit(request, publisher_id, mapping_type):

    mappings_by_canonical_value = {}
    for mapping in ValueMapping.objects.filter(publisher_id=publisher_id, mapping_type=mapping_type):
        if mapping.canonical_value not in mappings_by_canonical_value:

            try:
                display_value = ValueMappingDisplay.objects.get(
                    publisher_id=publisher_id,
                    mapping_type=mapping_type,
                    canonical_value=mapping.canonical_value
                ).display_value
            except ValueMappingDisplay.DoesNotExist:
                display_value = None

            mappings_by_canonical_value[mapping.canonical_value] = {
                'canonical_value': mapping.canonical_value,
                'display_value': display_value,
                'original_values': [mapping.original_value]
            }
        else:
            mappings_by_canonical_value[mapping.canonical_value]['original_values'].append(mapping.original_value)

    response = render(request, 'value_mappings/edit.html', {
        'mappings': mappings_by_canonical_value.values(),
    })

    return response
