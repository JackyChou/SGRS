#coding:utf-8

from django.shortcuts import render
from django.http import Http404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordChangeForm

from GeneralReport.utils import ObjectDict

@login_required
def index(request):
    user = request.user
    report_solo_perm_list = user.get_all_report_permissions()
    report_comb_perm_list = user.get_all_report_combination_permissions()

    # single report
    report_solo_info_dict = ObjectDict()
    for solo_obj in report_solo_perm_list:
        solo_class = solo_obj.report_type.name if solo_obj.report_type else u'Unclassified'
        solo_url = request.build_absolute_uri('/sgrs/report/%s' %solo_obj.name)
        solo_desc = solo_obj.description
        solo_info = ObjectDict(
            name = solo_obj.name,
            desc = solo_desc,
            report_url = solo_url,
        )
        report_solo_info_dict.setdefault(solo_class,[]).append(solo_info)

    for key in report_solo_info_dict:
        report_solo_info_dict[key].sort(key=lambda x:x.desc)

    # combination report
    report_comb_info_list = []
    for comb_obj in report_comb_perm_list:
        comb_url = request.build_absolute_uri('/sgrs/combreport/%s' %comb_obj.id)
        comb_info = ObjectDict(
            name = comb_obj.name,
            desc = comb_obj.description,
            report_url = comb_url,
        )
        report_comb_info_list.append(comb_info)
    report_comb_info_list.sort(key=lambda x:x.desc)

    data = {
        'report_solo_info_dict':report_solo_info_dict,
        'report_comb_info_list':report_comb_info_list,
    }

    return render(request, 'GeneralReport/index.html', data)

@login_required
def report(request, report_key):
    raise Http404("to be continue")

@login_required
def combreport(request, comb_id):
    raise Http404("to be continue")

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

