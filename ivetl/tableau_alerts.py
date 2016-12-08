REPORTS = {
    'hot-article-tracker': {
        'name': 'Hot Article Tracker',
    }
}


def get_report_params_display_string(alert):
    return alert.report_id.title()
