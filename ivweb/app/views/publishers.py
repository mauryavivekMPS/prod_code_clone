import datetime
import requests
import json
import time
import uuid
from bs4 import BeautifulSoup
from django import forms
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.http import JsonResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import Publisher_Metadata, Publisher_User, Audit_Log, Publisher_Journal, Scopus_Api_Key, Demo
from ivetl.tasks import setup_reports
from ivetl.connectors import TableauConnector
from ivetl.common import common
from .pipelines import get_pending_files_for_demo, move_demo_files_to_pending


@login_required
def list_publishers(request):
    alt_error_message = ''
    messages = []
    if 'from' in request.GET:
        from_value = request.GET['from']
        if from_value == 'no-keys':
            alt_error_message = 'There are no Scopus API keys available. Please contact your administrator before creating a new publisher.'
        elif from_value == 'new-error':
            alt_error_message = 'There was an error setting up reports for the new publisher in Tableau. Please contact your administrator.'
        elif from_value == 'save-success':
            messages.append("Changes to your publisher account have been saved.")
        elif from_value == 'new-success':
            messages.append("Your new publisher account is created and ready to go.")

    list_type = request.GET.get('list_type', 'all')

    if request.user.superuser:
        all_accessible_publishers = Publisher_Metadata.objects.all()
    else:
        all_accessible_publishers = request.user.get_accessible_publishers()

    filtered_publishers = []
    for publisher in all_accessible_publishers:
        if publisher.publisher_id != common.HW_PUBLISHER_ID:  # special case to exclude the HighWire publisher record
            if list_type == 'all' or (list_type == 'demos' and publisher.demo) or (list_type == 'publishers' and not publisher.demo):
                filtered_publishers.append(publisher)

    descending = False
    sort = request.GET.get('sort', 'name')
    if sort.startswith('-'):
        descending = True
        sort_key = sort[1:]
    else:
        sort_key = sort

    filtered_publishers = sorted(filtered_publishers, key=lambda p: p[sort_key], reverse=descending)

    return render(request, 'publishers/list.html', {
        'publishers': filtered_publishers,
        'alt_error_message': alt_error_message,
        'messages': messages,
        'reset_url': reverse('publishers.list') + '?sort=' + sort,
        'list_type': list_type,
        'sort_key': sort_key,
        'descending': descending,
    })


