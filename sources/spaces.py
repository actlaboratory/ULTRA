# twitter spaces module for ULTRA

import json
import pickle
import re
import requests
import sys
import time
import traceback
import tweepy
import wx

from logging import getLogger

import constants
import errorCodes
import globalVars
import recorder
import simpleDialog
import sources.base
import twitterService

interval = 15

class Spaces(sources.base.SourceBase):
	name = "Spaces"
	friendlyName = _("Twitter スペース")
	index = 1

	def __init__(self):
		super().__init__()
		self.log = getLogger("%s.%s" % (constants.LOG_PREFIX, "sources.spaces"))
		self.setStatus(_("未接続"))
		self.guestToken: str
		self.initialized = 0
		self.tokenManager = TokenManager()
		self.client: tweepy.Client
		self.users = UserList()
		self.shouldExit = False
		self.notified = []

	def initialize(self):
		result = self.getGuestToken()
		if result != errorCodes.OK:
			self.showError(result)
			return False
		if not self.tokenManager.load():
			simpleDialog.dialog(_("Twitterアカウント連携"), _("ブラウザを起動し、Twitterアカウントの連携を行います。"))
			if not self.tokenManager.authorize():
				return False
			if not self.tokenManager.save():
				simpleDialog.errorDialog(_("認証情報の保存に失敗しました。"))
				return False
		self.client = tweepy.Client(consumer_key=constants.TWITTER_CONSUMER_KEY, consumer_secret=constants.TWITTER_CONSUMER_SECRET, access_token=self.tokenManager.getAccessToken(), access_token_secret=self.tokenManager.getAccessTokenSecret(), return_type=dict)
		self.initialized = 1
		return super().initialize()

	def getGuestToken(self):
		headers = {
			"authorization": constants.TWITTER_BEARER
		}
		try:
			response = requests.post("https://api.twitter.com/1.1/guest/activate.json", headers=headers)
		except Exception as e:
			self.log.error(traceback.format_exc())
			return errorCodes.CONNECTION_ERROR
		try:
			response = response.json()
			guestToken = response["guest_token"]
		except Exception as e:
			self.log.error(traceback.format_exc())
			return errorCodes.INVALID_RECEIVED
		self.log.debug("guest_token: " + guestToken)
		self.guestToken = guestToken
		return errorCodes.OK

	def run(self):
		if self.initialized == 0 and not self.initialize():
			return
		globalVars.app.hMainView.addLog(_("接続完了"), _("スペースの監視を開始しました。"), self.friendlyName)
		globalVars.app.hMainView.menu.CheckMenu("SPACES_ENABLE", True)
		globalVars.app.hMainView.menu.EnableMenu("HIDE")
		self.setStatus(_("接続済み"))
		while not self.shouldExit:
			self._process()
			time.sleep(interval)
			wx.YieldIfNeeded()

	def _process(self):
		pass

	def exit(self):
		self.shouldExit = True
		globalVars.app.hMainView.menu.EnableMenu("HIDE", False)
		globalVars.app.hMainView.addLog(_("切断"), _("Twitterとの接続を切断しました。"), self.friendlyName)
		globalVars.app.hMainView.menu.CheckMenu("SPACES_ENABLE", False)
		self.setStatus(_("未接続"))

	def checkSpaceStatus(self, users):
		try:
			ret = self.client.get_spaces(user_ids=users)
			print(ret)
		except Exception as e:
			self.log.error(e)

	def recFromUrl(self, url):
		spaceId = self.getSpaceIdFromUrl(url)
		if spaceId is None:
			self.log.error("Space ID not found: " + url)
			return errorCodes.INVALID_URL
		metadata = self.getMetadata(spaceId)
		if type(metadata) == int:
			self.showError(metadata)
			return
		if metadata.isEnded():
			self.log.debug("is ended: " + metadata)
			return errorCodes.SPACE_ENDED
		mediaKey = metadata.getMediaKey()
		if mediaKey == errorCodes.INVALID_RECEIVED:
			self.log.error("Media key not found: " + metadata)
			self.showError(errorCodes.INVALID_RECEIVED)
			return
		location = self.getMediaLocation(mediaKey)
		if type(location) == int:
			self.showError(location)
			return
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
		try:
			response = requests.get("https://twitter.com/i/api/graphql/jyQ0_DEMZHeoluCgHJ-U5Q/AudioSpaceById", params=params, headers=headers)
		except Exception as e:
			self.log.error(traceback.format_exc())
			return errorCodes.CONNECTION_ERROR
		try:
			metadata = response.json()
		except Exception as e:
			self.log.error(traceback.format_exc())
			return errorCodes.INVALID_RECEIVED
		return Metadata(metadata)

	def getMediaLocation(self, mediaKey):
		headers = {
			"authorization": constants.TWITTER_BEARER,
			"cookie": "auth_token="
		}
		try:
			response = requests.get("https://twitter.com/i/api/1.1/live_video_stream/status/" + mediaKey, headers=headers)
		except Exception as e:
			self.log.error(traceback.format_exc())
			return errorCodes.CONNECTION_ERROR
		try:
			data = response.json()
			return data["source"]["location"]
		except Exception as e:
			self.log.error(traceback.format_exc())
			return errorCodes.INVALID_RECEIVED

	def showError(self, code):
		if code == errorCodes.CONNECTION_ERROR:
			simpleDialog.errorDialog(_("Twitterとの接続に失敗しました。インターネット接続に問題がない場合は、しばらくたってから再度お試しください。この問題が再度発生する場合は、開発者までお問い合わせください。"))
		elif code == errorCodes.INVALID_RECEIVED:
			simpleDialog.errorDialog(_("Twitterからの応答が不正です。開発者までご連絡ください。"))

	def getUser(self, user, showNotFound=True):
		try:
			ret = self.client.get_user(username=user, user_auth=True)
		except (tweepy.TweepyException, tweepy.HTTPException) as e:
			self.log.error(e)
			if showNotFound:
				simpleDialog.errorDialog(_("指定されたユーザ名が正しくありません。"))
			return
		if "error" in ret.keys():
			self.log.error(ret)
			if showNotFound:
				simpleDialog.errorDialog(_("指定されたユーザが見つかりません。"))
			return
		return ret["data"]

