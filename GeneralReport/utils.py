#coding:utf-8

import os
import re
import json
import datetime
import time

from django.db import connections
from django.conf import settings
from GeneralReport.forms import DynamicForm

class ObjectDict(dict):
    """
    Makes a dictionary behave like an object, with attribute-style access.
    """
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

def dictfetchall(cursor):
    """
    Returns all rows from a cursor as a dict
    >>> cursor.execute("SELECT id, parent_id from test LIMIT 2");
    >>> dictfetchall(cursor)
    [{'parent_id': None, 'id': 54360982L}, {'parent_id': None, 'id': 54360880L}]
    """
    desc = cursor.description
    query_header = [{i:i} for i in [col[0].encode('utf8') for col in desc]]
    return ([
        ObjectDict(zip([col[0].encode('utf8') for col in desc], row))
        for row in cursor.fetchall()
    ], query_header)

def parse_filter_conf(filter_conf,sql_conf,form):
    """
    Create where clause according to filter_conf,and update SQL
    """
    # create where clause
    raw_filter_condition = {}
    form_data = form.cleaned_data
    for f_key in filter_conf:
        item = filter_conf[f_key]
        form_data_key = f_key
        if not form_data.get(form_data_key,None) and str(item['required']) == '0':
            raw_filter_condition[f_key] = '1=1'
        else:
            if item['operate'] == 'like':
                like_condition_data = form_data.get(form_data_key,'')
                raw_filter_condition[f_key] = ' '.join([
                    item['field'],
                    item['operate'],
                    "\'%%%s%%\'" % like_condition_data
                ])

            elif item['operate'] == 'in':
                in_condition_data = form_data.get(form_data_key,[])
                if isinstance(in_condition_data,list):
                    in_condition_data_str = ("\'%s\'," * len(in_condition_data))[0:-1] % tuple(in_condition_data)
                else:
                    in_condition_data_str = in_condition_data.replace('，',',')
                raw_filter_condition[f_key] = ' '.join([
                    item['field'],
                    item['operate'],
                    '(',
                    in_condition_data_str,
                    ')',
                ])

            elif item.get('sql_injection','0') == '0':
                other_condition_data = str(form_data.get(form_data_key,''))
                if item['type'] == 'date':
                    other_condition_data = other_condition_data.split()[0]
                if str(item.get('isoformat','1')) == '0':
                    other_condition_data = other_condition_data.replace('-','')
                    other_condition_data = other_condition_data.replace(' ','')
                    other_condition_data = other_condition_data.replace(':','')
                raw_filter_condition[f_key] = ' '.join([
                    item['field'],
                    item['operate'],
                    "\'%s\'" % other_condition_data if str(item.get('dblink','0')) == '0' else "\'\'%s\'\'" % other_condition_data,
                ])

            else:
                # use SQL injection
                sql_injection_condition_data = str(form_data.get(form_data_key,''))
                raw_filter_condition[f_key] = ' '.join([
                    item['field'],
                    item['operate'],
                    sql_injection_condition_data,
                ])

    # update SQL
    re_list = re.findall(r'{{\s*\S+\s*}}', sql_conf)
    for item in re_list:
        tmp_item = item.replace(' ','')
        tmp_item = tmp_item.replace('{','')
        tmp_item = tmp_item.replace('}','')
        key = tmp_item
        sql_conf = sql_conf.replace(item,raw_filter_condition[key])

    return sql_conf

def parse_user_ext_info(user,sql_conf,re_list):
    """
    Create where clause according to user.ext_info,and update SQL
    """
    ext_info = json.loads(user.ext_info)
    for item in re_list:
        tmp_item = item.replace(' ','')
        tmp_item = tmp_item.replace('{','')
        tmp_item = tmp_item.replace('}','')
        key = tmp_item.split('.')[-1]
        sql_conf = sql_conf.replace(item,"\'%s\'" %ext_info[key])
    return sql_conf

def run_sql(db_name,sql):
    """
    Execute SQL
    """
    db_conn = connections[db_name]
    db_cur = db_conn.cursor().cursor
    db_cur.execute(sql)
    query_data, query_header = dictfetchall(db_cur)
    return query_data, query_header

def parse_output_conf(query_data,output_conf):
    """
    Convert format
    """
    output_data = []
    header_data = []
    field_order = []
    for item in output_conf:
        header_data.append(item.values()[0])
        field_order.append(item.keys()[0])

    for data in query_data:
        tmp_data_list = []
        for field in field_order:
            tmp_data = str(data[field.encode('utf8')]) if data[field.encode('utf8')] is not None else ''
            tmp_data_list.append(tmp_data)
        output_data.append(tmp_data_list)
    return output_data, header_data

def parse_sql(user,filter_conf,db_conf,sql_conf,form=None,preview=False):
    """
    Parse sql and return Query Results
    """
    if filter_conf:
        sql_conf = parse_filter_conf(filter_conf,sql_conf,form)

    query_data, query_header = [], []

    if not preview:
        query_data, query_header = run_sql(db_conf,sql_conf)

    output_data, header_data  = parse_output_conf(query_data,query_header)

    return output_data, header_data, sql_conf

