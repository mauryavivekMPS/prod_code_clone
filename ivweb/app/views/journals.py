import json
import logging
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import PublisherJournal, AttributeValues, CitableSection, PublisherMetadata
from ivetl import utils
from ivweb.app.views import utils as view_utils

log = logging.getLogger(__name__)


@login_required
def list_journals(request, publisher_id=None):

    messages = []
    if 'from' in request.GET:
        from_value = request.GET['from']
        if from_value == 'save-success':
            messages.append("Changes to the citable sections have been saved.")

    single_publisher_user = False
    unsorted_journals = []
    if request.user.is_superuser:
        if publisher_id:
            unsorted_journals = PublisherJournal.objects.filter(publisher_id=publisher_id)
        else:
            unsorted_journals = PublisherJournal.objects.all()
    else:
        accessible_publisher_ids = [p.publisher_id for p in request.user.get_accessible_publishers()]
        if publisher_id:
            if publisher_id in accessible_publisher_ids:
                unsorted_journals = PublisherJournal.objects.filter(publisher_id=publisher_id)
        else:
            unsorted_journals = PublisherJournal.objects.filter(publisher_id__in=accessible_publisher_ids)
        if len(accessible_publisher_ids) == 1:
            single_publisher_user = True

    filtered_journals = [j for j in unsorted_journals if j.product_id == 'published_articles']

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('journal-list-sort', 'publisher_id'))
    sorted_journals = sorted(filtered_journals, key=lambda j: (j[sort_key] or '', j['journal_code'] or ''), reverse=sort_descending)

    for journal in unsorted_journals:
        num_citable_sections = CitableSection.objects.filter(publisher_id=journal.publisher_id, journal_issn=journal.electronic_issn)
        setattr(journal, 'num_citable_sections', num_citable_sections.count())

    publisher = None
    if publisher_id:
        reset_url = reverse('publishers.journals', kwargs={'publisher_id': publisher_id})
        publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)
    else:
        reset_url = reverse('journals.list')

    response = render(request, 'journals/list.html', {
        'messages': messages,
        'journals': sorted_journals,
        'reset_url': reset_url + '?sort=' + sort_param,
        'sort_key': sort_key,
        'sort_descending': sort_descending,
        'single_publisher_user': single_publisher_user,
        'publisher': publisher,
    })

    response.set_cookie('journal-list-sort', value=sort_param, max_age=30*24*60*60)

    return response


@login_required
def choose_citable_sections(request, publisher_id=None, uid=None):
    journal = PublisherJournal.objects.get(publisher_id=publisher_id, product_id='published_articles', uid=uid)
    publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)

    sections = {}
    try:
        attribute_value = AttributeValues.objects.get(
            publisher_id=publisher_id,
            name='citable_sections.' + journal.electronic_issn
        )
        for section in json.loads(attribute_value.values_json):
            if section and section != 'None':
                try:
                    CitableSection.objects.get(
                        publisher_id=publisher_id,
                        journal_issn=journal.electronic_issn,
                        article_type=section
                    )
                    cited = True
                except CitableSection.DoesNotExist:
                    cited = False
                sections[section] = cited

    except AttributeValues.DoesNotExist:
        pass

    sorted_sections = sorted([(section, cited) for section, cited in sections.items()], key=lambda s: s[0])

    if request.method == 'POST':
        from_value = request.POST.get('from')

        # delete existing citable records
        existing_section_records = CitableSection.objects.filter(publisher_id=publisher_id, journal_issn=journal.electronic_issn)
        existing_sections = set([e.article_type for e in existing_section_records])
        for section in existing_section_records:
            section.delete()

        new_sections = set([p[8:] for p in request.POST if p.startswith('section_')])

        # add all new ones
        for section in new_sections:
            CitableSection.objects.create(
                publisher_id=publisher_id,
                journal_issn=journal.electronic_issn,
                article_type=section
            )

        added_sections = list(new_sections - existing_sections)
        deleted_sections = list(existing_sections - new_sections)

        if added_sections:
            utils.add_audit_log(
                user_id=request.user.user_id,
                publisher_id=publisher_id,
                action='add-citable_sections',
                description='Add citable sections: %s' % ", ".join(added_sections)
            )

        if deleted_sections:
            utils.add_audit_log(
                user_id=request.user.user_id,
                publisher_id=publisher_id,
                action='delete-citable_sections',
                description='Delete citable sections: %s' % ", ".join(deleted_sections)
            )

        if from_value == 'publisher-journals':
            return HttpResponseRedirect(reverse('publishers.journals', kwargs={'publisher_id': publisher_id}) + '?from=save-success')
        else:
            return HttpResponseRedirect(reverse('journals.list') + '?from=save-success')
    else:
        from_value = request.GET.get('from')

    return render(request, 'journals/choose_citable_sections.html', {
        'journal': journal,
        'sections': sorted_sections,
        'from_value': from_value,
        'publisher': publisher,
    })

