import logging
from django import forms
from django.shortcuts import render, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import PublisherJournal
from ivweb.app.views import utils as view_utils

log = logging.getLogger(__name__)


@login_required
def list_journals(request):

    # messages = []
    # if 'from' in request.GET:
    #     from_value = request.GET['from']
    #     if from_value == 'save-success':
    #         messages.append("Changes to your alert have been saved.")
    #     elif from_value == 'new-success':
    #         messages.append("Your new alert is created and ready to go.")

    single_publisher_user = False
    if request.user.superuser:
        unsorted_journals = PublisherJournal.objects.all()
    else:
        accessible_publisher_ids = [p.publisher_id for p in request.user.get_accessible_publishers()]
        unsorted_journals = PublisherJournal.objects.filter(publisher_id__in=accessible_publisher_ids)
        if len(accessible_publisher_ids) == 1:
            single_publisher_user = True

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('journal-list-sort', 'publisher_id'))
    sorted_journals = sorted(unsorted_journals, key=lambda j: (j[sort_key], j['journal_code']), reverse=sort_descending)

    response = render(request, 'citable_sections/list.html', {
        # 'messages': messages,
        'journals': sorted_journals,
        'reset_url': reverse('citable_sections.list') + '?sort=' + sort_param,
        'sort_key': sort_key,
        'sort_descending': sort_descending,
        'single_publisher_user': single_publisher_user,
    })

    response.set_cookie('journal-list-sort', value=sort_param, max_age=30*24*60*60)

    return response


class CitableSectionForm(forms.Form):
    journal_uid = forms.CharField(widget=forms.HiddenInput, required=True)

    def __init__(self, *args, instance=None, **kwargs):
        initial = {}

        if instance:
            self.instance = instance
            initial = dict(instance)
        else:
            self.instance = None

        super(CitableSectionForm, self).__init__(initial=initial, *args, **kwargs)


@login_required
def choose_citable_sections(request, publisher_id=None, uid=None):
    journal = PublisherJournal.objects.get(publisher_id=publisher_id, product_id='published_articles', uid=uid)

    if request.method == 'POST':
        form = CitableSectionForm(request.POST, instance=journal)
    else:
        form = CitableSectionForm(instance=journal)

    return render(request, 'citable_sections/choose_citable_sections.html', {
        'journal': journal,
        'form': form,
    })
