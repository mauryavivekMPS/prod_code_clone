import datetime
import sendgrid
import base64
from sendgrid.helpers.mail import Email, Content, Mail, CustomArg, Attachment
from django.template import loader
from ivetl.connectors import TableauConnector
from ivetl.models import TableauNotification, TableauNotificationByAlert
from ivetl.common import common


def check_for_citation_amount(publisher_id):
    return True


ALERT_TEMPLATES = {
    'hot-article-tracker': {
        'choice_description': 'IV: Hot Article Tracker',
        'name_template': 'IV: Hot Article Tracker Update',
        'name': 'IV: Hot Article Tracker',
        'workbooks': {
            'full': 'hot_article_tracker.twb',
            'full-name': 'Hot Article Tracker',
            'configure': 'alert_hot_article_tracker_configure.twb',
            'export': 'alert_hot_article_tracker_export.twb',
        },
        'filter_worksheet_name': 'HAT-Articles',
        'export_value_name': 'Published Articles',
        'thumbnail': 'thumbnail-hot-article-tracker.png',
        'frequency': 'monthly',
        'type': 'scheduled',
        'order': 1,
    },
    'rejected-article-tracker': {
        'choice_description': 'IV: Rejected Article Tracker',
        'name_template': 'IV: Rejected Article Tracker Update',
        'name': 'IV: Rejected Article Tracker',
        'workbooks': {
            'full': 'rejected_article_tracker.twb',
            'full-name': 'Rejected Article Tracker',
            'configure': 'alert_rejected_article_tracker_configure.twb',
            'export': 'alert_rejected_article_tracker_export.twb',
        },
        'filter_worksheet_name': 'Summary Status',
        'thumbnail': 'thumbnail-rejected-article-tracker.png',
        'frequency': 'quarterly',
        'type': 'scheduled',
        'order': 2,
    },
    'advance-correlator-citation-usage': {
        'choice_description': 'IV: Advanced Correlator of Citations & Usage',
        'name_template': 'IV: Advanced Correlator of Citations & Usage Update',
        'name': 'IV: Advanced Correlator of Citations & Usage',
        'workbooks': {
            'full': 'advance_correlator_citation_usage.twb',
            'full-name': 'Advance Correlator of Citations &amp; Usage',
            'configure': 'alert_advance_correlator_citation_usage_configure.twb',
            'export': 'alert_advance_correlator_citation_usage_export.twb',
        },
        'filter_worksheet_name': 'AAC-Articles',
        'export_value_name': 'Published Articles',
        'thumbnail': 'thumbnail-advanced-correlator.png',
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
            'full-name': 'UV: Institutional Usage',
            'export': 'alert_uv_institutional_usage_export.twb',
        },
        'thumbnail': 'thumbnail-institutional-usage.png',
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


def process_alert(alert, monthly_message=None, attachment_only_emails_override=None, full_emails_override=None, custom_message_override=None):
    template = ALERT_TEMPLATES[alert.template_id]

    t = TableauConnector(
        username=common.TABLEAU_USERNAME,
        password=common.TABLEAU_PASSWORD,
        server=common.TABLEAU_SERVER
    )

    run_notification = False

    if alert.send_with_no_data:
        run_notification = True
    else:
        has_data = False
        export_workbook_id = template['workbooks'].get('export')
        if export_workbook_id:
            export_workbooks = t.list_workbooks_by_name(export_workbook_id,
                alert.publisher_id)
            if len(export_workbooks >= 0):
                export_workbook = export_workbooks[0]
                export_view_id = t.view_by_publisher_workbook(export_workbook)
                has_data = t.check_report_for_data(export_view_id,
                    template.get('export_value_name', 'Number of Records'))

        if has_data:
            run_notification = True

    if run_notification:

        if custom_message_override:
            custom_message = custom_message_override
        else:
            custom_message = alert.custom_message

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
            custom_message=custom_message,
        )

        # and add an entry to the notification lookup table
        TableauNotificationByAlert.objects.create(
            publisher_id=notification.publisher_id,
            alert_id=notification.alert_id,
            notification_id=notification.notification_id,
            notification_date=notification.notification_date,
        )

        if attachment_only_emails_override or full_emails_override:
            attachment_only_emails = attachment_only_emails_override
            full_emails = full_emails_override
        else:
            attachment_only_emails = alert.attachment_only_emails
            full_emails = alert.full_emails

        sg = sendgrid.SendGridAPIClient(apikey=common.SG_API_KEY)
        from_email = Email(common.EMAIL_FROM)
        subject = alert.name

        attachment_workbook_id = template['workbooks'].get('full-name')
        attachment_workbook = t.list_workbooks_by_name(attachment_workbook_id,
            alert.publisher_id)
        attachment_view_id = t.view_by_publisher_workbook(attachment_workbook[0])
        attachment_filename = '%s %s.pdf' % (alert.name.replace('/', '-').replace('\\', '-'), now.strftime('%Y-%m-%d'))
        attachment_content_id = 'report'

        pdf_path = t.generate_pdf_report(attachment_view_id)
        pdf_content = open(pdf_path, 'rb').read()
        encoded_pdf_content = base64.b64encode(pdf_content).decode()

        email_template = loader.get_template('tableau_alerts/notification_email.html')

        if attachment_only_emails:
            html = email_template.render({
                'notification': notification,
                'monthly_message': monthly_message,
                'include_live_report_link': False,
            })
            content = Content('text/html', html)

            for to_email_address in attachment_only_emails:
                to_email = Email(to_email_address)
                mail = Mail(from_email, subject, to_email, content)

                mail.add_custom_arg(CustomArg('notification_id', str(notification.notification_id)))
                mail.add_custom_arg(CustomArg('alert_id', str(notification.alert_id)))
                mail.add_custom_arg(CustomArg('publisher_id', notification.publisher_id))

                attachment = Attachment()
                attachment.content = encoded_pdf_content
                attachment.type = "application/pdf"
                attachment.filename = attachment_filename
                attachment.disposition = "attachment"
                attachment.content_id = attachment_content_id
                mail.add_attachment(attachment)

                sg.client.mail.send.post(request_body=mail.get())

        if full_emails:
            notification_url = '%s/n/%s/' % (common.IVETL_WEB_ADDRESS, notification.notification_id)
            thumbnail_url = '%s/static/dist/%s' % (common.IVETL_WEB_ADDRESS, template['thumbnail'])

            html = email_template.render({
                'notification': notification,
                'include_live_report_link': True,
                'notification_url': notification_url,
                'thumbnail_url': thumbnail_url,
            })
            content = Content('text/html', html)

            for to_email_address in full_emails:
                to_email = Email(to_email_address)
                mail = Mail(from_email, subject, to_email, content)

                mail.add_custom_arg(CustomArg('notification_id', str(notification.notification_id)))
                mail.add_custom_arg(CustomArg('alert_id', str(notification.alert_id)))
                mail.add_custom_arg(CustomArg('publisher_id', notification.publisher_id))

                attachment = Attachment()
                attachment.content = encoded_pdf_content
                attachment.type = "application/pdf"
                attachment.filename = attachment_filename
                attachment.disposition = "attachment"
                attachment.content_id = attachment_content_id
                mail.add_attachment(attachment)

                sg.client.mail.send.post(request_body=mail.get())