@login_required
def list_demos(request):
    messages = []
    if 'from' in request.GET:
        from_value = request.GET['from']
        if from_value == 'save-success':
            messages.append("The changes to your demo have been saved.")
        elif from_value == 'new-success':
            messages.append("Your new demo has been created and successfully saved.")
        elif from_value == 'submitted-for-review':
            messages.append("Your demo has been submitted for review! As the administrator completes the configuration "
                            "and testing of the demo account you'll receive progress updates via email. Or you can "
                            "check back here any time.")
    if request.user.superuser:
        demos = Demo.objects.all()
    else:
        demos = Demo.objects.filter(requestor_id=request.user.user_id)
    demos = sorted(demos, key=lambda p: p.name.lower().lstrip('('))
    return render(request, 'publishers/list_demos.html', {
        'demos': demos,
        'messages': messages,
        'reset_url': reverse('publishers.list_demos'),
    })


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
    demo = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    demo_id = forms.CharField(widget=forms.HiddenInput, required=False)
    published_articles = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    rejected_manuscripts = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    cohort_articles = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    issn_values_cohort = forms.CharField(widget=forms.HiddenInput, required=False)
    reports_username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}), required=False)
    reports_password = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Password', 'style': 'display:none'}), required=False)
    reports_project = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project folder'}), required=False)

    # demo-specific fields
    start_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control'}, format='%m/%d/%Y'), required=False)
    demo_notes = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Add notes about the demo'}), required=False)
    status = forms.ChoiceField(choices=common.DEMO_STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    convert_to_publisher = forms.BooleanField(widget=forms.HiddenInput, required=False)
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter custom message for notification email (optional)'}), required=False)

    def __init__(self, creating_user, *args, instance=None, is_demo=False, convert_from_demo=False, **kwargs):
        self.is_demo = is_demo
        self.creating_user = creating_user
        self.issn_values_list = []
        self.issn_values_cohort_list = []
        initial = {}
        if instance:
            self.instance = instance
            initial = dict(instance)

            if self.is_demo or convert_from_demo:
                properties = json.loads(initial.get('properties', '{}'))
                initial['hw_addl_metadata_available'] = properties.get('hw_addl_metadata_available', False)
                initial['use_crossref'] = properties.get('use_crossref', False)
                initial['supported_products'] = properties.get('supported_products', [])
                initial['crossref_username'] = properties.get('crossref_username')
                initial['crossref_password'] = properties.get('crossref_password')
                initial['issn_values_list'] = properties.get('issn_values_list', [])
                initial['issn_values_cohort_list'] = properties.get('issn_values_cohort_list', [])
                initial['demo_notes'] = properties.get('demo_notes')

            initial.pop('reports_password', None)  # clear out the encoded password
            initial['scopus_api_keys'] = ', '.join(initial.get('scopus_api_keys', []))
            initial['published_articles'] = 'published_articles' in initial['supported_products']
            initial['rejected_manuscripts'] = 'rejected_manuscripts' in initial['supported_products']
            initial['cohort_articles'] = 'cohort_articles' in initial['supported_products']
            initial['use_crossref'] = initial.get('use_crossref') or initial['crossref_username'] or initial['crossref_password']

            if self.is_demo or convert_from_demo:
                self.issn_values_list = initial['issn_values_list']
                initial['issn_values'] = json.dumps(self.issn_values_list)
            else:
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

            if self.is_demo or convert_from_demo:
                self.issn_values_cohort_list = initial['issn_values_cohort_list']
                initial['issn_values_cohort'] = json.dumps(self.issn_values_cohort_list)
            else:
                index = 0
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
            initial['status'] = common.DEMO_STATUS_CREATING

        # pre-initialize the demo ID so that we can upload files to a known location
        if is_demo and not instance:
            initial['demo_id'] = str(uuid.uuid4())

        if convert_from_demo:
            initial['demo'] = True

        super(PublisherForm, self).__init__(initial=initial, *args, **kwargs)

        if self.is_demo:
            self.fields['publisher_id'].required = False
            self.fields['email'].required = False
            self.fields['issn_values'].required = False
            self.fields['name'].widget.attrs['placeholder'] = 'Enter demo publisher name'

    def clean_publisher_id(self):
        publisher_id = self.cleaned_data['publisher_id']

        if not self.is_demo:
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

        if self.is_demo:
            demo_id = self.cleaned_data['demo_id']

            demo = None
            if demo_id:
                try:
                    demo = Demo.objects.get(demo_id=demo_id)
                except Demo.DoesNotExist:
                    pass

            if not demo:
                demo = Demo.objects.create(
                    demo_id=demo_id,
                    requestor_id=self.creating_user.user_id
                )

            properties = {
                'hw_addl_metadata_available': self.cleaned_data['hw_addl_metadata_available'],
                'use_crossref': self.cleaned_data['use_crossref'],
                'crossref_username': self.cleaned_data['crossref_username'],
                'crossref_password': self.cleaned_data['crossref_password'],
                'supported_products': supported_products,
                'issn_values_list': json.loads(self.cleaned_data['issn_values']),
                'issn_values_cohort_list': json.loads(self.cleaned_data['issn_values_cohort']),
                'demo_notes': self.cleaned_data['demo_notes'],
            }

            status = self.cleaned_data.get('status')
            if not status:
                status = common.DEMO_STATUS_CREATING

            demo.update(
                name=self.cleaned_data['name'],
                start_date=self.cleaned_data['start_date'],
                status=status,
                properties=json.dumps(properties),
            )

            return demo

        else:
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
                demo=self.cleaned_data['demo'],
                demo_id=self.cleaned_data['demo_id'],
            )

            publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)

            if self.instance:
                new_password = self.cleaned_data['reports_password']
                if new_password:
                    t = TableauConnector(
                        username=common.TABLEAU_USERNAME,
                        password=common.TABLEAU_PASSWORD,
                        server=common.TABLEAU_SERVER
                    )
                    t.set_user_password(publisher.reports_user_id, new_password)
                    publisher.update(
                        reports_password=self.cleaned_data['reports_password'],
                    )
            else:
                publisher.update(
                    reports_username=self.cleaned_data['reports_username'],
                    reports_password=self.cleaned_data['reports_password'],
                    reports_project=self.cleaned_data['reports_project'],
                )

            for journal in Publisher_Journal.objects.filter(publisher_id=publisher_id):
                journal.delete()

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
    convert_from_demo = False
    if publisher_id:
        new = False
        publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)

    # bail quickly if there are no API keys
    if new:
        if Scopus_Api_Key.objects.count() < 5:
            return HttpResponseRedirect(reverse('publishers.list') + '?from=no-keys')

    from_value = ''
    demo_files_custom_article_data = []
    demo_files_rejected_articles = []

    if request.method == 'POST':
        form = PublisherForm(request.user, request.POST, instance=publisher)
        if form.is_valid():
            publisher = form.save()

            if new:
                if not request.user.superuser:
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

                # move any uploaded files across if this was a conversion
                if publisher.demo:
                    move_demo_files_to_pending(publisher.demo_id, publisher.publisher_id, 'published_articles', 'custom_article_data')
                    move_demo_files_to_pending(publisher.demo_id, publisher.publisher_id, 'rejected_manuscripts', 'rejected_articles')

                # tableau setup takes a while, run it through celery
                setup_reports.s(publisher.publisher_id, request.user.user_id).delay()

                return HttpResponseRedirect(reverse("publishers.edit", kwargs={
                    'publisher_id': publisher.publisher_id,
                }) + '?from=new-publisher')

            return HttpResponseRedirect(reverse('publishers.list') + '?from=save-success')
    else:
        from_value = ''
        if 'from' in request.GET:
            from_value = request.GET['from']

        if 'demo_id' in request.GET:
            convert_from_demo = True
            demo = Demo.objects.get(demo_id=request.GET['demo_id'])
            form = PublisherForm(request.user, instance=demo, convert_from_demo=True)
            demo_files_custom_article_data = get_pending_files_for_demo(demo.demo_id, 'published_articles', 'custom_article_data')
            demo_files_rejected_articles = get_pending_files_for_demo(demo.demo_id, 'rejected_manuscripts', 'rejected_articles')

        else:
            form = PublisherForm(request.user, instance=publisher)

    demo_from_publisher = None
    if publisher and publisher.demo_id:
        demo_from_publisher = Demo.objects.get(demo_id=publisher.demo_id)

    return render(request, 'publishers/new.html', {
        'form': form,
        'publisher': publisher,
        'is_demo': False,
        'convert_from_demo': convert_from_demo,
        'issn_values_list': form.issn_values_list,
        'issn_values_json': json.dumps(form.issn_values_list),
        'issn_values_cohort_list': form.issn_values_cohort_list,
        'issn_values_cohort_json': json.dumps(form.issn_values_cohort_list),
        'from_value': from_value,
        'demo_from_publisher': demo_from_publisher,
        'demo_files_custom_article_data': demo_files_custom_article_data,
        'demo_files_rejected_articles': demo_files_rejected_articles
    })


