# twitter spaces module for ULTRA

from logging import getLogger

import constants
from sources.base import SourceBase

class Spaces(SourceBase):
	name = "TwitterSpaces"
	friendlyName = _("Twitter スペース")
	index = 1

	def __init__(self):
		super().__init__()
		self.log = getLogger("%s.%s" %(constants.LOG_PREFIX, "sources.spaces"))
		self.setStatus(_("準備完了"))
