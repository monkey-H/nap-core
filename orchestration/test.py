#!/usr/bin/python

from orchestration.nap_api import app_info
from orchestration.database import database_update
from orchestration.nap_api import project_create

#print app_info.delete_user("mongo")
#print app_info.create_user("mongo", "mongo")
#print app_info.delete_user("mongo")
#
print app_info.destroy_project('mongo', 'mongo', 'test')
#print app_info.destroy_project('wangwy', 'wangwy', 'cdh')
#print project_create.create_project_from_url('mongo', 'mongo', 'test', 'git@github.com:monkey-H/test_argv.git')
#print project_create.create_project_from_url('wangwy', 'wangwy', 'cdh', 'git@github.com:co2y/cdh_app.git')
#print project_create.create_project_from_url('mongo', 'mongo', 'test', 'git@github.com:monkey-H/mrbs_app.git')
print project_create.create_project_from_url('mongo', 'mongo', 'test', 'git@github.com:monkey-H/web_app.git')

#di = {}
#for item in data[1]:
#    di[item] = 'hello'
#
#print project_create.replace_argv('apple', 'apple', '/home/monkey/Documents/filebrowser/apple/test', 'test', di)
#print app_info.project_list('wangwy', 'wangwy', 0, 3)
#print app_info.service_list('wangwy', 'wangwy', 'cdh')
print app_info.project_list('mongo', 'mongo', 0, 3)
print app_info.service_list('mongo', 'mongo', 'test')
