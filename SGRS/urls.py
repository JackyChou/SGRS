from django.conf.urls import include, url
from django.contrib import admin

def i18n_javascript(request):
    return admin.site.i18n_javascript(request)

urlpatterns = [
    url(r'^$', 'GeneralReport.views.index'),
    url(r'^sgrs/', include('GeneralReport.urls')),
    url(r'^admin/jsi18n', i18n_javascript),
    url(r'^admin/', include(admin.site.urls)),
]
