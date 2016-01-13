# flake8: noqa
from .config import ConfigDetails
from .config import ConfigurationError
from .config import DOCKER_CONFIG_KEYS
from .config import find
from .config import get_service_name_from_net
from .config import load
from .config import merge_environment
from .config import parse_environment

log_path='/home/monkey/Documents/filebrowser/logspout_log/syslog'
database_url = '114.212.189.147'
c_version = '1.21'
split_mark = '-'
client_list = ['114.212.189.147:2376', '114.212.189.140:2376']
rootname = 'root'
rootpass = 'monkey'
hostname = 'monkey'
container_path = '/nap'
volume_image = 'docker.iwanna.xyz:5000/hmonkey/busybox'
project_path='/home/monkey/Documents/filebrowser'
base_path = '/home/monkey/Documents/filebrowser'
