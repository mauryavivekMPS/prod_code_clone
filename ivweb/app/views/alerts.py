import logging
from operator import attrgetter
from django import forms
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from ivetl.models import Alert
from ivweb.app.views import utils as view_utils

log = logging.getLogger(__name__)


def list_alerts(request, publisher_id=None):
    if publisher_id:
        alerts = Alert.objects.filter(publisher_id=publisher_id)
    else:
        alerts = Alert.objects.all()

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('alert-list-sort', 'publisher_id'))
    sorted_alerts = sorted(alerts, key=attrgetter(sort_key), reverse=sort_descending)

    response = render(request, 'alerts/list.html', {
        'alerts': sorted_alerts,
        'sort_key': sort_key,
        'sort_descending': sort_descending,
    })

    response.set_cookie('publisher-list-sort', value=sort_param, max_age=30*24*60*60)

    return response


# class AdminUserForm(forms.Form):
#     user_id = forms.CharField(widget=forms.HiddenInput, required=False)
#     email = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'user@domain.com'}))
#     password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)
#     first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}), required=False)
#     last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}), required=False)
#     staff = forms.BooleanField(widget=forms.CheckboxInput, required=False)
#     superuser = forms.BooleanField(widget=forms.CheckboxInput, required=False)
#     publishers = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated list of publisher IDs'}), required=False)
#
#     def __init__(self, *args, instance=None, for_publisher=None, **kwargs):
#         self.for_publisher = for_publisher
#         initial = {}
#         if instance:
#             self.instance = instance
#             initial = dict(instance)
#             initial.pop('password')  # clear out the encoded password
#             if not for_publisher:
#                 initial['publishers'] = ', '.join([p.publisher_id for p in Publisher_User.objects.filter(user_id=instance.user_id)])
#         else:
#             self.instance = None
#
#         super(AdminUserForm, self).__init__(initial=initial, *args, **kwargs)
#
#         if instance:
#             self.fields['password'].widget.attrs['style'] = 'display:none'
#
#     def clean_email(self):
#         email = self.cleaned_data['email']
#         if not self.instance or email != self.instance.email:
#             if User.objects.filter(email=email).count():
#                 raise forms.ValidationError("This email address is already in use.")
#         return email
#
#     def save(self):
#         user_id = self.cleaned_data['user_id']
#         if user_id:
#             user = User.objects.get(user_id=user_id)
#         else:
#             user = User.objects.create()
#
#         if self.for_publisher:
#             user.update(
#                 email=self.cleaned_data['email'],
#                 first_name=self.cleaned_data['first_name'],
#                 last_name=self.cleaned_data['last_name'],
#                 # no setting of staff or superuser
#             )
#
#             # add perms for just the current publisher
#             Publisher_User.objects.create(user_id=user.user_id, publisher_id=self.for_publisher.publisher_id)
#
#         else:
#             user.update(
#                 email=self.cleaned_data['email'],
#                 first_name=self.cleaned_data['first_name'],
#                 last_name=self.cleaned_data['last_name'],
#                 staff=self.cleaned_data['staff'],
#                 superuser=self.cleaned_data['superuser'],
#             )
#
#             publisher_id_list = [id.strip() for id in self.cleaned_data['publishers'].split(",")]
#
#             # delete existing
#             for publisher_user in Publisher_User.objects.filter(user_id=user.user_id):
#                 publisher_user.delete()
#
#             # and recreate
#             for publisher_id in publisher_id_list:
#                 if publisher_id:
#                     Publisher_User.objects.create(user_id=user.user_id, publisher_id=publisher_id)
#
#         if self.cleaned_data['password']:
#             user.set_password(self.cleaned_data['password'])
#
#         return user


def edit(request, publisher_id=None, user_id=None):
    # if publisher_id:
    #     publisher = Publisher_Metadata.objects.get(publisher_id=publisher_id)
    # else:
    #     publisher = None
    #
    # user = None
    # if user_id:
    #     user = User.objects.get(user_id=user_id)
    #
    # if request.method == 'POST':
    #     form = AdminUserForm(request.POST, instance=user, for_publisher=publisher)
    #     if form.is_valid():
    #         user = form.save()
    #         Audit_Log.objects.create(
    #             user_id=request.user.user_id,
    #             event_time=datetime.datetime.now(),
    #             action='edit-user' if user_id else 'create-user',
    #             entity_type='user',
    #             entity_id=str(user.user_id),
    #         )
    #         if publisher:
    #             return HttpResponseRedirect(reverse('publishers.users', kwargs={'publisher_id': publisher.publisher_id}))
    #         else:
    #             return HttpResponseRedirect(reverse('users.list'))
    # else:
    #     form = AdminUserForm(instance=user, for_publisher=publisher)
    #
    return render(request, 'alerts/new.html', {
        # 'form': form,
        # 'user': user,
        # 'publisher': publisher,
    })
