import datetime
from django import forms
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from ivetl.models import User, Publisher_User, Audit_Log


def list_users(request):
    users = User.objects.all()
    return render(request, 'users/list.html', {'users': users})


class AdminUserForm(forms.Form):
    user_id = forms.CharField(widget=forms.HiddenInput, required=False)
    email = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'user@domain.com'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}), required=False)
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}), required=False)
    staff = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    superuser = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    publishers = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated list of publisher IDs'}), required=False)

    def __init__(self, *args, instance=None, **kwargs):
        initial = {}
        if instance:
            self.instance = instance
            initial = dict(instance)
            initial.pop('password')  # clear out the encoded password
            initial['publishers'] = ', '.join([p.publisher_id for p in Publisher_User.objects.filter(user_id=instance.user_id)])
        else:
            self.instance = None

        super(AdminUserForm, self).__init__(initial=initial, *args, **kwargs)

        if instance:
            self.fields['password'].widget.attrs['style'] = 'display:none'

    def clean_email(self):
        email = self.cleaned_data['email']
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

        user.update(
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            staff=self.cleaned_data['staff'],
            superuser=self.cleaned_data['superuser'],
        )

        publishers = []
        if self.cleaned_data['publishers']:
            publisher_id_list = [id.strip() for id in self.cleaned_data['publishers'].split(",")]

            # delete existing
            for publisher_user in Publisher_User.objects(user_id=user.user_id):
                publisher_user.delete()

            # and recreate
            for publisher_id in publisher_id_list:
                Publisher_User.objects.create(user_id=user.user_id, publisher_id=publisher_id)

        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])

        return user


def edit(request, user_id=None):
    user = None
    if user_id:
        user = User.objects.get(user_id=user_id)

    if request.method == 'POST':
        form = AdminUserForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            Audit_Log.objects.create(
                user_id=request.user.user_id,
                event_time=datetime.datetime.now(),
                action='edit-user' if user_id else 'create-user',
                entity_type='user',
                entity_id=str(user.user_id),
            )
            return HttpResponseRedirect(reverse('users.list'))
    else:
        form = AdminUserForm(instance=user)

    return render(request, 'users/new.html', {'form': form, 'user': user})
