from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ivetl.models import AuditLog, User


@login_required
def show(request):
    audit_log = sorted(AuditLog.objects.all().limit(1000), key=lambda l: l.event_time, reverse=True)
    user_id_to_email = {str(u.user_id): u.email for u in User.objects.all()}
    for log in audit_log:
        setattr(log, 'user_email', user_id_to_email[str(log.user_id)])
        if log.entity_type == 'user':
            log.entity_id = user_id_to_email[log.entity_id]
    return render(request, 'audit_log.html', {'audit_log': audit_log})

