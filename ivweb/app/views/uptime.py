import logging
from django import forms
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import UptimeOverride
from ivetl import tasks

log = logging.getLogger(__name__)

OVERRIDE_FILTERS = [
    {
        'name': 'Check ID',
        'id': 'check_id',
        'plural': 'check IDs',
    },
    {
        'name': 'Publisher Code',
        'id': 'publisher_code',
        'plural': 'publisher codes',
    },
    {
        'name': 'Site Code',
        'id': 'site_code',
        'plural': 'site codes',
    },
    {
        'name': 'Site Platform',
        'id': 'site_platform',
        'plural': 'site platform values',
    },
]


@login_required
def list_overrides(request):
    messages = []
    if 'from' in request.GET:
        from_value = request.GET['from']
        if from_value == 'new-success':
            messages.append("Your new override has been created and is being applied.")

    overrides = UptimeOverride.objects.all()

    response = render(request, 'uptime/list_overrides.html', {
        'overrides': overrides,
        'messages': messages,
    })

    return response


class UptimeOverrideForm(forms.Form):
    label = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Override Label'}), required=True)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control'}, format='%m/%d/%Y'), required=True)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control'}, format='%m/%d/%Y'), required=True)
    match_expression_json = forms.CharField(widget=forms.HiddenInput, required=True)
    notes = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}), required=False)

    def save(self):
        override = UptimeOverride.objects.create(
            label=self.cleaned_data['label'],
            start_date=self.cleaned_data['start_date'],
            end_date=self.cleaned_data['end_date'],
            match_expression_json=self.cleaned_data['match_expression_json'],
            notes=self.cleaned_data['notes'],
        )
        return override


@login_required
def new_override(request):
    if request.method == 'POST':
        form = UptimeOverrideForm(request.POST)
        if form.is_valid():
            override = form.save()
            tasks.apply_override.s(override.override_id).delay()
            return HttpResponseRedirect(reverse('uptime.list_overrides') + '?from=new-success')
    else:
        form = UptimeOverrideForm()

    return render(request, 'uptime/new_override.html', {
        'form': form,
        'filters': OVERRIDE_FILTERS,
        'filter_ids': [f['id'] for f in OVERRIDE_FILTERS],
    })


@login_required
def delete_override(request):
    override_id = request.POST['override_id']
    override = UptimeOverride.objects.get(override_id=override_id)
    tasks.revert_and_delete_override.s(override.override_id).delay()
    return HttpResponse('ok')
