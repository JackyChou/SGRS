#coding:utf-8

import json

from django.db import models
from django.db import connections
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractUser

from GeneralReport.utils import replace_invalid_quote

CONDITION_TYPES = [
    'choice',
    'mchoice',
    'text',
    'date',
    'datetime',
]

# each CONDITION_TYPES allow operate
CONDITION_TYPE_OPERATE_MAP = {
    'choice'  : ['=','like','~','in'],
    'mchoice' : ['in',],
    'text'    : ['=','<','<=','>','>=','like','in'],
    'date'    : ['=','<','<=','>','>='],
    'datetime': ['=','<','<=','>','>='],
}

class JsonField(models.TextField):
    __metaclass__ = models.SubfieldBase
    description = "JsonField"

    def to_python(self, value):
        v = models.TextField.to_python(self, value)
        try:
            return json.loads(v)['v']
        except:
            pass
        return v

    def get_prep_value(self, value):
        return json.dumps({'v':value})

class SGRSUser(AbstractUser):

    class Meta:
        app_label = 'GeneralReport'
        db_table = 'sgrs_user'
        verbose_name_plural = verbose_name = _('SGRS User')

    def has_report_perm(self):
        pass

    def get_all_roles(self):
        pass

    def get_all_report_permissions(self):
        pass

    def get_all_report_combination_permissions(self):
        pass

class AbstractBaseModel(models.Model):
    touch_date = models.DateTimeField(editable=False, auto_now_add=True)
    create_date = models.DateTimeField(editable=False, auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.full_clean()
        super(AbstractBaseModel, self).save(*args, **kwargs)

class ReportType(AbstractBaseModel):
    name = models.CharField(max_length=100, db_index=True)

    class Meta:
        app_label = 'GeneralReport'
        db_table = 'sgrs_report_type'
        ordering = ['name']

    def __unicode__(self):
        return u"%s" % (self.name)

class ReportPermission(AbstractBaseModel):
    name = models.CharField(max_length=100, db_index=True, unique=True)
    description = models.TextField(blank=True)
    report_type = models.ForeignKey(ReportType, blank=True, null=True)
    db_conf = models.CharField(blank=True, verbose_name=_(u"DB_name"), max_length=128, choices=settings.DB_FOR_CHOICES)
    SQL_conf = models.TextField(verbose_name=_(u"SQL conf"))
    filter_conf = JsonField()

    class Meta:
        app_label = 'GeneralReport'
        db_table = 'sgrs_report_permission'
        ordering = ['report_type__name', 'name']

    def __unicode__(self):
        return u"%s | %s | %s" % (
            unicode(self.report_type.name) if self.report_type else u"Unclassified",
            unicode(self.description),
            unicode(self.name)
        )

    def clean(self):
        # check name
        import re
        pattern = '^[a-z][a-z\-]+[a-z]$'
        if re.match(pattern, self.name ) is None:
            raise ValidationError(
                "Only lowercase characters and \"-\" are allowed!")

        # check filter_conf
        self.filter_conf = replace_invalid_quote(self.filter_conf)
        try:
            tmp_filter_conf = json.loads(self.filter_conf)
        except:
            raise ValidationError(u"filter_conf is not a valid json")
        if not isinstance(tmp_filter_conf, dict):
            raise ValidationError(u"filter_conf must be dict")
        condition_keys = tmp_filter_conf.keys()

        for ckey in condition_keys:
            item_field = tmp_filter_conf[ckey].get('field',None)
            item_type = tmp_filter_conf[ckey].get('type',None)
            item_operate = tmp_filter_conf[ckey].get('operate',None)

            if item_type not in CONDITION_TYPES:
                raise ValidationError(u"%s is not a valid type, only support %s" %(item_type,CONDITION_TYPES))
            if item_field is None or item_type is None or item_operate is None:
                raise ValidationError(u"Please supply %s's key：field / type / operate" % ckey)
            if item_operate not in CONDITION_TYPE_OPERATE_MAP[item_type]:
                raise ValidationError(u"%s only can use %s" %(item_type,CONDITION_TYPE_OPERATE_MAP[item_type]))

        # check db_conf whether in settings
        try:
            connections[self.db_conf]
        except:
            raise ValidationError(u"Database %s isn't configured" % self.db_conf)

        # check filter_conf matching SQL_conf?
        sql_condition_list = re.findall(r'{{(\S+)}}',self.SQL_conf)
        sql_condition_list = list(set(sql_condition_list))
        sql_condition_list.sort()
        condition_keys.sort()
        if sql_condition_list != condition_keys:
            raise ValidationError(u"where clauses not match, filter_conf is %s, SQL_conf is %s"%(condition_keys,sql_condition_list))

class ReportPermissionCombination(AbstractBaseModel):
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True)
    report_permissions = models.ManyToManyField(ReportPermission, blank=True)

    class Meta:
        app_label = 'GeneralReport'
        db_table = 'sgrs_report_permission_combination'
        ordering = ['id']

    def __unicode__(self):
        return self.name

class SGRSRole(AbstractBaseModel):
    name = models.CharField(max_length=255, db_index=True, unique=True)
    description = models.TextField(blank=True)
    can_download = models.BooleanField(default=True)
    report_permissions = models.ManyToManyField(ReportPermission, blank=True)
    report_permission_combinations = models.ManyToManyField(ReportPermissionCombination, blank=True)

    class Meta:
        app_label = 'GeneralReport'
        db_table = 'sgrs_role'
        ordering = ['name']
        verbose_name_plural = verbose_name = _('SGRS Role')

    def __unicode__(self):
        return self.name

class SGRSUserAssignment(AbstractBaseModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, db_index=True)
    roles = models.ManyToManyField(SGRSRole)

    class Meta:
        app_label = 'GeneralReport'
        db_table = 'sgrs_user_assignment'
        ordering = ['user']
        verbose_name_plural = verbose_name = _('SGRS User Assignment')

    def __unicode__(self):
        return u'%s Role Assignment' %self.user
