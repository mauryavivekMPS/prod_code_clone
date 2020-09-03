import re
import logging
import requests
import datetime
from operator import attrgetter
from django import forms
from django.http import JsonResponse
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.connectors import TableauConnector
from ivetl.models import TableauAlert, TableauNotification, TableauNotificationByAlert, PublisherMetadata, User
from ivetl.tableau_alerts import ALERT_TEMPLATES, ALERT_TEMPLATES_BY_SOURCE_PIPELINE, process_alert
from ivetl.common import common
from ivetl import utils
from ivweb.app.views import utils as view_utils

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
    if request.user.is_superuser:
        alerts = TableauAlert.objects.filter(archived=False)
    else:
        accessible_publisher_ids = [p.publisher_id for p in request.user.get_accessible_publishers()]
        alerts = [a for a in TableauAlert.objects.filter(archived=False) if a.publisher_id in accessible_publisher_ids]
        if len(accessible_publisher_ids) == 1:
            single_publisher_user = True

    publisher_name_by_id = {}
    for alert in alerts:

        # add publisher name
        if alert.publisher_id not in publisher_name_by_id:
            publisher_name_by_id[alert.publisher_id] = PublisherMetadata.objects.get(publisher_id=alert.publisher_id).name
        setattr(alert, 'publisher_name', publisher_name_by_id[alert.publisher_id])

        # add alert type name
        alert_type = ALERT_TEMPLATES[alert.template_id]
        setattr(alert, 'alert_type', alert_type['name'])

        # add alert user
        if alert.created_by:
            try:
                user = User.objects.get(user_id=alert.created_by)
            except User.DoesNotExist:
                user = None
        else:
            user = None
        setattr(alert, 'user', user)

        # get most recent notification date
        notifications_for_this_alert = TableauNotificationByAlert.objects.filter(publisher_id=alert.publisher_id, alert_id=alert.alert_id)
        if notifications_for_this_alert:
            sorted_notifications = sorted(notifications_for_this_alert, key=attrgetter('notification_date'), reverse=True)
            setattr(alert, 'num_notifications', len(sorted_notifications))
            setattr(alert, 'last_notification_date', sorted_notifications[0].notification_date)

    all_publishers = set()
    all_alert_types = set()
    for alert in alerts:
        all_publishers.add((alert.publisher_id, alert.publisher_name))
        all_alert_types.add((alert.template_id, alert.alert_type))

    publisher_choices = sorted([{'publisher_id': c[0], 'name': c[1]} for c in all_publishers], key=lambda p: p['name'])
    alert_type_choices = sorted([{'template_id': c[0], 'name': c[1]} for c in all_alert_types], key=lambda p: p['name'])

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('tableau-alert-list-sort', 'publisher_id'))
    sorted_alerts = sorted(alerts, key=attrgetter(sort_key), reverse=sort_descending)

    response = render(request, 'tableau_alerts/list.html', {
        'alerts': sorted_alerts,
        'messages': messages,
        'reset_url': reverse('tableau_alerts.list') + '?sort=' + sort_param,
        'sort_key': sort_key,
        'sort_descending': sort_descending,
        'single_publisher_user': single_publisher_user,
        'publisher_choices': publisher_choices,
        'alert_type_choices': alert_type_choices,
    })

    response.set_cookie('tableau-alert-list-sort', value=sort_param, max_age=30*24*60*60)

    return response


def _parse_email_list(s):
    return [e.strip() for e in re.split('[\s,;]+', s) if s if e]


