import logging
import json
from operator import attrgetter
from django import forms
from django.shortcuts import render, HttpResponseRedirect
from django.http import JsonResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import Alert, Publisher_Metadata, Attribute_Values
from ivetl.alerts import CHECKS
from ivetl.common import common
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
        alerts = Alert.objects.all()
    else:
        accessible_publisher_ids = [p.publisher_id for p in request.user.get_accessible_publishers()]
        alerts = Alert.objects.filter(publisher_id__in=accessible_publisher_ids)
        if len(accessible_publisher_ids) == 1:
            single_publisher_user = True

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('alert-list-sort', 'publisher_id'))
    sorted_alerts = sorted(alerts, key=attrgetter(sort_key), reverse=sort_descending)

    for alert in sorted_alerts:
        check = CHECKS[alert.check_id]
        setattr(alert, 'check_name', check['name'])

        # build neat little param display strings
        check_params = json.loads(alert.check_params)
        param_strings = []
        for p in check['check_type']['params']:
            if p['name'] in check_params:
                param_strings.append('%s = %s' % (p['label'], check_params[p['name']]))
        setattr(alert, 'param_display_string', ", ".join(param_strings))

        # build neat little filter display strings
        filter_params = json.loads(alert.filter_params)
        filter_strings = []
        for f in check['filters']:
            if f['name'] in filter_params:
                filter_strings.append('%s = %s' % (f['label'], filter_params[f['name']]))
        setattr(alert, 'filter_display_string', ", ".join(filter_strings))

    response = render(request, 'alerts/list.html', {
        'alerts': sorted_alerts,
        'messages': messages,
        'reset_url': reverse('alerts.list') + '?sort=' + sort_param,
        'sort_key': sort_key,
        'sort_descending': sort_descending,
        'single_publisher_user': single_publisher_user,
    })

    response.set_cookie('publisher-list-sort', value=sort_param, max_age=30*24*60*60)

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

        if user.superuser:
            self.fields['publisher_id'].choices = [(p.publisher_id, p.name) for p in Publisher_Metadata.objects.all()]
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
            if param_type == 'integer':
                param_value = int(param_value)
            elif param_type == 'percentage':
                param_value = float(param_value)

            params[param_name] = param_value

        filters = {}
        for check_filter in check.get('filters', []):
            filter_name = check_filter['name']
            filter_value = self.data[filter_name]

            if filter_value:
                filters[filter_name] = filter_value

        emails = [email.strip() for email in self.cleaned_data['comma_separated_emails'].split(",")]

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
            values = json.loads(Attribute_Values.objects.get(publisher_id=publisher_id, name=filter_name).values_json)
        except Attribute_Values.DoesNotExist:
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
    if not request.user.superuser:
        accessible_publisher_ids = [p.publisher_id for p in request.user.get_accessible_publishers()]
        if len(accessible_publisher_ids) == 1:
            single_publisher_user = True

    if request.method == 'POST':
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
    return render(request, 'alerts/include/params.html', {
        'check': CHECKS[check_id],
        'is_include': True,
    })


@login_required
def include_alert_filters(request):
    check_id = request.GET['check_id']
    publisher_id = request.GET['publisher_id']
    check = CHECKS[check_id]
    _add_filter_values(publisher_id, check)

    return render(request, 'alerts/include/filters.html', {
        'check': check,
        'is_include': True,
    })


def get_check_choices_for_publisher(publisher_id):
    publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)
    supported_checks = set()
    for check_id, check in CHECKS.items():
        for product in check['products']:
            if product in publisher.supported_products:
                supported_checks.add(check_id)

    check_choices =  [(check_id, CHECKS[check_id]['name']) for check_id in supported_checks]
    sorted_check_choices = sorted(check_choices, key=lambda c: c[1])

    return sorted_check_choices


@login_required
def include_check_choices(request):
    publisher_id = request.GET['publisher_id']
    check_choices = get_check_choices_for_publisher(publisher_id)
    return render(request, 'alerts/include/check_choices.html', {
        'check_choices': check_choices,
    })
