import json
import datetime
from django.core.urlresolvers import reverse
from ivetl.models import Alert, Notification, NotificationSummary, PublisherMetadata
from ivetl.common import common


def exceeds_integer(new_value=None, old_value=None, params=None, extra_values=None):
    delta = new_value - params['threshold']
    if delta > 0:

        # if an old_value is supplied, it must be lower than the threshold to trigger
        if (not old_value) or (old_value and old_value <= params['threshold']):
            return True, {'delta': delta}

    return False, {}


def percentage_change(new_value=None, old_value=None, params=None, extra_values=None):
    if not old_value:
        return False, {}
    else:
        percentage_delta = (new_value - old_value) / old_value * 100
        if percentage_delta > params['percentage_change']:
            return True, {'percentage_increase': percentage_delta}
        else:
            return False, {}


def below_threshold_in_window(new_value=None, old_value=None, params=None, extra_values=None):
    days_below_threshold = 0
    lowest_uptime = 100
    threshold_seconds = 60 * 60 * 24 * (params['threshold_uptime'] / 100)
    for uptime in extra_values['uptimes'][-params['window_days']:]:

        if uptime is not None:
            if uptime < threshold_seconds:
                days_below_threshold += 1
            if uptime < lowest_uptime:
                lowest_uptime = uptime

    if days_below_threshold >= params['threshold_days']:
        return True, {
            'days_below_threshold': days_below_threshold,
            'lowest_uptime': lowest_uptime
        }

    return False, {}


def generate_article_alert_email(values):
    if values['num_notifications'] == 1:
        notification_subject = '1 article exceeded threshold for %s' % values['alert_name']
        notification_intro = '<p>There is <b>1</b> article that exceeded the threshold for <b>%s</a>' % values['alert_name']
    else:
        notification_subject = '%s articles exceeded threshold for %s' % (values['num_notifications'], values['alert_name'])
        notification_intro = '<p>There were %s articles that exceeded threshold for %s' % (values['num_notifications'], values['alert_name'])

    subject = 'Impact Vizor (%s): %s' % (values['publisher_id'], notification_subject)
    body = """
        %s
        <p>&nbsp;&nbsp;&nbsp;&nbsp;<a href="%s%s?notification_summary_id=%s#notification-%s">View notification details</a></p>
        <p>Thank you,<br/>Impact Vizor Team</p>
    """ % (
        notification_intro,
        common.IVETL_WEB_ADDRESS,
        reverse('notifications.list'),
        values['notification_summary'].notification_summary_id,
        values['notification_summary'].notification_summary_id,
    )

    return subject, body


def generate_site_check_email(values):
    if values['num_notifications'] == 1:
        notification_subject = '1 site below uptime threshold for %s' % values['alert_name']
        notification_intro = '<p>There was <b>1</b> site that fell below the uptime threshold for <b>%s</a>' % values['alert_name']
    else:
        notification_subject = '%s sites below threshold for %s' % (values['num_notifications'], values['alert_name'])
        notification_intro = '<p>There were %s sites below the uptime threshold for %s' % (values['num_notifications'], values['alert_name'])

    subject = 'Impact Vizor: %s' % notification_subject
    body = """
        %s
        <p>Params: %s</p>
        <p>Filters: %s</p>
        <p>&nbsp;&nbsp;&nbsp;&nbsp;<a href="%s%s?notification_summary_id=%s#notification-%s">View notification details</a></p>
        <p>Thank you,<br/>Impact Vizor Team</p>
    """ % (
        notification_intro,
        get_check_params_display_string(values['alert']),
        get_filter_params_display_string(values['alert']),
        common.IVETL_WEB_ADDRESS,
        reverse('notifications.list'),
        values['notification_summary'].notification_summary_id,
        values['notification_summary'].notification_summary_id,
    )

    return subject, body


CHECK_TYPES = {
    'exceeds-integer': {
        'function': exceeds_integer,
        'params': [
            {
                'name': 'threshold',
                'label': 'Threshold',
                'type': 'integer',
                'requirement_text': 'An integer value for threshold'
            },
        ]
    },
    'percentage-change': {
        'function': percentage_change,
        'params': [
            {
                'name': 'percentage_change',
                'label': 'Percentage Change',
                'type': 'percentage-integer',
                'requirement_text': 'A percentage change value'
            },
        ]
    },
    'below-threshold-in-window': {
        'function': below_threshold_in_window,
        'params': [
            {
                'name': 'window_days',
                'label': 'Window',
                'type': 'integer',
                'requirement_text': 'A window length in days'
            },
            {
                'name': 'threshold_days',
                'label': 'Days',
                'type': 'integer',
                'requirement_text': 'A number of days below'
            },
            {
                'name': 'threshold_uptime',
                'label': 'Threshold',
                'type': 'percentage-float',
                'requirement_text': 'A percentage threshold'
            },
        ]
    }
}

