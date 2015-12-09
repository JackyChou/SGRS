#coding:utf-8

from django.conf.urls import patterns, include, url
#from django.contrib import auth

urlpatterns = patterns('GeneralReport.views',
    url(r'^$','index',name='SGRS_index'),

    url(r'^login/?$','login',name='auth_login'),
    url(r'^logout/$','logout',name='auth_logout'),
    url(r'^pwd_change/$','pwd_change',name='pwd_change'),
    url(r'^pwd_change_done/$','pwd_change_done',name='pwd_change_done'),
)