class TableauAlertForm(forms.Form):
    alert_id = forms.CharField(widget=forms.HiddenInput, required=False)
    publisher_id = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), required=True)
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alert Name'}), required=True)
    template_id = forms.CharField(widget=forms.HiddenInput, required=True)
    alert_params = forms.CharField(widget=forms.HiddenInput, initial='{}', required=False)
    alert_filters = forms.CharField(widget=forms.HiddenInput, initial='{}', required=False)
    attachment_only_emails = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Comma-separated emails'}), required=False)
    full_emails = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Comma-separated emails'}), required=False)
    custom_message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Plain text custom message, no HTML'}), required=False)
    enabled = forms.BooleanField(widget=forms.CheckboxInput, initial=True, required=False)
    send_with_no_data = forms.BooleanField(widget=forms.CheckboxInput, initial=True, required=False)

    def __init__(self, *args, instance=None, user=None, **kwargs):
        initial = {}
        self.user = user

        if instance:
            self.instance = instance
            initial = dict(instance)
            initial['attachment_only_emails'] = ", ".join(instance.attachment_only_emails)
            initial['full_emails'] = ", ".join(instance.full_emails)
        else:
            self.instance = None

        if self.user.is_superuser:
            publisher_choices = [(p.publisher_id, p.name) for p in PublisherMetadata.objects.all()]
        else:
            publisher_choices = [(p.publisher_id, p.name) for p in self.user.get_accessible_publishers()]

        if len(publisher_choices) == 1:
            initial['publisher_id'] = publisher_choices[0][0]

        super(TableauAlertForm, self).__init__(initial=initial, *args, **kwargs)

        self.fields['publisher_id'].choices = sorted(publisher_choices, key=lambda p: p[0])

        if len(publisher_choices) > 1:
            self.fields['publisher_id'].choices.insert(0, ('', 'Select a publisher'))

    def save(self):
        alert_id = self.cleaned_data['alert_id']
        template_id = self.cleaned_data['template_id']
        publisher_id = self.cleaned_data['publisher_id']
        if alert_id:
            alert = TableauAlert.objects.get(
                publisher_id=publisher_id,
                alert_id=alert_id,
            )
        else:
            alert = TableauAlert.objects.create(
                publisher_id=publisher_id,
                template_id=template_id,
                created=datetime.datetime.now(),
                created_by=self.user.user_id,
            )

        attachment_only_emails_string = self.cleaned_data.get('attachment_only_emails')
        attachment_only_emails = _parse_email_list(attachment_only_emails_string)

        full_emails_string = self.cleaned_data.get('full_emails')
        full_emails = _parse_email_list(full_emails_string)

        alert_params_string = self.cleaned_data.get('alert_params')
        if not alert_params_string:
            alert_params_string = '{}'

        alert_filters_string = self.cleaned_data.get('alert_filters')
        if not alert_filters_string:
            alert_filters_string = '{}'

        alert.update(
            name=self.cleaned_data['name'],
            alert_params=alert_params_string,
            alert_filters=alert_filters_string,
            attachment_only_emails=attachment_only_emails,
            full_emails=full_emails,
            custom_message=self.cleaned_data['custom_message'],
            send_with_no_data=self.cleaned_data['send_with_no_data'],
            enabled=True,
            archived=False,
        )

        return alert


