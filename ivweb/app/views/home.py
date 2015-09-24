from django.shortcuts import render
from ivweb.app.models import Publisher_Metadata


def home(request):
    publisher = Publisher_Metadata.objects.get(publisher_id='test')
    return render(request, 'home.html', {'publisher': publisher})
