from django.shortcuts import render
from ivweb.app.models import Publisher_Metadata


def detail(request, pipeline_id):
    publishers = []

    # get all publishers that support this pipeline
    for publisher in Publisher_Metadata.objects.all():
        if pipeline_id in publisher.supported_pipelines:
            publishers.append(publisher)

    return render(request, 'pipeline/detail.html', {'pipeline_id': pipeline_id, 'publishers': publishers})

