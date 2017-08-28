import codecs
import datetime
import json
import logging
import os
import shutil
import stat
import subprocess
import time
import uuid
import humanize
from dateutil.parser import parse
from django import forms
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.template import loader, RequestContext
from ivetl.common import common
from ivetl import utils
from ivetl import tableau_alerts
from ivetl.pipelines.pipeline import Pipeline
from ivweb.app.models import PublisherMetadata, PipelineStatus, PipelineTaskStatus, SystemGlobal, PublisherJournal
from ivweb.app.views import utils as view_utils

log = logging.getLogger(__name__)


def get_recent_runs_for_publisher(pipeline_id, product_id, publisher, only_completed_runs=False, prioritize_most_recent_running=True):

    # get all the runs
    all_runs = PipelineStatus.objects(publisher_id=publisher.publisher_id, product_id=product_id, pipeline_id=pipeline_id)

    if only_completed_runs:
        all_runs = [run for run in all_runs if run.status == 'completed']

    # sort the runs by date, most recent at top, take only the top 4
    recent_runs = sorted(all_runs, key=lambda r: r.start_time or datetime.datetime.min, reverse=True)[:4]

    # now get all the tasks for each run
    tasks_by_run = []
    for run in recent_runs:
        tasks = PipelineTaskStatus.objects(publisher_id=publisher.publisher_id, product_id=product_id, pipeline_id=pipeline_id, job_id=run.job_id)
        sorted_tasks = sorted(tasks, key=lambda t: t.start_time or datetime.datetime.min)

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
            num_tasks = len(recent_run['tasks'])
            if num_tasks > 0:
                recent_task = recent_run['tasks'][num_tasks - 1]

    return {
        'publisher': publisher,
        'runs': tasks_by_run,
        'additional_previous_runs': len(all_runs) - len(tasks_by_run),
        'recent_run': recent_run['run'] if recent_run else None,
        'recent_task': recent_task,
        'pending_files': get_pending_files_for_publisher(publisher.publisher_id, product_id, pipeline_id),
        'queued_files': get_queued_files_for_publisher(publisher.publisher_id, product_id, pipeline_id)
    }


def _get_filtered_publishers(filter_param, user, product_id, pipeline_id):
    pipeline = common.PIPELINE_BY_ID[pipeline_id]

    # get all publishers that support this pipeline
    supported_publishers = []

    for publisher in user.get_accessible_publishers():
        if product_id in publisher.supported_products:

            single_publisher_pipeline = pipeline.get('single_publisher_pipeline')

            # ignore highwire pub if it's not a single pub pipeline
            if not single_publisher_pipeline and publisher.publisher_id == common.HW_PUBLISHER_ID:
                continue

            if single_publisher_pipeline:
                if publisher.publisher_id == pipeline['single_publisher_id']:
                    supported_publishers.append(publisher)

            elif filter_param == 'all' or (filter_param == 'demos' and publisher.demo) or (filter_param == 'publishers' and not publisher.demo):
                # special support for other pipeline-level filters
                if pipeline.get('filter_for_benchpress_support'):
                    benchpress_journals = PublisherJournal.objects.filter(
                        publisher_id=publisher.publisher_id,
                        product_id='published_articles',
                        use_benchpress=True
                    )
                    if benchpress_journals.count():
                        supported_publishers.append(publisher)
                else:
                    supported_publishers.append(publisher)

    return supported_publishers


@login_required
def list_pipelines(request, product_id, pipeline_id):
    product = common.PRODUCT_BY_ID[product_id]
    pipeline = common.PIPELINE_BY_ID[pipeline_id]

    filter_param = request.GET.get('filter', request.COOKIES.get('pipeline-list-filter', 'all'))
    supported_publishers = _get_filtered_publishers(filter_param, request.user, product_id, pipeline_id)

    recent_runs_by_publisher = []
    for publisher in supported_publishers:
        recent_runs_by_publisher.append(get_recent_runs_for_publisher(pipeline_id, product_id, publisher))

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('pipeline-list-sort', 'publisher'))

    def _get_sort_value(item, sort_key):
        if sort_key == 'start_time':
            r = item.get('recent_run')
            if r:
                return r.start_time
            else:
                return datetime.datetime.min
        elif sort_key == 'end_time':
            r = item.get('recent_run')
            if r:
                return r.end_time
            else:
                return datetime.datetime.max
        elif sort_key == 'publisher':
            return item['publisher'].display_name.lower()
        elif sort_key == 'status':
            r = item.get('recent_run')
            if r:
                if r.status == 'started':
                    return 1
                elif r.status == 'in-progress':
                    return 2
                elif r.status == 'completed':
                    return 3
                elif r.status == 'error':
                    return 4
                else:
                    return 5
            else:
                return 6
        else:
            return item['sort_key'].lower()

    sorted_recent_runs_by_publisher = sorted(recent_runs_by_publisher, key=lambda r: _get_sort_value(r, sort_key), reverse=sort_descending)

    from_date_label = ''
    to_date_label = ''

    high_water_mark = None
    high_water_mark_label = ''
    if pipeline.get('use_high_water_mark'):
        try:
            high_water_mark = SystemGlobal.objects.get(name=pipeline_id + '_high_water').date_value
            high_water_mark_label = high_water_mark.strftime('%m/%d/%Y')
        except SystemGlobal.DoesNotExist:
            high_water_mark_label = 'never'

    if pipeline.get('include_date_range_controls'):
        yesterday = datetime.datetime.now() - datetime.timedelta(1)
        if high_water_mark:
            from_date = high_water_mark + datetime.timedelta(1)
        else:
            from_date = yesterday

        to_date = yesterday

        from_date_label = from_date.strftime('%m/%d/%Y')
        to_date_label = to_date.strftime('%m/%d/%Y')

    if tableau_alerts.ALERT_TEMPLATES_BY_SOURCE_PIPELINE.get((product_id, pipeline_id)):
        has_alerts = True
    else:
        has_alerts = False

    response = render(request, 'pipelines/list.html', {
        'product': product,
        'pipeline': pipeline,
        'runs_by_publisher': sorted_recent_runs_by_publisher,
        'publisher_id_list_as_json': json.dumps([p.publisher_id for p in supported_publishers]),
        'opened': False,
        'list_type': filter_param,
        'high_water_mark': high_water_mark_label,
        'from_date': from_date_label,
        'to_date': to_date_label,
        'sort_key': sort_key,
        'sort_descending': sort_descending,
        'filter_param': filter_param,
        'has_alerts': has_alerts,
    })

    response.set_cookie('pipeline-list-sort', value=sort_param, max_age=30*24*60*60)
    response.set_cookie('pipeline-list-filter', value=filter_param, max_age=30*24*60*60)

    return response


