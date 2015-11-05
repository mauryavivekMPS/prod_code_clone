import datetime
import requests
import json
from django import forms
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import Publisher_Metadata, Publisher_User, Audit_Log, Publisher_Journal
from ivetl.common import common


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
        self.issn_values_list = []
        initial = {}
        if instance:
            self.instance = instance
            initial = dict(instance)
            initial['scopus_api_keys'] = ', '.join(initial['scopus_api_keys'])
            initial['published_articles'] = 'published_articles' in initial['supported_products']
            initial['rejected_articles'] = 'rejected_articles' in initial['supported_products']
            initial['cohort_articles'] = 'cohort_articles' in initial['supported_products']
            initial['use_crossref'] = initial['crossref_username'] or initial['crossref_password']

            for code in Publisher_Journal.objects.filter(publisher_id=instance.publisher_id):
                self.issn_values_list.append({
                    'product_id': 'published_articles',
                    'electronic_issn': code.electronic_issn,
                    'print_issn': code.print_issn,
                    'journal_code': code.journal_code,
                })
            initial['issn_values'] = json.dumps(self.issn_values_list)

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

        publisher_id = self.cleaned_data['publisher_id']
        Publisher_Metadata.objects(publisher_id=publisher_id).update(
            name=self.cleaned_data['name'],
            hw_addl_metadata_available=self.cleaned_data['hw_addl_metadata_available'],
            scopus_api_keys=scopus_api_keys,
            crossref_username=self.cleaned_data['crossref_username'],
            crossref_password=self.cleaned_data['crossref_password'],
            supported_products=supported_products,
            pilot=self.cleaned_data['pilot'],
        )

        publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)

        Publisher_Journal.objects.filter(publisher_id=publisher_id).delete()
        for issn_value in json.loads(self.cleaned_data['issn_values']):
            Publisher_Journal.objects.create(
                product_id='published_articles',
                publisher_id=publisher_id,
                electronic_issn=issn_value['electronic_issn'],
                print_issn=issn_value['print_issn'],
                journal_code=issn_value['journal_code'],
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

    return render(request, 'publishers/new.html', {
        'form': form,
        'publisher': publisher,
        'issn_values_list': form.issn_values_list,
        'issn_values_json': json.dumps(form.issn_values_list),
    })


@login_required
def validate_crossref(request):
    username = request.GET['username']
    password = request.GET['password']
    r = requests.get('http://doi.crossref.org/servlet/getForwardLinks?usr=%s&pwd=%s' % (username, password))

    if r.status_code == 400:
        return HttpResponse('ok')

    return HttpResponse('fail')


def validate_issn(issn):
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


def validate_journal_code(code):
    r = requests.get('http://sass.highwire.org/%s.atom' % code)
    if r.status_code == 200 and '<atom:id>' in r.text:
            return True
    return False


@login_required
def add_issn_values(request):
    raw_issn_values = request.POST.get('issn_values', '')
    new_electronic_issn = request.POST.get('new_electronic_issn', '')
    new_print_issn = request.POST.get('new_print_issn', '')
    new_journal_code = request.POST.get('new_journal_code', '')
    new_electronic_issn_error = False
    new_print_issn_error = False
    new_journal_code_error = False

    if raw_issn_values:
        issn_values_list = json.loads(raw_issn_values)
    else:
        issn_values_list = []

    if new_electronic_issn:
        if not validate_issn(new_electronic_issn):
            new_electronic_issn_error = True

        if new_journal_code:
            if not validate_journal_code(new_journal_code):
                new_journal_code_error = True

        # if we have good values, add them to the list and clear out the values
        if not new_electronic_issn_error and not new_journal_code_error:
            issn_values_list.append({
                'electronic_issn': new_electronic_issn,
                'print_issn': new_print_issn,
                'journal_code': new_journal_code,
            })

            new_electronic_issn = ''
            new_print_issn = ''
            new_journal_code = ''

    return render(request, 'publishers/include/issn_table.html', {
        'issn_values_list': issn_values_list,
        'issn_values_json': json.dumps(issn_values_list),
        'new_electronic_issn': new_electronic_issn,
        'new_electronic_issn_error': new_electronic_issn_error,
        'new_print_issn': new_print_issn,
        'new_print_issn_error': new_print_issn_error,
        'new_journal_code': new_journal_code,
        'new_journal_code_error': new_journal_code_error,
        'is_include': True,
    })

def register_for_scopus():
    'https://www.developers.elsevier.com/action/customer/profile/display?pageOrigin=home&zone=header&'
    'http://www.developers.elsevier.com/action/devprojects?originPageLogout=devportal&icr=true'
    'http://www.developers.elsevier.com/action/devnewsite'
