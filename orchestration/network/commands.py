from orchestration import config
from orchestration.database import database_update

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
		database_update.set_net(username, password)

	def get_net(self, username, password):
		return database_update.get_net(username, password)
