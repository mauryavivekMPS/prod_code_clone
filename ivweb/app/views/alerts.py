import logging
import json
from operator import attrgetter
from django import forms
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import Alert, Publisher_Metadata
from ivetl.alerts import checks, check_choices
from ivweb.app.views import utils as view_utils

log = logging.getLogger(__name__)


@login_required
def list_alerts(request, publisher_id=None):

    messages = []
    if 'from' in request.GET:
        from_value = request.GET['from']
        if from_value == 'save-success':
            messages.append("Changes to your alert have been saved.")
        elif from_value == 'new-success':
            messages.append("Your new alert is created and ready to go.")

    if publisher_id:
        alerts = Alert.objects.filter(publisher_id=publisher_id)
    else:
        alerts = Alert.objects.all()

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('alert-list-sort', 'publisher_id'))
    sorted_alerts = sorted(alerts, key=attrgetter(sort_key), reverse=sort_descending)

    response = render(request, 'alerts/list.html', {
        'alerts': sorted_alerts,
        'messages': messages,
        'reset_url': reverse('alerts.list') + '?sort=' + sort_param,
        'sort_key': sort_key,
        'sort_descending': sort_descending,
    })

    response.set_cookie('publisher-list-sort', value=sort_param, max_age=30*24*60*60)

    return response


class AlertForm(forms.Form):
    alert_id = forms.CharField(widget=forms.HiddenInput, required=False)
    publisher_id = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), required=True)
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alert Name'}), required=True)
    check_id = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), required=True)
    check_params = forms.CharField(widget=forms.HiddenInput, required=False)
    enabled = forms.BooleanField(widget=forms.CheckboxInput, initial=True, required=False)

    def __init__(self, *args, instance=None, user=None, **kwargs):
        initial = {}

        if instance:
            self.instance = instance
            initial = dict(instance)
        else:
            self.instance = None

        super(AlertForm, self).__init__(initial=initial, *args, **kwargs)

        self.fields['check_id'].choices = [('', 'Select a check')] + check_choices

        if user:
            self.fields['publisher_id'].choices = [(p.publisher_id, p.name) for p in user.get_accessible_publishers()]
        else:
            self.fields['publisher_id'].choices = [(p.publisher_id, p.name) for p in Publisher_Metadata.objects.all()]

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

        check = checks[check_id]
        params = {}
        for param in check['check_type']['params']:
            param_name = param['name']
            param_value = self.data[param_name]

            param_type = param['type']
            if param_type == 'integer':
                param_value = int(param_value)
            elif param_type == 'percentage':
                param_value = float(param_value)

            params[param_name] = param_value

        alert.update(
            name=self.cleaned_data['name'],
            check_params=json.dumps(params),
            enabled=self.cleaned_data['enabled'],
        )

        return alert


@login_required
def edit(request, alert_id=None):

    if alert_id:
        alert = Alert.objects.get(alert_id=alert_id)
        new = False
    else:
        alert = None
        new = True

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

    return render(request, 'alerts/new.html', {
        'form': form,
        'alert': alert,
        'check': checks[alert.check_id] if alert else None,
    })


@login_required
def include_alert_params(request):
    check_id = request.GET['check_id']
    return render(request, 'alerts/include/params.html', {
        'check': checks[check_id],
        'is_include': True,
    })
