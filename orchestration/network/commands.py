import MySQLdb
from orchestration import config

class Net(object):
	"""
	network for a project.
	"""

	service_name = None

	def __init__(self, username, password):
		self.net = self.get_net(username, password)

	@property
	def id(self):
		return self.net

	mode = id

	def set_net(self, username, password):
		db = MySQLdb.connect(config.database_url, username, password, username)
		cursor = db.cursor()
		cursor.execute("insert into info(net) values(%s) where name='%s'" % (username, username))
		db.commit()
		db.close()
		return True

	def get_net(self, username, password):
	     db = MySQLdb.connect(config.database_url, username, password, username)
	     cursor = db.cursor()
	     cursor.execute("select net from info where name='%s'" % username)
	     data = cursor.fetchone()
	     db.close()
	     return data[0]
