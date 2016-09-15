import logging
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import UptimeOverride

log = logging.getLogger(__name__)


@login_required
def list_overrides(request):
    overrides = UptimeOverride.objects.all()

    response = render(request, 'uptime/list_overrides.html', {
        'overrides': overrides,
    })

    return response
