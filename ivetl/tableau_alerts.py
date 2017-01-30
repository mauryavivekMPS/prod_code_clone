import datetime
from ivetl.connectors import TableauConnector
from ivetl.models import WorkbookUrl, TableauNotification
from ivetl.common import common


def check_for_citation_amount(publisher_id):
    return True

ALERT_TEMPLATES = {
    'hot-article-tracker': {
        'choice_description': 'Hot Article Tracker',
        'name_template': 'Hot Article Tracker Update',
        'name': 'Hot Article Tracker',
        'workbooks': {
            'full': 'hot_article_tracker.twb',
            'configure': 'alert_hot_article_tracker_configure.twb',
            'export': 'alert_hot_article_tracker_export.twb',
        },
        'frequency': 'monthly',
        'type': 'scheduled',
        'order': 1,
    },
    'rejected-article-tracker': {
        'choice_description': 'Rejected Article Tracker',
        'name_template': 'Rejected Article Tracker Update',
        'name': 'Rejected Article Tracker',
        'workbooks': {
            'full': 'rejected_article_tracker.twb',
            'configure': 'alert_rejected_article_tracker_configure.twb',
            'export': 'alert_rejected_article_tracker_export.twb',
        },
        'frequency': 'quarterly',
        'type': 'scheduled',
        'order': 2,
    },
    'advance-correlator-citation-usage': {
        'choice_description': 'Advanced Correlator of Citations & Usage',
        'name_template': 'Advanced Correlator of Citations & Usage Update',
        'name': 'Advanced Correlator of Citations & Usage',
        'workbooks': {
            'full': 'advance_correlator_citation_usage.twb',
            'configure': 'alert_advance_correlator_citation_usage_configure.twb',
            'export': 'alert_advance_correlator_citation_usage_export.twb',
        },
        'frequency': 'monthly',
        'type': 'scheduled',
        'order': 3,
    },
    'uv-institutional-usage': {
        'choice_description': 'UV: Institutional Usage',
        'name_template': 'UV: Institutional Usage Update',
        'name': 'UV: Institutional Usage',
        'workbooks': {
            'full': 'uv_institutional_usage.twb',
            'export': 'alert_uv_institutional_usage_export.twb',
        },
        'frequency': 'monthly',
        'type': 'scheduled',
        'order': 4,
    },
    # 'articles-citations-exceed-integer': {
    #     'choice_description': 'Articles that exceed [] citations',
    #     'name_template': 'New Articles That Exceed %s Citations',
    #     'report_name': 'Hot Article Tracker',
    #     'type': 'threshold',
    #     'threshold_type': 'integer',
    #     'threshold_default_value': 20,
    #     'threshold_function': check_for_citation_amount,
    #     'order': 1,
    # },
    # 'articles-citations-increase-exceed-percentage': {
    #     'choice_description': 'Articles that increase their citations by [] or greater',
    #     'name_template': 'New Articles With Citation Growth of %s%% or Greater',
    #     'report_name': 'Hot Article Tracker',
    #     'type': 'threshold',
    #     'threshold_type': 'percentage',
    #     'threshold_default_value': 50,
    #     'threshold_function': check_for_citation_amount,
    #     'order': 2,
    # },
}

ALERT_TEMPLATES_BY_SOURCE_PIPELINE = {
    ('rejected_manuscripts', 'rejected_articles'): [
        'rejected-article-tracker',
    ],
    ('rejected_manuscripts', 'benchpress_rejected_articles'): [
        'rejected-article-tracker',
    ],
    ('rejected_manuscripts', 'reprocess_rejected_articles'): [
        'rejected-article-tracker',
    ],
    ('article_citations', 'article_citations'): [
        'hot-article-tracker',
        'advance-correlator-citation-usage',
    ],
    ('institutions', 'update_institution_usage_deltas'): [
        'uv-institutional-usage',
    ],
}


def get_report_params_display_string(alert):
    return alert.report_id.title()


def process_alert(alert):
    # check for data

    t = TableauConnector(
        username=common.TABLEAU_USERNAME,
        password=common.TABLEAU_PASSWORD,
        server=common.TABLEAU_SERVER
    )

    template = ALERT_TEMPLATES[alert.template_id]
    export_workbook_id = template['workbooks'].get('export')

    has_data = True
    if export_workbook_id:
        workbook_url = WorkbookUrl.objects.get(publisher_id=alert.publisher_id, workbook_id=export_workbook_id)
        workbook_home_view = common.TABLEAU_WORKBOOKS_BY_ID[export_workbook_id]['home_view']
        view_url = '%s/%s' % (workbook_url, workbook_home_view)
        # TODO: add filters and params here!!
        has_data = t.check_report_for_data(view_url)

    if has_data:

        # create notification record
        now = datetime.datetime.now()
        expiration_date = now + datetime.timedelta(days=365)
        notification = TableauNotification.objects.create(
            alert_id=alert.alert_id,
            publisher_id=alert.publisher_id,
            template_id=alert.template_id,
            notification_date=now,
            expiration_date=expiration_date,
            name=alert.name,
            alert_params=alert.alert_params,
            alert_filters=alert.alert_filters,
            custom_message=alert.custom_message,
        )

        # send any lite emails
        if alert.attachment_only_emails:
            pass

        # send any full emails
        if alert.full_emails:
            # TODO: make notification URL absolute here
            notification_url = '/n/%s/' % notification.notification_id
            pass