@login_required
def edit_demo(request, demo_id=None):
    demo = None
    new = True
    if demo_id:
        demo = Demo.objects.get(demo_id=demo_id)
        new = False

    if request.method == 'POST':
        form = PublisherForm(request.user, request.POST, instance=demo, is_demo=True)
        if form.is_valid():

            previous_status = None
            if demo:
                previous_status = demo.status

            demo = form.save()

            if previous_status and demo.status != previous_status:
                _notify_on_new_status(demo, request, message=form.cleaned_data['message'])

            if new:
                from_value = 'new-success'
            else:
                from_value = 'save-success'

            if not request.user.superuser and demo.status == common.DEMO_STATUS_SUBMITTED_FOR_REVIEW:
                from_value = 'submitted-for-review'


            if request.user.superuser and form.cleaned_data['convert_to_publisher']:
                return HttpResponseRedirect(reverse('publishers.new') + '?demo_id=%s' % demo.demo_id)

            return HttpResponseRedirect(reverse('publishers.list_demos') + '?from=' + from_value)
    else:
        form = PublisherForm(request.user, instance=demo, is_demo=True)

    demo_files_custom_article_data = []
    demo_files_rejected_articles = []
    publisher_from_demo = None

    if demo:
        demo_files_custom_article_data = get_pending_files_for_demo(demo_id, 'published_articles', 'custom_article_data', with_lines_and_sizes=True)
        demo_files_rejected_articles = get_pending_files_for_demo(demo_id, 'rejected_manuscripts', 'rejected_articles', with_lines_and_sizes=True)

        try:
            publisher_from_demo = Publisher_Metadata.objects.get(demo_id=demo_id)
        except Publisher_Metadata.DoesNotExist:
            pass

    else:
        demo_id = form.initial['demo_id']

    read_only = False
    if not form.initial.get('status', common.DEMO_STATUS_CREATING) in (common.DEMO_STATUS_CREATING, common.DEMO_STATUS_CHANGES_NEEDED):
        if not request.user.superuser:
            read_only = True
            for f in form.fields:
                form.fields[f].widget.attrs['readonly'] = True
                form.fields[f].widget.attrs['disabled'] = True

    return render(request, 'publishers/new.html', {
        'form': form,
        'demo': demo,
        'demo_id': demo_id,
        'is_demo': True,
        'issn_values_list': form.issn_values_list,
        'issn_values_json': json.dumps(form.issn_values_list),
        'issn_values_cohort_list': form.issn_values_cohort_list,
        'issn_values_cohort_json': json.dumps(form.issn_values_cohort_list),
        'demo_files_custom_article_data': demo_files_custom_article_data,
        'demo_files_rejected_articles': demo_files_rejected_articles,
        'read_only': read_only,
        'publisher_from_demo': publisher_from_demo,
    })


