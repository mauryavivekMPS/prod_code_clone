import datetime
import requests
import json
import time
from bs4 import BeautifulSoup
from django import forms
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.http import JsonResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import Publisher_Metadata, Publisher_User, Audit_Log, Publisher_Journal, Scopus_Api_Key


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
    issn_values = forms.CharField(widget=forms.HiddenInput)
    use_scopus_api_keys_from_pool = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    scopus_api_keys = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated API keys'}), required=False)
    email = forms.CharField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    use_crossref = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    crossref_username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}), required=False)
    crossref_password = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Password'}), required=False)
    hw_addl_metadata_available = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    pilot = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    published_articles = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    rejected_manuscripts = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    cohort_articles = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    issn_values_cohort = forms.CharField(widget=forms.HiddenInput, required=False)
    report_username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}), required=False)
    report_password = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Password'}), required=False)
    project_folder = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project folder'}), required=False)

    def __init__(self, creating_user, *args, instance=None, **kwargs):
        self.creating_user = creating_user
        self.issn_values_list = []
        self.issn_values_cohort_list = []
        initial = {}
        if instance:
            self.instance = instance
            initial = dict(instance)
            initial['scopus_api_keys'] = ', '.join(initial['scopus_api_keys'])
            initial['published_articles'] = 'published_articles' in initial['supported_products']
            initial['rejected_manuscripts'] = 'rejected_manuscripts' in initial['supported_products']
            initial['cohort_articles'] = 'cohort_articles' in initial['supported_products']
            initial['use_crossref'] = initial['crossref_username'] or initial['crossref_password']

            index = 0
            for code in Publisher_Journal.objects.filter(publisher_id=instance.publisher_id, product_id='published_articles'):
                self.issn_values_list.append({
                    'product_id': 'published_articles',
                    'electronic_issn': code.electronic_issn,
                    'print_issn': code.print_issn,
                    'journal_code': code.journal_code,
                    'index': 'pa-%s' % index,  # just needs to be unique on the page
                })
                index += 1
            initial['issn_values'] = json.dumps(self.issn_values_list)

            for code in Publisher_Journal.objects.filter(publisher_id=instance.publisher_id, product_id='cohort_articles'):
                self.issn_values_cohort_list.append({
                    'product_id': 'cohort_articles',
                    'electronic_issn': code.electronic_issn,
                    'print_issn': code.print_issn,
                    'index': 'ca-%s' % index,  # ditto, needs to be unique on the page
                })
                index += 1
            initial['issn_values_cohort'] = json.dumps(self.issn_values_cohort_list)

        else:
            self.instance = None
            initial['use_scopus_api_keys_from_pool'] = True

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
        if self.cleaned_data['rejected_manuscripts']:
            supported_products.append('rejected_manuscripts')
        if self.cleaned_data['cohort_articles']:
            supported_products.append('cohort_articles')

        scopus_api_keys = []
        if self.cleaned_data['scopus_api_keys']:
            scopus_api_keys = [s.strip() for s in self.cleaned_data['scopus_api_keys'].split(",")]
        if not self.instance and self.cleaned_data['use_scopus_api_keys_from_pool']:
            # grab 5 API keys from the pool
            for key in Scopus_Api_Key.objects.all()[:5]:
                scopus_api_keys.append(key.key)
                key.delete()

        publisher_id = self.cleaned_data['publisher_id']
        Publisher_Metadata.objects(publisher_id=publisher_id).update(
            name=self.cleaned_data['name'],
            email=self.cleaned_data['email'],
            hw_addl_metadata_available=self.cleaned_data['hw_addl_metadata_available'],
            scopus_api_keys=scopus_api_keys,
            crossref_username=self.cleaned_data['crossref_username'],
            crossref_password=self.cleaned_data['crossref_password'],
            supported_products=supported_products,
            pilot=self.cleaned_data['pilot'],
        )

        publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)

        Publisher_Journal.objects.filter(publisher_id=publisher_id).delete()
        if self.cleaned_data['issn_values']:
            for issn_value in json.loads(self.cleaned_data['issn_values']):
                Publisher_Journal.objects.create(
                    product_id='published_articles',
                    publisher_id=publisher_id,
                    electronic_issn=issn_value['electronic_issn'],
                    print_issn=issn_value['print_issn'],
                    journal_code=issn_value['journal_code'],
                )
        if self.cleaned_data['issn_values_cohort']:
            for issn_value in json.loads(self.cleaned_data['issn_values_cohort']):
                Publisher_Journal.objects.create(
                    product_id='cohort_articles',
                    publisher_id=publisher_id,
                    electronic_issn=issn_value['electronic_issn'],
                    print_issn=issn_value['print_issn'],
                )

        return publisher


