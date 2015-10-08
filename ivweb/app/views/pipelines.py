import os
import re
import shutil
import tempfile
import importlib
import humanize
import subprocess
from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render, HttpResponseRedirect
from ivetl.common import common
from ivweb.app.models import Publisher_Metadata, Pipeline_Status, Pipeline_Task_Status


def list_pipelines(request, pipeline_id):
    pipeline = common.PIPELINE_BY_ID[pipeline_id]
    all_runs_by_publisher = []

    # get all publishers that support this pipeline
    for publisher in Publisher_Metadata.objects.all():
        if pipeline_id in publisher.supported_pipelines:

            # get all the runs
            all_runs = Pipeline_Status.objects(publisher_id=publisher.publisher_id, pipeline_id=pipeline_id)

            all_runs_by_publisher.append({
                'publisher': publisher,
                'all_runs': all_runs,
            })

    recent_runs_by_publisher = []
    for publisher in all_runs_by_publisher:
        tasks_by_run = []

        # sort the runs by date, most recent at top, take only the top 4
        recent_runs = sorted(publisher['all_runs'], key=lambda r: r.start_time, reverse=True)[:4]

        # now get all the tasks for each run
        for run in recent_runs:
            tasks = Pipeline_Task_Status.objects(publisher_id=publisher['publisher'].publisher_id, pipeline_id=pipeline_id, job_id=run.job_id)

            tasks_by_run.append({
                'run': run,
                'tasks': tasks,
            })

        recent_runs_by_publisher.append({
            'publisher': publisher['publisher'],
            'runs': tasks_by_run,
            'additional_previous_runs': len(publisher['all_runs']) - len(tasks_by_run)
        })

    # bubble up task info for most recent run, with extra info for running or error items
    for publisher in recent_runs_by_publisher:
        if publisher['runs']:
            recent_run = publisher['runs'][0]
            if recent_run['run'].status == 'error' and recent_run['tasks']:
                publisher['error_task_id'] = recent_run['tasks'][len(recent_run['tasks']) - 1].task_id
            publisher['recent_run'] = recent_run['run']

    return render(request, 'pipelines/list.html', {'pipeline': pipeline, 'runs_by_publisher': recent_runs_by_publisher})


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
            temp_file.close()

            # get the pipeline class
            pipeline_module_name, class_name = pipeline['class'].rsplit('.', 1)
            pipeline_class = getattr(importlib.import_module(pipeline_module_name), class_name)

            # get the validator class, if any, and run validation
            if pipeline['validator_class']:
                validator_module_name, class_name = pipeline['validator_class'].rsplit('.', 1)
                validator_class = getattr(importlib.import_module(validator_module_name), class_name)
                validator = validator_class()
                line_count, raw_errors = validator.validate_files([temp_file.name], publisher_id)

                # parse errors into line number and message
                validation_errors = []
                error_regex = re.compile('^\w+ : (\d+) - (.*)$')
                # %s : %s - Incorrect
                for error in raw_errors:
                    m = error_regex.match(error)
                    if m:
                        line_number, message = m.groups()
                        # validation_errors.append({'line_number': line_number, 'message': message})
                        validation_errors.append('%s. %s\n' % (line_number, message))

            else:
                validation_errors = []

                # just count the lines
                with open(temp_file.name) as f:
                    for i, l in enumerate(f):
                        pass
                    line_count = i + 1

            # if it passes, move to the pipeline inbox
            incoming_dir = pipeline_class.get_or_create_incoming_dir_for_publisher(common.BASE_INCOMING_DIR, publisher_id)
            shutil.move(temp_file.name, os.path.join(incoming_dir, uploaded_file_name))

            if validation_errors:
                return render(request, 'pipelines/upload_error.html', {
                    'pipeline': pipeline,
                    'publisher_id': publisher_id,
                    'file_name': uploaded_file_name,
                    'file_size': uploaded_file_size,
                    'line_count': line_count,
                    'validation_errors': validation_errors,
                })

            else:
                return render(request, 'pipelines/upload_success.html', {
                    'pipeline': pipeline,
                    'publisher_id': publisher_id,
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


class RunForm(forms.Form):
    publisher = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), required=False)

    def __init__(self, *args, **kwargs):
        super(RunForm, self).__init__(*args, **kwargs)
        all_choices = list(Publisher_Metadata.objects.values_list('publisher_id', 'name'))
        self.fields['publisher'].choices = [['', 'Select a publisher']] + all_choices


def run(request, pipeline_id):
    pipeline = common.PIPELINE_BY_ID[pipeline_id]

    if request.method == 'POST':
        form = RunForm(request.POST)
        if form.is_valid():
            publisher_id = form.cleaned_data['publisher']
            if publisher_id:
                publisher_id_list = [publisher_id]
            else:
                publisher_id_list = []

            # get the pipeline class
            module_name, class_name = pipeline['class'].rsplit('.', 1)
            pipeline_class = getattr(importlib.import_module(module_name), class_name)

            # kick the pipeline off
            pipeline_class.s(publisher_id_list=publisher_id_list).delay()

            return HttpResponseRedirect(reverse('pipelines.list', kwargs={'pipeline_id': pipeline_id}))

    else:
        form = RunForm()

    return render(request, 'pipelines/run.html', {
        'pipeline': pipeline,
        'form': form
    })


def tail(request, pipeline_id):
    pipeline = common.PIPELINE_BY_ID[pipeline_id]
    publisher_id = request.REQUEST['publisher_id']
    job_id = request.REQUEST['job_id']
    task_id = request.REQUEST['task_id']
    log_file = os.path.join(common.BASE_WORK_DIR, job_id[:8], publisher_id, pipeline_id, job_id, task_id, '%s.log' % task_id)
    content = subprocess.check_output('tail -n 20 %s' % log_file, shell=True).decode('utf-8')

    # strip up to a previously loaded line if provided
    if 'last_line' in request.REQUEST:
        last_line = request.REQUEST['last_line']
        if last_line and last_line in content:
            content = content[content.index(last_line) + len(last_line):]

    # get rid of leading and trailing whitespace, and add just a single trailing newline
    content = content.strip()
    if content:
        content += '\n'  # just want a single newline

    return render(request, 'pipelines/include/tail.html', {
        'pipeline': pipeline,
        'content': content,
    })
