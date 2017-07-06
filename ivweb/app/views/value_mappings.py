import logging
import string
from django.shortcuts import render, HttpResponse
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
    display_values_by_canonical_value = {}
    mappings_by_canonical_value = {}
    for mapping in ValueMapping.objects.filter(publisher_id=publisher_id, mapping_type=mapping_type):
        canonical_value = mapping.canonical_value
        if canonical_value not in mappings_by_canonical_value:
            display_value = display_values_by_canonical_value.get(canonical_value)
            if not display_value:
                try:
                    display_value = ValueMappingDisplay.objects.get(
                        publisher_id=publisher_id,
                        mapping_type=mapping_type,
                        canonical_value=canonical_value
                    ).display_value
                except ValueMappingDisplay.DoesNotExist:
                    display_value = canonical_value.title()
                display_values_by_canonical_value[canonical_value] = display_value

            mappings_by_canonical_value[mapping.canonical_value] = {
                'canonical_value': mapping.canonical_value,
                'display_value': display_value,
                'original_values': [mapping.original_value]
            }
        else:
            mappings_by_canonical_value[mapping.canonical_value]['original_values'].append(mapping.original_value)

    canonical_choices = [{'id': k, 'name': v} for k, v in display_values_by_canonical_value.items()]
    sorted_canonical_choices = sorted(canonical_choices, key=lambda c: c['name'])

    response = render(request, 'value_mappings/edit.html', {
        'publisher_id': publisher_id,
        'mapping_type': mapping_type,
        'mappings': mappings_by_canonical_value.values(),
        'mapping_type_display': string.capwords(mapping_type.replace('_', ' ')),
        'canonical_choices': sorted_canonical_choices,
    })

    return response


@login_required
def update_value_display(request):
    publisher_id = request.POST['publisher_id']
    mapping_type = request.POST['mapping_type']
    canonical_value = request.POST['canonical_value']
    display_value = request.POST['display_value']

    ValueMappingDisplay.objects(
        publisher_id=publisher_id,
        mapping_type=mapping_type,
        canonical_value=canonical_value
    ).update(
        display_value=display_value
    )

    return HttpResponse('ok')


@login_required
def update_value_mapping(request):
    publisher_id = request.POST['publisher_id']
    mapping_type = request.POST['mapping_type']
    original_value = request.POST['original_value']
    canonical_value = request.POST['canonical_value']

    ValueMapping.objects(
        publisher_id=publisher_id,
        mapping_type=mapping_type,
        original_value=original_value
    ).update(
        canonical_value=canonical_value
    )

    return HttpResponse('ok')
