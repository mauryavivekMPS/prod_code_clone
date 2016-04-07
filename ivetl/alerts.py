import json
import datetime
from ivetl.models import Alert, Notification


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
        'check_type': check_types['exceeds-integer'],
    },
    'citation-percentage-page': {
        'check_type': check_types['percentage-change'],
    },
}


def run_alert(check_id=None, publisher_id=None, new_value=None, old_value=None):

    now = datetime.datetime.now()

    # get the check metadata
    check = checks[check_id]
    check_function = check['check_type']['function']

    # get all alerts for this publisher for this check
    for alert in Alert.objects.allow_filtering().filter(publisher_id=publisher_id, check_id=check_id, enabled=True):

        params = json.loads(alert.params)

        # run the test
        if check_function(new_value=new_value, old_value=old_value, params=params):

            # add a notification
            Notification.objects.create(
                notification_date=now,
                alert_id=alert.alert_id,
                publisher_id=publisher_id,
                notes='Here are some notes!',
                dismissed=False,
            )

            # send an email
            pass
