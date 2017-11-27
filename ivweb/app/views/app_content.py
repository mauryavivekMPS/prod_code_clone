import logging
from operator import attrgetter
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ivetl.models import ContentBlock

log = logging.getLogger(__name__)


@login_required
def list_blocks(request):
    all_blocks = ContentBlock.objects.all()
    sorted_blocks = sorted(all_blocks, key=attrgetter('block_id'))
    return render(request, 'app_content/list.html', {
        'blocks': sorted_blocks,
    })


@login_required
def edit_block(request, block_id):

    return render(request, 'app_content/edit.html', {
    })
