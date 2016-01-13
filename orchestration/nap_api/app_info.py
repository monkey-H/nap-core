import MySQLdb
import commands
import os
import shutil

from docker import Client
from orchestration import config

# c_version='1.21'
# split_mark = '-'
# rootname = 'root'
# rootpass = 'monkey'
# hostname = 'monkey'
# container_path = '/nap'
# volume_image = 'docker.iwanna.xyz:5000/hmonkey/busybox'
# database_url='114.212.189.147'
# client_list = ['114.212.189.147:2376', '114.212.189.140:2376']
# project_path='/home/monkey/Documents/filebrowser'

def tuple_in_tuple(db_tuple):
    ret_data = []
    for item in db_tuple:
        ret_data.append(item[0])
    return ret_data

def create_user(username, password):
    for client in config.client_list:
        # still need mfsmount
        a,b = commands.getstatusoutput("ssh %s@%s 'docker run -d --name %s -v %s/%s:%s %s'" % (config.hostname, client.split(":")[0], username + "_volume", config.project_path, username, config.container_path, config.volume_image))

    commands.getstatusoutput("ssh %s@%s 'docker network create -d overlay %s'" % (config.hostname, config.client_list[0].split(":")[0], username))
    commands.getstatusoutput("ssh %s@%s 'cd %s && mkdir %s'" % (config.hostname, config.client_list[0].split(":")[0], config.project_path, username))

    db = MySQLdb.connect(config.database_url, config.rootname, config.rootpass)
    cursor = db.cursor()
    cursor.execute("show databases;")
    database_list = cursor.fetchall()
    database_l = tuple_in_tuple(database_list)

    for user in database_l:
        if user == username:
            return False, 'username: %s already exists, please try another name' % username

    cursor.execute("create database %s;" % username)
    cursor.execute("create user '%s'@'%s' identified by '%s';" % (username, '%', password))
    cursor.execute("grant all on %s.* to '%s'@'%s';" % (username, username, '%'))
    db.commit()
    db.close()

    # create some tables for this user
    user_db = MySQLdb.connect(config.database_url, username, password, username)
    user_cursor = user_db.cursor()
    user_cursor.execute("create table info(name char(50) not null, net char(50), volume char(50));")
    user_cursor.execute("create table machine(id int unsigned not null, ip char(50));")
    user_cursor.execute(
        "create table project(id int unsigned not null auto_increment primary key, name char(50), url char(50));")
    user_cursor.execute("create table service(name char(50), machine int unsigned, project char(50));")
    user_cursor.execute("insert into info values('%s', '%s', '%s_volume');" % (username, username, username))
    client_id = 0
    for client in config.client_list:
        user_cursor.execute("insert into machine values(%d, '%s');" % (client_id, client))
        client_id += 1
    # user_cursor.execute("insert into machine values(0, '192.168.56.105:2376');")
    # user_cursor.execute("insert into machine values(1, '192.168.56.106:2376');")
    user_db.commit()
    user_db.close()

    # something else need, net volume_from and soon
    # for client in config.client_list:
    #     # still need mfsmount
    #     a,b = commands.getstatusoutput("ssh %s@%s 'docker run -d --name %s -v %s/%s:%s %s'" % (config.hostname, client.split(":")[0], username + "_volume", config.project_path, username, config.container_path, volume_image))
    #
    # commands.getstatusoutput("ssh %s@%s 'docker network create -d overlay %s'" % (config.hostname, config.client_list[0].split(":")[0], username))
    # commands.getstatusoutput("ssh %s@%s 'cd %s && mkdir %s'" % (config.hostname, config.client_list[0].split(":")[0], config.project_path, username))

    return [True, "create user success"]

def delete_user(username):
    try:
        db = MySQLdb.connect(config.database_url, config.rootname, config.rootpass)
        cursor = db.cursor()
        cursor.execute('drop user %s' % username)
        cursor.execute('drop database %s' % username)
        cursor.execute('flush privileges')
        db.commit()
        db.close()
    except MySQLdb.OperationalError as e:
        return False, e.message

    for client in config.client_list:
        # still need mfsmount
        a,b = commands.getstatusoutput("ssh %s@%s 'docker rm %s'" % (config.hostname, client.split(":")[0], username + "_volume"))

    commands.getstatusoutput("ssh %s@%s 'cd %s && rm -r %s'" % (config.hostname, client.split(":")[0], config.project_path, username))
    a,b = commands.getstatusoutput("ssh %s@%s 'docker network rm %s'" % (config.hostname, config.client_list[0].split(":")[0], username))

    return True, 'Delete user success'

