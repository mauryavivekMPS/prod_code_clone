def check_for_citation_amount(publisher_id):
    return True

ALERTS = {
    'rejected-article-tracker': {
        'choice_description': 'Rejected Article Tracker',
        'name_template': 'Rejected Article Tracker Update',
        'report_name': 'Rejected Article Tracker',
        'workbooks': {
            'full': 'rejected_article_tracker.twb',
            'configure': 'alert_rejected_article_tracker.twb',
            'export': 'alert_rejected_article_tracker_export.twb',
        },
        'type': 'scheduled',
        'order': 1,
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

ALERTS_BY_SOURCE_PIPELINE = {
    ('rejected_manuscripts', 'rejected_articles'): [
        'rejected-article-tracker',
    ],
    # ('article_citations', 'article_citations'): [
    #     'articles-citations-exceed-integer',
    #     'articles-citations-increase-exceed-percentage',
    # ],
}


def get_report_params_display_string(alert):
    return alert.report_id.title()
