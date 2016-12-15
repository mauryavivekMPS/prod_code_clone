def check_for_citation_amount(publisher_id):
    return True


def check_for_mendeley_amount(publisher_id):
    return True


def check_for_mendeley_percentage_change(publisher_id):
    return True

ALERTS = {
    'hot-article-tracker': {
        'choice_description': 'Hot Article Tracker',
        'name_template': 'Hot Article Tracker Update',
        'type': 'scheduled',
        'order': 1,
    },
    'rejected-article-tracker': {
        'choice_description': 'Rejected Article Tracker',
        'name_template': 'Rejected Article Tracker Update',
        'type': 'scheduled',
        'order': 2,
    },
    'articles-citations-exceed-integer': {
        'choice_description': 'Articles that exceed [] citations',
        'name_template': 'New Articles That Exceed %s Citations',
        'type': 'threshold',
        'threshold_type': 'integer',
        'threshold_default_value': 20,
        'threshold_function': check_for_citation_amount,
        'order': 1,
    },
    'articles-citations-increase-exceed-percentage': {
        'choice_description': 'Articles that increase their citations by [] or greater',
        'name_template': 'New Articles With Citation Growth of %s%% or Greater',
        'type': 'threshold',
        'threshold_type': 'percentage',
        'threshold_default_value': 50,
        'threshold_function': check_for_citation_amount,
        'order': 2,
    },
    'section-performance-analyzer-scheduled': {
        'choice_description': 'Section Performance Analyzer',
        'name_template': 'Section Performance Analyzer Update',
        'type': 'scheduled',
        'order': 3,
    },
    'articles-mendeley-saves-exceed-integer': {
        'choice_description': 'Articles that exceed [] saves on Mendeley',
        'name_template': 'New Articles That Exceed %s Saves on Mendeley',
        'type': 'threshold',
        'threshold_type': 'integer',
        'threshold_default_value': 20,
        'threshold_function': check_for_mendeley_amount,
        'order': 3,
    },
    'articles-mendeley-saves-increase-exceed-percentage': {
        'choice_description': 'Articles that increase their saves on Mendeley by [] or greater',
        'name_template': 'New Articles With Saves on Mendeley Growth of %s%% or Greater',
        'type': 'threshold',
        'threshold_type': 'percentage',
        'threshold_default_value': 100,
        'threshold_function': check_for_mendeley_percentage_change,
        'order': 4,
    },
    'citation-distribution-surveyor': {
        'choice_description': 'Citation Distribution Surveyor',
        'name_template': 'Citation Distribution Surveyor Update',
        'type': 'scheduled',
        'order': 4,
    },
    'cohort-comparator-scheduled': {
        'choice_description': 'Cohort Comparator',
        'name_template': 'Cohort Comparator Update',
        'type': 'scheduled',
        'order': 5,
    },
}

ALERTS_BY_SOURCE_PIPELINE = {
    ('article_citations', 'article_citations'): [
        'hot-article-tracker-scheduled',
        'hot-article-tracker-amount-trigger',
        'hot-article-tracker-percentage-trigger',
    ],
    ('published_articles', 'article_usage'): [
        'section-performance-analyzer-scheduled',
        'section-performance-analyzer-amount-trigger',
        'section-performance-analyzer-percentage-trigger',
    ],
}

ALERT_TYPES = {
    'scheduled': {
        'instruction_text': 'Send a notification when this report is updated:',
    },
    'threshold': {
        'instruction_text': 'Send a notification for articles that meet the following',
    }
}


def get_report_params_display_string(alert):
    return alert.report_id.title()
