import logging
from operator import attrgetter
from django import forms
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from ivetl.models import Alert, Publisher_Metadata
from ivetl.alerts import checks_choices
from ivweb.app.views import utils as view_utils

log = logging.getLogger(__name__)


def list_alerts(request, publisher_id=None):
    if publisher_id:
        alerts = Alert.objects.filter(publisher_id=publisher_id)
    else:
        alerts = Alert.objects.all()

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('alert-list-sort', 'publisher_id'))
    sorted_alerts = sorted(alerts, key=attrgetter(sort_key), reverse=sort_descending)

    response = render(request, 'alerts/list.html', {
        'alerts': sorted_alerts,
        'sort_key': sort_key,
        'sort_descending': sort_descending,
    })

    response.set_cookie('publisher-list-sort', value=sort_param, max_age=30*24*60*60)

    return response


class AlertForm(forms.Form):
    alert_id = forms.CharField(widget=forms.HiddenInput, required=False)
    publisher_id = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), choices=[('foo', 'Foo'), ('blood', 'Blood')], required=True)
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alert Name'}), required=True)
    check_id = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), choices=checks_choices, required=True)
    params = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '{}'}), required=False)
    enabled = forms.BooleanField(widget=forms.CheckboxInput, required=False)


def edit(request, alert_id=None):

    if alert_id:
        alert = Alert.objects.get(alert_id=alert_id)
    else:
        alert = None

    if request.method == 'POST':
        form = AlertForm(request.POST, instance=alert)
        if form.is_valid():
            alert = form.save()
            return HttpResponseRedirect(reverse('alerts.list'))
    else:
        form = AlertForm()

    return render(request, 'alerts/new.html', {
        'form': form,
        'alert': alert,
    })
