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
    # create notification record
    # set expiry to a year!!
    # get email bits
    # send email
    pass
