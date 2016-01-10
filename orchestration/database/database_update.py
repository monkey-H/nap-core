from docker import Client
import MySQLdb

# database_url = '114.212.189.147'
# c_version = '1.21'
# split_mark = '-'
# client_list = ['114.212.189.147:2376', '114.212.189.140:2376']

def tuple_in_tuple(db_tuple):
    ret_data = []
    for item in db_tuple:
        ret_data.append(item[0])
    return ret_data

def get_net(username, password):
     db = MySQLdb.connect(config.database_url, username, password, username)
     cursor = db.cursor()
     cursor.execute("select net from info where name='%s'" % username)
     data = cursor.fetchone()
     db.close()
     return data[0]

def get_volume(username, password):
     db = MySQLdb.connect(config.database_url, username, password, username)
     cursor = db.cursor()
     cursor.execute("select volume from info where name='%s'" % username)
     data = cursor.fetchone()
     db.close()
     return data

def service_name_list(username, password, project_name):
    db = MySQLdb.connect(config.database_url, username, password, username)
    cursor = db.cursor()
    cursor.execute("select name from service where project = '%s'" % project_name)
    data = cursor.fetchall()
    db.close()
    if data == None:
        return None
    name_list = tuple_in_tuple(data)
    return name_list

def project_exists(username, password, project_name):
    db = MySQLdb.connect(config.database_url, username, password, username)
    cursor = db.cursor()
    cursor.execute("select name from project where name='%s'" % project_name)
    data = cursor.fetchone()
    db.close()

    if data != None:
        return False
    return True

def roll_back(username, password, project_name):
    db = MySQLdb.connect(config.database_url, username, password, username)
    cursor = db.cursor()

    logs = ''
    service_list = service_name_list(username, password, project_name)
    if not service_list == None:
        for service_name in service_list:
            url = machine_ip(username, password, project_name, service_name)
            if url == '-':
                continue
            cli = Client(base_url=url, version=config.c_version)
            full_name = username + config.split_mark + project_name + config.split_mark + service_name
            if container_exists(cli, full_name):
                logs = logs + full_name + '\n' + cli.logs(container=full_name) + '\n'
                cli.stop(container=full_name)
                cli.remove_container(container=full_name)
        cursor.execute("delete from service where project='%s'" % project_name)
        db.commit()
        db.close()

    return logs

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

def get_machine(username, password):
    db = MySQLdb.connect(config.database_url, username, password, username)
    cursor = db.cursor()
    cursor.execute("select ip from machine")
    data = cursor.fetchall()
    db.close()
    return tuple_in_tuple(data)

def create_service(username, password, service_name, service_id, project_name):
    db = MySQLdb.connect(config.database_url, username, password, username)
    cursor = db.cursor()
    cursor.execute("insert into service values('%s', %d, '%s')" % (service_name, service_id, project_name))
    db.commit()
    db.close()
