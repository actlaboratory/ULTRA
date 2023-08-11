# yt-dlp module for ULTRA

import datetime
import json
import logging
import os
import sys
import threading
import time
import traceback

import wx
import yt_dlp

import constants
import globalVars
import recorder
import simpleDialog
from sources.base import SourceBase

# debug
# 0: 何もしない、1:info_jsonを保存
DEBUG = 0


class YDL(SourceBase):
	name = "ydl"
	friendlyName = _("その他のサービス（yt-dlp）")
	index = 1
	filetypes = {
		"b": _("動画"),
		"ba": _("音声のみ"),
	}
	defaultFiletype = "b"

	def __init__(self):
		super().__init__()
		self.log = logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "sources.ydl"))
		self.listManager = ListManager(self)
		self.initThread()
		self.exitFlag = False
		self.setStatus(_("一括ダウンロード無効"))

	def run(self):
		wx.CallAfter(globalVars.app.hMainView.menu.CheckMenu, "YDL_ENABLE", True)
		self.setStatus(_("一括ダウンロード有効"))
		while True:
			self.log.debug("outer loop")
			for key in self.listManager.getKeys():
				self.log.debug("inner loop key: %s" % key)
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
				lastTime = self.listManager.getLastTime(key)
				if lastTime and (datetime.datetime.fromtimestamp(lastTime) + datetime.timedelta(seconds=self.listManager.getInterval(key)) > datetime.datetime.now()):
					self.log.debug("skipped")
					time.sleep(3)
					# 終了すべきかどうか
					if self.exitFlag:
						self.log.debug("exit flag is set")
						break
					continue
				downloader = PlaylistDownloader(self, self.listManager.getUrl(key), key)
				downloader.start()
				time.sleep(3)
				# 終了すべきかどうか
				if self.exitFlag:
					self.log.debug("exit flag is set")
					break
			self.log.debug("inner loop ended")
			if self.exitFlag:
				self.exitFlag = False
				break

	def downloadVideo(self, url, skipExisting=False):
		try:
			info = self.extractInfo(url)
		except Exception as e:
			self.log.error(traceback.format_exc())
			wx.CallAfter(simpleDialog.errorDialog, _("動画情報の取得に失敗しました。\n詳細：%s") % e)
			return
		_type = info.get("_type", "video")
		if _type == "playlist":
			# redirect to Playlist Downloader
			self.log.debug("redirect to Playlist Downloader")
			entry = self.listManager.convertInfoToEntry(info, 3600, True)
			key = tuple(entry.keys())[0]
			if self.listManager.hasKey(key):
				wx.CallAfter(simpleDialog.errorDialog, _("このプレイリストは、一括ダウンロードURLとして登録されています。"))
				return
			self.exit()
			globalVars.app.hMainView.menu.EnableMenu("YDL_DOWNLOAD", False)
			globalVars.app.hMainView.menu.EnableMenu("YDL_MANAGE_LISTS", False)
			self.listManager.addEntry(entry)
			downloader = PlaylistDownloader(self, self.listManager.getUrl(key), key)
			downloader.start()
			return
		elif _type != "video":
			self.log.error("unsupported: %s" % _type)
			wx.CallAfter(simpleDialog.errorDialog, _("%sのダウンロードは現在サポートされていません。") % _type)
			return
		url = info["url"]
		user = "%(user)s(%(extractor)s)" % {"user": info.get("uploader", "unknown_user"), "extractor": info.get("extractor", "unknown_service")}
		if "timestamp" in info.keys():
			time = info["timestamp"]
		elif "upload_date" in info.keys() and info["upload_date"] is not None:
			time = datetime.datetime.strptime(info["upload_date"], "%Y%m%d")
		else:
			time = None
		id = info["id"]
		headers = info.get("http_headers", {})
		r = recorder.Recorder(self, url, user, time, id, header=headers, userAgent="", ext=info["ext"], skipExisting=skipExisting)
		r.start()
		return r

	def extractInfo(self, url):
		# yt-dlpのオプション
		options = {
			# 詳しいログを出す
			"verbose": True,
			# ダウンロードするファイル形式
			"format": self.getFiletype(),
			# ログ出力
			"logger": logging.getLogger("%s.%s:%d" % (constants.LOG_PREFIX, "sources.ydl.yt-dlp", int(time.time()))),
			# プレイリストの各アイテムをダウンロードしないようにする
			"extract_flat": "in_playlist",
		}
		with yt_dlp.YoutubeDL(options) as ydl:
			info = ydl.extract_info(url, False)
		# debug
		if DEBUG:
			with open("info_%s.json" % info["id"], "w", encoding="utf-8") as f:
				json.dump(info, f, ensure_ascii=False, indent="\t")
		return info

	def getPlaylistItems(self, url):
		try:
			info = self.extractInfo(url)
		except Exception as e:
			self.log.error(traceback.format_exc())
			wx.CallAfter(simpleDialog.errorDialog, _("プレイリストの取得に失敗しました。\n詳細：%s") % e)
			return
		ret = []
		for entry in info.get("entries", []):
			_type = entry.get("_type", "video")
			if _type == "playlist":
				ret += self.getPlaylistItems(entry["webpage_url"])
			elif _type == "url":
				ret.append(entry["url"])
		return ret

	def onStart(self, key):
		wx.CallAfter(globalVars.app.hMainView.addLog, _("プレイリストの保存"), _("処理開始：%s") % self.listManager.getTitle(key), self.friendlyName)
		self.listManager.onStart(key)

	def onFinish(self, key):
		wx.CallAfter(globalVars.app.hMainView.addLog, _("プレイリストの保存"), _("処理終了：%s") % self.listManager.getTitle(key), self.friendlyName)
		self.listManager.onFinish(key)

	def onCancel(self, key):
		wx.CallAfter(globalVars.app.hMainView.addLog, _("プレイリストの保存"), _("処理中止：%s") % self.listManager.getTitle(key), self.friendlyName)
		self.listManager.onCancel(key)

	def exit(self):
		wx.CallAfter(globalVars.app.hMainView.menu.CheckMenu, "YDL_ENABLE", False)
		self.exitFlag = True
		self.setStatus(_("一括ダウンロード無効"))


