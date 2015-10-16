from django import forms
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import Publisher_Metadata


@login_required
def list_publishers(request):
    publishers = Publisher_Metadata.objects.all()
    return render(request, 'publishers/list.html', {'publishers': publishers})


class PublisherForm(forms.Form):
    publisher_id = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a short, unique identifier'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a name for display'}))
    published_articles_issns_to_lookup = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated ISSNs'}), required=False)
    issn_to_hw_journal_code = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated pairs of ISSN : Journal Code'}), required=False)
    scopus_api_keys = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated API keys'}), required=False)
    crossref_username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}), required=False)
    crossref_password = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Password'}), required=False)
    hw_addl_metadata_available = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    pilot = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    published_articles = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    article_citations = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    custom_article_data = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    rejected_article_tracker = forms.BooleanField(widget=forms.CheckboxInput, required=False)

    def __init__(self, *args, instance=None, **kwargs):
        initial = {}
        if instance:
            initial = dict(instance)
            initial['scopus_api_keys'] = ','.join(initial['scopus_api_keys'])
            initial['published_articles_issns_to_lookup'] = ','.join(initial['published_articles_issns_to_lookup'])
            initial['issn_to_hw_journal_code'] = ','.join(['%s:%s' % (k, v) for k, v in initial['issn_to_hw_journal_code'].items()])
            initial['published_articles'] = 'published_articles' in initial['supported_pipelines']
            initial['article_citations'] = 'article_citations' in initial['supported_pipelines']
            initial['custom_article_data'] = 'custom_article_data' in initial['supported_pipelines']
            initial['rejected_article_tracker'] = 'rejected_article_tracker' in initial['supported_pipelines']

        super(PublisherForm, self).__init__(initial=initial, *args, **kwargs)

    def save(self):
        supported_pipelines = []
        if self.cleaned_data['published_articles']:
            supported_pipelines.append('article_citations')
        if self.cleaned_data['article_citations']:
            supported_pipelines.append('published_articles')
        if self.cleaned_data['custom_article_data']:
            supported_pipelines.append('custom_article_data')
        if self.cleaned_data['rejected_article_tracker']:
            supported_pipelines.append('rejected_article_tracker')

        scopus_api_keys = []
        if self.cleaned_data['scopus_api_keys']:
            scopus_api_keys = [s.strip() for s in self.cleaned_data['scopus_api_keys'].split(",")]

        published_articles_issns_to_lookup = []
        if self.cleaned_data['published_articles_issns_to_lookup']:
            published_articles_issns_to_lookup = [s.strip() for s in self.cleaned_data['published_articles_issns_to_lookup'].split(",")]

        issn_to_hw_journal_code = {}
        if self.cleaned_data['issn_to_hw_journal_code']:
            issn_to_hw_journal_code = {k: v for k, v in [[p.strip() for p in s.strip().split(":")] for s in self.cleaned_data['issn_to_hw_journal_code'].split(",")]}

        publisher = Publisher_Metadata.objects(publisher_id=self.cleaned_data['publisher_id']).update(
            name=self.cleaned_data['name'],
            hw_addl_metadata_available=self.cleaned_data['hw_addl_metadata_available'],
            issn_to_hw_journal_code=issn_to_hw_journal_code,
            published_articles_issns_to_lookup=published_articles_issns_to_lookup,
            scopus_api_keys=scopus_api_keys,
            crossref_username=self.cleaned_data['crossref_username'],
            crossref_password=self.cleaned_data['crossref_password'],
            supported_pipelines=supported_pipelines,
            pilot=self.cleaned_data['pilot'],
        )

        return publisher


@login_required
def edit(request, publisher_id=None):
    publisher = None
    if publisher_id:
        publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)

    if request.method == 'POST':
        form = PublisherForm(request.POST, instance=publisher)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('publishers.list'))
    else:
        form = PublisherForm(instance=publisher)

    return render(request, 'publishers/new.html', {'form': form, 'publisher': publisher})
