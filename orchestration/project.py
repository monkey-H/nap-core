from __future__ import absolute_import
from __future__ import unicode_literals

import logging
from functools import reduce

import paramiko
import os
import MySQLdb
import random
from orchestration.database import database_update
from orchestration.moosefs import commands as mfs_commands
from orchestration.network import commands as net_commands

from orchestration.moosefs.commands import Moosefs
from orchestration.network.commands import Net

from docker.errors import APIError
from docker.errors import NotFound

from .config import ConfigurationError
from .config import get_service_name_from_net
from .const import DEFAULT_TIMEOUT
from .const import LABEL_ONE_OFF
from .const import LABEL_PROJECT
from .const import LABEL_SERVICE
from .container import Container
from .legacy import check_for_legacy_containers
from .service import ConvergenceStrategy
from .service import parse_volume_from_spec
from .service import nap_parse_volume_from_spec
from .service import Service
from .service import VolumeFromSpec
from .utils import parallel_execute

import sys

log = logging.getLogger(__name__)
# database_ip = '192.168.56.101'

def sort_service_dicts(services):
    # Topological sort (Cormen/Tarjan algorithm).
    unmarked = services[:]
    temporary_marked = set()
    sorted_services = []

    def get_service_names(links):
        return [link.split(':')[0] for link in links]

    def get_service_names_from_volumes_from(volumes_from):
        return [
            parse_volume_from_spec(volume_from).source
            for volume_from in volumes_from
        ]

    def get_service_dependents(service_dict, services):
        name = service_dict['name']
        return [
            service for service in services
            if (name in get_service_names(service.get('links', [])) or
                name in get_service_names_from_volumes_from(service.get('volumes_from', [])) or
                name == get_service_name_from_net(service.get('net')))
        ]

    def visit(n):
        if n['name'] in temporary_marked:
            if n['name'] in get_service_names(n.get('links', [])):
                raise DependencyError('A service can not link to itself: %s' % n['name'])
            if n['name'] in n.get('volumes_from', []):
                raise DependencyError('A service can not mount itself as volume: %s' % n['name'])
            else:
                raise DependencyError('Circular import between %s' % ' and '.join(temporary_marked))
        if n in unmarked:
            temporary_marked.add(n['name'])
            for m in get_service_dependents(n, services):
                visit(m)
            temporary_marked.remove(n['name'])
            unmarked.remove(n)
            sorted_services.insert(0, n)

    while unmarked:
        visit(unmarked[-1])

    return sorted_services