class ListManager:
	def __init__(self, ydl: YDL):
		self.ydl = ydl
		self.log = logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "sources.ydl.listManager"))
		self._data = {}
		self.load()
		# ファイル作成を兼ねて保存
		self.save()
		# 前回、processingフラグを消さずに終了していた場合に備えて、最初にすべて削除する
		self.clearProcessingFlags()
		# 一時的に追加したはずの項目が残っていれば削除
		self.clearTemporaryItems()

	def load(self):
		try:
			with open(constants.YDL_LIST_DATA, "r", encoding="utf-8") as f:
				self._data = json.load(f)
				self.log.info("loaded %d items" % len(self._data))
		except:
			self.log.warn("Failed to load list")
			self.log.error(traceback.format_exc())

	def save(self):
		if hasattr(sys, "frozen"):
			indent = None
		else:
			indent = "\t"
		try:
			with open(constants.YDL_LIST_DATA, "w", encoding="utf-8") as f:
				json.dump(self._data, f, ensure_ascii=False, indent=indent)
				self.log.info("Saved %s" % os.path.basename(constants.YDL_LIST_DATA))
		except:
			self.log.error("Failed to save list.\n" + traceback.format_exc())

	def convertInfoToEntry(self, info, interval, temporary=False):
		key = "%s:%s" % (info["extractor"], info["id"])
		# KeyValueSettingの仕様に合わせて、キーは小文字で管理する
		key = key.lower()
		val = {
			"title": info["title"],
			"url": info["original_url"],
			"interval": interval,
		}
		if temporary:
			val["temporary"] = True
		ret = {key: val}
		self.log.debug("converted entry: %s" % ret)
		return ret

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
		# 削除すべきプレイリストが処理中ならば停止させる
		activeDownloaders = getActiveDownloaders()
		for downloader in activeDownloaders:
			if downloader.getKey() in rm:
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
		if self.isTemporary(key):
			self.log.debug("remove temporary entry: %s" % key)
			del self._data[key]
		self.save()

	def onFinish(self, key):
		del self._data[key]["processing"]
		self._data[key]["last"] = time.time()
		if self.isTemporary(key):
			self.log.debug("remove temporary entry: %s" % key)
			del self._data[key]
			globalVars.app.hMainView.menu.EnableMenu("YDL_DOWNLOAD", True)
			globalVars.app.hMainView.menu.EnableMenu("YDL_MANAGE_LISTS", True)
			if globalVars.app.config.getboolean("ydl", "enable", True):
				self.ydl.initThread()
				self.ydl.start()
		self.save()

	def getKeys(self):
		return self._data.keys()

	def getInterval(self, key):
		return self._data[key]["interval"]

	def getLastTime(self, key):
		return self._data[key].get("last", None)

	def getUrl(self, key):
		return self._data[key]["url"]

	def getTitle(self, key):
		return self._data[key]["title"]

	def isProcessing(self, key):
		return "processing" in self._data[key]

	def isTemporary(self, key):
		return self._data[key].get("temporary", False)

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

	def clearTemporaryItems(self):
		self.log.debug("clearing temporary items...")
		for key in tuple(self._data.keys()):
			if "temporary" in self._data[key].keys():
				self.log.debug("clearing %s" % key)
				del self._data[key]
		self.log.debug("finished clearing temporary items")
		self.save()


class PlaylistDownloader(threading.Thread):
	def __init__(self, ydl: YDL, url: str, key:str):
		super().__init__(daemon=True)
		self.ydl = ydl
		self.key = key
		self.url = url
		self.exitFlag = False

	def run(self):
		self.ydl.onStart(self.key)
		urls = self.ydl.getPlaylistItems(self.url)
		cnt = 0
		total = len(urls)
		for url in urls:
			if self.exitFlag:
				return
			cnt += 1
			wx.CallAfter(globalVars.app.hMainView.addLog, _("プレイリストの保存"), _("処理中（%(title)s）：%(cnt)d/%(total)d") % {"title": self.ydl.listManager.getTitle(self.key), "cnt": cnt, "total": total}, self.ydl.friendlyName)
			r = self.ydl.downloadVideo(url, True)
			while r.is_alive():
				if self.exitFlag:
					return
				time.sleep(0.1)
		self.ydl.onFinish(self.key)

	def getKey(self):
		return self.key

	def exit(self):
		self.exitFlag = True
		self.ydl.onCancel(self.key)


def getActiveDownloaders():
	ret = []
	for t in threading.enumerate():
		if type(t) == PlaylistDownloader:
			ret.append(t)
	return ret
