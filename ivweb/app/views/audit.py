from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ivetl.models import Audit_Log


@login_required
def show(request):
    audit_log = Audit_Log.objects.all()
    return render(request, 'audit_log.html', {'audit_log': audit_log})

