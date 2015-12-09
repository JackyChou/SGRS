#coding:utf-8

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from GeneralReport.models import SGRSUser, SGRSRole, SGRSUserAssignment
from GeneralReport.models import ReportType, ReportPermission
from GeneralReport.models import ReportPermissionCombination
from GeneralReport.forms import UserChangeForm, UserCreationForm, AdminPasswordChangeForm

class SGRSUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

class SGRSRoleAdmin(admin.ModelAdmin):
    search_fields = ['name']
    filter_horizontal = ('report_permissions', 'report_permission_combinations')

class SGRSUserAssignmentAdmin(admin.ModelAdmin):
    search_fields = ['user__username', 'roles__name']
    raw_id_fields = ('user', )
    filter_horizontal = ('roles', )

class ReportTypeAdmin(admin.ModelAdmin):
    search_fields = ['name']

class ReportPermissionAdmin(admin.ModelAdmin):
    search_fields = ['description',]

class ReportPermissionCombinationAdmin(admin.ModelAdmin):
    search_fields = ['name',]
    filter_horizontal = ('report_permissions', )

admin.site.register(SGRSUser, SGRSUserAdmin)
admin.site.register(SGRSRole, SGRSRoleAdmin)
admin.site.register(SGRSUserAssignment, SGRSUserAssignmentAdmin)
admin.site.register(ReportType, ReportTypeAdmin)
admin.site.register(ReportPermission, ReportPermissionAdmin)
admin.site.register(ReportPermissionCombination, ReportPermissionCombinationAdmin)
