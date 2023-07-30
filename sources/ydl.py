# yt-dlp module for ULTRA

import datetime
import json
import logging
import os
import sys
import traceback

import wx
import yt_dlp

import constants
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
		self.listManager = ListManager()

	def downloadVideo(self, url, skipExisting=False):
		try:
			info = self.extractInfo(url)
		except Exception as e:
			self.log.error(traceback.format_exc())
			wx.CallAfter(simpleDialog.errorDialog, _("動画情報の取得に失敗しました。\n詳細：%s") % e)
			return
		# ビデオ以外は現状サポートしていない
		_type = info.get("_type", "video")
		if _type != "video":
			self.log.error("unsupported: %s" % _type)
			wx.CallAfter(simpleDialog.errorDialog, _("%sのダウンロードは現在サポートされていません。") % _type)
			return
		url = info["url"]
		user = "%(user)s(%(extractor)s)" % {"user": info.get("uploader", "unknown_user"), "extractor": info.get("extractor", "unknown_service")}
		if "timestamp" in info.keys():
			time = info["timestamp"]
		elif "upload_date" in info.keys():
			time = datetime.datetime.strptime(info["upload_date"], "%Y%m%d")
		else:
			time = None
		id = info["id"]
		headers = info.get("http_headers", {})
		r = recorder.Recorder(self, url, user, time, id, header=headers, userAgent="", ext=info["ext"], skipExisting=skipExisting)
		r.start()

	def extractInfo(self, url):
		# yt-dlpのオプション
		options = {
			# 詳しいログを出す
			"verbose": True,
			# ダウンロードするファイル形式
			"format": self.getFiletype(),
			# ログ出力
			"logger": self.log,
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


class ListManager:
	def __init__(self):
		self.log = logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "ydl.listManager"))
		self._data = {}
		self.load()
		# ファイル作成を兼ねて保存
		self.save()

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

	def convertInfoToEntry(self, info, interval):
		key = "%s:%s" % (info["extractor"], info["id"])
		val = {
			"title": info["title"],
			"url": info["original_url"],
			"interval": interval,
		}
		ret = {key: val}
		return ret

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
		for key in rm:
			del self._data[key]
		self.save()
