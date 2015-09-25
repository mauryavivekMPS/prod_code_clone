from django.shortcuts import render
from ivweb.app.models import Publisher_Metadata, Pipeline_Status


def detail(request, pipeline_id):
    status_by_publisher = []

    # get all publishers that support this pipeline
    for publisher in Publisher_Metadata.objects.all():
        if pipeline_id in publisher.supported_pipelines:
            status_items = Pipeline_Status.objects(publisher_id=publisher.publisher_id, pipeline_id=pipeline_id)
            status_by_publisher.append({
                'publisher': publisher,
                'status_items': status_items,
            })

    return render(request, 'pipeline/detail.html', {'pipeline_id': pipeline_id, 'status_by_publisher': status_by_publisher})
