import MySQLdb
from orchestration import config

class Moosefs(object):
	"""
	moosefs for a project
	"""

	def __init__(self, username, password):
		self.volume = self.get_volume(username, password)

	def set_volume(self, username, password):
		db = MySQLdb.connect(config.database_url, username, password, username)
		cursor = db.cursor()
		cursor.execute("insert into info(volume) values(%s) where name='%s'" % (username, username))
		db.commit()
		db.close()
		return True

	def get_volume(self, username, password):
	    db = MySQLdb.connect(config.database_url, username, password, username)
	    cursor = db.cursor()
	    cursor.execute("select volume from info where name='%s'" % username)
	    data = cursor.fetchone()
	    db.close()
	    return data
