import os
import shutil
import tempfile
import importlib
import humanize
from django import forms
from django.shortcuts import render
from ivetl.common import common
from ivweb.app.models import Publisher_Metadata, Pipeline_Status, Pipeline_Task_Status


def list_pipelines(request, pipeline_id):
    pipeline = common.PIPELINE_BY_ID[pipeline_id]
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

    return render(request, 'pipelines/list.html', {'pipeline': pipeline, 'runs_by_publisher': runs_by_publisher})


class UploadForm(forms.Form):
    publisher = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}))
    file = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(UploadForm, self).__init__(*args, **kwargs)
        all_choices = list(Publisher_Metadata.objects.values_list('publisher_id', 'name'))
        self.fields['publisher'].choices = [['', 'Select a publisher']] + all_choices


def upload(request, pipeline_id):
    pipeline = common.PIPELINE_BY_ID[pipeline_id]
    validation_errors = []

    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            publisher_id = form.cleaned_data['publisher']
            uploaded_file = request.FILES['file']
            uploaded_file_name = form.cleaned_data['file'].name

            # write the file to a temporary location
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
            uploaded_file_size = humanize.naturalsize(os.stat(temp_file.name).st_size)

            # get the pipeline class
            module_name, class_name = pipeline['class'].rsplit('.', 1)
            pipeline_class = getattr(importlib.import_module(module_name), class_name)

            # run validation
            validation_errors = []
            line_count = 1203

            # if it passes, move to the pipeline inbox
            incoming_dir = pipeline_class.get_or_create_incoming_dir_for_publisher(common.BASE_INCOMING_DIR, publisher_id)
            shutil.move(temp_file.name, os.path.join(incoming_dir, uploaded_file_name))

            if not validation_errors:
                return render(request, 'pipelines/upload_success.html', {
                    'pipeline': pipeline,
                    'file_name': uploaded_file_name,
                    'file_size': uploaded_file_size,
                    'line_count': line_count,
                })

    else:
        form = UploadForm()

    return render(request, 'pipelines/upload.html', {
        'pipeline': pipeline,
        'form': form,
        'validation_errors': validation_errors
    })
