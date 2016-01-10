import app_info
import database_update
import project_create

print app_info.delete_user("mongo")
print app_info.create_user("mongo", "mongo")
#print app_info.delete_user("mongo")
#
#print app_info.destroy_project('apple', 'apple', 'test')
#print project_create.create_project_from_url('apple', 'apple', 'test', 'git@github.com:monkey-H/web_app.git')

#di = {}
#for item in data[1]:
#    di[item] = 'hello'
#
#print project_create.replace_argv('apple', 'apple', '/home/monkey/Documents/filebrowser/apple/test', 'test', di)
#print app_info.project_list('apple', 'apple', 0, 3)
#print app_info.service_list('apple', 'apple', 'test')
