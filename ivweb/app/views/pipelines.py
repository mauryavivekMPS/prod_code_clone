import os
import humanize
import subprocess
import json
import logging
import datetime
import stat
import shutil
import codecs
import uuid
from dateutil.parser import parse
from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.template import loader, RequestContext
from ivetl.common import common
from ivweb.app.models import Publisher_Metadata, Pipeline_Status, Pipeline_Task_Status, Audit_Log, System_Global

log = logging.getLogger(__name__)


def get_recent_runs_for_publisher(pipeline_id, product_id, publisher, only_completed_runs=False, prioritize_most_recent_running=True):

    # get all the runs
    all_runs = Pipeline_Status.objects(publisher_id=publisher.publisher_id, product_id=product_id, pipeline_id=pipeline_id)

    if only_completed_runs:
        all_runs = [run for run in all_runs if run.status == 'completed']

    # sort the runs by date, most recent at top, take only the top 4
    recent_runs = sorted(all_runs, key=lambda r: r.start_time, reverse=True)[:4]

    # now get all the tasks for each run
    tasks_by_run = []
    for run in recent_runs:
        tasks = Pipeline_Task_Status.objects(publisher_id=publisher.publisher_id, product_id=product_id, pipeline_id=pipeline_id, job_id=run.job_id)
        sorted_tasks = sorted(tasks, key=lambda t: t.start_time)

        tasks_by_run.append({
            'run': run,
            'tasks': sorted_tasks,
        })

    # bubble up task info for a summary, with extra info for running or error items
    recent_run = None
    recent_task = None
    if tasks_by_run:

        # take the most recent running task
        if prioritize_most_recent_running:
            for run in tasks_by_run:
                if run['run'].status == 'in-progress':
                    recent_run = run
                    break

        # if no task is running, just get the most recent
        if not recent_run:
            recent_run = tasks_by_run[0]

        if recent_run['tasks']:
            recent_task = recent_run['tasks'][len(recent_run['tasks']) - 1]

    return {
        'publisher': publisher,
        'runs': tasks_by_run,
        'additional_previous_runs': len(all_runs) - len(tasks_by_run),
        'recent_run': recent_run['run'] if recent_run else None,
        'recent_task': recent_task,
        'pending_files': get_pending_files_for_publisher(publisher.publisher_id, product_id, pipeline_id),
        'queued_files': get_queued_files_for_publisher(publisher.publisher_id, product_id, pipeline_id)
    }


@login_required
def list_pipelines(request, product_id, pipeline_id):
    product = common.PRODUCT_BY_ID[product_id]
    pipeline = common.PIPELINE_BY_ID[pipeline_id]

    list_type = request.GET.get('list_type', 'all')

    # get all publishers that support this pipeline
    supported_publishers = []

    for publisher in request.user.get_accessible_publishers():
        if product_id in publisher.supported_products:
            if list_type == 'all' or (list_type == 'demos' and publisher.demo) or (list_type == 'publishers' and not publisher.demo):
                supported_publishers.append(publisher)

    supported_publishers = sorted(supported_publishers, key=lambda p: p.name.lower().lstrip('('))

    recent_runs_by_publisher = []
    for publisher in supported_publishers:
        recent_runs_by_publisher.append(get_recent_runs_for_publisher(pipeline_id, product_id, publisher))

    high_water_mark = ''
    if pipeline['use_high_water_mark']:
        try:
            high_water_mark = System_Global.objects.get(name=pipeline_id + '_high_water').date_value.strftime('%m/%d/%Y')
        except System_Global.DoesNotExist:
            high_water_mark = 'never'

    return render(request, 'pipelines/list.html', {
        'product': product,
        'pipeline': pipeline,
        'runs_by_publisher': recent_runs_by_publisher,
        'publisher_id_list_as_json': json.dumps([p.publisher_id for p in supported_publishers]),
        'opened': False,
        'list_type': list_type,
        'high_water_mark': high_water_mark,
        'from_date': (datetime.datetime.now() - datetime.timedelta(2)).strftime('%m/%d/%Y'),
        'to_date': (datetime.datetime.now() - datetime.timedelta(1)).strftime('%m/%d/%Y'),
    })


