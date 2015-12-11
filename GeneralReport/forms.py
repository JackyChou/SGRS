#coding:utf-8

import copy

from django import forms
from django.contrib.admin import widgets
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from GeneralReport.models import SGRSUser

TYPE_FIELD_MAP = {
    'choice'   : forms.ChoiceField,
    'mchoice'  : forms.MultipleChoiceField,
    'text'     : forms.CharField,
    'date'     : forms.DateTimeField,
    'datetime' : forms.DateTimeField,
}

TYPE_WIDGET_MAP = {
    'choice'   : forms.Select,
    'mchoice'  : forms.CheckboxSelectMultiple,
    'text'     : forms.TextInput(),
    'date'     : widgets.AdminDateWidget(),
    'datetime' : widgets.AdminSplitDateTime(),
}

class DynamicForm(forms.Form):
    '''dynamic form class'''
    def __init__(self, *args, **kwargs):
        need_upload_file = copy.deepcopy(kwargs.get('need_upload_file'))
        del kwargs['need_upload_file']
        dynamic_fields = copy.deepcopy(kwargs.get('dynamic_fields'))
        del kwargs['dynamic_fields']
        super(DynamicForm, self).__init__(*args, **kwargs)
        if need_upload_file is True:
            # just for upload file
            self.fields['file'] = forms.FileField(label = u"Upload File")
        if dynamic_fields:
            d_field_list = dynamic_fields.keys()
            d_field_list.sort()
            for d_field in d_field_list:
                d_field_info = dynamic_fields[d_field]
                field_class = TYPE_FIELD_MAP.get(d_field_info['type'],None)

                if field_class is None:
                    continue

                label = d_field_info['name']
                required = True if str(d_field_info['required']) == '1' else False
                widget = TYPE_WIDGET_MAP[d_field_info['type']]
                choices = d_field_info['value']

                kwargs = dict(
                    label = label,
                    required = required,
                    widget = widget,
                )
                if d_field_info['type'] in ['choice','mchoice']:
                    kwargs.update(
                        choices = choices,
                    )

                self.fields[d_field] = field_class(**kwargs)
        if need_upload_file is not True:
            # just for query
            # paging option
            self.fields['use_paging'] = forms.BooleanField(
                required = False,
                label = u"paging",
                widget = forms.CheckboxInput,
            )
            self.fields['page_size'] = forms.CharField(
                required = False,
                initial = 50,
                label = u"page size",
                widget = forms.TextInput(),
            )
            # perview SQL
            self.fields['preview'] = forms.BooleanField(
                required = False,
                label = u"perview SQL(not execute SQL)",
                widget = forms.CheckboxInput,
            )

class UserChangeForm(forms.ModelForm):
    username = forms.RegexField(
        label=_("Username"), max_length=30, regex=r"^[\w.@+-]+$",
        help_text=_("Required. 30 characters or fewer. Letters, digits and "
                      "@/./+/-/_ only."),
        error_messages={
            'invalid': _("This value may contain only letters, numbers and "
                         "@/./+/-/_ characters.")})
    password = ReadOnlyPasswordHashField(label=_("Password"),
        help_text=_("Raw passwords are not stored, so there is no way to see "
                    "this user's password, but you can change the password "
                    "using <a href=\"password/\">this form</a>."))

    class Meta:
        model = SGRSUser
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        f = self.fields.get('user_permissions', None)
        if f is not None:
            f.queryset = f.queryset.select_related('content_type')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """
    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    username = forms.RegexField(label=_("Username"), max_length=30,
        regex=r'^[\w.@+-]+$',
        help_text=_("Required. 30 characters or fewer. Letters, digits and "
                      "@/./+/-/_ only."),
        error_messages={
            'invalid': _("This value may contain only letters, numbers and "
                         "@/./+/-/_ characters.")})
    password1 = forms.CharField(label=_("Password"),
        widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"),
        widget=forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."))

    class Meta:
        model = SGRSUser
        fields = ("username",)

    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            SGRSUser._default_manager.get(username=username)
        except SGRSUser.DoesNotExist:
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username'],
            code='duplicate_username',
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class AdminPasswordChangeForm(forms.Form):
    """
    A form used to change the password of a user in the admin interface.
    """
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password (again)"),
                                widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(AdminPasswordChangeForm, self).__init__(*args, **kwargs)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return password2

    def save(self, commit=True):
        """
        Saves the new password.
        """
        self.user.set_password(self.cleaned_data["password1"])
        if commit:
            self.user.save()
        return self.user

    def _get_changed_data(self):
        data = super(AdminPasswordChangeForm, self).changed_data
        for name in self.fields.keys():
            if name not in data:
                return []
        return ['password']
    changed_data = property(_get_changed_data)

