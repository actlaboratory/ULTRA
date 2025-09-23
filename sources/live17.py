# 17LIVE module for ULTRA

import datetime
import json
import logging
import os
import requests
import sys
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
		self.listManager = ListManager(self)
		self.initThread()
		self.exitFlag = False
		self.setStatus(_("準備完了"))

	def run(self):
		wx.CallAfter(globalVars.app.hMainView.menu.CheckMenu, "LIVE17_ENABLE", True)
		self.setStatus(_("一括ダウンロード有効"))
		while True:
			for key in self.listManager.getKeys():
				self.log.debug("auto download key: %s" % key)
				# 処理中なら何もしない
				if self.listManager.isProcessing(key):
					self.log.debug("%s is processing" % key)
					time.sleep(3)
					# 終了すべきかどうか
					if self.exitFlag:
						self.log.debug("exit flag is set")
						break
					continue
				# 次に処理すべき日時に達していなければ何もしない
				if (datetime.datetime.fromtimestamp(self.listManager.getLastTime(key)) + datetime.timedelta(seconds=self.listManager.getInterval(key)) > datetime.datetime.now()):
					self.log.debug("skipped")
					time.sleep(3)
					# 終了すべきかどうか
					if self.exitFlag:
						self.log.debug("exit flag is set")
						break
					continue
				downloader = ArchiveDownloader(self, key, self.listManager.getTitle(key))
				downloader.start()
				time.sleep(3)
				# 終了すべきかどうか
				if self.exitFlag:
					self.log.debug("exit flag is set")
					break
			if self.exitFlag:
				self.exitFlag = False
				break
			time.sleep(3)


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
		self.listManager.onStart(key)

	def onFinish(self, key):
		self.listManager.onFinish(key)

	def onCancel(self, key):
		self.listManager.onCancel(key)

	def exit(self):
		wx.CallAfter(globalVars.app.hMainView.menu.CheckMenu, "LIVE17_ENABLE", False)
		self.exitFlag = True
		self.setStatus(_("一括ダウンロード無効"))

class ArchiveDownloader(threading.Thread):
	def __init__(self, live17, user_id, user_display_name):
		super().__init__(daemon=True)
		self.log = logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "sources.17live"))
		self.live17 = live17
		self.user_id = user_id
		self.user_display_name = user_display_name
		self.exitFlag = False
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
		self.live17.onStart(self.user_id)
		movies = self.getUserArchiveList()
		movies.reverse()	# 古い方からダウンロードしたい

		wx.CallAfter(globalVars.app.hMainView.addLog, _("一括録画"), _("%(title)s：アーカイブ%(total)d件") % {"title": self.user_display_name, "total": len(movies)}, self.live17.friendlyName)
		count = 0
		for info in movies:
			if self.exitFlag:
				wx.CallAfter(globalVars.app.hMainView.addLog, _("一括録画"), _("処理中止　%i件録画しました。") % count, self.live17.friendlyName)
				return
			result = self.live17.recordArchive(info["archive"], True, True, self.user_display_name, self.user_id)
			time.sleep(1)
			if result != errorCodes.RECORD_SKIPPED:
				wx.CallAfter(globalVars.app.hMainView.addLog, _("一括録画"), _("録画を実行しました。"), self.live17.friendlyName)
				count += 1
			continue
		wx.CallAfter(globalVars.app.hMainView.addLog, _("一括録画"), _("完了　%i件録画しました。") % count, self.live17.friendlyName)
		self.live17.onFinish(self.user_id)

	def getUserId(self):
		return self.user_id

	def exit(self):
		self.exitFlag = True
		self.live17.onCancel(self.key)


def getHeaders():
	return {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
		"Referer": "https://17.live/",
		"language": "JP",
		"deviceType": "WEB",
		"userIpRegion": "JP",
		"Origin": "https://17.live",
	}

class ListManager:
	def __init__(self, live17: Live17):
		self.live17 = live17
		self.log = logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "sources.live17.listManager"))
		self._data = self.load()
		# ファイル作成を兼ねて保存
		self.save()
		# 前回、processingフラグを消さずに終了していた場合に備えて、最初にすべて削除する
		self.clearProcessingFlags()

	def load(self):
		try:
			with open(constants.LIVE17_LIST_DATA, "r", encoding="utf-8") as f:
				data = json.load(f)
				self.log.info("loaded %d items" % len(data))
				return data
		except:
			self.log.warn("Failed to load list")
			self.log.error(traceback.format_exc())
			return {}

	def save(self):
		if hasattr(sys, "frozen"):
			indent = None
		else:
			indent = "\t"
		try:
			with open(constants.LIVE17_LIST_DATA, "w", encoding="utf-8") as f:
				json.dump(self._data, f, ensure_ascii=False, indent=indent)
				self.log.info("Saved %s" % os.path.basename(constants.LIVE17_LIST_DATA))
		except:
			self.log.error("Failed to save list.\n" + traceback.format_exc())

	def addEntry(self, entry):
		self.log.debug("add: %s" % entry)
		self._data.update(entry)
		self.save()

	def getData(self):
		return self._data

	def setData(self, newData):
		self.log.debug("updating list...")
		for newKey1 in newData:
			if newKey1 not in self._data:
				self.log.debug("new key: %s" % newKey1)
				self._data[newKey1] = newData[newKey1]
				continue
			self.log.debug("existing key: %s" % newKey1)
			oldValue = self._data[newKey1]
			newValue = newData[newKey1]
			for newKey2 in newValue:
				if oldValue[newKey2] != newValue[newKey2]:
					self.log.debug("%s-%s: %s -> %s" % (newKey1, newKey2, oldValue[newKey2], newValue[newKey2]))
					oldValue[newKey2] = newValue[newKey2]
		rm = []
		for oldKey in self._data:
			if oldKey not in newData:
				self.log.debug("removed: %s" % oldKey)
				rm.append(oldKey)
		# 削除すべきユーザーが処理中ならば停止させる
		activeDownloaders = getActiveDownloaders()
		for downloader in activeDownloaders:
			if downloader.getUserId() in rm:
				downloader.exit()
		# 不要なエントリーを削除
		for key in rm:
			del self._data[key]
		self.save()

	def onStart(self, key):
		self._data[key]["processing"] = True
		self.save()

	def onCancel(self, key):
		del self._data[key]["processing"]
		self.save()

	def onFinish(self, key):
		del self._data[key]["processing"]
		self._data[key]["last"] = time.time()
		self.save()

	def getKeys(self):
		return self._data.keys()

	def getInterval(self, key):
		return self._data[key]["interval"]

	def getLastTime(self, key):
		return self._data[key].get("last", 0)

	def getUrl(self, key):
		return self._data[key]["url"]

	def getTitle(self, key):
		return self._data[key]["title"]

	def isProcessing(self, key):
		return "processing" in self._data[key]

	def hasKey(self, key):
		return key in self._data.keys()

	def clearProcessingFlags(self):
		self.log.debug("clearing processing flags...")
		for key in self._data.keys():
			if "processing" in self._data[key].keys():
				self.log.debug("clearing %s" % key)
				del self._data[key]["processing"]
		self.log.debug("finished clearing processing flags")
		self.save()

def getActiveDownloaders():
	ret = []
	for t in threading.enumerate():
		if type(t) == ArchiveDownloader:
			ret.append(t)
	return ret
