# 17LIVE module for ULTRA

import json
import logging
import os
import requests
import threading
import time
import traceback
import urllib.parse
import wx

import constants
import errorCodes
import globalVars
import recorder
import simpleDialog
from sources.base import SourceBase


class Live17(SourceBase):
	name = "17live"
	friendlyName = "17LIVE"
	index = 2
	filetypes = {
		"mp4": _("動画"),
		"mp3": _("音声のみ"),
	}
	defaultFiletype = "mp4"

	def __init__(self):
		super().__init__()
		self.log = logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "sources.17live"))
		self.exitFlag = False
		self.setStatus(_("準備完了"))

	def run(self):
		pass

	def getArchiveList(self, url):
		# アーカイブ一覧ページURLの形式：https://17.live/ja/profile/r/ルームID/…
		try:
			room_id = self.parseRoomUrl(url)
		except Exception as e:	
			wx.CallAfter(simpleDialog.errorDialog, str(e))
			return
		self.log.debug("getArchiveList:room_id=" + str(room_id))

		try:
			user = self.getUserFromRoomId(room_id)
		except Exception as e:	
			wx.CallAfter(simpleDialog.errorDialog, str(e))
			return
		self.log.debug("getArchiveList:user_id=" + str(user["user_id"]))
		ArchiveDownloader(self, user["user_id"], user["user_display_name"]).start()

	def parseRoomUrl(self, url):
		parsed = urllib.parse.urlparse(url)
		if parsed.netloc != "17.live":
			raise Exception(_("入力されたURLは17LIVEのものではありません。"))
		path = parsed.path.split("/")
		if len(path) <= 4 or path[2] != "profile" or path[3] != "r":
			raise Exception(_("入力されたURLはユーザーページのものではありません。"))
		return path[4]

	def getUserFromRoomId(self, room_id):
		session = requests.session()
		session.get("https://17.live", headers=getHeaders())
		url = "https://wap-api.17app.co/api/v1/user/room/" + str(room_id)

		self.log.debug("getUserIdFromRoomId:" + url)
		response = session.get(url, headers=getHeaders())
		self.log.debug("getUserIdFromRoomId:" + str(response.status_code))
		self.log.debug("getUserIdFromRoomId:" + response.text)
		response_data = json.loads(response.text)
		return {
			"user_id": response_data["userID"],
			"user_display_name": response_data["displayName"]
		}

	def downloadArchive(self, url, skipExisting=False, silent=False, join=False):
		# アーカイブURLの形式：https://17.live/ja/profile/u/userID/video/archiveID
		try:
			parameters = self.parseArchiveUrl(url)
		except Exception as e:	
			wx.CallAfter(simpleDialog.errorDialog, str(e))
			return
		try:
			info = self.getArchiveInfo(parameters["archive_id"])
		except Exception as e:
			self.log.error(traceback.format_exc())
			wx.CallAfter(simpleDialog.errorDialog, _("動画情報の取得に失敗しました。\n詳細：%s") % e)
			return
		self.recordArchive(info, skipExisting, join, info["userInfo"]["displayName"], info["userInfo"]["userID"])

	# 一括の場合と単体の場合でinfoの中身が微妙に違っていて、片方にはuserInfoが入っていないのでそこだけ別の引数でもらっている
	def recordArchive(self, info, skipExisting, join, user_display_name, user_id):
		if info["isDeleted"]:
			# TODO:通知する
			self.log.debug("downloadArchive:this live was deleted")
			return

		url = info["videoURL"]
		self.log.debug("downloadArchive:" + url)
		time = info["createdAt"]
		user = "%(user)s(%(id)s)" % {"user": user_display_name, "id": user_id}
		id = info["streamID"]

		r = recorder.Recorder(self, url, user, time, id, header=getHeaders(), userAgent="", ext=self.getFiletype(), skipExisting=skipExisting)
		if r.shouldSkip():
			return errorCodes.RECORD_SKIPPED
		r.start()
		if join:
			r.join()

	def parseArchiveUrl(self, url):
		parsed = urllib.parse.urlparse(url)
		if parsed.netloc != "17.live":
			raise Exception(_("入力されたURLは17LIVEのものではありません。"))
		path = parsed.path.split("/")
		if len(path) != 7 or path[2] != "profile" or path[3] not in ("u", "r") or path[5] != "video" or not path[6].startswith("archive-"):
			raise Exception(_("入力されたURLはアーカイブページのものではありません。"))
		return {
			"user_id": path[4],
			"archive_id": path[6],
		}

	def getArchiveInfo(self, archive_id):
		session = requests.session()
		session.get("https://17.live", headers=getHeaders())
		url = "https://wap-api.17app.co/api/v1/archives/" + archive_id
		self.log.debug("getArchiveInfo:" + url)
		response = session.get(url, headers=getHeaders())
		self.log.debug("getArchiveInfo:" + str(response.status_code))
		self.log.debug("getArchiveInfo:" + response.text)
		return json.loads(response.text)

	def onStart(self, key):
		pass

	def onFinish(self, key):
		pass

	def onCancel(self, key):
		pass

	def exit(self):
		self.exitFlag = True

class ArchiveDownloader(threading.Thread):
	def __init__(self, live17, user_id, user_display_name):
		super().__init__(daemon=True)
		self.log = logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "sources.17live"))
		self.live17 = live17
		self.user_id = user_id
		self.user_display_name = user_display_name
		self.hasError = 0

	def getUserArchiveList(self):
		cursor = ""
		result = []

		session = requests.session()
		session.get("https://17.live", headers=getHeaders())
		while True:
			url = "https://wap-api.17app.co/api/v1/cells?tab=archive&userID=" + self.user_id + "&cursor=" + cursor + "&sortBy=createdAt&count=10&visibility=1"

			self.log.debug("getArchiveList:" + url)
			response = session.get(url, headers=getHeaders())
			self.log.debug("getArchiveList:" + str(response.status_code))
			self.log.debug("getArchiveList:" + response.text)
			receive_data = json.loads(response.text)

			result += receive_data["cells"]
			cursor = receive_data["cursor"]
			if cursor == "":
				break
			time.sleep(1)
		return result


	def run(self):
		wx.CallAfter(globalVars.app.hMainView.addLog, _("一括録画"), _("アーカイブ一覧を取得しています。"), self.live17.friendlyName)
		movies = self.getUserArchiveList()
		movies.reverse()	# 古い方からダウンロードしたい

		wx.CallAfter(globalVars.app.hMainView.addLog, _("一括録画"), _("処理を開始します。対象ライブ数：%i") % len(movies), self.live17.friendlyName)
		count = 0
		for info in movies:
			result = self.live17.recordArchive(info["archive"], True, True, self.user_display_name, self.user_id)
			time.sleep(1)
			if result != errorCodes.RECORD_SKIPPED:
				wx.CallAfter(globalVars.app.hMainView.addLog, _("一括録画"), _("録画を実行しました。"), self.live17.friendlyName)
			count += 1
			continue
		wx.CallAfter(globalVars.app.hMainView.addLog, _("一括録画"), _("完了。%i件録画しました。") % count, self.live17.friendlyName)

def getHeaders():
	return {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
		"Referer": "https://17.live/",
		"language": "JP",
		"deviceType": "WEB",
		"userIpRegion": "JP",
		"Origin": "https://17.live",
	}
