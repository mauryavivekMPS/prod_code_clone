import datetime
import logging
from operator import attrgetter
from django import forms
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import User, PublisherUser, PublisherMetadata
from ivetl import utils
from ivweb.app.views import utils as view_utils

log = logging.getLogger(__name__)


@login_required
def list_users(request, publisher_id=None):
    if publisher_id:
        publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)
        publisher_users = [u.user_id for u in PublisherUser.objects.allow_filtering().filter(publisher_id=publisher_id)]
        users = User.objects.filter(user_id__in=publisher_users)
    else:
        publisher = None
        users = User.objects.all()

    users = sorted(users, key=lambda u: u.email)

    sort_param, sort_key, sort_descending = view_utils.get_sort_params(request, default=request.COOKIES.get('user-list-sort', 'email'))
    sorted_users = sorted(users, key=attrgetter(sort_key), reverse=sort_descending)

    response = render(request, 'users/list.html', {
        'users': sorted_users,
        'publisher': publisher,
        'sort_key': sort_key,
        'sort_descending': sort_descending,
    })

    response.set_cookie('user-list-sort', value=sort_param, max_age=30*24*60*60)

    return response


USER_TYPE_CHOICES = [
    (10, 'Publisher Staff (FTP Only)'),
    (20, 'Publisher Staff (Manager and FTP)'),
    (30, 'HW Staff'),
    (40, 'HW Superuser'),
]


class AdminUserForm(forms.Form):
    user_id = forms.CharField(widget=forms.HiddenInput, required=False)
    email = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'user@domain.com'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}), required=False)
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}), required=False)
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    # publishers = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated list of publisher IDs'}), required=False)
    publishers = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, instance=None, for_publisher=None, **kwargs):
        self.for_publisher = for_publisher
        self.old_publisher_ids = []
        self.new_publisher_ids = []
        initial = {}
        if instance:
            self.instance = instance
            initial = dict(instance)
            initial.pop('password')  # clear out the encoded password
            if not for_publisher:
                initial['publishers'] = ', '.join([p.publisher_id for p in PublisherUser.objects.filter(user_id=instance.user_id)])
        else:
            self.instance = None

        super(AdminUserForm, self).__init__(initial=initial, *args, **kwargs)

        if instance:
            self.fields['password'].widget.attrs['style'] = 'display:none'

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if not self.instance or email != self.instance.email:
            if User.objects.filter(email=email).count():
                raise forms.ValidationError("This email address is already in use.")
        return email

    def save(self):
        user_id = self.cleaned_data['user_id']
        if user_id:
            user = User.objects.get(user_id=user_id)
        else:
            user = User.objects.create()

        if self.for_publisher:
            user.update(
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                user_type=20,  # default to publisher staff
            )

            # add perms for just the current publisher
            PublisherUser.objects.create(user_id=user.user_id, publisher_id=self.for_publisher.publisher_id)

        else:
            user.update(
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                user_type=self.cleaned_data['user_type'],
            )

            existing_publishers = PublisherUser.objects.filter(user_id=user.user_id)

            self.old_publisher_ids = [e.publisher_id for e in existing_publishers]
            self.new_publisher_ids = [id.strip() for id in self.cleaned_data['publishers'].split(",") if id]

            # delete existing
            for publisher_user in existing_publishers:
                publisher_user.delete()

            # and recreate
            for publisher_id in self.new_publisher_ids:
                if publisher_id:
                    PublisherUser.objects.create(user_id=user.user_id, publisher_id=publisher_id)

        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])

        return user


@login_required
def edit(request, publisher_id=None, user_id=None):
    if publisher_id:
        for_publisher = PublisherMetadata.objects.get(publisher_id=publisher_id)
    else:
        for_publisher = None

    user = None
    if user_id:
        user = User.objects.get(user_id=user_id)

    if request.method == 'POST':
        form = AdminUserForm(request.POST, instance=user, for_publisher=for_publisher)
        if form.is_valid():
            user = form.save()

            if user_id:
                utils.add_audit_log(
                    user_id=request.user.user_id,
                    action='edit-user',
                    publisher_id='system',
                    description='Edit user %s' % user.email,
                )
            else:
                utils.add_audit_log(
                    user_id=request.user.user_id,
                    action='create-user',
                    publisher_id='system',
                    description='Create user %s' % user.email,
                )

            old_publisher_ids = set(form.old_publisher_ids)
            new_publisher_ids = set(form.new_publisher_ids)

            for deleted_publisher_id in old_publisher_ids - new_publisher_ids:
                utils.add_audit_log(
                    user_id=request.user.user_id,
                    publisher_id=deleted_publisher_id,
                    action='revoked-user-access',
                    description='Revoked access to %s for %s' % (deleted_publisher_id, user.email),
                )

            for added_publisher_id in new_publisher_ids - old_publisher_ids:
                utils.add_audit_log(
                    user_id=request.user.user_id,
                    publisher_id=added_publisher_id,
                    action='granted-user-access',
                    description='Granted access to %s for %s' % (added_publisher_id, user.email),
                )

            if for_publisher:
                return HttpResponseRedirect(reverse('publishers.users', kwargs={'publisher_id': for_publisher.publisher_id}))
            else:
                return HttpResponseRedirect(reverse('users.list'))
    else:
        form = AdminUserForm(instance=user, for_publisher=for_publisher)

    if not for_publisher:
        all_publishers = PublisherMetadata.objects.all()
        accessible_publisher_ids = [p.publisher_id for p in request.user.get_accessible_publishers()]
        publisher_name_by_id = {p.publisher_id: p.name for p in request.user.get_accessible_publishers()}
    else:
        all_publishers = None
        accessible_publisher_ids = None
        publisher_name_by_id = {}

    if user:
        selected_publisher_ids = [p.publisher_id for p in PublisherUser.objects.filter(user_id=user.user_id)]
    else:
        selected_publisher_ids = []

    return render(request, 'users/new.html', {
        'form': form,
        'user': user,
        'for_publisher': for_publisher,
        'all_publishers': all_publishers,
        'accessible_publisher_ids': accessible_publisher_ids,
        'selected_publisher_ids': selected_publisher_ids,
        'publisher_name_by_id': publisher_name_by_id,
    })
