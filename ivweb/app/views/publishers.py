import datetime
from django import forms
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import Publisher_Metadata, Publisher_User, Audit_Log, User


@login_required
def list_publishers(request):
    if request.user.superuser:
        publishers = Publisher_Metadata.objects.all()
    else:
        publisher_id_list = [p.publisher_id for p in request.user.get_accessible_publishers()]
        publishers = Publisher_Metadata.objects.filter(publisher_id__in=publisher_id_list)
    return render(request, 'publishers/list.html', {'publishers': publishers})


class PublisherForm(forms.Form):
    publisher_id = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a short, unique identifier'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a name for display'}))
    published_articles_issns_to_lookup = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated ISSNs'}), required=False)
    issn_to_hw_journal_code = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated pairs of ISSN : Journal Code'}), required=False)
    scopus_api_keys = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated API keys'}), required=False)
    use_crossref = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    crossref_username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}), required=False)
    crossref_password = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Password'}), required=False)
    hw_addl_metadata_available = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    pilot = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    published_articles = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    rejected_articles = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    cohort_articles = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    report_username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}), required=False)
    report_password = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Password'}), required=False)
    project_folder = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project folder'}), required=False)

    def __init__(self, *args, instance=None, **kwargs):
        initial = {}
        if instance:
            self.instance = instance
            initial = dict(instance)
            initial['scopus_api_keys'] = ', '.join(initial['scopus_api_keys'])
            initial['published_articles_issns_to_lookup'] = ', '.join(initial['published_articles_issns_to_lookup'])
            initial['issn_to_hw_journal_code'] = ', '.join(['%s:%s' % (k, v) for k, v in initial['issn_to_hw_journal_code'].items()])
            initial['published_articles'] = 'published_articles' in initial['supported_products']
            initial['rejected_articles'] = 'rejected_articles' in initial['supported_products']
            initial['cohort_articles'] = 'cohort_articles' in initial['supported_products']
            initial['use_crossref'] = initial['crossref_username'] or initial['crossref_password']
        else:
            self.instance = None

        super(PublisherForm, self).__init__(initial=initial, *args, **kwargs)

    def clean_publisher_id(self):
        publisher_id = self.cleaned_data['publisher_id']

        if self.instance:
            return self.instance.publisher_id  # can't change this
        else:
            if Publisher_Metadata.objects.filter(publisher_id=publisher_id).count():
                raise forms.ValidationError("This publisher ID is already in use.")

        return publisher_id

    def save(self):
        supported_products = []
        if self.cleaned_data['published_articles']:
            supported_products.append('published_articles')
        if self.cleaned_data['rejected_articles']:
            supported_products.append('rejected_articles')
        if self.cleaned_data['cohort_articles']:
            supported_products.append('cohort_articles')

        scopus_api_keys = []
        if self.cleaned_data['scopus_api_keys']:
            scopus_api_keys = [s.strip() for s in self.cleaned_data['scopus_api_keys'].split(",")]

        published_articles_issns_to_lookup = []
        if self.cleaned_data['published_articles_issns_to_lookup']:
            published_articles_issns_to_lookup = [s.strip() for s in self.cleaned_data['published_articles_issns_to_lookup'].split(",")]

        issn_to_hw_journal_code = {}
        if self.cleaned_data['issn_to_hw_journal_code']:
            issn_to_hw_journal_code = {k: v for k, v in [[p.strip() for p in s.strip().split(":")] for s in self.cleaned_data['issn_to_hw_journal_code'].split(",")]}

        publisher_id = self.cleaned_data['publisher_id']
        Publisher_Metadata.objects(publisher_id=publisher_id).update(
            name=self.cleaned_data['name'],
            hw_addl_metadata_available=self.cleaned_data['hw_addl_metadata_available'],
            issn_to_hw_journal_code=issn_to_hw_journal_code,
            published_articles_issns_to_lookup=published_articles_issns_to_lookup,
            scopus_api_keys=scopus_api_keys,
            crossref_username=self.cleaned_data['crossref_username'],
            crossref_password=self.cleaned_data['crossref_password'],
            supported_products=supported_products,
            pilot=self.cleaned_data['pilot'],
        )

        publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)

        return publisher


@login_required
def edit(request, publisher_id=None):
    publisher = None
    new = True
    if publisher_id:
        new = False
        publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)

    if request.method == 'POST':
        form = PublisherForm(request.POST, instance=publisher)
        if form.is_valid():
            publisher = form.save()

            if new and not request.user.superuser:
                Publisher_User.objects.create(
                    user_id=request.user.user_id,
                    publisher_id=publisher.publisher_id,
                )

            Audit_Log.objects.create(
                user_id=request.user.user_id,
                event_time=datetime.datetime.now(),
                action='create-publisher' if new else 'edit-publisher',
                entity_type='publisher',
                entity_id=publisher.publisher_id,
            )

            return HttpResponseRedirect(reverse('publishers.list'))
    else:
        form = PublisherForm(instance=publisher)

    return render(request, 'publishers/new.html', {'form': form, 'publisher': publisher})