class Project(object):
    """
    A collection of services.
    """
    links = []
    def __init__(self, name, services, client, use_networking=False, network_driver=None):
        self.name = name
        self.links = []
        self.services = services
        self.client = client
        self.use_networking = use_networking
        self.network_driver = network_driver
        self.net = ""
        self.volume = ""

    def labels(self, one_off=False):
        return [
            '{0}={1}'.format(LABEL_PROJECT, self.name),
            '{0}={1}'.format(LABEL_ONE_OFF, "True" if one_off else "False"),
        ]


    @classmethod
    def nap_from_dicts(cls, username, password, name, service_dicts, client_list, use_networking=False, network_driver=None):
        """
        Construct a ServiceCollection from a list of dicts representing services.
        """
        project = cls(name, [], client_list, use_networking=use_networking, network_driver=network_driver)
        project.net = Net(username, password)
        project.volume = Moosefs(username, password).volume

        if use_networking:
            remove_links(service_dicts)

        for srv_dict in service_dicts:
            if not 'container_name' in srv_dict:
                srv_dict['container_name'] = srv_dict['name']
            srv_dict['hostname'] = username + '-' + name + '-' + srv_dict['container_name']

    	for srv_dict in service_dicts:
            if 'command' in srv_dict:
                command = srv_dict['command']
                if "{{" in command:
    	            for s_dict in service_dicts:
                        before = s_dict['container_name']
                        after = username + "-" + name + "-" + before
                        before = "{{" + before + "}}"
                        command = command.replace(before, after)
    	        srv_dict['command'] = command

        for service_dict in sort_service_dicts(service_dicts):
            l = project.nap_get_links(service_dict)
            log.info('from_dicts service_dict: %s', service_dict)
            if len(l):
                cls.links.append(l);
            index = random.randint(0,1)
            cc = client_list[index]

            # a = database(username, password)
            # service_dict['volumes_from'] = a.get_volume()

            # log.info(a.get_volume())
            # service_dict['volumes_from'] = database_update.get_volume(username, password)
            # service_dict['volumes_from'] = mfs_commands.get_volume(username, password)
            service_dict['volumes_from'] = project.volume
            print project.volume

            log.info(service_dict)

            volumes_from = project.nap_get_volumes_from(service_dict, cc)
            # net = Net(a.get_net())
            # net = project.nap_net(service_dict, username, password)
            net = project.net

            database_update.create_service(username, password, service_dict['container_name'], index, name)

            log.info("===============")

            service_dict['name'] = username + "-" + name + "-" + service_dict['name']
            service_dict['container_name'] = username + "-" + name + "-" + service_dict['container_name']

            if 'ports' in service_dict:
                ports = service_dict['ports']
                if not '4200' in ports:
                    ports.append('4200')
                    service_dict['ports'] = ports
            else:
                ports = []
                ports.append('4200')
                service_dict['ports'] = ports

            log.info(service_dict)

            project.services.append(
                Service(
                    client_list=cc,
                    project=name,
                    use_networking=use_networking,
                    links=[],
                    net=net,
                    volumes_from=volumes_from,
                    **service_dict))
        return project

    @property
    def service_names(self):
        return [service.name for service in self.services]

    def get_service(self, name):
        """
        Retrieve a service by name. Raises NoSuchService
        if the named service does not exist.
        """
        for service in self.services:
            if service.name == name:
                return service

        raise NoSuchService(name)

    def validate_service_names(self, service_names):
        """
        Validate that the given list of service names only contains valid
        services. Raises NoSuchService if one of the names is invalid.
        """
        valid_names = self.service_names
        for name in service_names:
            if name not in valid_names:
                raise NoSuchService(name)

    def get_services(self, service_names=None, include_deps=False):
        """
        Returns a list of this project's services filtered
        by the provided list of names, or all services if service_names is None
        or [].

        If include_deps is specified, returns a list including the dependencies for
        service_names, in order of dependency.

        Preserves the original order of self.services where possible,
        reordering as needed to resolve dependencies.

        Raises NoSuchService if any of the named services do not exist.
        """
        if service_names is None or len(service_names) == 0:
            return self.get_services(
                service_names=self.service_names,
                include_deps=include_deps
            )
        else:
            unsorted = [self.get_service(name) for name in service_names]
            services = [s for s in self.services if s in unsorted]

            if include_deps:
                services = reduce(self._inject_deps, services, [])

            uniques = []
            [uniques.append(s) for s in services if s not in uniques]
            return uniques

#return a->b like [(a,b,link1),(a,c,link2)]
    def nap_get_links(self, service_dict):
        links = []
        if 'links' in service_dict:
            for link in service_dict.get('links', []):
                if ':' in link:
                    service_name, link_name = link.split(':', 1)
#                    log.info("get_links- service name: " + service_name)
#                    log.info("get_links- link name: " + link_name)
                else:
                    service_name, link_name = link, None
                try:
#                    log.info('get_links- %s->%s, %s', service_dict.get('name'), service_name, link_name)
                    links.append((service_dict.get('name'), service_name, link_name))
                except NoSuchService:
                    raise ConfigurationError(
                        'Service "%s" has a link to service "%s" which does not '
                        'exist.' % (service_dict['name'], service_name))
            del service_dict['links']
        #log.info('len: %d',len(links))
        return links

    def nap_get_volumes_from(self, service_dict, client):
        volumes_from = []
        if 'volumes_from' in service_dict:
            for volume_from_config in service_dict.get('volumes_from', []):
                volume_from_spec = parse_volume_from_spec(volume_from_config)
                # Get service
                try:
                    service_name = self.get_service(volume_from_spec.source)
                    volume_from_spec = VolumeFromSpec(service_name, volume_from_spec.mode)
                except NoSuchService:
                    try:
                        container_name = Container.from_id(client, volume_from_spec.source)
                        volume_from_spec = VolumeFromSpec(container_name, volume_from_spec.mode)
                    except APIError:
                        raise ConfigurationError(
                            'Service "%s" mounts volumes from "%s", which is '
                            'not the name of a service or container.' % (
                                service_dict['name'],
                                volume_from_spec.source))
                volumes_from.append(volume_from_spec)
            del service_dict['volumes_from']
        # volume_from_spec = nap_parse_volume_from_spec()
        # volumes_from.append(volume_from_spec)
        return volumes_from

    def start(self, service_names=None, **options):
        for service in self.get_services(service_names):
            service.start(**options)

    def stop(self, service_names=None, **options):
        parallel_execute(
            objects=self.containers(service_names),
            obj_callable=lambda c: c.stop(**options),
            msg_index=lambda c: c.name,
            msg="Stopping"
        )

    def pause(self, service_names=None, **options):
        for service in reversed(self.get_services(service_names)):
            service.pause(**options)

    def unpause(self, service_names=None, **options):
        for service in self.get_services(service_names):
            service.unpause(**options)

    def kill(self, service_names=None, **options):
        parallel_execute(
            objects=self.containers(service_names),
            obj_callable=lambda c: c.kill(**options),
            msg_index=lambda c: c.name,
            msg="Killing"
        )

    def remove_stopped(self, service_names=None, **options):
        all_containers = self.containers(service_names, stopped=True)
        stopped_containers = [c for c in all_containers if not c.is_running]
        parallel_execute(
            objects=stopped_containers,
            obj_callable=lambda c: c.remove(**options),
            msg_index=lambda c: c.name,
            msg="Removing"
        )

    def restart(self, service_names=None, **options):
        for service in self.get_services(service_names):
            service.restart(**options)

    def build(self, service_names=None, no_cache=False, pull=False):
        for service in self.get_services(service_names):
            if service.can_be_built():
                service.build(no_cache, pull)
            else:
                log.info('%s uses an image, skipping' % service.name)

    def up(self,
           service_names=None,
           start_deps=True,
           strategy=ConvergenceStrategy.changed,
           do_build=True,
           timeout=DEFAULT_TIMEOUT,
           detached=False):

        services = self.get_services(service_names, include_deps=start_deps)

        for service in services:
            service.remove_duplicate_containers()

        plans = self._get_convergence_plans(services, strategy)

        if self.use_networking:
            self.ensure_network_exists()

        list = [
            container
            for service in services
            for container in service.execute_convergence_plan(
                plans[service.name],
                do_build=do_build,
                timeout=timeout,
                detached=detached
            )
        ]

        log.info("========")
        for item in list:
            tt = item.client.exec_create(container=item.name, cmd='shellinaboxd -t -b')
            item.client.exec_start(exec_id=tt, detach=True)
            # tt = item.client.exec_create(container=item.name, cmd='/bin/bash -c \"echo \\\"%s    %s\\\" >> /etc/hosts\"' % (item.ip, item.name))
            # item.client.exec_start(exec_id=tt, detach=True)
            # command = 'useradd admin && echo -e "admin\nadmin" | passwd admin'
            # tttt = item.client.exec_create(container=item.name, cmd='touch /useradd', stdout=True)
            # item.client.exec_start(exec_id=tttt, detach=True)
            # ttt = item.client.exec_create(container=item.name, cmd="/bin/bash -c \"echo \\\"hello\\\"\\\" > /hello\"")
            # ttt = item.client.exec_create(container=item.name, cmd='/bin/bash -c "echo \\"useradd admin && echo -e \\\"admin\\\\nadmin\\\" | passwd admin\\" > /useradd"')
            # useradd admin && echo -e adminnadmin | passwd admin
            ttt = item.client.exec_create(container=item.name, cmd='/bin/bash -c \"useradd admin && echo -e \\\"admin\\\\nadmin\\\" | passwd admin\"')
            item.client.exec_start(exec_id=ttt, detach=True, stream=True, tty=True)

