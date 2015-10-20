from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ivetl.models import Publisher_Metadata
from ivetl.common import common


@login_required
def home(request):
    if request.user.staff:
        if request.user.superuser:
            publishers = request.user.get_accessible_publishers()
        else:
            publishers = Publisher_Metadata.objects.all()

        return render(request, 'staff_home.html', {
            'publishers': publishers
        })

    else:
        publisher_stats = []
        for publisher in request.user.get_accessible_publishers():

            pipeline_stats = []
            for pipeline in publisher.supported_pipelines:
                pipeline_stats.append({
                    'pipeline': common.PIPELINE_BY_ID[pipeline],
                })

            publisher_stats.append({
                'publisher': publisher,
                'pipeline_stats': pipeline_stats,
            })

        return render(request, 'user_home.html', {
            'publisher_stats': publisher_stats
        })
