import datetime
import humanize
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.common import common
from ivetl.models import PipelineStatus, PipelineTaskStatus
from ivweb.app.views.pipelines import get_recent_runs_for_publisher, get_pending_files_for_publisher


@login_required
def home(request):
    if request.user.superuser:
        return HttpResponseRedirect(reverse('publishers.list'))

    elif request.user.staff:
        return HttpResponseRedirect(reverse('publishers.list_demos'))

    else:
        messages = []
        running_publisher = ''
        running_pipeline = ''
        if 'from' in request.GET and request.GET['from'] == 'run':
            running_publisher = request.GET['publisher']
            running_pipeline = request.GET['pipeline']
            messages.append("Your uploads are being processed and you'll be sent an email upon completion.")

        publisher_stats_list = []
        for publisher in request.user.get_accessible_publishers():

            product_stats_list = []
            for product_id in publisher.supported_products:
                product = common.PRODUCT_BY_ID[product_id]

                pipeline_stats_list = []
                for pipeline in product['pipelines']:
                    recent_runs = get_recent_runs_for_publisher(pipeline['pipeline']['id'], product_id, publisher)

                    file_based_pipeline_currently_running = False

                    # only show running status if it's a file-based pipeline, otherwise green or empty
                    if recent_runs['recent_run']:
                        if pipeline['pipeline'].get('has_file_input') and recent_runs['recent_run'].status == 'in-progress':
                            status = recent_runs['recent_run']
                            file_based_pipeline_currently_running = True
                        else:
                            status = True
                    else:
                        status = False

                    if 'user_facing_display_name' in pipeline['pipeline']:
                        pipeline_name = pipeline['pipeline']['user_facing_display_name']
                    else:
                        pipeline_name = pipeline['pipeline']['name'].lower().capitalize()

                    if file_based_pipeline_currently_running or running_publisher == publisher.publisher_id and running_pipeline == pipeline['pipeline']['id']:
                        message = '%s currently being processed' % pipeline_name
                    else:
                        if status:
                            if pipeline['pipeline'].get('use_colon_instead_of_updated'):
                                message = '%s: %s' % (pipeline_name, humanize.naturaltime(recent_runs['recent_run'].updated))
                            elif pipeline['pipeline'].get('use_uploaded_instead_of_updated'):
                                message = '%s uploaded %s' % (pipeline_name, humanize.naturaltime(recent_runs['recent_run'].updated))
                            else:
                                message = '%s updated %s' % (pipeline_name, humanize.naturaltime(recent_runs['recent_run'].updated))
                        else:
                            message = '%s: never' % pipeline_name

                    pending_files = []
                    if pipeline['pipeline'].get('has_file_input'):
                        pending_files = get_pending_files_for_publisher(publisher.publisher_id, product_id, pipeline['pipeline']['id'], with_lines_and_sizes=False)

                    pipeline_stats_list.append({
                        'pipeline': pipeline['pipeline'],
                        'status': status,
                        'file_based_pipeline_currently_running': file_based_pipeline_currently_running,
                        'message': message,
                        'recent_run': recent_runs['recent_run'],
                        'pending_files': pending_files,
                    })

                product_stats_list.append({
                    'product': product,
                    'pipeline_stats_list': pipeline_stats_list,
                })

            sorted_product_stats_list = sorted(product_stats_list, key=lambda p: p['product']['order'])

            publisher_stats_list.append({
                'publisher': publisher,
                'product_stats_list': sorted_product_stats_list,
            })

        return render(request, 'home.html', {
            'publisher_stats_list': publisher_stats_list,
            'messages': messages,
            'reset_url': reverse('home'),
            'running_publisher': running_publisher,
            'running_pipeline': running_pipeline,
        })


@login_required
def recent_jobs(request):
    if not request.user.superuser:
        return HttpResponseRedirect(reverse('home'))
    else:

        filter_param = request.GET.get('filter', request.COOKIES.get('jobs-list-filter', 'all'))

        viewable_statuses = []
        if filter_param in ('all', 'in-progress'):
            viewable_statuses.append('in-progress')
        if filter_param in ('all', 'completed'):
            viewable_statuses.append('completed')
        if filter_param in ('all', 'error'):
            viewable_statuses.append('error')

        all_publishers = request.user.get_accessible_publishers()

        # publishers ordered by name
        ordered_publishers = sorted(all_publishers, key=lambda p: p.name.lower().lstrip('('))

        # temporary run storage by publisher ID
        runs_by_pub = {p.publisher_id: {'publisher': p, 'runs': []} for p in all_publishers}

        num_recent_days = 14
        earliest_start_time = datetime.datetime.now() - datetime.timedelta(days=num_recent_days)

        # get anything within the past two weeks
        recent_runs = [run for run in PipelineStatus.objects().limit(500) if run.status in viewable_statuses and run.start_time > earliest_start_time]

        # sort the runs by pub
        for run in recent_runs:
            tasks = PipelineTaskStatus.objects(publisher_id=run.publisher_id, product_id=run.product_id, pipeline_id=run.pipeline_id, job_id=run.job_id)
            sorted_tasks = sorted(tasks, key=lambda t: t.start_time)
            runs_by_pub[run.publisher_id]['runs'].append({
                'run': run,
                'tasks': sorted_tasks,
                'product': common.PRODUCT_BY_ID[run.product_id],
                'pipeline': common.PIPELINE_BY_ID[run.pipeline_id],
            })

        ordered_runs = []
        for publisher in ordered_publishers:
            if runs_by_pub[publisher.publisher_id]['runs']:
                ordered_runs.append({
                    'publisher': publisher,
                    'runs': runs_by_pub[publisher.publisher_id]['runs'],
                })

        response = render(request, 'recent_jobs.html', {
            'runs_by_publisher': ordered_runs,
            'filter_param': filter_param,
            'num_recent_days': num_recent_days,
        })

        response.set_cookie('jobs-list-filter', value=filter_param, max_age=30 * 24 * 60 * 60)

        return response


@login_required
def growth(request):
    if not request.user.superuser:
        return HttpResponseRedirect(reverse('home'))
    else:
        return render(request, 'growth.html', {})


@login_required
def performance(request):
    if not request.user.superuser:
        return HttpResponseRedirect(reverse('home'))
    else:
        return render(request, 'performance.html', {})
