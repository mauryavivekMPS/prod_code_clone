import logging
import requests
import datetime
from operator import attrgetter
from django import forms
from django.http import JsonResponse
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import TableauAlert, TableauNotification, PublisherMetadata, WorkbookUrl
from ivetl.tableau_alerts import ALERT_TEMPLATES, ALERT_TEMPLATES_BY_SOURCE_PIPELINE
from ivweb.app.views import utils as view_utils
from ivetl.common import common

log = logging.getLogger(__name__)


@login_required
def list_alerts(request):

    messages = []
    if 'from' in request.GET:
        from_value = request.GET['from']
        if from_value == 'save-success':
            messages.append("Changes to your alert have been saved.")
        elif from_value == 'new-success':
            messages.append("Your new alert is created and ready to go.")

    single_publisher_user = False
    if request.user.superuser:
        alerts = TableauAlert.objects.filter(archived=False)
    else:
        accessible_publisher_ids = [p.publisher_id for p in request.user.get_accessible_publishers()]
        alerts = TableauAlert.objects.filter(publisher_id__in=accessible_publisher_ids, archived=False)
        if len(accessible_publisher_ids) == 1:
            single_publisher_user = True

    filter_param = request.GET.get('filter', request.COOKIES.get('tableau-alert-list-filter', 'all'))

    filtered_alerts = []
    if filter_param == 'all':
        filtered_alerts = alerts
    elif filter_param == 'enabled':
        for alert in alerts:
            if alert.enabled:
                filtered_alerts.append(alert)
    elif filter_param == 'disabled':
        for alert in alerts:
            if not alert.enabled:
                filtered_alerts.append(alert)

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('tableau-alert-list-sort', 'publisher_id'))
    sorted_alerts = sorted(filtered_alerts, key=attrgetter(sort_key), reverse=sort_descending)

    for alert in sorted_alerts:
        alert_type = ALERT_TEMPLATES[alert.template_id]
        setattr(alert, 'name', alert_type['name'])

    response = render(request, 'tableau_alerts/list.html', {
        'alerts': sorted_alerts,
        'messages': messages,
        'reset_url': reverse('tableau_alerts.list') + '?sort=' + sort_param,
        'sort_key': sort_key,
        'filter_param': filter_param,
        'sort_descending': sort_descending,
        'single_publisher_user': single_publisher_user,
    })

    response.set_cookie('tableau-alert-list-sort', value=sort_param, max_age=30*24*60*60)
    response.set_cookie('tableau-alert-list-filter', value=filter_param, max_age=30*24*60*60)

    return response


class TableauAlertForm(forms.Form):
    alert_id = forms.CharField(widget=forms.HiddenInput, required=False)
    publisher_id = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), required=True)
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alert Name'}), required=True)
    template_id = forms.CharField(widget=forms.HiddenInput, required=True)
    alert_params = forms.CharField(widget=forms.HiddenInput, required=False)
    alert_filters = forms.CharField(widget=forms.HiddenInput, required=False)
    attachment_only_emails = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Comma-separated emails'}), required=False)
    full_emails = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Comma-separated emails'}), required=False)
    custom_message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Plain text custom message, no HTML'}), required=False)
    enabled = forms.BooleanField(widget=forms.CheckboxInput, initial=True, required=False)
    send_with_no_data = forms.BooleanField(widget=forms.CheckboxInput, initial=True, required=False)

    def __init__(self, *args, instance=None, user=None, **kwargs):
        initial = {}

        if instance:
            self.instance = instance
            initial = dict(instance)
            initial['attachment_only_emails'] = ", ".join(instance.attachment_only_emails)
            initial['full_emails'] = ", ".join(instance.full_emails)
        else:
            self.instance = None

        super(TableauAlertForm, self).__init__(initial=initial, *args, **kwargs)

        if user.superuser:
            publisher_choices = [(p.publisher_id, p.name) for p in PublisherMetadata.objects.all()]
        else:
            publisher_choices = [(p.publisher_id, p.name) for p in user.get_accessible_publishers()]

        self.fields['publisher_id'].choices = publisher_choices

        if len(publisher_choices) > 1:
            self.fields['publisher_id'].choices.insert(0, ('', 'Select a publisher'))

    def save(self):
        alert_id = self.cleaned_data['alert_id']
        template_id = self.cleaned_data["template_id"]
        if alert_id:
            alert = TableauAlert.objects.get(
                alert_id=alert_id,
            )
        else:
            alert = TableauAlert.objects.create(
                publisher_id=self.cleaned_data['publisher_id'],
                template_id=template_id,
            )

        attachment_only_emails_string = self.cleaned_data.get('attachment_only_emails')
        full_emails_string = self.cleaned_data.get('full_emails')
        attachment_only_emails = [email.strip() for email in attachment_only_emails_string.split(",") if attachment_only_emails_string]
        full_emails = [email.strip() for email in full_emails_string.split(",") if full_emails_string]

        alert.update(
            name=self.cleaned_data['name'],
            alert_params=self.cleaned_data.get('alert_params', '{}'),
            alert_filters=self.cleaned_data.get('alert_filters', '{}'),
            attachment_only_emails=attachment_only_emails,
            full_emails=full_emails,
            custom_message=self.cleaned_data['custom_message'],
            enabled=True,
            archived=False,
        )

        return alert


