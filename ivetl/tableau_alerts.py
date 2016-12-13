def check_for_citation_amount(publisher_id):
    return True


def check_for_mendeley_amount(publisher_id):
    return True


def check_for_mendeley_percentage_change(publisher_id):
    return True

ALERTS = {
    'hot-article-tracker-scheduled': {
        'name': 'Hot Article Tracker (Scheduled)',
        'choice_description': 'Send me the Hot Article Tracker as soon as it has been updated.',
        'type': 'scheduled',
    },
    'hot-article-tracker-citation-amount-trigger': {
        'name': 'Hot Article Tracker (Citation Amount Trigger)',
        'choice_description': 'Send me the Hot Article Tracker whenever article citations exceed a threshold amount.',
        'type': 'threshold',
        'threshold_function': check_for_citation_amount,
    },
    'section-performance-analyzer-scheduled': {
        'name': 'Section Performance Analyzer (Scheduled)',
        'choice_description': 'Send me the Section Performance Analyzer as soon as it has been updated.',
        'type': 'scheduled',
    },
    'section-performance-analyzer-amount-trigger': {
        'name': 'Section Performance Analyzer (Mendeley Amount Trigger)',
        'choice_description': 'Send me the Section Performance Analyzer whenever Mendeley shares exeed a threshold amount.',
        'type': 'threshold',
        'threshold_function': check_for_mendeley_amount,
    },
    'section-performance-analyzer-percentage-trigger': {
        'name': 'Section Performance Analyzer (Mendeley % Trigger)',
        'choice_description': 'Send me the Section Performance Analyzer whenever Mendeley shares increase by a percentage.',
        'type': 'threshold',
        'threshold_function': check_for_mendeley_percentage_change,
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


def get_report_params_display_string(alert):
    return alert.report_id.title()
