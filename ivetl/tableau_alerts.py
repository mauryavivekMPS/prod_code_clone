def check_for_citation_amount(publisher_id):
    return True


def check_for_mendeley_amount(publisher_id):
    return True


def check_for_mendeley_percentage_change(publisher_id):
    return True

ALERTS = {
    'rejected-article-tracker': {
        'name': 'Rejected Article Tracker (Scheduled)',
        'choice_description': 'Rejected Article Tracker',
        'type': 'scheduled',
        'order': 1,
    },
    'hot-article-tracker': {
        'name': 'Hot Article Tracker (Scheduled)',
        'choice_description': 'Hot Article Tracker',
        'type': 'scheduled',
        'order': 2,
    },
    'hot-article-tracker-citation-amount-trigger': {
        'name': 'Hot Article Tracker (Citation Amount Trigger)',
        'choice_description': 'Articles that exceed [] citations',
        'type': 'threshold',
        'threshold_type': 'integer',
        'threshold_default_value': 20,
        'threshold_function': check_for_citation_amount,
        'order': 1,
    },
    'hot-article-tracker-citation-percentage-trigger': {
        'name': 'Hot Article Tracker (Citation Amount Trigger)',
        'choice_description': 'Articles that increase their citations by [] or greater',
        'type': 'threshold',
        'threshold_type': 'percentage',
        'threshold_default_value': 50,
        'threshold_function': check_for_citation_amount,
        'order': 2,
    },
    'section-performance-analyzer-scheduled': {
        'name': 'Section Performance Analyzer (Scheduled)',
        'choice_description': 'Section Performance Analyzer',
        'type': 'scheduled',
        'order': 3,
    },
    'section-performance-analyzer-amount-trigger': {
        'name': 'Section Performance Analyzer (Mendeley Amount Trigger)',
        'choice_description': 'Articles that exceed [] saves on Mendeley',
        'type': 'threshold',
        'threshold_type': 'integer',
        'threshold_default_value': 20,
        'threshold_function': check_for_mendeley_amount,
        'order': 3,
    },
    'section-performance-analyzer-percentage-trigger': {
        'name': 'Section Performance Analyzer (Mendeley % Trigger)',
        'choice_description': 'Articles that increase their saves on Mendeley by [] or greater',
        'type': 'threshold',
        'threshold_type': 'percentage',
        'threshold_default_value': 100,
        'threshold_function': check_for_mendeley_percentage_change,
        'order': 4,
    },
    'citation-distribution-surveyor': {
        'name': 'Citation Distribution Surveyor (Scheduled)',
        'choice_description': 'Citation Distribution Surveyor',
        'type': 'scheduled',
        'order': 4,
    },
    'cohort-comparator-scheduled': {
        'name': 'Cohort Comparator (Scheduled)',
        'choice_description': 'Cohort Comparator',
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
