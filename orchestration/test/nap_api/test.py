from orchestration.nap_api.project_create import create_project_from_url
from orchestration.nap_api.app_info import destroy_project 

print destroy_project('mongo', 'mongo', 'test')
print create_project_from_url('mongo', 'mongo', 'test', 'git@github.com:monkey-H/web_app.git')
