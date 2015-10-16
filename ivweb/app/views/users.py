from django import forms
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from ivetl.models import User


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

    def __init__(self, *args, instance=None, **kwargs):
        initial = {}
        if instance:
            initial = dict(instance)
            initial.pop('password')  # clear out the encoded password

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