@login_required
def edit(request, publisher_id=None):
    publisher = None
    new = True
    if publisher_id:
        new = False
        publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)

    if request.method == 'POST':
        form = PublisherForm(request.user, request.POST, instance=publisher)
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
        form = PublisherForm(request.user, instance=publisher)

    return render(request, 'publishers/new.html', {
        'form': form,
        'publisher': publisher,
        'issn_values_list': form.issn_values_list,
        'issn_values_json': json.dumps(form.issn_values_list),
        'issn_values_cohort_list': form.issn_values_cohort_list,
        'issn_values_cohort_json': json.dumps(form.issn_values_cohort_list),
    })


@login_required
def validate_crossref(request):
    username = request.GET['username']
    password = request.GET['password']
    r = requests.get('http://doi.crossref.org/servlet/getForwardLinks?usr=%s&pwd=%s' % (username, password))

    if r.status_code == 400:
        return HttpResponse('ok')

    return HttpResponse('fail')


@login_required
def validate_issn(request):
    electronic_issn = request.GET['electronic_issn']
    print_issn = request.GET['print_issn']

    electronic_issn_ok = check_issn(electronic_issn)

    if 'journal_code' in request.GET:
        journal_code = request.GET['journal_code']

        r = requests.get('http://sass.highwire.org/%s.atom' % journal_code)
        if r.status_code == 200 and '<atom:id>' in r.text:
            journal_code_ok = True

            soup = BeautifulSoup(r.content, 'xml')
            matching_electronic_issn = soup.find('pub-id', attrs={'pub-id-type': "eissn"}).text
            matching_print_issn = soup.find('pub-id', attrs={'pub-id-type': "issn"}).text

            if electronic_issn == matching_electronic_issn and print_issn == matching_print_issn:
                matching_codes = True
            else:
                matching_codes = False
        else:
            journal_code_ok = False
            matching_codes = True  # can't test until journal code is ok

    else:
        journal_code_ok = True
        matching_codes = True

    if electronic_issn_ok and journal_code_ok:
        if matching_codes:
            # things are ok
            return JsonResponse({
                'status': 'ok',
            })
        else:
            # thigns are ok, but return a warning
            return JsonResponse({
                'status': 'warning',
                'warning_message': "The ISSNs do not match the HighWire database.",
            })

    error_fields = []

    if not electronic_issn_ok:
        error_fields.append('Electronic ISSN')

    if not journal_code_ok:
        error_fields.append('Journal Code')

    if len(error_fields) == 1:
        error_message = error_fields[0]
    elif len(error_fields) == 2:
        error_message = error_fields[0] + ' and ' + error_fields[1]
    elif len(error_fields) > 2:
        error_message = ", ".join(error_fields[:-1]) + ' and ' + error_fields[len(error_fields - 1)]

    # things are bad
    return JsonResponse({
        'status': 'error',
        'error_message': "Validation failed for %s." % error_message,
    })


def check_issn(issn):
    r = requests.get('http://api.crossref.org/journals/%s' % issn)
    if r.status_code == 200:
        try:
            issn_json = r.json()
            # the title below seems to show up for most random ISSNs, so treating it as an error
            if issn_json['message']['title'] != 'Zeitschrift für Die Gesamte Experimentelle Medizin einschließlich experimenteller Chirurgie':
                return True
        except ValueError:
            pass
    return False


@login_required
def new_issn(request):
    return render(request, 'publishers/include/issn_row.html', {
        'index': str(time.time()).replace('.', ''),  # just a non-clashing random number
        'cohort': 'cohort' in request.GET,
        'is_include': True,
    })
