import os
import re
import shutil
import tempfile
import importlib
import humanize
import subprocess
import json
import logging
import datetime
from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from ivetl.common import common
from ivweb.app.models import Publisher_Metadata, Pipeline_Status, Pipeline_Task_Status, Audit_Log

log = logging.getLogger(__name__)


def get_recent_runs_for_publisher(pipeline_id, publisher):
    # get all the runs
    all_runs = Pipeline_Status.objects(publisher_id=publisher.publisher_id, pipeline_id=pipeline_id)

    # sort the runs by date, most recent at top, take only the top 4
    recent_runs = sorted(all_runs, key=lambda r: r.start_time, reverse=True)[:4]

    # now get all the tasks for each run
    tasks_by_run = []
    for run in recent_runs:
        tasks = Pipeline_Task_Status.objects(publisher_id=publisher.publisher_id, pipeline_id=pipeline_id, job_id=run.job_id)
        sorted_tasks = sorted(tasks, key=lambda t: t.start_time)

        tasks_by_run.append({
            'run': run,
            'tasks': sorted_tasks,
        })

    # bubble up task info for most recent run, with extra info for running or error items
    recent_run = None
    recent_task = None
    if tasks_by_run:
        recent_run = tasks_by_run[0]
        if recent_run['tasks']:
            recent_task = recent_run['tasks'][len(recent_run['tasks']) - 1]

    return {
        'publisher': publisher,
        'runs': tasks_by_run,
        'additional_previous_runs': len(all_runs) - len(tasks_by_run),
        'recent_run': recent_run['run'] if recent_run else None,
        'recent_task': recent_task,
    }


@login_required
def list_pipelines(request, product_id, pipeline_id):
    product = common.PRODUCT_BY_ID[product_id]
    pipeline = common.PIPELINE_BY_ID[pipeline_id]

    # get all publishers that support this pipeline
    supported_publishers = []
    if not product['cohort']:  # leave cohort products empty for now
        for publisher in request.user.get_accessible_publishers():
            if product_id in publisher.supported_products:
                supported_publishers.append(publisher)

    recent_runs_by_publisher = []
    for publisher in supported_publishers:
        recent_runs_by_publisher.append(get_recent_runs_for_publisher(pipeline_id, publisher))

    return render(request, 'pipelines/list.html', {
        'product': product,
        'pipeline': pipeline,
        'runs_by_publisher': recent_runs_by_publisher,
        'publisher_id_list_as_json': json.dumps([p.publisher_id for p in supported_publishers]),
        'opened': False,
    })


@login_required
def include_updated_publisher_runs(request, product_id, pipeline_id):
    product = common.PRODUCT_BY_ID[product_id]
    publisher_id = request.GET['publisher_id']
    current_job_id_on_client = request.GET.get('current_job_id')
    current_task_id_on_client = request.GET.get('current_task_id')
    current_task_status_on_client = request.GET.get('current_task_status')
    opened = True if request.GET.get('opened') == '1' else False

    publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)
    publisher_runs = get_recent_runs_for_publisher(pipeline_id, publisher)

    has_updates = True

    # get the current run and task
    if publisher_runs['runs']:
        if current_job_id_on_client and current_task_id_on_client and current_task_status_on_client:
            current_run = publisher_runs['runs'][0]
            current_task = current_run['tasks'][len(current_run['tasks']) - 1]
            if current_run['run'].job_id == current_job_id_on_client and current_task.task_id == current_task_id_on_client and current_task.status == current_task_status_on_client:
                # there are no updates, bail
                has_updates = False
    else:
        has_updates = False

    if not has_updates:
        return HttpResponse('No updates')  # TODO: this should probably be done with status code

    return render(request, 'pipelines/include/publisher_details.html', {
        'publisher_runs': publisher_runs,
        'opened': opened,
    })


class UploadForm(forms.Form):
    publisher = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}))
    file = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control'}))

    def __init__(self, user, *args, publisher=None, **kwargs):
        super(UploadForm, self).__init__(*args, **kwargs)
        if publisher:
            all_choices = [(publisher.publisher_id, publisher.name)]
        else:
            all_choices = list(user.get_accessible_publishers().values_list('publisher_id', 'name'))

        self.fields['publisher'].choices = [['', 'Select a publisher']] + all_choices


@login_required
def upload(request, product_id, pipeline_id):
    product = common.PRODUCT_BY_ID[product_id]
    pipeline = common.PIPELINE_BY_ID[pipeline_id]
    validation_errors = []
    publisher = None

    if request.method == 'POST':
        form = UploadForm(request.user, request.POST, request.FILES)
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
                    'product': product,
                    'pipeline': pipeline,
                    'publisher_id': publisher_id,
                    'file_name': uploaded_file_name,
                    'file_size': uploaded_file_size,
                    'line_count': line_count,
                    'validation_errors': validation_errors,
                })

            else:

                Audit_Log.objects.create(
                    user_id=request.user.user_id,
                    event_time=datetime.datetime.now(),
                    action='upload-file',
                    entity_type='pipeline-file',
                    entity_id='%s, %s' % (pipeline_id, uploaded_file_name),
                )

                return render(request, 'pipelines/upload_success.html', {
                    'product': product,
                    'publisher_id': publisher_id,
                    'file_name': uploaded_file_name,
                    'file_size': uploaded_file_size,
                    'line_count': line_count,
                })

    else:
        publisher_id = request.GET.get('publisher')
        if publisher_id:
            publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)

        form = UploadForm(request.user, publisher=publisher)

    return render(request, 'pipelines/upload.html', {
        'product': product,
        'pipeline': pipeline,
        'form': form,
        'validation_errors': validation_errors,
        'publisher': publisher,
    })


class RunForm(forms.Form):
    publisher = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), required=False)

    def __init__(self, user, *args, **kwargs):
        super(RunForm, self).__init__(*args, **kwargs)
        all_choices = list(user.get_accessible_publishers().values_list('publisher_id', 'name'))
        self.fields['publisher'].choices = [['', 'Select a publisher']] + all_choices


@login_required
def run(request, product_id, pipeline_id):
    product = common.PRODUCT_BY_ID[product_id]
    pipeline = common.PIPELINE_BY_ID[pipeline_id]

    if request.method == 'POST':
        form = RunForm(request.user, request.POST)
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

            Audit_Log.objects.create(
                user_id=request.user.user_id,
                event_time=datetime.datetime.now(),
                action='run-pipeline',
                entity_type='pipeline',
                entity_id=pipeline_id,
            )

            return HttpResponseRedirect(reverse('pipelines.list', kwargs={'pipeline_id': pipeline_id}))

    else:
        form = RunForm(request.user)

    return render(request, 'pipelines/run.html', {
        'product': product,
        'pipeline': pipeline,
        'form': form
    })


@login_required
def tail(request, product_id, pipeline_id):
    product = common.PRODUCT_BY_ID[product_id]
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
        'product': product,
        'pipeline': pipeline,
        'content': content,
    })
