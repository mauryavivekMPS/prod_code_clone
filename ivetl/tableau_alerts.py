REPORTS = {
    'hot-article-tracker-scheduled': {
        'name': 'Hot Article Tracker (Scheduled)',
        'choice_description': 'Send me the Hot Article Tracker as soon as it has been updated.'
    },
    'hot-article-tracker-citation-amount-trigger': {
        'name': 'Hot Article Tracker (Citation Amount Trigger)',
        'choice_description': 'Send me the Hot Article Tracker whenever article citations exceed a threshold amount.'
    },
    'section-performance-analyzer-scheduled': {
        'name': 'Section Performance Analyzer (Scheduled)',
        'choice_description': 'Send me the Section Performance Analyzer as soon as it has been updated.'
    },
    'section-performance-analyzer-amount-trigger': {
        'name': 'Section Performance Analyzer (Mendeley Amount Trigger)',
        'choice_description': 'Send me the Section Performance Analyzer whenever Mendeley shares exeed a threshold amount.'
    },
    'section-performance-analyzer-percentage-trigger': {
        'name': 'Section Performance Analyzer (Mendeley % Trigger)',
        'choice_description': 'Send me the Section Performance Analyzer whenever Mendeley shares increase by a percentage.'
    },
}


def get_report_params_display_string(alert):
    return alert.report_id.title()