def service_name_list(username, password, project_name):
    db = MySQLdb.connect(config.database_url, username, password, username)
    cursor = db.cursor()
    cursor.execute("select name from service where project='%s'" % project_name)
    data = cursor.fetchall()
    db.close()
    if data == None:
        return None
    else:
        return tuple_in_tuple(data)

def service_list(username, password, project_name):
    name_list = service_name_list(username, password, project_name)
    if name_list == None:
        return '-'

    srv_list = []
    for service_name in name_list:
        url = machine_ip(username, password, project_name, service_name)
        cli = Client(base_url=url, version=config.c_version)
        full_name = username + config.split_mark + project_name + config.split_mark + service_name
        if not container_exists(cli, full_name):
            print 'no container: %s in hosts' % full_name
            continue

        srv_dict = {}
        srv_dict['name'] = service_name
        srv_dict['ip'] = str(url).split(":")[0]
        srv_dict['status'] = get_status(username, password, project_name, service_name)
        ports = get_port(username, password, project_name, service_name)
        if ports == None:
            srv_dict['port'] = '-'
            srv_dict['shell'] = '-'
        elif not len(ports):
            srv_dict['port'] = '-'
            srv_dict['shell'] = '-'
        else:
            expose_port = []
            for key in ports:
                if not ports[key] == None:
                    if key == '4200/tcp':
                        srv_dict['shell'] = ports[key][0]['HostPort']
                    else:
                        expose_port.append(ports[key][0]['HostPort'])
                else:
                    expose_port.append('-')
            srv_dict['port'] = expose_port
        srv_list.append(srv_dict)
    return srv_list

def project_list(username, password, begin, length):
    db = MySQLdb.connect(config.database_url, username, password, username)
    cursor = db.cursor()
    cursor.execute("select name, url from project limit %s,%s" % (begin, length))
    data = cursor.fetchall()
    db.close()
    return data

def destroy_project(username, password, project_name):
    if os.path.exists('%s/%s/%s' % (config.project_path, username, project_name)):
        shutil.rmtree('%s/%s/%s' % (config.project_path, username, project_name))

    db = MySQLdb.connect(config.database_url, username, password, username)
    cursor = db.cursor()
    cursor.execute("select name from project where name ='%s'" % project_name)
    data = cursor.fetchone()
    if data == None:
        db.close()
        return True, 'Destroy project: %s success' % project_name

    data = service_name_list(username, password, project_name)
    for service_name in data:
        url = str(machine_ip(username, password, project_name, service_name))
        if url == '-':
            continue
        cli = Client(base_url=url, version=config.c_version)
        full_name = username + config.split_mark + project_name + config.split_mark + service_name
        if container_exists(cli, full_name):
            cli.stop(container=full_name)
            cli.remove_container(container=full_name)

    cursor.execute("delete from service where project = '%s'" % project_name)
    cursor.execute("delete from project where name = '%s'" % project_name)
    db.commit()
    db.close()

    return True, 'Destroy project: %s success' % project_name

def get_status(username, password, project_name, service_name):
    cip = machine_ip(username, password, project_name, service_name)
    if cip == '-':
        return 'no such project or service'

    cli = Client(base_url=cip, version=config.c_version)
    full_name = username + config.split_mark + project_name + config.split_mark + service_name

    if container_exists(cli, full_name):
        detail = cli.inspect_container(full_name)
        return detail['State']['Status']
    else:
        return 'no such container'

def get_port(username, password, project_name, service_name):
    cip = machine_ip(username, password, project_name, service_name)
    if cip == '-':
        return 'no such project or service'

    cli = Client(base_url=cip, version=config.c_version)
    full_name = username + config.split_mark + project_name + config.split_mark + service_name

    if container_exists(cli, full_name):
        detail = cli.inspect_container(full_name)
        return detail['NetworkSettings']['Ports']
    else:
        return 'no such container'

def container_exists(cli, container_name):
    containers = cli.containers(all=True)
    for k in containers:
        if '/' + container_name in k['Names']:
            return True
    return False

def machine_ip(username, password, project_name, service_name):
    db = MySQLdb.connect(config.database_url, username, password, username)
    cursor = db.cursor()
    cursor.execute("select machine from service where name = '%s' and project = '%s'" % (service_name, project_name))
    data = cursor.fetchone()
    if data == None:
        db.close()
        return '-'
    else:
        cursor.execute("select ip from machine where id = %s" % data[0])
        data = cursor.fetchone()
        db.close()
        return data[0]

def get_logs(username, password, project_name, service_name):
    cip = machine_ip(username, password, project_name, service_name)
    if cip == '-':
        return 'no such project or service'
    cli = Client(base_url=cip, version=config.c_version)
    full_name = username + config.split_mark + project_name + config.split_mark + service_name

    if container_exists(cli, full_name):
        logs = cli.logs(container=full_name)
        return logs
    else:
        return 'no such container'
