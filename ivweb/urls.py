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

    # published articles
    url(r'^pipelines/(?P<pipeline_id>[\w]+)/$', 'pipelines.list_pipelines', name='pipelines.list'),

    # published articles
    url(r'^pipelines/(?P<pipeline_id>[\w]+)/upload/$', 'pipelines.upload', name='pipelines.upload'),

) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
