import logging
import requests
from operator import attrgetter
from django import forms
from django.http import JsonResponse
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import TableauAlert, TableauNotification, PublisherMetadata
from ivetl.tableau_alerts import ALERTS
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
    if request.user.superuser:
        alerts = TableauAlert.objects.all()
    else:
        accessible_publisher_ids = [p.publisher_id for p in request.user.get_accessible_publishers()]
        alerts = TableauAlert.objects.filter(publisher_id__in=accessible_publisher_ids)
        if len(accessible_publisher_ids) == 1:
            single_publisher_user = True

    filter_param = request.GET.get('filter', request.COOKIES.get('tableau-alert-list-filter', 'all'))

    filtered_alerts = []
    if filter_param == 'active':
        for alert in alerts:
            if not alert.archived:
                filtered_alerts.append(alert)
    elif filter_param == 'archived':
        for alert in alerts:
            if alert.archived:
                filtered_alerts.append(alert)

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('tableau-alert-list-sort', 'publisher_id'))
    sorted_alerts = sorted(alerts, key=attrgetter(sort_key), reverse=sort_descending)

    for alert in sorted_alerts:
        alert_type = ALERTS[alert.report_id]
        setattr(alert, 'report_name', alert_type['report_name'])

    response = render(request, 'tableau_alerts/list.html', {
        'alerts': sorted_alerts,
        'messages': messages,
        'reset_url': reverse('tableau_alerts.list') + '?sort=' + sort_param,
        'sort_key': sort_key,
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
    report_id = forms.CharField(widget=forms.HiddenInput, required=True)
    alert_params = forms.CharField(widget=forms.HiddenInput, required=False)
    alert_filters = forms.CharField(widget=forms.HiddenInput, required=False)
    attachment_only_emails = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Comma-separated emails'}), required=False)
    full_emails = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Comma-separated emails'}), required=False)
    enabled = forms.BooleanField(widget=forms.CheckboxInput, initial=True, required=False)
    send_with_no_data = forms.BooleanField(widget=forms.CheckboxInput, initial=True, required=False)

    def __init__(self, *args, instance=None, user=None, **kwargs):
        initial = {}

        if instance:
            self.instance = instance
            initial = dict(instance)
            initial['attachment_only_emails'] = ", ".join(instance.attachment_only_emails)
            initial['full_emails'] = ", ".join(instance.attachment_only_emails)
        else:
            self.instance = None

        super(TableauAlertForm, self).__init__(initial=initial, *args, **kwargs)

        if user.superuser:
            self.fields['publisher_id'].choices = [(p.publisher_id, p.name) for p in PublisherMetadata.objects.all()]
        else:
            self.fields['publisher_id'].choices = [(p.publisher_id, p.name) for p in user.get_accessible_publishers()]

        self.fields['publisher_id'].choices.insert(0, ('', 'Select a publisher'))

    def save(self):
        alert_id = self.cleaned_data['alert_id']
        report_id = self.cleaned_data['report_id']
        if alert_id:
            alert = TableauAlert.objects.get(
                alert_id=alert_id,
            )
        else:
            alert = TableauAlert.objects.create(
                publisher_id=self.cleaned_data['publisher_id'],
                report_id=report_id,
            )

        attachment_only_emails = [email.strip() for email in self.cleaned_data['attachment_only_emails'].split(",")]
        full_emails = [email.strip() for email in self.cleaned_data['full_emails'].split(",")]

        alert.update(
            name=self.cleaned_data['name'],
            alert_params=self.cleaned_data['alert_params'],
            alert_filters=self.cleaned_data['alert_filters'],
            attachment_only_emails=attachment_only_emails,
            full_emails=full_emails,
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
        form = None

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
        report = ALERTS[alert.report_id]
        report_choices = get_report_choices_for_publisher(alert.publisher_id)
    else:
        report = None
        report_choices = []

    return render(request, 'tableau_alerts/new.html', {
        'form': form,
        'alert': alert,
        'report': report,
        'report_choices': report_choices,
        'single_publisher_user': single_publisher_user,
    })


def show_external_notification(request, notification_id):
    notification = TableauNotification.objects.get(notification_id=notification_id)
    return render(request, 'tableau_alerts/external_notification.html', {
        'notification': notification,
    })


def get_report_choices_for_publisher(publisher_id, alert_type):
    publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)

    # supported_reports = set()
    # for check_id, check in CHECKS.items():
    #     for product in check['products']:
    #         if product in publisher.supported_products:
    #             supported_checks.add(check_id)
    #
    # check_choices = [(check_id, CHECKS[check_id]['name']) for check_id in supported_checks]
    # sorted_check_choices = sorted(check_choices, key=lambda c: c[1])
    #
    # return sorted_check_choices

    report_choices = []
    for alert_id, alert in ALERTS.items():
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

            report_choices.append({
                'id': alert_id,
                'description': rendered_alert_description,
                'has_widgets': has_widgets,
                'order': alert['order'],
                'name_template': alert['name_template'],
            })

    sorted_report_choices = sorted(report_choices, key=lambda a: a['order'])

    return sorted_report_choices


@login_required
def include_report_choices(request):
    publisher_id = request.GET['publisher_id']
    alert_type = request.GET['alert_type']
    report_choices = get_report_choices_for_publisher(publisher_id, alert_type)
    return render(request, 'tableau_alerts/include/report_choices.html', {
        'report_choices': report_choices,
    })


def get_trusted_token():
    response = requests.post('http://10.0.1.201/trusted', data={'username': 'nmehta'})
    return response.text


def get_trusted_report_url(request):
    token = get_trusted_token()
    # url = 'http://10.0.0.143/trusted/%s/views/RejectedArticleTracker_5/Overview' % token
    # url = 'http://10.0.0.143/trusted/%s/views/alert_rejected_article_tracker/Overview' % token
    embed_type = request.GET.get('embed_type', 'full')
    if embed_type == 'configure':
        url = 'http://10.0.1.201/trusted/%s/views/alert_rejected_article_tracker/Overview' % token
    else:
        url = 'http://10.0.1.201/trusted/%s/views/RejectedArticleTracker_2/Overview' % token

    return JsonResponse({
        'url': url,
    })