@login_required
def include_updated_publisher_runs(request, product_id, pipeline_id):
    product = common.PRODUCT_BY_ID[product_id]
    pipeline = common.PIPELINE_BY_ID[pipeline_id]
    publisher_id = request.GET['publisher_id']
    current_job_id_on_client = request.GET.get('current_job_id')
    current_task_id_on_client = request.GET.get('current_task_id')
    current_task_status_on_client = request.GET.get('current_task_status')
    opened = True if request.GET.get('opened') == '1' and request.user.superuser else False

    publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)
    publisher_runs = get_recent_runs_for_publisher(pipeline_id, product_id, publisher)

    has_section_updates = True

    has_progress_bar_updates = False
    total_record_count = 0
    current_record_count = 0
    percent_complete = 0

    high_water_mark = ''

    # get the current run and task
    if publisher_runs['runs']:
        if current_job_id_on_client and current_task_id_on_client and current_task_status_on_client:
            current_run = publisher_runs['runs'][0]
            current_task = current_run['tasks'][len(current_run['tasks']) - 1]
            if current_run['run'].job_id == current_job_id_on_client and current_task.task_id == current_task_id_on_client and current_task.status == current_task_status_on_client:
                has_section_updates = False
            if current_task.status == 'in-progress':
                has_progress_bar_updates = True
                total_record_count = current_task.total_record_count
                current_record_count = current_task.current_record_count
                percent_complete = current_task.percent_complete()
    else:
        has_section_updates = False

    publisher_details_html = ''
    if has_section_updates:
        template = loader.get_template('pipelines/include/publisher_details.html')
        context = RequestContext(request, {
            'product': product,
            'pipeline': pipeline,
            'publisher_runs': publisher_runs,
            'opened': opened,
        })
        publisher_details_html = template.render(context)

        if current_task.status == 'completed':
            if pipeline['use_high_water_mark']:
                try:
                    high_water_mark = System_Global.objects.get(name=pipeline_id + '_high_water').date_value.strftime('%m/%d/%Y')
                except System_Global.DoesNotExist:
                    pass

    return JsonResponse({
        'has_section_updates': has_section_updates,
        'publisher_details_html': publisher_details_html,
        'has_progress_bar_updates': True,
        'total_record_count': total_record_count,
        'current_record_count': current_record_count,
        'percent_complete': percent_complete,
        'high_water_mark': high_water_mark
    })


def get_or_create_uploaded_file_dir(publisher_id, product_id, pipeline_id):
    pub_dir = os.path.join('/tmp', publisher_id, product_id, pipeline_id)
    os.makedirs(pub_dir, exist_ok=True)
    return pub_dir


def get_or_create_uploaded_file_path(publisher_id, product_id, pipeline_id, name):
    return os.path.join(get_or_create_uploaded_file_dir(publisher_id, product_id, pipeline_id), name)


def get_or_create_demo_file_dir(demo_id, product_id, pipeline_id):
    demo_dir = os.path.join(common.BASE_DEMO_DIR, str(demo_id), product_id, pipeline_id)
    os.makedirs(demo_dir, exist_ok=True)
    return demo_dir


def get_or_create_demo_file_path(demo_id, product_id, pipeline_id, name):
    return os.path.join(get_or_create_demo_file_dir(demo_id, product_id, pipeline_id), name)


class RunForm(forms.Form):
    publisher = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), required=True)
    move_pending_files = forms.BooleanField(widget=forms.HiddenInput, required=False)

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
            pipeline_class = common.get_pipeline_class(pipeline)

            # optionally move files from pending to incoming
            if form.cleaned_data['move_pending_files']:
                move_pending_files(publisher_id, product_id, pipeline_id, pipeline_class)

            # kick the pipeline off (special case for uptime pipeline)
            if pipeline['include_date_range_controls']:
                from_date = parse(request.POST['from_date'])
                to_date = parse(request.POST['to_date'])
                pipeline_class.s(
                    publisher_id_list=publisher_id_list,
                    product_id=product_id,
                    initiating_user_email=request.user.email,
                    from_date=from_date,
                    to_date=to_date,
                ).delay()
            else:
                pipeline_class.s(
                    publisher_id_list=publisher_id_list,
                    product_id=product_id,
                    initiating_user_email=request.user.email
                ).delay()

            Audit_Log.objects.create(
                user_id=request.user.user_id,
                event_time=datetime.datetime.now(),
                action='run-pipeline',
                entity_type='pipeline',
                entity_id=pipeline_id,
            )

            if request.user.staff:
                return HttpResponseRedirect(reverse('pipelines.list', kwargs={'pipeline_id': pipeline_id, 'product_id': product_id}))
            else:
                return HttpResponseRedirect('%s?from=run&publisher=%s&pipeline=%s' % (reverse('home'), publisher_id, pipeline_id))

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


