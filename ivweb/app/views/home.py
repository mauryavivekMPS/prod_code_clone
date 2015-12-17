import humanize
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.common import common
from ivweb.app.views.pipelines import get_recent_runs_for_publisher, get_pending_files_for_publisher


@login_required
def home(request):
    if request.user.superuser:
        return HttpResponseRedirect(reverse('dashboard'))

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
                        if pipeline['pipeline']['has_file_input'] and recent_runs['recent_run'].status == 'in-progress':
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
                            message = '%s updated %s' % (pipeline_name, humanize.naturaltime(recent_runs['recent_run'].updated))
                        else:
                            message = '%s not recently updated' % pipeline_name

                    pending_files = []
                    if pipeline['pipeline']['has_file_input']:
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
def dashboard(request):
    if not request.user.superuser:
        return HttpResponseRedirect(reverse('home'))

    else:

        return render(request, 'dashboard.html', {
        })
