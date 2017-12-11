import logging
import json
import requests
from operator import attrgetter
from django import forms
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import Alert, PublisherMetadata, AttributeValues
from ivetl.alerts import CHECKS, get_check_params_display_string, get_filter_params_display_string
from ivweb.app.views import utils as view_utils
from ivetl.connectors import TableauConnector

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
        alerts = Alert.objects.all()
    else:
        accessible_publisher_ids = [p.publisher_id for p in request.user.get_accessible_publishers()]
        alerts = Alert.objects.filter(publisher_id__in=accessible_publisher_ids)
        if len(accessible_publisher_ids) == 1:
            single_publisher_user = True

    filter_param = request.GET.get('filter', request.COOKIES.get('alert-list-filter', 'all'))

    filtered_alerts = []
    if filter_param == 'active':
        for alert in alerts:
            if not alert.archived:
                filtered_alerts.append(alert)
    elif filter_param == 'archived':
        for alert in alerts:
            if alert.archived:
                filtered_alerts.append(alert)

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('alert-list-sort', 'publisher_id'))
    sorted_alerts = sorted(alerts, key=attrgetter(sort_key), reverse=sort_descending)

    for alert in sorted_alerts:
        check = CHECKS[alert.check_id]
        setattr(alert, 'check_name', check['name'])
        setattr(alert, 'param_display_string', get_check_params_display_string(alert))
        setattr(alert, 'filter_display_string', get_filter_params_display_string(alert))

    response = render(request, 'alerts/list.html', {
        'alerts': sorted_alerts,
        'messages': messages,
        'reset_url': reverse('alerts.list') + '?sort=' + sort_param,
        'sort_key': sort_key,
        'sort_descending': sort_descending,
        'single_publisher_user': single_publisher_user,
        'filter_param': filter_param,
    })

    response.set_cookie('alert-list-sort', value=sort_param, max_age=30*24*60*60)
    response.set_cookie('alert-list-filter', value=filter_param, max_age=30*24*60*60)

    return response


class AlertForm(forms.Form):
    alert_id = forms.CharField(widget=forms.HiddenInput, required=False)
    publisher_id = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), required=True)
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alert Name'}), required=True)
    check_id = forms.CharField(required=True)
    check_params = forms.CharField(widget=forms.HiddenInput, required=False)
    filter_params = forms.CharField(widget=forms.HiddenInput, required=False)
    comma_separated_emails = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated emails'}), required=False)
    enabled = forms.BooleanField(widget=forms.CheckboxInput, initial=True, required=False)

    def __init__(self, *args, instance=None, user=None, **kwargs):
        initial = {}

        if instance:
            self.instance = instance
            initial = dict(instance)
            initial['comma_separated_emails'] = ", ".join(instance.emails)
        else:
            self.instance = None
            initial['comma_separated_emails'] = user.email

        super(AlertForm, self).__init__(initial=initial, *args, **kwargs)

        if user.is_superuser:
            self.fields['publisher_id'].choices = [(p.publisher_id, p.name) for p in PublisherMetadata.objects.all()]
        else:
            self.fields['publisher_id'].choices = [(p.publisher_id, p.name) for p in user.get_accessible_publishers()]

        # self.fields['check_id'].choices = [('', 'Select a check')] + check_choices

    def save(self):
        alert_id = self.cleaned_data['alert_id']
        check_id = self.cleaned_data['check_id']
        if alert_id:
            alert = Alert.objects.get(
                alert_id=alert_id,
            )
        else:
            alert = Alert.objects.create(
                publisher_id=self.cleaned_data['publisher_id'],
                check_id=check_id,
            )

        check = CHECKS[check_id]
        params = {}
        for check_param in check['check_type'].get('params', []):
            param_name = check_param['name']
            param_value = self.data[param_name]

            param_type = check_param['type']
            if param_type in ['integer', 'percentage-integer']:
                param_value = int(param_value)
            elif param_type in ['float', 'percentage-float']:
                param_value = float(param_value)

            params[param_name] = param_value

        filters = {}
        for check_filter in check.get('filters', []):
            filter_name = check_filter['name']
            filter_value = self.data[filter_name]

            if filter_value:
                filters[filter_name] = filter_value

        emails = [email.strip() for email in self.cleaned_data["attachment_only_emails"].split(",")]

        alert.update(
            name=self.cleaned_data['name'],
            check_params=json.dumps(params),
            filter_params=json.dumps(filters),
            emails=emails,
            enabled=self.cleaned_data['enabled'],
        )

        return alert


