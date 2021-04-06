from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from ivweb.app.views import (alerts, app_content, audit, auth, home,
    journals, notifications, pipelines, publishers, rejected_article_overrides,
    reports, sendgrid, survey, tableau_alerts, uploaded_files, uptime, users,
    value_mappings)

urlpatterns = [

    # auth
    url(r'^login/$', auth.login, name='login'),
    url(r'^logout/$', auth.logout, name='logout'),

    # user settings
    url(r'^settings/$', auth.settings, name='settings'),

    # audit log
    url(r'^audit/$', audit.show, name='audit'),

    # surveys
    url(r'^survey/(?P<survey_id>[\w\-.]+)/$', survey.redirect, name='survey'),
    url(r'^vizorsurveylink/(?P<survey_id>[\w\-.]+)/$', survey.vizor_survey_link, name='vizor_survey_link'),

    # homepage
    url(r'^$', home.home, name='home'),
    url(r'^jobs/$', home.recent_jobs, name='recent_jobs'),
    url(r'^growth/$', home.growth, name='growth'),
    url(r'^performance/$', home.performance, name='performance'),
    url(r'^support/$', home.support, name='home.support'),

    # users
    url(r'^users/$', users.list_users, name='users.list'),
    url(r'^users/new/$', users.edit, name='users.new'),
    url(r'^users/(?P<user_id>[\w\-.]+)/$', users.edit, name='users.edit'),

    # alerts
    url(r'^oldalerts/$', alerts.list_alerts, name='alerts.list'),
    url(r'^oldalerts/new/$', alerts.edit, name='alerts.new'),
    url(r'^oldalerts/(?P<alert_id>[\w\-.]+)/$', alerts.edit, name='alerts.edit'),

    # tableau alerts
    url(r'^alerts/$', tableau_alerts.list_alerts, name='tableau_alerts.list'),
    url(r'^alerts/new/$', tableau_alerts.edit, name='tableau_alerts.new'),
    url(r'^alerts/(?P<alert_id>[\w\-.]+)/$', tableau_alerts.edit, name='tableau_alerts.edit'),

    # sendgrid
    url(r'^sendgrid/$', sendgrid.event_hook, name='sendgrid.event_hook'),

    # tableau external notifications
    url(r'^n/(?P<notification_id>[\w\-.]+)/$', tableau_alerts.show_external_notification, name='tableau_alerts.show_external_notification'),

    # notifications
    url(r'^notifications/$', notifications.list_notifications, name='notifications.list'),

    # journals and citable sections
    url(r'^journals/$', journals.list_journals, name='journals.list'),
    url(r'^journals/(?P<publisher_id>[\w]+)/(?P<uid>[\w\-.]+)/citablesections/$', journals.choose_citable_sections, name='journals.choose_citable_sections'),

    # tableau admin
    url(r'^updatereports/$', reports.update_reports, name='reports.update_reports'),

    # site uptime admin
    url(r'^uptimeoverrides/$', uptime.list_overrides, name='uptime.list_overrides'),
    url(r'^uptimeoverrides/new/$', uptime.new_override, name='uptime.new_override'),

    # value mappings
    url(r'^metadatamappings/$', value_mappings.list_mappings, name='value_mappings.list_mappings'),
    url(r'^metadatamappings/(?P<publisher_id>[\w]+)/(?P<mapping_type>[\w]+)/$', value_mappings.edit, name='value_mappings.edit'),

    # app content
    url(r'^appcontent/$', app_content.list_blocks, name='app_content.list_blocks'),
    url(r'^appcontent/new/$', app_content.edit_block, name='app_content.new_block'),
    url(r'^appcontent/(?P<block_id>[\w\-]+)/$', app_content.edit_block, name='app_content.edit_block'),

    # uploaded files
    url(r'^uploadedfiles/$', uploaded_files.list_files, name='uploaded_files.list_files'),
    url(r'^uploadedfiles/(?P<publisher_id>[\w]+)/(?P<uploaded_file_id>[\w\-]+)/$', uploaded_files.download, name='uploaded_files.download'),

    # demos
    url(r'^demos/$', publishers.list_demos, name='publishers.list_demos'),
    url(r'^demos/new/$', publishers.edit_demo, name='publishers.new_demo'),
    url(r'^demos/(?P<demo_id>[\w\-\.]+)/$', publishers.edit_demo, name='publishers.edit_demo'),

    # publishers
    url(r'^publishers/$', publishers.list_publishers, name='publishers.list'),
    url(r'^publishers/new/$', publishers.edit, name='publishers.new'),
    url(r'^publishers/(?P<publisher_id>[\w]+)/$', publishers.edit, name='publishers.edit'),
    url(r'^publishers/(?P<publisher_id>[\w]+)/users/$', users.list_users, name='publishers.users'),
    url(r'^publishers/(?P<publisher_id>[\w]+)/users/new/$', users.edit, name='publishers.users.new'),
    url(r'^publishers/(?P<publisher_id>[\w]+)/journals/$', journals.list_journals, name='publishers.journals'),
    url(r'^publishers/(?P<publisher_id>[\w]+)/journals/(?P<uid>[\w\-.]+)/citablesections/$', journals.choose_citable_sections, name='publishers.journals.choose_citable_sections'),
    url(r'^publishers/(?P<publisher_id>[\w]+)/users/(?P<user_id>[\w\-.]+)/$', users.edit, name='publishers.users.edit'),

    # pipeline details
    url(r'^pipelines/(?P<product_id>[\w]+)/(?P<pipeline_id>[\w]+)/$', pipelines.list_pipelines, name='pipelines.list'),
    url(r'^pipelines/(?P<product_id>[\w]+)/(?P<pipeline_id>[\w]+)/include/updatedpublisherruns/$', pipelines.include_updated_publisher_runs, name='pipelines.include_updated_publisher_runs'),

    # upload files for a pipeline or demo
    url(r'^pipelines/(?P<product_id>[\w]+)/(?P<pipeline_id>[\w]+)/pendingfiles/$', pipelines.pending_files, name='pipelines.pending_files_validator'),
    url(r'^pipelines/(?P<product_id>[\w]+)/(?P<pipeline_id>[\w]+)/pendingfiles_legacy/$', pipelines.pending_files_legacy, name='pipelines.pending_files'),
    url(r'^api/pipelines/(?P<publisher_id>[\w]+)/(?P<product_id>[\w]+)/(?P<pipeline_id>[\w]+)/pendingfiles', pipelines.api_get_pending_files_for_publisher, name='pipelines.api_get_pending_files_for_publisher'),
    # run a pipeline
    url(r'^pipelines/(?P<product_id>[\w]+)/(?P<pipeline_id>[\w]+)/run/$', pipelines.run, name='pipelines.run'),

    # tail a task
    url(r'^pipelines/(?P<product_id>[\w]+)/(?P<pipeline_id>[\w]+)/task/$', pipelines.tail, name='pipelines.tail'),

    # perform action on a job
    url(r'^pipelines/(?P<product_id>[\w]+)/(?P<pipeline_id>[\w]+)/action/$', pipelines.job_action, name='pipelines.job_action'),

    # various tools
    url(r'^validatecrossref/$', publishers.validate_crossref, name='publishers.validate_crossref'),
    url(r'^validateissn/$', publishers.validate_issn, name='publishers.validate_issn'),
    url(r'^newissn/$', publishers.new_issn, name='publishers.new_issn'),
    url(r'^checksetupstatus/$', publishers.check_setup_status, name='publishers.check_setup_status'),
    url(r'^updatedemostatus/$', publishers.update_demo_status, name='publishers.update_demo_status'),
    url(r'^uploadfile/$', pipelines.upload_pending_file_inline, name='pipelines.upload_pending_file_inline'),
    url(r'^deletefile/$', pipelines.delete_pending_file_inline, name='pipelines.delete_pending_file_inline'),
    url(r'^savemonthlymessage/$', pipelines.save_monthly_message, name='pipelines.save_monthly_message'),
    url(r'^includealertparams/$', alerts.include_alert_params, name='alerts.include_alert_params'),
    url(r'^includealertfilters/$', alerts.include_alert_filters, name='alerts.include_alert_filters'),
    url(r'^includecheckchoices/$', alerts.include_check_choices, name='alerts.include_check_choices'),
    url(r'^includenotificationdetails/$', notifications.include_notification_details, name='notifications.include_notification_details'),
    url(r'^dismissnotification/$', notifications.dismiss_notification, name='notifications.dismiss_notification'),
    url(r'^updatereportitem/$', reports.update_item, name='reports.update_item'),
    url(r'^includereportitemstatuses/$', reports.include_item_statuses, name='reports.include_item_statuses'),
    url(r'^deleteuptimeoverride/$', uptime.delete_override, name='uptime.delete_override'),
    url(r'^deletealert/$', tableau_alerts.delete_alert, name='tableau_alerts.delete_alert'),
    url(r'^togglealert/$', tableau_alerts.toggle_alert, name='tableau_alerts.toggle_alert'),
    url(r'^sendalertnow/$', tableau_alerts.send_alert_now, name='tableau_alerts.send_alert_now'),
    url(r'^includetemplatechoices/$', tableau_alerts.include_template_choices, name='tableau_alerts.include_template_choices'),
    url(r'^gettrustedreporturl/$', tableau_alerts.get_trusted_report_url, name='tableau_alerts.get_trusted_report_url'),
    url(r'^updatevaluedisplay/$', value_mappings.update_value_display, name='value_mappings.update_value_display'),
    url(r'^updatevaluemapping/$', value_mappings.update_value_mapping, name='value_mappings.update_value_mapping'),
    url(r'^runrefreshvaluemappings/$', value_mappings.run_refresh_mappings_pipeline, name='value_mappings.run_refresh_mappings_pipeline'),
    url(r'^rejectedarticleoverrides/$',
        rejected_article_overrides.list_overrides,
        name='rejected_article_overrides.list_overrides'),
    url(r'^rejectedarticleoverrides/new/$',
        rejected_article_overrides.new_override,
        name='rejected_article_overrides.new_override'),
    url(r'^rejectedarticleoverrides/delete/$',
        rejected_article_overrides.delete_override,
        name='rejected_article_overrides.delete_override')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
