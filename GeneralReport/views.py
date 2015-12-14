#coding:utf-8

import os
import json

from django.shortcuts import render
from django.http import Http404
from django.http import HttpResponse, HttpResponseRedirect
from django.http import StreamingHttpResponse
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordChangeForm
from django.core.cache import cache

from GeneralReport.utils import ObjectDict
from GeneralReport.utils import parse_sql
from GeneralReport.utils import parse_dynamic_form
from GeneralReport.utils import create_download_file
from GeneralReport.models import ReportPermission

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
    # check permission
    user = request.user
    if not user.has_report_perm(report_key):
        return HttpResponseRedirect(reverse('SGRS_index'))

    # load permission config
    report_perm =  ReportPermission.objects.get(name=report_key)
    filter_conf = json.loads(report_perm.filter_conf)
    db_conf = report_perm.db_conf
    sql_conf = report_perm.SQL_conf

    sql = ''
    query_data = []
    query_data_total = 0
    header_data = []
    download_file_url = ''
    form = parse_dynamic_form(filter_conf)
    page_num = request.GET.get('page_num', None)
    page_size = request.GET.get('page_size', None)
    paging_urls = []

    user_role_list = user.get_all_roles()
    perm_role_list = report_perm.sgrsrole_set.all()
    can_download = any([i.can_download \
        for i in user_role_list if i in perm_role_list])

    if request.method == 'POST':
        query_dict = request.POST.copy()
        if 'csrfmiddlewaretoken' in query_dict:
            del query_dict['csrfmiddlewaretoken']
        if 'use_paging' in query_dict:
            del query_dict['use_paging']
        if 'preview' in query_dict:
            del query_dict['preview']
        form = parse_dynamic_form(filter_conf,data=request.POST.copy())

    elif page_num is not None and page_size is not None:
        query_dict = request.GET.copy()
        form = parse_dynamic_form(filter_conf,data=request.GET.copy())

    if form.is_valid():
        # query from cache, cache_key be made up of from field
        # (except use_paging,page_size and perview)
        cache_key_dict = form.cleaned_data.copy()
        if 'use_paging' in cache_key_dict:
            del cache_key_dict['use_paging']
        if 'page_size' in cache_key_dict:
            del cache_key_dict['page_size']
        if 'preview' in cache_key_dict:
            del cache_key_dict['preview']
        cache_key = '%s:%s:%s' %(user.username, report_key, \
            '-'.join(['%s=%s' %(k,v) for k,v in cache_key_dict.items()]))
        cache_result = cache.get(cache_key)
        result = json.loads(cache_result) if cache_result else {}

        preview = form.cleaned_data['preview']
        if result:
            sql = result.get('sql','')
            if not preview:
                query_data, header_data = result['q_data'], result['h_data']
        else:
            # if there is not cache, set a placeholder
            if not cache_result:
                cache.set(cache_key, json.dumps({}), 60 * 10)

            # query from database, and write into cache
            query_data, header_data, sql = parse_sql(user,filter_conf,
                db_conf,sql_conf,form=form,preview=preview)

            if not preview:
                result = {'q_data':query_data,'h_data':header_data,'sql':sql}
                if not cache_result:
                    cache.set(cache_key, json.dumps(result), 60 * 10)

        # create download file
        if can_download:
            download_file_name = create_download_file( \
                user,report_key,header_data,query_data)

        query_data_total = len(query_data)

        # paging
        use_paging = form.cleaned_data['use_paging']
        browser_line_limit = 50000
        page_size = int(form.cleaned_data['page_size'])
        if query_data_total >= browser_line_limit:
            use_paging = True
            page_size = 1000 if page_size < 1000 else page_size
        if use_paging or page_num and page_size:
            page_num = int(page_num or 1)
            max_page_num = len(query_data) / page_size
            if max_page_num * page_size < len(query_data):
                max_page_num += 1
            # create paging url
            for tmp_page_num in range(1, max_page_num + 1):
                query_dict['page_num'] = tmp_page_num
                page_url = request.build_absolute_uri('/sgrs/report/%s?%s' \
                    % (report_key,query_dict.urlencode()))
                page_info = ObjectDict(
                    url = page_url,
                    page_num = tmp_page_num,
                    link = 0 if tmp_page_num == page_num else 1, # current url can't click
                )
                paging_urls.append(page_info)

            # split query_data
            query_data = query_data[(page_num - 1) * page_size: page_num * page_size]

    #if query_data and can_download:
    #    download_file_url = request.build_absolute_uri( \
    #        '/sgrs/download/%s' %(download_file_name))

    # edit entry for admin
    edit_permission_url = ''
    if user.is_staff:
        edit_permission_url = request.build_absolute_uri('/admin/GeneralReport/reportpermission/%s' % report_perm.id)

    data = {
        'filter_conf':filter_conf,
        'report_key':report_key,
        'perm_desc':report_perm.description,
        'sql':sql,
        'query_data_total':query_data_total,
        'query_data':query_data,
        'header_data':header_data,
        'filter_form':form,
        'download_file_url':download_file_url,
        'paging_urls':paging_urls,
        'edit_permission_url':edit_permission_url,
        'can_download':can_download,
    }
    return render(request, 'GeneralReport/report.html', data)

@login_required
def combreport(request, comb_id):
    raise Http404("to be continue")

@login_required
def download_file(request, filename):

    def file_iterator(file_name, chunk_size=512):
        with open(file_name) as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break

    # check permission
    user = request.user
    report_key = filename.split('.')[0].split('_')[-2] #username_perm_timestamp.xls

    if not user.has_report_perm(report_key):
        return HttpResponseRedirect(reverse('SGRS_index'))

    file_dir = os.path.join(settings.STATIC_ROOT, "download_file")
    the_file_name = os.path.join(file_dir,filename)

    response = StreamingHttpResponse(file_iterator(the_file_name))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(filename)

    return response

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

