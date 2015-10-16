from django import forms
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from ivetl.models import User, Publisher_User


def list_users(request):
    users = User.objects.all()
    return render(request, 'users/list.html', {'users': users})


class AdminUserForm(forms.Form):
    email = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'user@domain.com'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}), required=False)
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}), required=False)
    staff = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    superuser = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    publishers = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated list of publisher IDs'}))

    def __init__(self, *args, instance=None, **kwargs):
        initial = {}
        if instance:
            initial = dict(instance)
            initial.pop('password')  # clear out the encoded password
            initial['publishers'] = ', '.join([p.publisher_id for p in Publisher_User.objects.filter(user_email=instance.email)])

        super(AdminUserForm, self).__init__(initial=initial, *args, **kwargs)

        if instance:
            self.fields['password'].widget.attrs['style'] = 'display:none'

    def save(self):
        email = self.cleaned_data['email']
        User.objects(email=email).update(
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            staff=self.cleaned_data['staff'],
            superuser=self.cleaned_data['superuser'],
        )

        user = User.objects.get(email=email)

        publishers = []
        if self.cleaned_data['publishers']:
            publisher_id_list = [id.strip() for id in self.cleaned_data['publishers'].split(",")]

            # delete existing
            for publisher_user in Publisher_User.objects(user_email=email):
                publisher_user.delete()

            # and recreate
            for publisher_id in publisher_id_list:
                Publisher_User.objects.create(user_email=email, publisher_id=publisher_id)

        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])

        return user


def edit(request, slug=None):
    user = None
    if slug:
        email = User.slug_to_email(slug)
        user = User.objects.get(email=email)

    if request.method == 'POST':
        form = AdminUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('users.list'))
    else:
        form = AdminUserForm(instance=user)

    return render(request, 'users/new.html', {'form': form, 'user': user})
