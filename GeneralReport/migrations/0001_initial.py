# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.auth.models
from django.conf import settings
import django.utils.timezone
import GeneralReport.models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('touch_date', models.DateTimeField(auto_now_add=True)),
                ('create_date', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(unique=True, max_length=100, db_index=True)),
                ('description', models.TextField(blank=True)),
                ('db_conf', models.CharField(max_length=128, verbose_name='DB_name', blank=True)),
                ('SQL_conf', models.TextField(verbose_name='SQL\u8bed\u53e5')),
                ('filter_conf', GeneralReport.models.JsonField()),
            ],
            options={
                'ordering': ['report_type__name', 'name'],
                'db_table': 'sgrs_report_permission',
            },
        ),
        migrations.CreateModel(
            name='ReportPermissionCombination',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('touch_date', models.DateTimeField(auto_now_add=True)),
                ('create_date', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, db_index=True)),
                ('description', models.TextField(blank=True)),
                ('report_permissions', models.ManyToManyField(to='GeneralReport.ReportPermission', blank=True)),
            ],
            options={
                'ordering': ['id'],
                'db_table': 'sgrs_report_permission_combination',
            },
        ),
        migrations.CreateModel(
            name='ReportType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('touch_date', models.DateTimeField(auto_now_add=True)),
                ('create_date', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, db_index=True)),
            ],
            options={
                'ordering': ['name'],
                'db_table': 'sgrs_report_type',
            },
        ),
        migrations.CreateModel(
            name='SGRSRole',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('touch_date', models.DateTimeField(auto_now_add=True)),
                ('create_date', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(unique=True, max_length=255, db_index=True)),
                ('description', models.TextField(blank=True)),
                ('can_download', models.BooleanField(default=True)),
                ('report_permission_combinations', models.ManyToManyField(to='GeneralReport.ReportPermissionCombination', blank=True)),
                ('report_permissions', models.ManyToManyField(to='GeneralReport.ReportPermission', blank=True)),
            ],
            options={
                'ordering': ['name'],
                'db_table': 'sgrs_role',
            },
        ),
        migrations.CreateModel(
            name='SGRSUserAssignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('touch_date', models.DateTimeField(auto_now_add=True)),
                ('create_date', models.DateTimeField(auto_now=True)),
                ('roles', models.ManyToManyField(to='GeneralReport.SGRSRole')),
            ],
            options={
                'ordering': ['user'],
                'db_table': 'sgrs_user_assignment',
            },
        ),
        migrations.CreateModel(
            name='SGRSUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, max_length=30, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.', 'invalid')], help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', unique=True, verbose_name='username')),
                ('first_name', models.CharField(max_length=30, verbose_name='first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='last name', blank=True)),
                ('email', models.EmailField(max_length=254, verbose_name='email address', blank=True)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={
                'db_table': 'sgrs_user',
            },
            managers=[
                (b'objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.AddField(
            model_name='sgrsuserassignment',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='reportpermission',
            name='report_type',
            field=models.ForeignKey(blank=True, to='GeneralReport.ReportType', null=True),
        ),
    ]
