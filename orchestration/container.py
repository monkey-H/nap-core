from __future__ import absolute_import
from __future__ import unicode_literals

from functools import reduce

import six
import logging

from .const import LABEL_CONTAINER_NUMBER
from .const import LABEL_PROJECT
from .const import LABEL_SERVICE

log = logging.getLogger(__name__)

class Container(object):
    """
    Represents a Docker container, constructed from the output of
    GET /containers/:id:/json.
    """
    def __init__(self, client, dictionary, has_been_inspected=False):
        self.client = client
        self.ip = '0.0.0.0'
        self.dictionary = dictionary
        self.has_been_inspected = has_been_inspected
        self.log_stream = None

    @classmethod
    def from_ps(cls, client, dictionary, **kwargs):
        """
        Construct a container object from the output of GET /containers/json.
        """
        name = get_container_name(dictionary)
        if name is None:
            return None

        new_dictionary = {
            'Id': dictionary['Id'],
            'Image': dictionary['Image'],
            'Name': '/' + name,
        }
        return cls(client, new_dictionary, **kwargs)

    @classmethod
    def from_id(cls, client, id):
        log.info("from_id")
        log.info(client)
        log.info(id)
        return cls(client, client.inspect_container(id))
        # return cls(client[0],client[0].inspect_container(id))
    @classmethod
    def create(cls, client, **options):
        response = client.create_container(**options)
#	    log.info("response: " + response['Id'])
        details = client.inspect_container(response.get('Id'))
#	    log.info(details['NetworkSettings']['IPAddress'])
        c = cls.from_id(client, response['Id']);
        return c

    @property
    def id(self):
        return self.dictionary['Id']

    @property
    def image(self):
        return self.dictionary['Image']

    @property
    def image_config(self):
        return self.client.inspect_image(self.image)

    @property
    def short_id(self):
        return self.id[:10]

    @property
    def name(self):
        return self.dictionary['Name'][1:]

    @property
    def service(self):
        return self.labels.get(LABEL_SERVICE)

    @property
    def name_without_project(self):
        project = self.labels.get(LABEL_PROJECT)

        if self.name.startswith('{0}_{1}'.format(project, self.service)):
            return '{0}_{1}'.format(self.service, self.number)
        else:
            return self.name

    @property
    def number(self):
        number = self.labels.get(LABEL_CONTAINER_NUMBER)
        if not number:
            raise ValueError("Container {0} does not have a {1} label".format(
                self.short_id, LABEL_CONTAINER_NUMBER))
        return int(number)

    @property
    def ports(self):
        self.inspect_if_not_inspected()
        return self.get('NetworkSettings.Ports') or {}

    @property
    def human_readable_ports(self):
        def format_port(private, public):
            if not public:
                return private
            return '{HostIp}:{HostPort}->{private}'.format(
                private=private, **public[0])

        return ', '.join(format_port(*item)
                         for item in sorted(six.iteritems(self.ports)))

    @property
    def labels(self):
        return self.get('Config.Labels') or {}

    @property
    def log_config(self):
        return self.get('HostConfig.LogConfig') or None

    @property
    def human_readable_state(self):
        if self.is_paused:
            return 'Paused'
        if self.is_running:
            return 'Ghost' if self.get('State.Ghost') else 'Up'
        else:
            return 'Exit %s' % self.get('State.ExitCode')

    @property
    def human_readable_command(self):
        entrypoint = self.get('Config.Entrypoint') or []
        cmd = self.get('Config.Cmd') or []
        return ' '.join('sleep 5; ' + entrypoint + "service shellinabox start &&" + cmd)

    @property
    def environment(self):
        return dict(var.split("=", 1) for var in self.get('Config.Env') or [])

    @property
    def is_running(self):
        return self.get('State.Running')

    @property
    def is_paused(self):
        return self.get('State.Paused')

    @property
    def log_driver(self):
        return self.get('HostConfig.LogConfig.Type')

    @property
    def has_api_logs(self):
        log_type = self.log_driver
        return not log_type or log_type != 'none'

    def attach_log_stream(self):
        """A log stream can only be attached if the container uses a json-file
        log driver.
        """
        if self.has_api_logs:
            self.log_stream = self.attach(stdout=True, stderr=True, stream=True)

    def get(self, key):
        """Return a value from the container or None if the value is not set.

        :param key: a string using dotted notation for nested dictionary
                    lookups
        """
        self.inspect_if_not_inspected()

        def get_value(dictionary, key):
            return (dictionary or {}).get(key)

        return reduce(get_value, key.split('.'), self.dictionary)

    def get_local_port(self, port, protocol='tcp'):
        port = self.ports.get("%s/%s" % (port, protocol))
        return "{HostIp}:{HostPort}".format(**port[0]) if port else None

    def start(self, **options):
        log.info('start containers')
        re = self.client.start(self.id, **options)
        details = self.client.inspect_container(self.id)
        networks = details['NetworkSettings']['Networks']
        for key in networks:
            ip = networks[key]['IPAddress']
        self.ip = ip
        return re

    def stop(self, **options):
        return self.client.stop(self.id, **options)

    def pause(self, **options):
        return self.client.pause(self.id, **options)

    def unpause(self, **options):
        return self.client.unpause(self.id, **options)

    def kill(self, **options):
        return self.client.kill(self.id, **options)

    def restart(self, **options):
        return self.client.restart(self.id, **options)

    def remove(self, **options):
        return self.client.remove_container(self.id, **options)

    def rename_to_tmp_name(self):
        """Rename the container to a hopefully unique temporary container name
        by prepending the short id.
        """
        self.client.rename(
            self.id,
            '%s_%s' % (self.short_id, self.name)
        )

    def inspect_if_not_inspected(self):
        if not self.has_been_inspected:
            self.inspect()

    def wait(self):
        return self.client.wait(self.id)

    def logs(self, *args, **kwargs):
        return self.client.logs(self.id, *args, **kwargs)

    def inspect(self):
        self.dictionary = self.client.inspect_container(self.id)
        self.has_been_inspected = True
        return self.dictionary

    # TODO: only used by tests, move to test module
    def links(self):
        links = []
        for container in self.client.containers():
            for name in container['Names']:
                bits = name.split('/')
                if len(bits) > 2 and bits[1] == self.name:
                    links.append(bits[2])
        return links

    def attach(self, *args, **kwargs):
        return self.client.attach(self.id, *args, **kwargs)

    def __repr__(self):
        return '<Container: %s (%s)>' % (self.name, self.id[:6])

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.id == other.id

    def __hash__(self):
        return self.id.__hash__()


def get_container_name(container):
    if not container.get('Name') and not container.get('Names'):
        return None
    # inspect
    if 'Name' in container:
        return container['Name']
    # ps
    shortest_name = min(container['Names'], key=lambda n: len(n.split('/')))
    return shortest_name.split('/')[-1]