@login_required
def include_updated_publisher_runs(request, product_id, pipeline_id):
    product = common.PRODUCT_BY_ID[product_id]
    pipeline = common.PIPELINE_BY_ID[pipeline_id]
    publisher_id = request.GET['publisher_id']
    current_job_id_on_client = request.GET.get('current_job_id')
    current_task_id_on_client = request.GET.get('current_task_id')
    current_task_status_on_client = request.GET.get('current_task_status')
    opened = True if request.GET.get('opened') == '1' and request.user.superuser else False

    publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)
    publisher_runs = get_recent_runs_for_publisher(pipeline_id, product_id, publisher)

    has_section_updates = True

    has_progress_bar_updates = False
    total_record_count = 0
    current_record_count = 0
    percent_complete = 0

    high_water_mark = ''

    # get the current run and task
    current_task = None
    if publisher_runs['runs']:
        if current_job_id_on_client and current_task_id_on_client and current_task_status_on_client:
            current_run = publisher_runs['runs'][0]

            num_tasks = len(current_run['tasks'])
            if num_tasks > 0:
                current_task = current_run['tasks'][num_tasks - 1]
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

        if current_task and current_task.status == 'completed' and pipeline.get('use_high_water_mark'):
            try:
                high_water_mark = SystemGlobal.objects.get(name=pipeline_id + '_high_water').date_value.strftime('%m/%d/%Y')
            except SystemGlobal.DoesNotExist:
                pass

    return JsonResponse({
        'has_section_updates': has_section_updates,
        'publisher_details_html': publisher_details_html,
        'has_progress_bar_updates': has_progress_bar_updates,
        'total_record_count': total_record_count,
        'current_record_count': current_record_count,
        'percent_complete': percent_complete,
        'high_water_mark': high_water_mark
    })


