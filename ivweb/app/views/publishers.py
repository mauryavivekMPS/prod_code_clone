from django.shortcuts import render
from ivetl.models import Publisher_Metadata


def list_publishers(request):
    publishers = Publisher_Metadata.objects.all()
    return render(request, 'publishers/list.html', {'publishers': publishers})
