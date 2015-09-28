from django.shortcuts import render
from ivweb.app.models import Publisher_Metadata, Pipeline_Status, Pipeline_Task_Status


def detail(request, pipeline_id):
    runs_by_publisher = []

    # get all publishers that support this pipeline
    for publisher in Publisher_Metadata.objects.all():
        if pipeline_id in publisher.supported_pipelines:
            tasks_by_run = []

            # get all the runs
            runs = Pipeline_Status.objects(publisher_id=publisher.publisher_id, pipeline_id=pipeline_id)

            # now get all the tasks for each run
            for run in runs:
                tasks = Pipeline_Task_Status.objects(publisher_id=publisher.publisher_id, pipeline_id=pipeline_id, job_id=run.job_id)

                tasks_by_run.append({
                    'run': run,
                    'tasks': tasks,
                })

            runs_by_publisher.append({
                'publisher': publisher,
                'runs': tasks_by_run,
            })

    return render(request, 'pipeline/detail.html', {'pipeline_id': pipeline_id, 'runs_by_publisher': runs_by_publisher})