def _add_filter_values(publisher_id, check):
    for check_filter in check.get('filters', []):
        filter_name = check_filter['table'] + '.' + check_filter['name']
        try:
            values = json.loads(AttributeValues.objects.get(publisher_id=publisher_id, name=filter_name).values_json)
        except AttributeValues.DoesNotExist:
            values = []

        check_filter['filter_values'] = values


@login_required
def edit(request, alert_id=None):

    if alert_id:
        alert = Alert.objects.get(alert_id=alert_id)
        new = False
    else:
        alert = None
        new = True

    single_publisher_user = False
    if not request.user.is_superuser:
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
                    return HttpResponseRedirect(reverse('alerts.list') + '?from=archive-alert&filter=archived')
                else:
                    return HttpResponseRedirect(reverse('alerts.list') + '?from=unarchive-alert&filter=active')

        form = AlertForm(request.POST, instance=alert, user=request.user)
        if form.is_valid():
            form.save()

            if new:
                return HttpResponseRedirect(reverse('alerts.list') + '?from=new-success')
            else:
                return HttpResponseRedirect(reverse('alerts.list') + '?from=save-success')
    else:
        form = AlertForm(instance=alert, user=request.user)

    if alert:
        check = CHECKS[alert.check_id]
        _add_filter_values(alert.publisher_id, check)
        check_choices = get_check_choices_for_publisher(alert.publisher_id)
    else:
        check = None
        check_choices = []

    return render(request, 'alerts/new.html', {
        'form': form,
        'alert': alert,
        'check': check,
        'check_choices': check_choices,
        'single_publisher_user': single_publisher_user,
    })


@login_required
def include_alert_params(request):
    check_id = request.GET['check_id']
    check = CHECKS[check_id]

    html = render_to_string('alerts/include/params.html', {
        'check': check,
        'is_include': True,
    }, request=request)

    return JsonResponse({
        'html': html,
        'params': check['check_type']['params'],
    })


@login_required
def include_alert_filters(request):
    check_id = request.GET['check_id']
    publisher_id = request.GET['publisher_id']
    check = CHECKS[check_id]
    _add_filter_values(publisher_id, check)

    html = render_to_string('alerts/include/filters.html', {
        'check': check,
        'is_include': True,
    }, request=request)

    return JsonResponse({
        'html': html,
        'filters': check['filters'],
    })


def get_check_choices_for_publisher(publisher_id):
    publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)
    supported_checks = set()
    for check_id, check in CHECKS.items():
        for product in check['products']:
            if product in publisher.supported_products:
                supported_checks.add(check_id)

    check_choices = [(check_id, CHECKS[check_id]['name']) for check_id in supported_checks]
    sorted_check_choices = sorted(check_choices, key=lambda c: c[1])

    return sorted_check_choices


@login_required
def include_check_choices(request):
    publisher_id = request.GET['publisher_id']
    check_choices = get_check_choices_for_publisher(publisher_id)
    return render(request, 'alerts/include/check_choices.html', {
        'check_choices': check_choices,
    })


@login_required
def get_trusted_report_url(request):
    response = requests.post('http://10.0.1.201/trusted', data={'username': 'nmehta'})
    token = response.text
    # url = 'http://10.0.0.143/trusted/%s/views/RejectedArticleTracker_5/Overview' % token
    # url = 'http://10.0.0.143/trusted/%s/views/alert_rejected_article_tracker/Overview' % token
    url = 'http://10.0.1.201/trusted/%s/views/alert_rejected_article_tracker/Overview' % token
    return JsonResponse({
        'url': url,
    })