def parse_dynamic_form(filter_conf,data=None,files=None,need_upload_file=False):
    dynamic_fields = dict()
    filter_conf_keys = filter_conf.keys()
    filter_conf_keys.sort()
    for item_key in filter_conf_keys:
        item = filter_conf[item_key]
        field = item_key
        field_name = item.get('name','')
        field_type = item['type']
        required = item.get('required','1')
        choice_value = item.get('value',None)

        # choice_value must be tuple
        if choice_value is not None:
            choice_value = tuple([tuple(i) for i in choice_value])

        dynamic_fields[field] = {
            'name':field_name,
            'type':field_type,
            'required':required,
            'value':choice_value,
        }

    form = DynamicForm(
        dynamic_fields=dynamic_fields,
        data=data,
        files=files,
        need_upload_file=need_upload_file,
    )
    return form

def remove_file_one_day_bofore(file_dir):
    """
    Clean tmp file when the first time to generate the download file each day
    """
    last_time_clean_timestamp = settings.CLEAN_TMP_FILE_TIMESTAMP
    today_begin = int(time.mktime(datetime.date.today().timetuple()))
    if today_begin > last_time_clean_timestamp:
        os_walk = os.walk(file_dir)
        for root,dirs,files in os_walk:
            for each_file in files:
                file_path = os.path.join(root,each_file)
                file_stat = os.stat(file_path)
                if today_begin > file_stat.st_mtime:
                    os.remove(file_path)
        settings.CLEAN_TMP_FILE_TIMESTAMP = today_begin
    return None

def create_download_file(user,report_key,header_data,query_data):
    """
    Use tablib to creat xls for download
    """
    if not query_data:
        return ''

    import tablib
    file_dir = os.path.join(settings.STATIC_ROOT, "download_file")
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    remove_file_one_day_bofore(file_dir)
    for i in range(5):
        file_name = '%s_%s_%s.xls' %(user.username,report_key,str(time.time()).replace('.',''))
        file_path = os.path.join(file_dir,file_name)
        if not os.path.exists(file_path):
            break

    file_handle = open(file_path, 'wb')

    dataset_list = []
    tmp_query_data_a = query_data
    sheet_tag = 1
    line_limit = 50000
    while tmp_query_data_a:
        tmp_query_data_b = tmp_query_data_a[:line_limit]
        dataset = tablib.Dataset(*tmp_query_data_b, headers=header_data)
        dataset.title = u'Result' + str(sheet_tag)
        sheet_tag += 1
        dataset_list.append(dataset)
        tmp_query_data_a = tmp_query_data_a[line_limit:]
    book = tablib.Databook(dataset_list)
    file_handle.write(book.xls)

    file_handle.close()
    return file_name

def handle_uploaded_file(f, user, report_key):
    file_dir = os.path.join(settings.STATIC_ROOT, "upload_file")
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    file_name = '%s_%s_upload_tmpfile' %(user.username, report_key)
    file_path = os.path.join(file_dir,file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    with open(file_path, 'wb') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_path

def dump_upload_file_into_db(file_path, user, perm_obj, filter_conf, form):
    values = []
    with open(file_path, 'r') as source:
        for line in source:
            line = line.strip()
            values.append(line)
    values_str = ','.join(["('%s')" %v for v in values])

    # create temporary table
    db_conn = connections[perm_obj.db_conf]
    db_cur = db_conn.cursor().cursor
    tmp_zlreports_table_name = 'tmp_zlreports_table_%s_%s' %(user.id, perm_obj.name.replace('-','_'))
    tmp_table_sql = """
        DROP TABLE IF EXISTS %s;
        CREATE TEMPORARY TABLE IF NOT EXISTS %s (
            tmp_filed varchar(128) NOT NULL
        );
        INSERT INTO %s VALUES %s;
    """ %tuple([tmp_zlreports_table_name,] * 3 + ['%s',])
    db_cur.execute(tmp_table_sql % values_str)

    # execute SQL
    sql_conf = perm_obj.SQL_conf.replace(' tmp_zlreports_table ', ' %s '%tmp_zlreports_table_name)
    if filter_conf:
        sql_conf = parse_filter_conf(filter_conf,sql_conf,form)

    db_cur.execute(sql_conf)
    query_data, header_data = dictfetchall(db_cur)
    header_data = [i.values()[0] for i in header_data]

    output_data = []
    if query_data:
        for item in query_data:
            tmp_output = []
            for k in header_data:
                tmp_output.append(str(item[k.encode('utf8')]) if item[k.encode('utf8')] is not None else '')
            output_data.append(tmp_output)

    # drop temporary table
    drop_tmp_table_sql = """
        DROP TABLE IF EXISTS %s;
    """ %tmp_zlreports_table_name
    db_cur.execute(drop_tmp_table_sql)
    db_cur.close()

    return output_data, header_data, sql_conf

