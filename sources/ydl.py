# yt-dlp module for ULTRA

import datetime
import json
import logging

import yt_dlp

import constants
import recorder
from sources.base import SourceBase


class YDL(SourceBase):
	name = "ydl"
	friendlyName = _("その他のサービス（yt-dlp）")
	index = 1
	filetypes = {
		"b": _("動画"),
		"a": _("音声のみ"),
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
			# とりあえず動画に固定
			"format": "b",
			# ログ出力
			"logger": self.log,
		}
		with yt_dlp.YoutubeDL(options) as ydl:
			info = ydl.extract_info(url, False)
			with open("info.json", "w", encoding="utf-8") as f:
				json.dump(info, f, ensure_ascii=False, indent=1)
		r = recorder.Recorder(self, info["url"], "%(user)s(%(extractor)s)" % {"user": info["channel"], "extractor": info["extractor"]}, datetime.datetime.strptime(info["upload_date"], "%Y%m%d"), info["id"], header=info["http_headers"], userAgent="", ext=info["ext"])
		r.start()
