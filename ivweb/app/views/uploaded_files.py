import logging
from operator import attrgetter
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from ivetl.models import UploadedFile, User

log = logging.getLogger(__name__)


@login_required
def list_files(request):
    files = list(UploadedFile.objects.all().fetch_size(1000).limit(100000))

    # add user display names to each entry
    user_id_to_display_name = {str(u.user_id): u.display_name for u in User.objects.all()}
    for file in files:
        if file and file.user_id:
            setattr(file, 'user_display_name', user_id_to_display_name[str(file.user_id)])

    sorted_files = sorted(files, key=attrgetter('processed_time'), reverse=True)

    return render(request, 'uploaded_files/list.html', {
        'files': sorted_files,
    })


@login_required
def download(request, publisher_id, uploaded_file_id):

    uploaded_file_record = UploadedFile.objects.get(
        publisher_id=publisher_id,
        uploaded_file_id=uploaded_file_id,
    )

    with open(uploaded_file_record.path, 'rb') as f:
        response = HttpResponse(f.read())

    response['content_type'] = 'text/csv'
    response['Content-Disposition'] = 'attachment; filename="%s"' % uploaded_file_record.original_name

    return response
