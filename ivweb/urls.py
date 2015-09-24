from django.conf import settings
from django.conf.urls import patterns, url
from django.conf.urls.static import static

urlpatterns = patterns(
    'ivweb.app.views',

    # homepage
    url(r'^$', 'home.home', name='home'),

    # published articles
    url(r'^pipelines/(?P<pipeline_id>[\w]+)/$', 'pipeline.detail', name='pipeline.detail'),

) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