@login_required
def edit(request, alert_id=None):

    if alert_id:
        alert = TableauAlert.objects.get(alert_id=alert_id)
        new = False
    else:
        alert = None
        new = True

    single_publisher_user = False
    if not request.user.superuser:
        accessible_publisher_ids = [p.publisher_id for p in request.user.get_accessible_publishers()]
        if len(accessible_publisher_ids) == 1:
            single_publisher_user = True

    if request.method == 'POST':
        if 'archive' in request.POST:
            if alert:
                alert.archived = True if request.POST['archive'] == 'on' else False

                # for disabled for archived alerts
                if alert.archived:
                    alert.enabled = False

                alert.save()

                if alert.archived:
                    return HttpResponseRedirect(reverse('tableau_alerts.list') + '?from=archive-alert&filter=archived')
                else:
                    return HttpResponseRedirect(reverse('tableau_alerts.list') + '?from=unarchive-alert&filter=active')

        form = TableauAlertForm(request.POST, instance=alert, user=request.user)
        if form.is_valid():
            form.save()

            if new:
                return HttpResponseRedirect(reverse('tableau_alerts.list') + '?from=new-success')
            else:
                return HttpResponseRedirect(reverse('tableau_alerts.list') + '?from=save-success')

    else:
        form = TableauAlertForm(instance=alert, user=request.user)

    if alert:
        alert_template = ALERT_TEMPLATES[alert.template_id]
        alert_template_choices = get_template_choices_for_publisher(alert.publisher_id, alert_template['type'])
    else:
        alert_template = None
        alert_template_choices = []

    return render(request, 'tableau_alerts/new.html', {
        'form': form,
        'alert': alert,
        'template': alert_template,
        'template_choices': alert_template_choices,
        'single_publisher_user': single_publisher_user,
    })


def show_external_notification(request, notification_id):
    notification = TableauNotification.objects.get(notification_id=notification_id)
    if notification.expiration_date and notification.expiration_date < datetime.datetime.now():
        return render(request, 'tableau_alerts/external_notification_expired.html', {
            'notification': notification,
        })
    else:
        return render(request, 'tableau_alerts/external_notification.html', {
            'notification': notification,
        })


def get_template_choices_for_publisher(publisher_id, alert_type):
    publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)

    supported_templates = set()
    for pipeline_tuple, template_ids in ALERT_TEMPLATES_BY_SOURCE_PIPELINE.items():
        product_id, pipeline_id = pipeline_tuple
        if product_id in publisher.supported_products:
            supported_templates.update(template_ids)

    template_choices = []
    for template_id in supported_templates:
        alert = ALERT_TEMPLATES[template_id]
        if alert['type'] == alert_type:
            rendered_alert_description = alert['choice_description']
            has_widgets = False
            if alert['type'] == 'threshold':
                if '[]' in rendered_alert_description:
                    has_widgets = True
                    if alert['threshold_type'] == 'percentage':
                        input_html = """
                            <div class="input-group">
                                <input type="text" class="form-control threshold-input" value="%s">
                                <span class="input-group-addon">%%</span>
                            </div>
                        """ % alert['threshold_default_value']
                    else:
                        input_html = """
                            <input type="text" class="form-control threshold-input" value="%s">
                        """ % alert['threshold_default_value']

                    rendered_alert_description = rendered_alert_description.replace('[]', input_html)

            template_choices.append({
                'id': template_id,
                'description': rendered_alert_description,
                'has_widgets': has_widgets,
                'order': alert['order'],
                'name_template': alert['name_template'],
            })

    sorted_template_choices = sorted(template_choices, key=lambda a: a['order'])

    return sorted_template_choices


@login_required
def include_template_choices(request):
    publisher_id = request.GET['publisher_id']
    alert_type = request.GET['alert_type']
    template_choices = get_template_choices_for_publisher(publisher_id, alert_type)
    return render(request, 'tableau_alerts/include/template_choices.html', {
        'template_choices': template_choices,
    })


@login_required
def delete_alert(request):
    alert_id = request.POST['alert_id']
    alert = TableauAlert.objects.get(alert_id=alert_id)
    alert.update(
        enabled=False,
        archived=True,
    )
    return HttpResponse('ok')


def get_trusted_token():
    response = requests.post('http://%s/trusted' % common.TABLEAU_IP, data={'username': common.TABLEAU_USERNAME})  # only IP works here, not hostname
    return response.text


def get_trusted_report_url(request):
    publisher_id = request.GET['publisher_id']
    template_id = request.GET['template_id']
    embed_type = request.GET.get('embed_type', 'full')

    # pick up the relevant workbook URL
    workbook_id = ALERT_TEMPLATES[template_id]['workbooks'][embed_type]
    workbook_url = WorkbookUrl.objects.get(publisher_id=publisher_id, workbook_id=workbook_id)
    workbook_home_view = common.TABLEAU_WORKBOOKS_BY_ID[workbook_id]['home_view']

    # get the trusted token from Tableau
    token = get_trusted_token()

    # construct the full URL
    url = 'http://%s/trusted/%s/views/%s/%s' % (common.TABLEAU_SERVER, token, workbook_url.url, workbook_home_view)

    return JsonResponse({
        'url': url,
    })
