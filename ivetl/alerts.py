import json
import datetime
from django.core.urlresolvers import reverse
from ivetl.models import Alert, Notification, Notification_Summary, Publisher_Metadata
from ivetl.common import common


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

CHECK_TYPES = {
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

CHECKS = {
    'mendeley-saves-exceeds-integer': {
        'name': 'Mendeley Saves Exceeds Integer',
        'check_type': CHECK_TYPES['exceeds-integer'],
        'filters': [
            {'name': 'article_type', 'label': 'Article Type', 'table': 'published_article'},
            {'name': 'subject_category', 'label': 'Subject Category', 'table': 'published_article'},
            {'name': 'is_open_access', 'label': 'Open Access', 'table': 'published_article'},
            {'name': 'custom', 'label': 'Custom 1', 'table': 'published_article'},
            {'name': 'custom', 'label': 'Custom 2', 'table': 'published_article'},
            {'name': 'custom', 'label': 'Custom 3', 'table': 'published_article'},
        ],
        'format_string': 'Article %(doi)s (%(issn)s): %(new_value)s saves',
        'table_order': [
            {'key': 'issn', 'name': 'ISSN'},
            {'key': 'doi', 'name': 'DOI'},
            {'key': 'new_value', 'name': 'Saves', 'align': 'right'},
            {'key': 'delta', 'name': 'Increase', 'align': 'right'},
        ],
        'products': [
            'published_articles',
        ]
        # set up example for threshold = 100
    },

    'citations-exceeds-integer': {
        'name': 'Citations Exceeds Integer',
        'check_type': CHECK_TYPES['exceeds-integer'],
        'filters': [
            {'name': 'article_type', 'label': 'Article Type', 'table': 'published_article'},
            {'name': 'subject_category', 'label': 'Subject Category', 'table': 'published_article'},
            {'name': 'is_open_access', 'label': 'Open Access', 'table': 'published_article'},
            {'name': 'custom', 'label': 'Custom 1', 'table': 'published_article'},
            {'name': 'custom', 'label': 'Custom 2', 'table': 'published_article'},
            {'name': 'custom', 'label': 'Custom 3', 'table': 'published_article'},
        ],
        'format_string': 'Article %(doi)s (%(issn)s): %(new_value)s citations',
        'table_order': [
            {'key': 'issn', 'name': 'ISSN'},
            {'key': 'doi', 'name': 'DOI'},
            {'key': 'new_value', 'name': 'Citations', 'align': 'right'},
            {'key': 'delta', 'name': 'Increase', 'align': 'right'},
        ],
        'products': [
            'published_articles',
        ]
        # example threshold = 2000
    },

    'uptime-percentage-decrease-over-five-days': {
        'name': 'Site Uptime Percentage Increase Over Five Days',
        'check_type': CHECK_TYPES['percentage-change'],
        'filters': [
            {'name': 'check_type', 'label': 'Check Type', 'table': 'uptime_check_metadata'},
            {'name': 'site_type', 'label': 'Site Type', 'table': 'uptime_check_metadata'},
            {'name': 'site_platform', 'label': 'Site Platform', 'table': 'uptime_check_metadata'},
        ],
        'format_string': 'Site %(site_code)s: %(new_value)s citations (from %(old_value), up %(percentage_increase))',
        'table_order': [
            {'key': 'site_code', 'name': 'Site Code'},
            {'key': 'old_value', 'name': 'Previous Uptime', 'align': 'right'},
            {'key': 'new_value', 'name': 'Current Uptime', 'align': 'right'},
            {'key': 'percentage_increase', 'name': 'Increase', 'align': 'right'},
        ],
        'products': [
            'highwire_sites',
        ]
        # looking at avg_response_ms from checkstat
    },
}


def run_alert(check_id=None, publisher_id=None, product_id=None, pipeline_id=None, job_id=None, new_value=None, old_value=None, extra_values=None):

    # get the check metadata
    check = CHECKS[check_id]
    check_function = check['check_type']['function']

    # get all alerts for this publisher for this check
    for alert in Alert.objects.allow_filtering().filter(publisher_id=publisher_id, check_id=check_id):

        if alert.enabled:
            check_params = json.loads(alert.check_params)
            filter_params = json.loads(alert.filter_params)

            # run the instance through filters
            passed_filters = True
            if filter_params:
                for param_name, param_value in filter_params.items():
                    required_value = param_value.lower()
                    given_value = extra_values.get(param_name, '').lower()
                    if not required_value == given_value:
                        passed_filters = False
                        break

            if passed_filters:

                # run the test
                passed_test, values_from_check_function = check_function(new_value=new_value, old_value=old_value, params=check_params)

                if passed_test:
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

        if notifications_for_alert:

            values_list = [json.loads(n.values_json) for n in notifications_for_alert]

            notification_summary = Notification_Summary.objects.create(
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
            num_notifications = len(values_list)
            subject = 'Impact Vizor (%s): %s notifications for %s' % (publisher_id, num_notifications, alert.name)
            body = """
                <p>There are <b>%s</b> new notifications for <b>%s</b>:</p>
                <p>&nbsp;&nbsp;&nbsp;&nbsp;<a href="%s%s?notification_summary_id=%s#notification-%s">View notification details</a></p>
                <p>Thank you,<br/>Impact Vizor Team</p>
            """ % (
                num_notifications,
                alert.name,
                common.IVETL_WEB_ADDRESS,
                reverse('notifications.list'),
                notification_summary.notification_summary_id,
                notification_summary.notification_summary_id,
            )

            if alert.emails:
                to = ",".join(alert.emails)
            else:
                publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)
                to = publisher.email

            common.send_email(subject, body, to=to)