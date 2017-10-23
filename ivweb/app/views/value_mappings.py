import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template import loader, RequestContext
from ivetl.value_mappings import MAPPING_TYPES, MAPPING_TYPE_PROPERTIES
from ivetl.models import ValueMapping, ValueMappingDisplay, PublisherMetadata
from ivetl.pipelines.publishedarticles import RefreshValueMappingsPipeline
from ivweb.app.views import utils

log = logging.getLogger(__name__)


@login_required
def list_mappings(request):
    mappings_by_publisher = []
    for publisher in request.user.get_accessible_publishers():
        for mapping_type in MAPPING_TYPES:
            num_canonicals = ValueMapping.objects.filter(publisher_id=publisher.publisher_id, mapping_type=mapping_type).count()
            num_displays = ValueMappingDisplay.objects.filter(publisher_id=publisher.publisher_id, mapping_type=mapping_type).count()
            mappings_by_publisher.append({
                'publisher_id': publisher.publisher_id,
                'publisher_name': publisher.name,
                'mapping_type': mapping_type,
                'mapping_type_display': MAPPING_TYPE_PROPERTIES[mapping_type]['display_name'],
                'num_canonicals': num_canonicals,
                'num_displays': num_displays,
            })

    sorted_mappings_by_publisher = sorted(mappings_by_publisher, key=lambda m: m['publisher_name'])

    response = render(request, 'value_mappings/list.html', {
        'mappings_by_publisher': sorted_mappings_by_publisher,
    })

    return response


@login_required
def edit(request, publisher_id, mapping_type):
    publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)

    try:
        current_page = int(request.GET.get('page', '1'))
    except ValueError:
        current_page = 1

    mappings_per_page = 100
    links_per_page = 5

    mappings_by_canonical_value = {}

    all_mappings = [m for m in ValueMapping.objects.filter(
        publisher_id=publisher_id,
        mapping_type=mapping_type
    )]

    all_display_values = ValueMappingDisplay.objects.filter(
        publisher_id=publisher_id,
        mapping_type=mapping_type,
    )

    display_values_by_canonical_value = {d.canonical_value: d.display_value for d in all_display_values}

    for mapping in all_mappings:
        canonical_value = mapping.canonical_value
        if canonical_value not in mappings_by_canonical_value:
            display_value = display_values_by_canonical_value.get(canonical_value)
            if not display_value:
                # if it's not already in the database, default to the title-ized version of the canonical
                display_values_by_canonical_value[canonical_value] = canonical_value.title()

            mappings_by_canonical_value[mapping.canonical_value] = {
                'canonical_value': mapping.canonical_value,
                'display_value': display_value,
                'original_values': [mapping.original_value]
            }
        else:
            mappings_by_canonical_value[mapping.canonical_value]['original_values'].append(mapping.original_value)

    all_sorted_mappings = sorted(mappings_by_canonical_value.values(), key=lambda m: m['display_value'].lower())

    num_total_mappings = len(all_sorted_mappings)

    first, last, low_page, high_page, num_pages = utils.paginate(current_page, num_total_mappings, mappings_per_page, links_per_page)
    all_pages = range(low_page, high_page + 1)

    this_page_sorted_mappings = all_sorted_mappings[first:last]

    canonical_choices = [{'id': k, 'name': v} for k, v in display_values_by_canonical_value.items()]
    sorted_canonical_choices = sorted(canonical_choices, key=lambda c: c['name'])

    response = render(request, 'value_mappings/edit.html', {
        'publisher': publisher,
        'publisher_id': publisher_id,
        'mapping_type': mapping_type,
        'mappings': this_page_sorted_mappings,
        'mapping_type_display': MAPPING_TYPE_PROPERTIES[mapping_type]['display_name'],
        'canonical_choices': sorted_canonical_choices,
        'current_page': current_page,
        'num_pages': num_pages,
        'low_page': low_page,
        'high_page': high_page,
        'all_pages': all_pages,
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

    return JsonResponse({'status':'ok'})


@login_required
def update_value_mapping(request):
    publisher_id = request.POST['publisher_id']
    mapping_type = request.POST['mapping_type']
    original_value = request.POST['original_value']
    canonical_value = request.POST['canonical_value']
    is_new_value = request.POST.get('is_new_value', '0') == '1'

    ValueMapping.objects(
        publisher_id=publisher_id,
        mapping_type=mapping_type,
        original_value=original_value
    ).update(
        canonical_value=canonical_value
    )

    new_mapping_html = ''
    if is_new_value:
        ValueMappingDisplay.objects(
            publisher_id=publisher_id,
            mapping_type=mapping_type,
            canonical_value=canonical_value
        ).update(
            display_value=canonical_value
        )

        mapping_for_template = {
            'canonical_value': canonical_value,
            'display_value': canonical_value,
            'original_values': [original_value]
        }

        template = loader.get_template('value_mappings/include/mapping_container.html')
        context = RequestContext(request, {
            'mapping': mapping_for_template,
        })
        new_mapping_html = template.render(context)

    return JsonResponse({
        'status': 'ok',
        'new_mapping_html': new_mapping_html,
    })


@login_required
def run_refresh_mappings_pipeline(request):
    publisher_id = request.POST['publisher_id']

    RefreshValueMappingsPipeline.s(
        publisher_id_list=[publisher_id],
        product_id='published_articles',
        initiating_user_email=request.user.email,
    ).delay()

    return JsonResponse({'status': 'ok'})
