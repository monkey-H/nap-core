from orchestration import config
from orchestration.database import database_update

class Moosefs(object):
	"""
	moosefs for a project
	"""

	def __init__(self, username, password):
		self.volume = self.get_volume(username, password)

	def set_volume(self, username, password):
		database_update.set_volume(username, password)

	def get_volume(self, username, password):
		return database_update.get_volume(username, password)
