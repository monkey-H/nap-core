import MySQLdb
from orchestration import config

def set_net(username, password):
	db = MySQLdb.connect(config.database_url, username, password, username)
	cursor = db.cursor()
	cursor.execute("insert into info(net) values(%s) where name='%s'" % (username, username))
	db.commit()
	db.close()
	return True

def get_net(username, password):
     db = MySQLdb.connect(config.database_url, username, password, username)
     cursor = db.cursor()
     cursor.execute("select net from info where name='%s'" % username)
     data = cursor.fetchone()
     db.close()
     return data[0]