@login_required
def check_reports(request):
    publisher_id = request.GET['publisher']
    publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)
    return JsonResponse({
        'status': publisher.reports_setup_status,
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


def _notify_on_new_status(demo, request, message=None):

    message_html = ''
    if message:
        message_html = '<p>---</p><p>' + message.replace('\n', '</p><p>') + '<p>---</p></p>'

    if demo.status == common.DEMO_STATUS_ACCEPTED:
        subject = "Impact Vizor (%s): Your demo has been accepted" % demo.name
        body = """
            <p>Your demo request has all of the required information. You'll be notified as progress updates are available.</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;Demo details: <a href="%s">%s</a></p>
            %s
            <p>Thank you,<br/>Impact Vizor Admin</p>
        """ % (
            request.build_absolute_uri(reverse('publishers.edit_demo', kwargs={'demo_id': demo.demo_id})),
            demo.name,
            message_html,
        )
        common.send_email(subject=subject, body=body, to=demo.requestor.email)

    elif demo.status == common.DEMO_STATUS_CHANGES_NEEDED:
        subject = "Impact Vizor (%s): Your demo needs changes" % demo.name
        body = """
            <p>Changes are needed to complete your demo request.</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;Demo details: <a href="%s">%s</a></p>
            <p>Please visit the demo page using the link above and resubmit when your changes are complete.</p>
            %s
            <p>Thank you,<br/>Impact Vizor Admin</p>
        """ % (
            request.build_absolute_uri(reverse('publishers.edit_demo', kwargs={'demo_id': demo.demo_id})),
            demo.name,
            message_html,
        )
        common.send_email(subject=subject, body=body, to=demo.requestor.email)

    elif demo.status == common.DEMO_STATUS_IN_PROGRESS:
        subject = "Impact Vizor (%s): Your demo is being setup" % demo.name
        body = """
            <p>We are in the process of building your demo.</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;Demo details: <a href="%s">%s</a></p>
            <p>You'll be notified once setup is complete.</p>
            %s
            <p>Thank you,<br/>Impact Vizor Admin</p>
        """ % (
            request.build_absolute_uri(reverse('publishers.edit_demo', kwargs={'demo_id': demo.demo_id})),
            demo.name,
            message_html
        )
        common.send_email(subject=subject, body=body, to=demo.requestor.email)

    elif demo.status == common.DEMO_STATUS_COMPLETED:

        publisher = Publisher_Metadata.objects.get(demo_id=demo.demo_id)

        subject = "Impact Vizor (%s): Your demo is ready" % demo.name
        body = """
            <p>Your demo is now marked as being complete and is ready for use.</p>
            <p>View reports at <a href="https://login.vizors.org/">login.vizors.org</a> in the %s project folder.</p>
            %s
            <p>Thank you,<br/>Impact Vizor Admin</p>
        """ % (publisher.reports_project, message_html)
        common.send_email(subject=subject, body=body, to=demo.requestor.email)

    elif demo.status == common.DEMO_STATUS_SUBMITTED_FOR_REVIEW:

        # notify the admin, not the end user

        subject = "Impact Vizor (%s): New demo submitted" % demo.name
        body = """
            <p>A demo was submitted for review by %s:</p>
            <p>&nbsp;&nbsp;&nbsp;&nbsp;<a href="%s">%s</a> (%s)</p>
        """ % (
            request.user.display_name,
            request.build_absolute_uri(reverse('publishers.edit_demo', kwargs={'demo_id': demo.demo_id})),
            demo.name,
            ", ".join([common.PRODUCT_BY_ID[product_id]['name'] for product_id in json.loads(demo.properties)['supported_products']]),
        )
        common.send_email(subject=subject, body=body)


@login_required
def update_demo_status(request):
    if request.POST:
        demo_id = request.POST['demo_id']
        demo = Demo.objects.get(demo_id=demo_id)
        status = request.POST['status']
        demo.status = status
        demo.save()

        message = request.POST.get('message')
        _notify_on_new_status(demo, request, message=message)

    return HttpResponse('ok')