class Metadata:
	# デバッグ用に、メタデータをファイルに書き出す
	debug = False
	def __init__(self, metadata):
		self._metadata = metadata
		if self.debug and not globalVars.app.GetFrozenStatus():
			import datetime
			import os
			if not os.path.exists("spaces_metadata_dumps"):
				os.mkdir("spaces_metadata_dumps")
			with open(os.path.join("spaces_metadata_dumps", datetime.datetime.now().strftime("%Y%m%d_%H%M%S.txt")), "w", encoding="utf-8") as f:
				json.dump(self._metadata, f, ensure_ascii=False, indent="\t")

	def getMediaKey(self):
		try:
			return self._metadata["data"]["audioSpace"]["metadata"]["media_key"]
		except KeyError as e:
			return errorCodes.INVALID_RECEIVED

	def getUserName(self):
		return self._metadata["data"]["audioSpace"]["metadata"]["creator_results"]["result"]["legacy"]["screen_name"]

	def getStartedTime(self):
		return int(self._metadata["data"]["audioSpace"]["metadata"]["started_at"] / 1000)

	def getSpaceId(self):
		return self._metadata["data"]["audioSpace"]["metadata"]["rest_id"]

	def isEnded(self):
		return self._metadata["data"]["audioSpace"]["metadata"]["state"] == "Ended"

	def __str__(self):
		return json.dumps(self._metadata, ensure_ascii=False, indent=None)

class TokenManager:
	def __init__(self):
		self._file = constants.AC_SPACES
		self._token = None
		self._tokenSecret = None
		self.log = getLogger("%s.%s" % (constants.LOG_PREFIX, "spaces.tokenManager"))

	def authorize(self):
		result = twitterService.getToken()
		if result is None:
			return False
		self._token, self._tokenSecret = result
		return True

	def load(self):
		try:
			with open(self._file, "rb") as f:
				self._token, self._tokenSecret = pickle.load(f)
		except Exception as e:
			self.log.error(traceback.format_exc())
			return False
		return True

	def save(self):
		try:
			with open(self._file, "wb") as f:
				pickle.dump((self._token, self._tokenSecret), f)
		except Exception as e:
			self.log.error(traceback.format_exc())
			return False
		return True

	def getAccessToken(self):
		return self._token

	def getAccessTokenSecret(self):
		return self._tokenSecret



class UserList:
	def __init__(self):
		self._file = constants.SPACES_USER_DATA
		self._data = {}
		self.log = getLogger("%s.%s" % (constants.LOG_PREFIX, "sources.spaces.userList"))
		self.load()

	def load(self):
		try:
			with open(self._file, "r", encoding="utf-8") as f:
				self._data = json.load(f)
				self.log.debug("loaded: " + self._file)
		except Exception as e:
			self.log.error(e)
	
	def save(self):
		if hasattr(sys, "frozen"):
			indent = None
		else:
			indent = "\t"
		try:
			with open(self._file, "w", encoding="utf-8") as f:
				json.dump(self._data, f, ensure_ascii=False, indent=indent)
				self.log.debug("saved: " + self._file)
		except Exception as e:
			self.log.error(e)
			simpleDialog.errorDialog(_("ユーザ情報の保存に失敗しました。"))

	def hasSpecificSetting(self, user):
		return self._data[user]["specific"]

	def getConfig(self, user):
		items = (
			"baloon",
			"record",
			"openBrowser",
			"sound",
		)
		config = {}
		if self.hasSpecificSetting(user):
			for i in items:
				config[i] = self._data[user][i]
			config["soundFile"] = self._data[user]["soundFile"]
		else:
			for i in items:
				config[i] = globalVars.app.config.getboolean("notification", i, False)
			config["soundFile"] = globalVars.app.config["notification"]["soundFile"]
		return config

	def getData(self):
		return self._data

	def setData(self, data):
		self._data = data

	def getUserIds(self):
		return self._data.keys()