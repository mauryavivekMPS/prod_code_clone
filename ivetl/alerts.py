import json
import datetime
from ivetl.models import Alert, Notification, Notification_Summary


def exceeds_integer(new_value=None, old_value=None, params=None):
    delta = new_value - params['threshold']
    if delta > 0:

        # if an old_value is supplied, it must be lower than the threshold to trigger
        if (not old_value) or (old_value and old_value <= params['threshold']):
            return True, {'delta': delta}

    return False, {}


def percentage_change(new_value=None, old_value=None, params=None):
    if not old_value:
        return False, {}
    else:
        percentage_delta = (new_value - old_value) / old_value * 100
        if percentage_delta > params['threshold']:
            return True, {'percentage_increase': percentage_delta}
        else:
            return False, {}

check_types = {
    'exceeds-integer': {
        'function': exceeds_integer,
        'params': [
            {'name': 'threshold', 'label': 'Threshold', 'type': 'integer'},
        ]
    },
    'percentage-change': {
        'function': percentage_change,
        'params': [
            {'name': 'threshold', 'label': 'Threshold', 'type': 'percentage'},
        ]
    },
}

# associate checks with pipelines so that they can be hidden in the UI when appropriate

checks = {
    'mendeley-saves-exceeds-integer': {
        'name': 'Mendeley Saves Exceeds Integer',
        'check_type': check_types['exceeds-integer'],
        'format_string': 'Article %(doi)s (%(issn)s): %(new_value)s saves',
        'table_order': [
            {'key': 'issn', 'name': 'ISSN'},
            {'key': 'doi', 'name': 'DOI'},
            {'key': 'new_value', 'name': 'Saves', 'align': 'right'},
            {'key': 'delta', 'name': 'Increase', 'align': 'right'},
        ],
        # set up example for threshold = 100
    },

    'citations-exceeds-integer': {
        'name': 'Citations Exceeds Integer',
        'check_type': check_types['exceeds-integer'],
        'format_string': 'Article %(doi)s (%(issn)s): %(new_value)s citations',
        'table_order': [
            {'key': 'issn', 'name': 'ISSN'},
            {'key': 'doi', 'name': 'DOI'},
            {'key': 'new_value', 'name': 'Citations', 'align': 'right'},
            {'key': 'delta', 'name': 'Increase', 'align': 'right'},
        ]
        # example threshold = 2000
    },

    'uptime-percentage-decrease-over-five-days': {
        'name': 'Site Uptime Percentage Increase Over Five Days',
        'check_type': check_types['percentage-change'],
        'format_string': 'Site %(site_code)s: %(new_value)s citations (from %(old_value), up %(percentage_increase))',
        'table_order': [
            {'key': 'site_code', 'name': 'Site Code'},
            {'key': 'old_value', 'name': 'Previous Uptime', 'align': 'right'},
            {'key': 'new_value', 'name': 'Current Uptime', 'align': 'right'},
            {'key': 'percentage_increase', 'name': 'Increase', 'align': 'right'},
        ]
        # add filtering for check metadata, e.g. site_type == homepage
        # looking at avg_response_ms from checkstat
    },
}

check_choices = [(check_id, checks[check_id]['name']) for check_id in checks]


def run_alert(check_id=None, publisher_id=None, product_id=None, pipeline_id=None, job_id=None, new_value=None, old_value=None, extra_values=None):

    # get the check metadata
    check = checks[check_id]
    check_function = check['check_type']['function']

    # get all alerts for this publisher for this check
    for alert in Alert.objects.allow_filtering().filter(publisher_id=publisher_id, check_id=check_id):

        if alert.enabled:
            check_params = json.loads(alert.check_params)

            passed, values_from_check_function = check_function(new_value=new_value, old_value=old_value, params=check_params)

            # run the test
            if passed:
                all_values = {'new_value': new_value, 'old_value': old_value}
                all_values.update(extra_values)
                all_values.update(values_from_check_function)
                all_values.update(check_params)

                # add a notification
                Notification.objects.create(
                    alert_id=alert.alert_id,
                    publisher_id=publisher_id,
                    product_id=product_id,
                    pipeline_id=pipeline_id,
                    job_id=job_id,
                    values_json=json.dumps(all_values),
                )


def send_alert_notifications(check_id=None, publisher_id=None, product_id=None, pipeline_id=None, job_id=None):

    now = datetime.datetime.now()

    for alert in Alert.objects.filter(publisher_id=publisher_id, check_id=check_id):

        notifications_for_alert = Notification.objects.filter(
            publisher_id=publisher_id,
            alert_id=alert.alert_id,
            product_id=product_id,
            pipeline_id=pipeline_id,
            job_id=job_id,
        )

        values_list = [json.loads(n.values_json) for n in notifications_for_alert]

        Notification_Summary.objects.create(
            publisher_id=publisher_id,
            alert_id=alert.alert_id,
            product_id=product_id,
            pipeline_id=pipeline_id,
            job_id=job_id,
            values_list_json=json.dumps(values_list),
            notification_date=now,
            dismissed=False,
        )

        # send notification email with a link to the notification page with notification open