def _get_files_in_dir(dir, with_lines_and_sizes=False, ignore=[]):
    files = [{'file_name': n} for n in os.listdir(dir) if not ignore or ignore and n not in ignore]
    if with_lines_and_sizes:
        for file in files:
            file_path = os.path.join(dir, file['file_name'])
            line_count = 0
            with codecs.open(file_path, encoding='utf-8') as f:
                for i, l in enumerate(f):
                    pass
                line_count = i + 1
            file['line_count'] = line_count
            file['file_size'] = humanize.naturalsize(os.stat(file_path).st_size)
            file['file_id'] = uuid.uuid4()
    return files


def get_pending_files_for_publisher(publisher_id, product_id, pipeline_id, with_lines_and_sizes=False, ignore=[]):
    pub_dir = get_or_create_uploaded_file_dir(publisher_id, product_id, pipeline_id)
    return _get_files_in_dir(pub_dir, with_lines_and_sizes, ignore)


def get_queued_files_for_publisher(publisher_id, product_id, pipeline_id, with_lines_and_sizes=False, ignore=[]):
    pipeline = common.PIPELINE_BY_ID[pipeline_id]
    pipeline_class = common.get_pipeline_class(pipeline)
    incoming_dir = pipeline_class.get_or_create_incoming_dir_for_publisher(common.BASE_INCOMING_DIR, publisher_id, pipeline_id)
    return _get_files_in_dir(incoming_dir, with_lines_and_sizes, ignore)


def get_pending_files_for_demo(demo_id, product_id, pipeline_id, with_lines_and_sizes=False, ignore=[]):
    demo_dir = get_or_create_demo_file_dir(demo_id, product_id, pipeline_id)
    return _get_files_in_dir(demo_dir, with_lines_and_sizes, ignore)


def move_demo_files_to_pending(demo_id, publisher_id, product_id, pipeline_id):
    demo_dir = get_or_create_demo_file_dir(demo_id, product_id, pipeline_id)
    files = get_pending_files_for_demo(demo_id, product_id, pipeline_id)
    pending_dir = get_or_create_uploaded_file_dir(publisher_id, product_id, pipeline_id)
    for file in files:
        source_file_path = os.path.join(demo_dir, file['file_name'])
        destination_file_path = os.path.join(pending_dir, file['file_name'])
        shutil.move(source_file_path, destination_file_path)
        os.chmod(destination_file_path, stat.S_IROTH | stat.S_IRGRP | stat.S_IWGRP | stat.S_IRUSR | stat.S_IWUSR)


def move_pending_files(publisher_id, product_id, pipeline_id, pipeline_class):
    pending_dir = get_or_create_uploaded_file_dir(publisher_id, product_id, pipeline_id)
    files = get_pending_files_for_publisher(publisher_id, product_id, pipeline_id)
    incoming_dir = pipeline_class.get_or_create_incoming_dir_for_publisher(common.BASE_INCOMING_DIR, publisher_id, pipeline_id)
    for file in files:
        source_file_path = os.path.join(pending_dir, file['file_name'])
        destination_file_path = os.path.join(incoming_dir, file['file_name'])
        shutil.move(source_file_path, destination_file_path)
        os.chmod(destination_file_path, stat.S_IROTH | stat.S_IRGRP | stat.S_IWGRP | stat.S_IRUSR | stat.S_IWUSR)


def delete_pending_publisher_file(publisher_id, product_id, pipeline_id, name):
    os.remove(os.path.join(get_or_create_uploaded_file_dir(publisher_id, product_id, pipeline_id), name))


def delete_pending_demo_file(demo_id, product_id, pipeline_id, name):
    os.remove(os.path.join(get_or_create_demo_file_dir(demo_id, product_id, pipeline_id), name))


