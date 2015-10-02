from django.conf import settings
from django.conf.urls import patterns, url
from django.conf.urls.static import static

urlpatterns = patterns(
    'ivweb.app.views',

    # homepage
    url(r'^$', 'home.home', name='home'),

    # users
    url(r'^users/$', 'users.list_users', name='users.list'),

    # publishers
    url(r'^publishers/$', 'publishers.list_publishers', name='publishers.list'),

    # pipeline details
    url(r'^pipelines/(?P<pipeline_id>[\w]+)/$', 'pipelines.list_pipelines', name='pipelines.list'),

    # upload files for a pipeline
    url(r'^pipelines/(?P<pipeline_id>[\w]+)/upload/$', 'pipelines.upload', name='pipelines.upload'),

    # run a pipeline
    url(r'^pipelines/(?P<pipeline_id>[\w]+)/run/$', 'pipelines.run', name='pipelines.run'),

    # tail a task
    url(r'^pipelines/(?P<pipeline_id>[\w]+)/task/$', 'pipelines.tail', name='pipelines.tail'),

) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