@login_required
def edit(request, alert_id=None):

    if alert_id:
        alert = TableauAlert.objects.allow_filtering().get(alert_id=alert_id)
        publisher = PublisherMetadata.objects.get(publisher_id=alert.publisher_id)
        new = False
    else:
        alert = None
        publisher = None
        new = True

    single_publisher_user = False
    if not request.user.is_superuser:
        accessible_publisher_ids = [p.publisher_id for p in request.user.get_accessible_publishers()]
        if len(accessible_publisher_ids) == 1:
            single_publisher_user = True

    if request.method == 'POST':
        form = TableauAlertForm(request.POST, instance=alert, user=request.user)
        if form.is_valid():
            saved_alert = form.save()

            if request.POST.get('send_notification'):
                process_alert(saved_alert)

            if new:
                utils.add_audit_log(
                    user_id=request.user.user_id,
                    publisher_id=saved_alert.publisher_id,
                    action='create-alert',
                    description='Create alert: %s (%s)' % (saved_alert.name, saved_alert.alert_id)
                )
                return HttpResponseRedirect(reverse('tableau_alerts.list') + '?from=new-success')
            else:
                utils.add_audit_log(
                    user_id=request.user.user_id,
                    publisher_id=saved_alert.publisher_id,
                    action='edit-alert',
                    description='Edit alert: %s (%s)' % (saved_alert.name, saved_alert.alert_id)
                )
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
        'publisher': publisher,
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
        template = ALERT_TEMPLATES[notification.template_id]
        return render(request, 'tableau_alerts/external_notification.html', {
            'notification': notification,
            'template': template,
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
                'frequency': alert['frequency'],
                'has_filter_configuration': '1' if alert['workbooks'].get('configure') else '',
                'filter_worksheet_name': alert.get('filter_worksheet_name'),
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
    publisher_id = request.POST['publisher_id']
    alert_id = request.POST['alert_id']
    expire_notifications = request.POST.get('expire_notifications', False)

    alert = TableauAlert.objects.get(publisher_id=publisher_id, alert_id=alert_id)
    alert.update(
        enabled=False,
        archived=True,
    )

    if expire_notifications:
        yesterday = datetime.datetime.today() - datetime.timedelta(1)
        for n in TableauNotification.objects.filter(alert_id=alert_id):
            n.update(expiration_date=yesterday)

    utils.add_audit_log(
        user_id=request.user.user_id,
        publisher_id=alert.publisher_id,
        action='archive-alert',
        description='Archive alert: %s (%s)' % (alert.name, alert.alert_id)
    )

    return HttpResponse('ok')


@login_required
def toggle_alert(request):
    publisher_id = request.POST['publisher_id']
    alert_id = request.POST['alert_id']
    enabled = request.POST.get('enabled')

    alert = TableauAlert.objects.get(publisher_id=publisher_id, alert_id=alert_id)
    alert.update(
        enabled=enabled,
    )

    return HttpResponse('ok')


@login_required
def send_alert_now(request):
    publisher_id = request.POST['publisher_id']
    alert_id = request.POST['alert_id']
    alert = TableauAlert.objects.get(publisher_id=publisher_id, alert_id=alert_id)
    attachment_only_emails_string = request.POST['attachment_only_emails']
    attachment_only_emails = _parse_email_list(attachment_only_emails_string)
    full_emails_string = request.POST['full_emails']
    full_emails = _parse_email_list(full_emails_string)
    custom_message = request.POST['custom_message']
    try:
        process_alert(alert, attachment_only_emails_override=attachment_only_emails, full_emails_override=full_emails, custom_message_override=custom_message)
        return HttpResponse('ok')
    except Exception as e:
        log.info('send_alert_now failed for %s, %s' %s (publisher_id, alert_id))
        return JsonResponse({
            'error': 'send_alert_now failed',
            'publisherId': publisher_id,
            'alertId': alert_id
        }, status=500)


def get_trusted_token():
    response = requests.post('http://%s/trusted' % common.TABLEAU_IP, data={'username': common.TABLEAU_USERNAME})  # only IP works here, not hostname
    return response.text


def get_trusted_report_url(request):
    publisher_id = request.GET['publisher_id']
    template_id = request.GET['template_id']
    embed_type = request.GET.get('embed_type', 'full')

    workbook_id = ALERT_TEMPLATES[template_id]['workbooks'][embed_type]
    workbook_home_view = common.TABLEAU_WORKBOOKS_BY_ID[workbook_id]['home_view']

    if not publisher_id:
        return JsonResponse({
            'error': 'invalid publisher id',
            'url': ''
        }, status=500)
    try:
        t = TableauConnector(
            username=common.TABLEAU_USERNAME,
            password=common.TABLEAU_PASSWORD,
            server=common.TABLEAU_SERVER
        )
        workbook_id = ALERT_TEMPLATES[template_id]['workbooks'][embed_type]
        workbooks = t.list_workbooks_by_name(workbook_id, publisher_id)
        if len(workbooks) < 1 or not workbooks[0]['content_url']:
            return JsonResponse({
                'error': 'workbook content url not found',
                'url': ''
            }, status=500)
        # there should always be at most one workbook per name per project
        content_url = workbooks[0]['content_url']

        token = get_trusted_token()

        if common.TABLEAU_HTTPS:
            scheme = 'https'
        else:
            scheme = 'http'

        # construct the full URL
        url_params = (scheme, common.TABLEAU_SERVER, token, content_url, workbook_home_view)
        url = '%s://%s/trusted/%s/views/%s/%s' % url_params

        return JsonResponse({
            'url': url,
        })
    except Exception as e:
        log.info('Exception, get_trusted_report_url: %s, %s: %s' % (publisher_id, template_id, e))
        return JsonResponse({
            'error': 'exception encountered',
            'url': ''
        }, status=500)


def show_email(request):
    return render(request, 'tableau_alerts/notification_email.html', {})
