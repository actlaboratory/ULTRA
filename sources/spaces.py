# twitter spaces module for ULTRA

import json
import re
import requests

from logging import getLogger

import constants
import errorCodes
import recorder
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

	def recFromUrl(self, url):
		spaceId = self.getSpaceIdFromUrl(url)
		metadata = self.getMetadata(spaceId)
		location = self.getMediaLocation(metadata.getMediaKey())
		r = recorder.Recorder(self, location, metadata.getUserName(), metadata.getStartedTime(), metadata.getSpaceId())
		r.start()

	def getSpaceIdFromUrl(self, url):
		ret = re.search(r"(?<=spaces/)\w*", url)
		if not ret:
			return None
		return ret.group(0)

	def getMetadata(self, spaceId):
		params = {
			"variables": json.dumps({
				"id": spaceId,
				"isMetatagsQuery": False,
				"withSuperFollowsUserFields": True,
				"withUserResults": True,
				"withBirdwatchPivots": False,
				"withReactionsMetadata": False,
				"withReactionsPerspective": False,
				"withSuperFollowsTweetFields": True,
				"withReplays": True,
				"withScheduledSpaces": True
			})
		}
		headers = {
			"authorization": constants.TWITTER_BEARER,
			"x-guest-token": self.guestToken,
		}
		response = requests.get("https://twitter.com/i/api/graphql/jyQ0_DEMZHeoluCgHJ-U5Q/AudioSpaceById", params=params, headers=headers)
		metadata = response.json()
		return Metadata(metadata)

	def getMediaLocation(self, mediaKey):
		headers = {
			"authorization": constants.TWITTER_BEARER,
			"cookie": "auth_token="
		}
		response = requests.get("https://twitter.com/i/api/1.1/live_video_stream/status/" + mediaKey, headers=headers)
		data = response.json()
		return data["source"]["location"]

class Metadata:
	# デバッグ用に、メタデータをファイルに書き出す
	debug = False
	def __init__(self, metadata):
		self._metadata = metadata
		if self.debug:
			import datetime
			import os
			if not os.path.exists("spaces_metadata_dumps"):
				os.mkdir("spaces_metadata_dumps")
			with open(os.path.join("spaces_metadata_dumps", datetime.datetime.now().strftime("%Y%m%d_%H%M%S.txt")), "w", encoding="utf-8") as f:
				json.dump(self._metadata, f, ensure_ascii=False, indent="\t")

	def getMediaKey(self):
		return self._metadata["data"]["audioSpace"]["metadata"]["media_key"]

	def getUserName(self):
		return self._metadata["data"]["audioSpace"]["metadata"]["creator_results"]["result"]["legacy"]["screen_name"]

	def getStartedTime(self):
		return int(self._metadata["data"]["audioSpace"]["metadata"]["started_at"] / 1000)

	def getSpaceId(self):
		return self._metadata["data"]["audioSpace"]["metadata"]["rest_id"]
