from django.shortcuts import render


def list_users(request):
    return render(request, 'users/list.html', {})