@login_required
def pending_files(request, product_id, pipeline_id):
    product = common.PRODUCT_BY_ID[product_id]
    pipeline = common.PIPELINE_BY_ID[pipeline_id]
    publisher_id = request.REQUEST['publisher']
    publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)

    return render(request, 'pipelines/pending_files.html', {
        'product': product,
        'pipeline': pipeline,
        'pending_files': get_pending_files_for_publisher(publisher_id, product_id, pipeline_id, with_lines_and_sizes=True),
        'publisher_id': publisher_id,
        'publisher': publisher,
    })


@login_required
def upload_pending_file_inline(request):

    if request.method == 'POST':
        product_id = request.POST['product_id']
        pipeline_id = request.POST['pipeline_id']
        product = common.PRODUCT_BY_ID[product_id]
        pipeline = common.PIPELINE_BY_ID[pipeline_id]
        file_type = request.POST['file_type']

        validation_errors = []
        all_uploaded_files = request.FILES.getlist('files')
        all_processed_files = []

        for uploaded_file in all_uploaded_files:

            publisher_id = None
            demo_id = None

            if file_type == 'publisher':
                publisher_id = request.POST['publisher_id']
                pending_file_path = get_or_create_uploaded_file_path(publisher_id, product_id, pipeline_id, uploaded_file.name)

            elif file_type == 'demo':
                demo_id = request.POST['demo_id']
                pending_file_path = get_or_create_demo_file_path(demo_id, product_id, pipeline_id, uploaded_file.name)

            pending_file = open(pending_file_path, 'wb')
            for chunk in uploaded_file.chunks():
                pending_file.write(chunk)
            pending_file.close()
            uploaded_file_size = humanize.naturalsize(os.stat(pending_file_path).st_size)

            # get the validator class, if any, and run validation
            if pipeline['validator_class']:
                validator_class = common.get_validator_class(pipeline)
                validator = validator_class()

                if file_type == 'publisher':
                    publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)
                    issns = publisher.all_issns
                    crossref_username = publisher.crossref_username
                    crossref_password = publisher.crossref_password
                else:
                    issns = json.loads(request.POST.get('issns', '[]'))
                    crossref_username = request.POST.get('crossref_username', '')
                    crossref_password = request.POST.get('crossref_password', '')

                line_count, raw_errors = validator.validate_files([pending_file_path], issns, crossref_username, crossref_password)
                validation_errors = validator.parse_errors(raw_errors)

            else:
                # just count the lines
                with codecs.open(pending_file_path, encoding='utf-8') as f:
                    for i, l in enumerate(f):
                        pass
                    line_count = i + 1

            if validation_errors:
                os.remove(pending_file_path)  # delete the file

            else:

                # make sure it's world readable, just to be safe
                os.chmod(pending_file_path, stat.S_IROTH | stat.S_IRGRP | stat.S_IWGRP | stat.S_IRUSR | stat.S_IWUSR)

                Audit_Log.objects.create(
                    user_id=request.user.user_id,
                    event_time=datetime.datetime.now(),
                    action='upload-file',
                    entity_type='pipeline-file',
                    entity_id='%s, %s' % (pipeline_id, uploaded_file.name),
                )

            all_processed_files.append({
                'file_name': uploaded_file.name,
                'file_size': uploaded_file_size,
                'line_count': line_count,
                'file_id': uuid.uuid4(),
                'validation_errors': validation_errors
            })

        ui_type = request.POST.get('ui_type', 'more')

        return render(request, 'pipelines/include/multiple_files.html', {
            'product': product,
            'pipeline': pipeline,
            'publisher_id': publisher_id,
            'processed_files': all_processed_files,
            'is_demo': file_type == 'demo',
            'ui_type': ui_type,
            'inline': True,
        })

    return HttpResponse('ok')

@login_required
def delete_pending_file_inline(request):

    if request.method == 'POST':
        file_to_delete = request.POST.get('file_to_delete')

        if file_to_delete:
            product_id = request.POST['product_id']
            pipeline_id = request.POST['pipeline_id']
            file_type = request.POST['file_type']

            if file_type == 'publisher':
                publisher_id = request.POST['publisher_id']
                delete_pending_publisher_file(publisher_id, product_id, pipeline_id, file_to_delete)

            elif file_type == 'demo':
                demo_id = request.POST['demo_id']
                delete_pending_demo_file(demo_id, product_id, pipeline_id, file_to_delete)

    return HttpResponse('ok')
