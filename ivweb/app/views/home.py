import humanize
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.common import common
from ivweb.app.views.pipelines import get_recent_runs_for_publisher


@login_required
def home(request):
    if request.user.superuser:
        return HttpResponseRedirect(reverse('publishers.list'))

    else:
        publisher_stats_list = []
        for publisher in request.user.get_accessible_publishers():

            product_stats_list = []
            for product_id in publisher.supported_products:
                product = common.PRODUCT_BY_ID[product_id]

                pipeline_stats_list = []
                for pipeline in product['pipelines']:
                    recent_runs = get_recent_runs_for_publisher(pipeline['pipeline']['id'], publisher)
                    status = True if recent_runs['recent_run'] else False
                    pipeline_name = pipeline['pipeline']['name'].lower().capitalize()

                    if status:
                        message = '%s updated %s' % (pipeline_name, humanize.naturaltime(recent_runs['recent_run'].updated))
                    else:
                        message = '%s not recently updated' % pipeline_name

                    pipeline_stats_list.append({
                        'pipeline': pipeline['pipeline'],
                        'status': status,
                        'message': message,
                        'recent_run': recent_runs['recent_run'],
                    })

                product_stats_list.append({
                    'product': product,
                    'pipeline_stats_list': pipeline_stats_list,
                })

            publisher_stats_list.append({
                'publisher': publisher,
                'product_stats_list': product_stats_list,
            })

        return render(request, 'user_home.html', {
            'publisher_stats_list': publisher_stats_list
        })
