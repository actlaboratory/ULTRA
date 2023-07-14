# yt-dlp module for ULTRA

import datetime
import json
import logging
import traceback

import yt_dlp

import constants
import recorder
import simpleDialog
from sources.base import SourceBase


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

	def download(self, url):
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
		try:
			with yt_dlp.YoutubeDL(options) as ydl:
				info = ydl.extract_info(url, False)
		except Exception as e:
			self.log.error(traceback.format_exc())
			simpleDialog.errorDialog(_("動画情報の取得に失敗しました。\n詳細：%s") % e)
			return
		# ビデオ以外は現状サポートしていない
		_type = info.get("_type", "video")
		if _type != "video":
			self.log.error("unsupported: %s" % _type)
			simpleDialog.errorDialog(_("%sのダウンロードは現在サポートされていません。") % _type)
			return
		r = recorder.Recorder(self, info["url"], "%(user)s(%(extractor)s)" % {"user": info["channel"], "extractor": info["extractor"]}, datetime.datetime.strptime(info["upload_date"], "%Y%m%d"), info["id"], header=info["http_headers"], userAgent="", ext=info["ext"])
		r.start()
