from django import forms
from django.shortcuts import render, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from ivetl.models import User


def login(request):
    error = False

    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        normalized_email = email.lower()

        try:
            user = User.objects.get(email=normalized_email)
            if user.check_password(password):
                request.session['user_id'] = str(user.user_id)
                return HttpResponseRedirect(reverse('home'))

        except User.DoesNotExist:
            pass  # just fall through

        error = True

    return render(request, 'login.html', {'error': error})


def logout(request):
    request.session['user_id'] = None
    return HttpResponseRedirect(reverse('login'))


class UserSettingsForm(forms.Form):
    email = forms.CharField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}), required=False)
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}), required=False)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password', 'style': 'display:none'}), required=False)
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password again', 'style': 'display:none'}), required=False)

    def __init__(self, *args, instance, **kwargs):
        self.instance = instance
        initial = dict(instance)
        initial.pop('password')  # clear out the encoded password
        super(UserSettingsForm, self).__init__(initial=initial, *args, **kwargs)

    def save(self):
        self.instance.email = self.cleaned_data['email']
        self.instance.first_name = self.cleaned_data['first_name']
        self.instance.last_name = self.cleaned_data['last_name']
        self.instance.save()

        if self.cleaned_data['password']:
            self.instance.set_password(self.cleaned_data['password'])

        return self.instance


@login_required
def settings(request):
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('home'))
    else:
        form = UserSettingsForm(instance=request.user)

    return render(request, 'settings.html', {'form': form})