#         for ll in Project.links:
#             for link in ll:
#                 a = link[0]
#                 b = link[1]
#                 cl = link[2]
#
#                 for c in list:
#                     if c.name == a:
#                         ca = c
#                     if c.name == b:
#                         cb = c
#
#                 hostlist = ca.client.base_url.split(':')
#                 hostname = hostlist[1].split('//')[1]
# #                log.info('up- hostname: ' + hostname)
#                 username = 'root'
#                 paramiko.util.log_to_file('syslogin.log')
#
#                 client = paramiko.SSHClient()
#                 client.load_system_host_keys()
#                 private_key = os.path.expanduser('/home/monkey/.ssh/id_rsa')
#                 key = paramiko.RSAKey.from_private_key_file(private_key)
#                 client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#
#                 client.connect(hostname=hostname, username=username, pkey=key)
#                 client.exec_command('echo "' + cb.ip + '    ' + cb.name + '" >> /var/lib/docker/containers/' + ca.id + '/hosts')
#                 client.exec_command('echo "' + cb.ip + '    ' + cl + '" >> /var/lib/docker/containers/' + ca.id + '/hosts')

#        for c in list:
#            log.info('up- container: %s', c)
#            log.info('up- container name: ' + c.name)
#            log.info('up- container id: ' + c.id)
#            log.info('up- container ip: ' + c.ip)
#            #client.exec_command('echo "' + c.ip + '    ' + c.name + '" >> /var/lib/docker/containers/' + list[0].id + '/hosts')

        return list

    def _get_convergence_plans(self, services, strategy):
        plans = {}

        for service in services:
            updated_dependencies = [
                name
                for name in service.get_dependency_names()
                if name in plans
                and plans[name].action == 'recreate'
            ]

            if updated_dependencies and strategy.allows_recreate:
                log.debug('%s has upstream changes (%s)',
                          service.name,
                          ", ".join(updated_dependencies))
                plan = service.convergence_plan(ConvergenceStrategy.always)
            else:
                plan = service.convergence_plan(strategy)

            plans[service.name] = plan

        return plans

    def pull(self, service_names=None, ignore_pull_failures=False):
        for service in self.get_services(service_names, include_deps=False):
            service.pull(ignore_pull_failures)

    def containers(self, service_names=None, stopped=False, one_off=False):
        if service_names:
            self.validate_service_names(service_names)
        else:
            service_names = self.service_names

        containers = list(filter(None, [
            Container.from_ps(self.client, container)
            for container in self.client.containers(
                all=stopped,
                filters={'label': self.labels(one_off=one_off)})]))

        def matches_service_names(container):
            return container.labels.get(LABEL_SERVICE) in service_names

        if not containers:
            check_for_legacy_containers(
                self.client,
                self.name,
                self.service_names,
            )

        return [c for c in containers if matches_service_names(c)]

    def get_network(self):
        try:
            return self.client.inspect_network(self.name)
        except NotFound:
            return None

    def ensure_network_exists(self):
        # TODO: recreate network if driver has changed?
        if self.get_network() is None:
            log.info(
                'Creating network "{}" with driver "{}"'
                .format(self.name, self.network_driver)
            )
            self.client.create_network(self.name, driver=self.network_driver)

    def remove_network(self):
        network = self.get_network()
        if network:
            self.client.remove_network(network['id'])

    def _inject_deps(self, acc, service):
        dep_names = service.get_dependency_names()

        if len(dep_names) > 0:
            dep_services = self.get_services(
                service_names=list(set(dep_names)),
                include_deps=True
            )
        else:
            dep_services = []

        dep_services.append(service)
        return acc + dep_services


def remove_links(service_dicts):
    services_with_links = [s for s in service_dicts if 'links' in s]
    if not services_with_links:
        return

    if len(services_with_links) == 1:
        prefix = '"{}" defines'.format(services_with_links[0]['name'])
    else:
        prefix = 'Some services ({}) define'.format(
            ", ".join('"{}"'.format(s['name']) for s in services_with_links))

    log.warn(
        '\n{} links, which are not compatible with Docker networking and will be ignored.\n'
        'Future versions of Docker will not support links - you should remove them for '
        'forwards-compatibility.\n'.format(prefix))

    for s in services_with_links:
        del s['links']


class NoSuchService(Exception):
    def __init__(self, name):
        self.name = name
        self.msg = "No such service: %s" % self.name

    def __str__(self):
        return self.msg


class DependencyError(ConfigurationError):
    pass
