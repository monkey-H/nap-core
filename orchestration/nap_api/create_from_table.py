from orchestration.database import database_update
from orchestration import config
import os
from git import Repo

def create_project_from_table(username, password, project_name, table):
    if not database_update.project_exists(username, password, project_name):
        return False, "Project: %s already exists! try another name and try again" % project_name

    if os.path.exists('%s/%s/%s' % (config.base_path, username, project_name)):
        return False, "File: %s already exists! try anoter name and try again" % project_name

    project_path = config.base_path + '/' + username + '/' + project_name
    os.mkdir(project_path)

    compose_file = open(project_path + '/docker-compose.yml', 'w')
    for service in table:
        if not "service_name" in service:
            return False, "service does not has a name"

        compose_file.write(service["service_name"] + ":\n")

        if not "type" in service:
            return False, "service: %s does not has a type" % service["service_name"]

        if service["type"] == "mpi":
            compose_file.write("  image: docker.iwanna.xyz:5000/mpi:v1\n")
            write_yml(compose_file, project_path, service)
            slaves = service['slaves']
            for i in range(int(slaves)):
                compose_file.write("slave" + str(i) + ':\n')
                compose_file.write("  image: docker.iwanna.xyz:5000/mpi:v1\n")
                compose_file.write("  command: \'/usr/sbin/sshd -D\'\n")
            continue

        if service["type"] == "mapreduce":
            continue

        if service["type"] == "hbase":
            continue

        if service["type"] == "apache":
            compose_file.write("  image: docker.iwanna.xyz:5000/apache2:v1\n")
            write_yml(compose_file, project_path, service)
            continue

        if service["type"] == "mysql":
            compose_file.write("  image: docker.iwanna.xyz:5000/user_mysql:v1\n")
            write_yml(compose_file, project_path, service)
            continue

        if service["type"] == "maven":
            compose_file.write("  image: docker.iwanna.xyz:5000/maven:v1\n")
            write_yml(compose_file, project_path, service)
            continue

    compose_file.close()

def write_yml(compose_file, project_path, service):
    for item in service:
        if item == "service_name":
            continue

        if item == "links":
            links = service[item]
            compose_file.write("  " + item + ":\n")
            for link in links:
                compose_file.write("    - " + link + '\n')
            continue

        if item == "ports":
            ports = service[item]
            compose_file.write("  " + item + ":" + '\n')
            for port in ports:
                compose_file.write("    - " + str(port) + '\n')
            continue

        if item == "url":
            Repo.clone_from(service["url"], project_path)
            continue

        if item == "environment":
            environments = service[item]
            compose_file.write("  enviroments:\n")
            for environment in environments:
                compose_file.write('    - ' + environment + '=' + environments[environment] + '\n')
            continue

        if item == "slaves" or item == "type":
            continue;

        if item == "command":
            compose_file.write("  command: \'" + service["command"] + "\'\n")
            continue

        compose_file.write("  " + item + ": " + service[item] + '\n')
