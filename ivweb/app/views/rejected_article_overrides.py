import logging
from django import forms
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.shortcuts import render, HttpResponseRedirect, HttpResponse

from ivetl.common import common
from ivetl.models import RejectedArticleOverride
from ivetl.models import PublisherMetadata

log = logging.getLogger(__name__)

@login_required
def list_overrides(request):
    messages = []
    alt_error_message = None
    if 'from' in request.GET:
        from_value = request.GET['from']
        if from_value == 'new-success':
            messages.append('Your new override has been created.')
        elif from_value == 'new-error':
            alt_error_message = 'Error creating new override'
        elif from_value == 'delete-success':
            messages.append('Override deleted successfully.')
        elif from_value == 'delete-error':
            alt_error_message = 'Error deleting override'

    overrides = RejectedArticleOverride.objects.all()
    response = render(request,
        'rejected_article_overrides/list_overrides.html', {
        'overrides': overrides,
        'messages': messages,
        'alt_error_message': alt_error_message
    })

    return response


class RejectedArticleOverrideForm(forms.Form):

    publisher_id = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Publisher ID'
    }), validators=[RegexValidator(r'^[0-9a-zA-Z\-]*$',
    'Only alphanumeric characters are allowed in publisher id values')])
    manuscript_id = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Manuscript ID'
    }))
    doi = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'DOI'
    }))
    label = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Override Label'
        }), required=False)


    def save(self):
        override = RejectedArticleOverride.objects.create(
            publisher_id=self.cleaned_data['publisher_id'],
            manuscript_id=self.cleaned_data['manuscript_id'],
            doi=common.normalizedDoi(self.cleaned_data['doi']),
            label=self.cleaned_data['label']
        )
        log.info('Creating override: %s, %s, %s, %s' % (
            override['publisher_id'], override['manuscript_id'],
            override['doi'], override['label']))
        return override


@login_required
def new_override(request):
    if request.method == 'POST':
        form = RejectedArticleOverrideForm(request.POST)
        if form.is_valid():
            try:
                override = form.save()
                return HttpResponseRedirect(
                    reverse('rejected_article_overrides.list_overrides') +
                    '?from=new-success')
            except:
                return HttpResponseRedirect(
                    reverse('rejected_article_overrides.list_overrides') +
                    '?from=new-error')
            # tasks.apply_override.s(override.override_id).delay()

    else:
        form = RejectedArticleOverrideForm()

    return render(request, 'rejected_article_overrides/new_override.html', {
        'form': form
    })


@login_required
def delete_override(request):
    form = RejectedArticleOverrideForm(request.POST)
    form.is_valid()
    publisher_id = form.cleaned_data['publisher_id']
    manuscript_id = form.cleaned_data['manuscript_id']
    doi = common.normalizedDoi(form.cleaned_data['doi'])
    label = form.cleaned_data['label']
    log.info('Deleting override: %s, %s, %s, %s' % (
      publisher_id, manuscript_id, doi, label
    ))
    try:
        RejectedArticleOverride.objects.get(publisher_id=publisher_id,
        manuscript_id=manuscript_id, doi=doi).delete()
        return HttpResponseRedirect(
            reverse('rejected_article_overrides.list_overrides') +
            '?from=delete-success')
    except:
        return HttpResponseRedirect(
            reverse('rejected_article_overrides.list_overrides') +
            '?from=delete-error')