def get_or_create_uploaded_file_dir(publisher_id, product_id, pipeline_id):
    pub_dir = os.path.join(common.TMP_DIR, publisher_id, product_id, pipeline_id)
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
    publisher = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), required=False)
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
                publisher_filter = request.POST.get('publisher_filter', 'all')
                supported_publishers = _get_filtered_publishers(publisher_filter, request.user, product_id, pipeline_id)
                publisher_id_list = [p.publisher_id for p in supported_publishers]

            # get the pipeline class
            pipeline_class = common.get_pipeline_class(pipeline)

            # optionally move files from pending to incoming
            if form.cleaned_data['move_pending_files']:
                move_pending_files(publisher_id, product_id, pipeline_id, pipeline_class)

            # look for a job_id, if found restart the job
            job_id = request.POST.get('restart_job_id')

            if request.POST.get('send_alerts'):
                send_alerts = True
            else:
                send_alerts = False

            # kick the pipeline off (special case for date range pipelines unless restart)
            if pipeline.get('include_date_range_controls') and not job_id:
                from_date = parse(request.POST['from_date'])
                to_date = parse(request.POST['to_date'])
                pipeline_class.s(
                    publisher_id_list=publisher_id_list,
                    product_id=product_id,
                    initiating_user_email=request.user.email,
                    from_date=from_date,
                    to_date=to_date,
                    send_alerts=send_alerts,
                ).delay()
            else:
                pipeline_class.s(
                    publisher_id_list=publisher_id_list,
                    product_id=product_id,
                    initiating_user_email=request.user.email,
                    job_id=job_id,
                    send_alerts=send_alerts,
                ).delay()

            utils.add_audit_log(
                user_id=request.user.user_id,
                publisher_id=publisher_id if publisher_id else '',
                action='run-pipeline',
                description='Run %s pipeline' % pipeline_id,
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
    publisher_id = request.GET['publisher_id']
    job_id = request.GET['job_id']
    task_id = request.GET['task_id']
    log_file = os.path.join(common.BASE_WORK_DIR, job_id[:8], publisher_id, pipeline_id, job_id, task_id, '%s.log' % task_id)

    # we do a little dance here to kick EFS in the butt and work around the latency
    max_attempts = 5
    wait_time = 2
    attempt = 0
    content = ''
    while attempt < max_attempts:
        attempt += 1
        if os.path.isfile(log_file):
            content = subprocess.check_output('tail -n 300 %s' % log_file, shell=True).decode('utf-8')
            if content:
                break
        time.sleep(wait_time)

    # strip up to a previously loaded line if provided
    if 'last_line' in request.GET:
        last_line = request.GET['last_line']
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


@login_required
def job_action(request, product_id, pipeline_id):
    publisher_id = request.POST['publisher_id']
    job_id = request.POST['job_id']
    action = request.POST['action']

    if action == 'mark-job-as-stopped':
        try:
            now = datetime.datetime.now()

            # kill the overall status
            p = PipelineStatus.objects.get(
                publisher_id=publisher_id,
                product_id=product_id,
                pipeline_id=pipeline_id,
                job_id=job_id
            )
            if p.status in ('started', 'in-progress'):
                p.update(
                    status='error',
                    end_time=now,
                    updated=now,
                    error_details='Marked as stopped'
                )

            # kill the task status
            t = PipelineTaskStatus.objects.get(
                publisher_id=publisher_id,
                product_id=product_id,
                pipeline_id=pipeline_id,
                job_id=job_id,
                task_id=p.current_task
            )
            if t.status in ('started', 'in-progress'):
                t.update(
                    status='error',
                    end_time=now,
                    updated=now,
                    error_details='Marked as stopped'
                )
        except (PipelineStatus.DoesNotExist, PipelineTaskStatus.DoesNotExist):
            pass

    elif action == 'stop-at-next-task':
        try:
            p = PipelineStatus.objects.get(
                publisher_id=publisher_id,
                product_id=product_id,
                pipeline_id=pipeline_id,
                job_id=job_id
            )
            if p.status in ('started', 'in-progress'):
                p.update(
                    stop_instruction='stop-asap',
                )
        except PipelineStatus.DoesNotExist:
            pass

    elif action == 'restart-from-first-task':
        Pipeline.restart_job(publisher_id, product_id, pipeline_id, job_id, start_from_stopped_task=False)

    elif action == 'restart-from-stopped-task':
        Pipeline.restart_job(publisher_id, product_id, pipeline_id, job_id, start_from_stopped_task=True)

    return HttpResponse('ok')


def get_pending_files_for_publisher(publisher_id, product_id, pipeline_id, with_lines_and_sizes=False, ignore=[]):
    pub_dir = get_or_create_uploaded_file_dir(publisher_id, product_id, pipeline_id)
    return utils.list_dir(pub_dir, with_lines_and_sizes, ignore)


def get_queued_files_for_publisher(publisher_id, product_id, pipeline_id, with_lines_and_sizes=False, ignore=[]):
    pipeline = common.PIPELINE_BY_ID[pipeline_id]
    pipeline_class = common.get_pipeline_class(pipeline)
    incoming_dir = pipeline_class.get_or_create_incoming_dir_for_publisher(common.BASE_INCOMING_DIR, publisher_id, pipeline_id)
    return utils.list_dir(incoming_dir, with_lines_and_sizes, ignore)


def get_pending_files_for_demo(demo_id, product_id, pipeline_id, with_lines_and_sizes=False, ignore=[]):
    demo_dir = get_or_create_demo_file_dir(demo_id, product_id, pipeline_id)
    return utils.list_dir(demo_dir, with_lines_and_sizes, ignore)


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
    publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)

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

        publisher_id = None
        demo_id = None

        for uploaded_file in all_uploaded_files:

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
            if pipeline.get('validator_class'):
                validator_class = common.get_validator_class(pipeline)
                validator = validator_class()

                if file_type == 'publisher':
                    publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)
                    issns = publisher.all_issns
                    crossref_username = publisher.crossref_username
                    crossref_password = publisher.crossref_password
                else:
                    issns = json.loads(request.POST.get('issns', '[]'))
                    crossref_username = request.POST.get('crossref_username', '')
                    crossref_password = request.POST.get('crossref_password', '')

                line_count, raw_errors = validator.validate_files(
                    [pending_file_path],
                    issns=issns,
                    publisher_id=publisher_id,
                    crossref_username=crossref_username,
                    crossref_password=crossref_password
                )
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

                utils.add_audit_log(
                    user_id=request.user.user_id,
                    publisher_id=publisher_id,
                    action='upload-file',
                    description='Uploaded %s file: %s' % (pipeline_id, uploaded_file),
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
