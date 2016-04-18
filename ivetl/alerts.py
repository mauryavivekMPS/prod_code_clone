import json
import datetime
from ivetl.models import Alert, Notification, Notification_Summary


def exceeds_integer(new_value=None, old_value=None, params=None):
    return new_value > params['threshold']


def percentage_change(new_value=None, old_value=None, params=None):
    if not old_value:
        return False  # not too sure this is correct??
    else:
        return (new_value - old_value) / old_value * 100 > params['threshold']

check_types = {
    'exceeds-integer': {
        'function': exceeds_integer,
        'params': [
            ('threshold', 'integer'),
        ]
    },
    'percentage-change': {
        'function': percentage_change,
        'params': [
            ('threshold', 'percentage'),
        ]
    },
}

checks = {
    'mendeley-saves-exceeds-integer': {
        'name': 'Mendeley Saves Exceeds Integer',
        'check_type': check_types['exceeds-integer'],
    },
    'citation-percentage-change': {
        'name': 'Citation Percentage Change',
        'check_type': check_types['percentage-change'],
    },
}

checks_choices = [(check_id, checks[check_id]['name']) for check_id in checks]


def run_alert(check_id=None, publisher_id=None, product_id=None, pipeline_id=None, job_id=None, new_value=None, old_value=None):

    now = datetime.datetime.now()

    # get the check metadata
    check = checks[check_id]
    check_function = check['check_type']['function']

    # get all alerts for this publisher for this check
    for alert in Alert.objects.allow_filtering().filter(publisher_id=publisher_id, check_id=check_id):

        if alert.enabled:
            params = json.loads(alert.params)

            # run the test
            if check_function(new_value=new_value, old_value=old_value, params=params):

                # add a notification
                Notification.objects.create(
                    alert_id=alert.alert_id,
                    publisher_id=publisher_id,
                    product_id=product_id,
                    pipeline_id=pipeline_id,
                    job_id=job_id,
                    value='foo = 8',
                )


def send_alert_notifications(check_id=None, publisher_id=None, product_id=None, pipeline_id=None, job_id=None):

    for alert in Alert.objects.allow_filtering().filter(publisher_id=publisher_id, check_id=check_id):

        notifications_for_alert = Notification.objects.filter(
            publisher_id=publisher_id,
            alert_id=alert.alert_id,
            product_id=product_id,
            pipeline_id=pipeline_id,
            job_id=job_id,
        )

        message = "\n".join([n.message for n in notifications_for_alert])

        Notification_Summary.objects.create(
            publisher_id=publisher_id,
            alert_id=alert.alert_id,
            product_id=product_id,
            pipeline_id=pipeline_id,
            job_id=job_id,
            message=message,
            dismissed=False,
        )
