# SGRS #

一个简单的PostgreSQL通用报表系统

## 系统说明 ##

1. 页面说明
    - 本系统只有admin管理页面,登陆页,注销页,统计首页,具体的统计页面,及组合统计页面。
    - 统计首页根据用户角色的不同,返回该用户可用的统计功能入口。
    - 具体的统计页面,根据相应的统计功能配置,动态生成表单和生成SQL语句,并执行查询,返回结果。
    - 组合统计页面,是将一些统计功能组合起来，将查询结果在同一页面展示。

2. 动态表单
    - `utils` 中的 `parse_dynamic_form` 会对配置数据进行预处理；
    - `forms` 中的 `DynamicForm`,会根据预处理数据,生成表单,并供前端页面使用。

3. 生成SQL相关方法
    - 相关方法均在 `utils` 文件中
    - `parse_sql` 提供给 `view` 调用的总方法
    - `parse_filter_conf` 负责将过滤配置替换成相应的SQL
    - `run_sql` 负责执行SQL

4. 查询结果缓存
    - 当后台接收到表单数据后,会根据 **功能权限的唯一key** 和 **表单查询参数** 生成`cache_key`,并写入`query_result_cache`表中,缓存时间为10分钟。分页功能其实是基于缓存数据做的分页。

5. 下载相关结果
    - 使用 tablib 库生成供下载的xls文件
    - 如果查询结果行数大于5万行,则相应的xls文件会分成多个sheet,每个sheet包含5万条数据
    - 每次从数据库查询数据,都会在/stats/download文件内生成相应的xls文件,文件名为 `username_per_key_timestamp.xls` ,如 用户jacky执行了query-promo-channel功能,则文件名为 `jacky_query-promo-channel_1453106863.xls`

6. 分页显示
    - 目前的分页显示其实是基于缓存数据的,并不是在SQL中添加limit子句实现。
    - 如果结果大于5万行，且未使用分页或分页行数小于1千，则强制使用分页，每页1千行。

7. 管理员预览SQL功能
    - 管理员用户在使用功能权限时,会提供预览SQL选项,供管理人员调试使用。此时并不执行该SQL语句。

## 部署说明 ##

1. 第三方库需求
    - Django==1.8
    - psycopg2==2.6.1
    - tablib==0.10.0

2. 建立相关表格
    - 配置数据库，并建立相关表
   
            python manage.py migrate
            python manage.py createcachetable query_result_cache

3. Django配置文件
    - `common_settings.py` 是通用配置
    
    - `dev_settings.py` 是基于通用配置的 **开发环境** 配置
    
    - `deploy_settings.py` 是基于通用配置的 **生产环境** 配置
    
    - `settings.py` 会根据全局变量 `MODE` 来对 `dev_settings.py` 和 `deploy_settings.py` 进行选择,默认使用 `dev_settings.py`
    
    - `MODE='dev'` 使用开发配置,`MODE='production'` 使用生产配置
    
    - 如在本地开发时,想使用生产配置调试,则使用
    
            MODE=production python manage.py runserver 0:8888

    - 目前部署使用 apache + nginx + wsgi 方式,在 wsgi.py 文件中,设置了MODE全局
    
            import os
            os.environ.setdefault("MODE", "production")

## 数据配置说明 ##

1. 先配置`ReportType`（报表类型），再配置`ReportPermission`（报表权限）；

2. 如有需要，配置`ReportPermissionCombination`（组合报表）；

3. 配置`SGRSRole`（角色），并将相关的`ReportPermission`和`ReportPermissionCombination`进行关联；

4. 配置`SGRSUser`（用户）；

5. 配置`SGRSUserAssignment`（用户分配），具体分配`SGRSUser`（用户）所属`SGRSRole`（角色）。

## `ReportPermission`字段说明 ##
- `name`权限名称，只允许字母和 - 组成

- `description`功能描述

- `report_type`报表所属类型

- `db_conf`查询的数据库配置,需是Django的settings文件中已配置的数据库

- `SQL_conf`该功能的SQL语句,目前可传入由`filter_conf`生成的where子句条件。

- `filter_conf`配置SQL语句中的where子句条件,json格式。下面的配置表示SQL中的 **{{c1}}** 和 **{{c2}}** 条件。配置详细说明见下文。如:

        {
            "c1":
                {
                    "field":"username",
                    "name":"姓名",
                    "required":"0",
                    "type":"text",
                    "operate":"like"
                },
            "c2":
                {
                    "field":"is_superuser",
                    "name":"是否管理员",
                    "required":"1",
                    "type":"choice",
                    "value":[
                        ["True","是"],
                        ["Flase","否"]],
                    "operate":"="
                }
        }


## `filter_conf`说明 ##

- `filter_conf`的key应与SQL语句的where子句对应。如SQL语句中有`where {{c1}} and {{c2}}`,则过滤配置应有`c1`和`c2`的配置。

- 配置详解
    + `field`:字段名称,生成where子句条件时作为列名
    
    + `name`:显示名称,供表单展示时使用
    
    + `required`:是否必须,字符串"0"或"1","1"为必须。当required为"0",且表单无上传值时,会用"1=1"代替该条件
    
    + `type`:表单类型,会根据此值在前端生成相应的表单,目前支持如下类型：

        <table>
            <tr>
                <th>类型</th><th>对应表单类型</th>
            </tr>
            <tr>
                <td>choice</td><td>下拉框</td>
            </tr>
            <tr>
                <td>mchoice</td><td>复选框</td>
            </tr>
            <tr>
                <td>text</td><td>文本框</td>
            </tr>
            <tr>
                <td>date</td><td>日期</td>
            </tr>
            <tr>
                <td>datetime</td><td>日期+时间</td>
            </tr>
        </table>

    + `value`:供`choice`和`mchoice`使用的可选值,由list组成的list。以下配置表示了一组备选值,其中 `True` 表示上传值, `是` 是表单展示给用户的值。如:

            [
                ["True","是"],
                ["Flase","否"]
            ]

    + `isoformat`:供date使用的选项,值为`0`或`1`(字符或数据均可)。当`isoformat`为`0`时,后台会将表单提交的`2015-09-06 00:00:00`转换`20150906`进行查询。为`1`时,则使用表单提交`2015-09-06 00:00:00`。
    
    + `operate`:相应的操作符,如`<`,`>`,`=`。目前各类型允许的操作如下：

        <table>
            <tr>
                <th>类型</th><th>对应表单类型</th><th>允许的操作</th>
            </tr>
            <tr>
                <td>choice</td><td>下拉框</td><td>['=',]</td>
            </tr>
            <tr>
                <td>mchoice</td><td>复选框</td><td>['in',]</td>
            </tr>
            <tr>
                <td>text</td><td>文本框</td><td>['=','<','<=','>','>=','like']</td>
            </tr>
            <tr>
                <td>date</td><td>日期</td><td>['=','<','<=','>','>=']</td>
            </tr>
            <tr>
                <td>datetime</td><td>日期+时间</td><td>['=','<','<=','>','>=']</td>
            </tr>
        </table>
    
    + `dblink`:供dblink查询条件使用。为`0`时,为普通的查询条件,会拼接成 `ctime > '2015-09-06'`。为`1`时,由于dblink的特殊性,拼接的条件为 `ctime > ''2015-09-06''`,注意是这里是两个单引号。

- 过滤条件生成,执行SQL前,会根据配置信息生成对应的条件,格式为：`field operate 表单上传值`,如 `id > 10`

## 功能权限配置示例 ##

待续
