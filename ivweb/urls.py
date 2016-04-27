from django.conf import settings
from django.conf.urls import patterns, url
from django.conf.urls.static import static

urlpatterns = patterns(
    'ivweb.app.views',

    # auth
    url(r'^login/$', 'auth.login', name='login'),
    url(r'^logout/$', 'auth.logout', name='logout'),

    # user settings
    url(r'^settings/$', 'auth.settings', name='settings'),

    # audit log
    url(r'^audit/$', 'audit.show', name='audit'),

    # homepage
    url(r'^$', 'home.home', name='home'),
    url(r'^pipelines/$', 'home.all_pipelines', name='all_pipelines'),
    url(r'^growth/$', 'home.growth', name='growth'),
    url(r'^performance/$', 'home.performance', name='performance'),

    # users
    url(r'^users/$', 'users.list_users', name='users.list'),
    url(r'^users/new/$', 'users.edit', name='users.new'),
    url(r'^users/(?P<user_id>[\w\-\.]+)/$', 'users.edit', name='users.edit'),

    # alerts
    url(r'^alerts/$', 'alerts.list_alerts', name='alerts.list'),
    url(r'^alerts/new/$', 'alerts.edit', name='alerts.new'),
    url(r'^alerts/(?P<alert_id>[\w\-\.]+)/$', 'alerts.edit', name='alerts.edit'),

    # notifications
    url(r'^notifications/$', 'notifications.list_notifications', name='notifications.list'),

    # demos
    url(r'^demos/$', 'publishers.list_demos', name='publishers.list_demos'),
    url(r'^demos/new/$', 'publishers.edit_demo', name='publishers.new_demo'),
    url(r'^demos/(?P<demo_id>[\w\-\.]+)/$', 'publishers.edit_demo', name='publishers.edit_demo'),

    # publishers
    url(r'^publishers/$', 'publishers.list_publishers', name='publishers.list'),
    url(r'^publishers/new/$', 'publishers.edit', name='publishers.new'),
    url(r'^publishers/(?P<publisher_id>[\w]+)/$', 'publishers.edit', name='publishers.edit'),
    url(r'^publishers/(?P<publisher_id>[\w]+)/users/$', 'users.list_users', name='publishers.users'),
    url(r'^publishers/(?P<publisher_id>[\w]+)/users/new/$', 'users.edit', name='publishers.users.new'),
    url(r'^publishers/(?P<publisher_id>[\w]+)/users/(?P<user_id>[\w\-\.]+)/$', 'users.edit', name='publishers.users.edit'),

    # pipeline details
    url(r'^pipelines/(?P<product_id>[\w]+)/(?P<pipeline_id>[\w]+)/$', 'pipelines.list_pipelines', name='pipelines.list'),
    url(r'^pipelines/(?P<product_id>[\w]+)/(?P<pipeline_id>[\w]+)/include/updatedpublisherruns/$', 'pipelines.include_updated_publisher_runs', name='pipelines.include_updated_publisher_runs'),

    # upload files for a pipeline or demo
    url(r'^pipelines/(?P<product_id>[\w]+)/(?P<pipeline_id>[\w]+)/pendingfiles/$', 'pipelines.pending_files', name='pipelines.pending_files'),

    # run a pipeline
    url(r'^pipelines/(?P<product_id>[\w]+)/(?P<pipeline_id>[\w]+)/run/$', 'pipelines.run', name='pipelines.run'),

    # tail a task
    url(r'^pipelines/(?P<product_id>[\w]+)/(?P<pipeline_id>[\w]+)/task/$', 'pipelines.tail', name='pipelines.tail'),

    # various tools
    url(r'^validatecrossref/$', 'publishers.validate_crossref', name='publishers.validate_crossref'),
    url(r'^validateissn/$', 'publishers.validate_issn', name='publishers.validate_issn'),
    url(r'^newissn/$', 'publishers.new_issn', name='publishers.new_issn'),
    url(r'^setupreports/$', 'publishers.setup_reports', name='publishers.setup_reports'),
    url(r'^checkreports/$', 'publishers.check_reports', name='publishers.check_reports'),
    url(r'^updatedemostatus/$', 'publishers.update_demo_status', name='publishers.update_demo_status'),
    url(r'^uploadfile/$', 'pipelines.upload_pending_file_inline', name='pipelines.upload_pending_file_inline'),
    url(r'^deletefile/$', 'pipelines.delete_pending_file_inline', name='pipelines.delete_pending_file_inline'),
    url(r'^includealertparams/$', 'alerts.include_alert_params', name='alerts.include_alert_params'),
    url(r'^includealertfilters/$', 'alerts.include_alert_filters', name='alerts.include_alert_filters'),
    url(r'^includenotificationdetails/$', 'notifications.include_notification_details', name='notifications.include_notification_details'),
    url(r'^dismissnotification/$', 'notifications.dismiss_notification', name='notifications.dismiss_notification'),

) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
