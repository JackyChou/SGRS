#coding:utf-8
import os

MODE = os.environ.get('MODE', 'dev')

if MODE == 'production':
    from deploy_settings import *
else:
    from dev_settings import *
try:
    from local_settings import *
except ImportError:
    pass

