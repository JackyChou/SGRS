#coding:utf-8

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordChangeForm

@login_required
def index(request):
    return render(request, 'GeneralReport/index.html')

def login(request):
    form = AuthenticationForm()

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST.copy())
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)
            if (user is not None) and user.is_active:
                auth_login(request, user)
            return HttpResponseRedirect(reverse("SGRS_index"))
    return render(request, 'GeneralReport/login.html', {'form':form})

@login_required
def logout(request):
    auth_logout(request)
    return HttpResponseRedirect(reverse('auth_login'))

@login_required
def pwd_change(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('pwd_change_done'))
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'GeneralReport/pwd_change.html', {'form':form})

def pwd_change_done(request):
    return render(request, 'GeneralReport/pwd_change_done.html')

