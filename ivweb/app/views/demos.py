from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ivetl.models import Demo


@login_required
def list_demos(request):

    if request.user.superuser:
        demos = Demo.objects.all()
    else:
        demos = Demo.objects.all()

    demos = sorted(demos, key=lambda p: p.name.lower().lstrip('('))

    return render(request, 'demos/list.html', {
        'publishers': demos,
    })


@login_required
def edit(request, demo_id=None):
    demo = None
    if request.method == 'POST':
        pass
    else:
        pass

    return render(request, 'demos/new.html', {
        'demo': demo,
    })
