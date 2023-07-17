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
		# debug
		if DEBUG:
			with open("info_%s.json" % info["id"], "w", encoding="utf-8") as f:
				json.dump(info, f, ensure_ascii=False, indent="\t")
		# ビデオ以外は現状サポートしていない
		_type = info.get("_type", "video")
		if _type != "video":
			self.log.error("unsupported: %s" % _type)
			simpleDialog.errorDialog(_("%sのダウンロードは現在サポートされていません。") % _type)
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
		r = recorder.Recorder(self, url, user, time, id, header=headers, userAgent="", ext=info["ext"])
		r.start()