CHECKS = {
    'mendeley-saves-exceeds-integer': {
        'name': 'Mendeley Saves for Article Greater Than Threshold',
        'check_type': CHECK_TYPES['exceeds-integer'],
        'filters': [
            {'name': 'article_journal', 'label': 'Journal', 'table': 'published_article'},
            {'name': 'article_journal_issn', 'label': 'ISSN', 'table': 'published_article'},
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
            {'key': 'article_title', 'name': 'Article', 'type': 'article-link', 'width': 'wide'},
            {'key': 'old_value', 'name': 'Previous Value', 'align': 'right'},
            {'key': 'new_value', 'name': 'New Value', 'align': 'right'},
        ],
        'email_generator_function': generate_article_alert_email,
        'products': [
            'published_articles',
        ]
    },

    'mendeley-saves-percentage-change': {
        'name': 'Mendeley Saves for Article Increases By Percentage',
        'check_type': CHECK_TYPES['percentage-change'],
        'filters': [
            {'name': 'article_journal', 'label': 'Journal', 'table': 'published_article'},
            {'name': 'article_journal_issn', 'label': 'ISSN', 'table': 'published_article'},
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
            {'key': 'article_title', 'name': 'Article', 'type': 'article-link', 'width': 'wide'},
            {'key': 'old_value', 'name': 'Previous Value', 'align': 'right'},
            {'key': 'new_value', 'name': 'New Value', 'align': 'right'},
        ],
        'email_generator_function': generate_article_alert_email,
        'products': [
            'published_articles',
        ]
    },

    'citations-exceeds-integer': {
        'name': 'Citations for Article Greater Than Threshold',
        'check_type': CHECK_TYPES['exceeds-integer'],
        'filters': [
            {'name': 'article_journal', 'label': 'Journal', 'table': 'published_article'},
            {'name': 'article_journal_issn', 'label': 'ISSN', 'table': 'published_article'},
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
            {'key': 'article_title', 'name': 'Article', 'type': 'article-link', 'width': 'wide'},
            {'key': 'old_value', 'name': 'Previous Value', 'align': 'right'},
            {'key': 'new_value', 'name': 'New Value', 'align': 'right'},
        ],
        'email_generator_function': generate_article_alert_email,
        'products': [
            'published_articles',
        ]
    },

    'citations-percentage-change': {
        'name': 'Citations for Article Increases By Percentage',
        'check_type': CHECK_TYPES['percentage-change'],
        'filters': [
            {'name': 'article_journal', 'label': 'Journal', 'table': 'published_article'},
            {'name': 'article_journal_issn', 'label': 'ISSN', 'table': 'published_article'},
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
            {'key': 'article_title', 'name': 'Article', 'type': 'article-link', 'width': 'wide'},
            {'key': 'old_value', 'name': 'Previous Value', 'align': 'right'},
            {'key': 'new_value', 'name': 'New Value', 'align': 'right'},
        ],
        'email_generator_function': generate_article_alert_email,
        'products': [
            'published_articles',
        ]
    },

    'site-uptime-below-threshold': {
        'name': 'Site Uptime Below Threshold',
        'check_type': CHECK_TYPES['below-threshold-in-window'],
        'filters': [
            {'name': 'check_type', 'label': 'Check Type', 'table': 'uptime_check_metadata'},
            {'name': 'site_platform', 'label': 'Platform', 'table': 'uptime_check_metadata'},
            {'name': 'site_type', 'label': 'Site Type', 'table': 'uptime_check_metadata'},
            {'name': 'publisher_name', 'label': 'Publisher Name', 'table': 'uptime_check_metadata'},
        ],
        'format_string': 'Site %(site_code)s: %(new_value)s citations (from %(old_value), up %(percentage_increase))',
        'table_order': [
            {'key': 'check_name', 'name': 'Check', 'type': 'check-link', 'width': 'wide'},
            {'key': 'site_code', 'name': 'Site Code'},
            {'key': 'site_type', 'name': 'Site Type'},
            {'key': 'site_platform', 'name': 'Platform'},
            {'key': 'pingdom_account', 'name': 'Account'},
            {'key': 'from_date', 'name': 'From Date'},
            {'key': 'to_date', 'name': 'To Date'},
        ],
        'email_generator_function': generate_site_check_email,
        'products': [
            'highwire_sites',
        ]
    },
}


def get_check_params_display_string(alert):
    check_params = json.loads(alert.check_params)
    param_strings = []
    for p in CHECKS[alert.check_id]['check_type']['params']:
        if p['name'] in check_params:
            param_strings.append('%s = %s' % (p['label'], check_params[p['name']]))
    return ", ".join(param_strings)


def get_filter_params_display_string(alert):
    filter_params = json.loads(alert.filter_params)
    filter_strings = []
    for f in CHECKS[alert.check_id]['filters']:
        if f['name'] in filter_params:
            filter_strings.append('%s = %s' % (f['label'], filter_params[f['name']]))
    return ", ".join(filter_strings)


def get_all_params_for_check(check_id=None, publisher_id=None):
    all_params = []
    for alert in Alert.objects.allow_filtering().filter(publisher_id=publisher_id, check_id=check_id):
        if alert.enabled:
            check_params = json.loads(alert.check_params)
            all_params.append(check_params)

    return all_params


def run_alerts(check_ids=[], publisher_id=None, product_id=None, pipeline_id=None, job_id=None, new_value=None, old_value=None, extra_values=None):

    for check_id in check_ids:

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
                        raw_value = extra_values.get(param_name)
                        if not raw_value:
                            raw_value = ''
                        given_value = raw_value.lower()
                        if not required_value == given_value:
                            passed_filters = False
                            break

                if passed_filters:

                    # run the test
                    passed_test, values_from_check_function = check_function(
                        new_value=new_value,
                        old_value=old_value,
                        params=check_params,
                        extra_values=extra_values,
                    )

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


def send_alert_notifications(check_ids=[], publisher_id=None, product_id=None, pipeline_id=None, job_id=None):

    now = datetime.datetime.now()

    for check_id in check_ids:
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

                notification_summary = NotificationSummary.objects.create(
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

                subject, body = CHECKS[check_id]['email_generator_function']({
                    'alert': alert,
                    'alert_name': alert.name,
                    'num_notifications': num_notifications,
                    'publisher_id': publisher_id,
                    'notification_summary': notification_summary,
                })

                # with open('/Users/john/email.txt', 'w') as f:
                #     f.write(subject)
                #     f.write('\n\n')
                #     f.write(body)

                if alert.emails:
                    to = ",".join(alert.emails)
                else:
                    publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)
                    to = publisher.email

                common.send_email(subject, body, to=to)
