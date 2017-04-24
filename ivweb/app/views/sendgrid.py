import json
import uuid
import datetime
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from ivetl.models import TableauNotificationEvent


@csrf_exempt
def event_hook(request):
    all_events = json.loads(request.body.decode('utf-8'))
    for event in all_events:
        event_id = event.get('sg_event_id')
        event_type = event.get('event')
        notification_id = uuid.UUID(event.get('notification_id'))

        if event_id and event_type and notification_id and event_type in ('click', 'open'):
            event_date = datetime.datetime.fromtimestamp(int(event['timestamp']))
            email = event.get('email')
            alert_id = uuid.UUID(event.get('alert_id'))
            publisher_id = event.get('publisher_id')

            TableauNotificationEvent.objects(
                notification_id=notification_id,
                event_type=event_type,
                event_id=event_id,
            ).update(
                alert_id=alert_id,
                publisher_id=publisher_id,
                event_date=event_date,
                email=email,
            )

    return HttpResponse()
