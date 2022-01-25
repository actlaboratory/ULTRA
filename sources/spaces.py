# twitter spaces module for ULTRA

import re
import requests

from logging import getLogger

import constants
import errorCodes
from sources.base import SourceBase

class Spaces(SourceBase):
	name = "TwitterSpaces"
	friendlyName = _("Twitter スペース")
	index = 1

	def __init__(self):
		super().__init__()
		self.log = getLogger("%s.%s" %(constants.LOG_PREFIX, "sources.spaces"))
		self.setStatus(_("準備完了"))
		self.guestToken: str
		self.initialized = 0

	def initialize(self):
		if self.getGuestToken() != errorCodes.OK:
			return False
		self.initialized = 1
		return super().initialize()

	def getGuestToken(self):
		headers = {
			"authorization": constants.TWITTER_BEARER
		}
		response = requests.post("https://api.twitter.com/1.1/guest/activate.json", headers=headers)
		response = response.json()
		guestToken = response["guest_token"]
		self.log.debug("guest_token: " + guestToken)
		self.guestToken = guestToken
		return errorCodes.OK

	def run(self):
		if self.initialized == 0 and not self.initialize():
			return
