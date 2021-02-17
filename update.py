# updater
# Copyright (C) 2020 Hiroki Fujii <hfujii@hisystron.com>

import requests
import wx
import constants
import errorCodes
import globalVars
import simpleDialog
import webbrowser
import os
import subprocess
import sys
from views import updateDialog
import time
import threading
import win32api
from logging import getLogger
import traceback

def getUpdaterVersion():
	""" return (pyVersion, exeVersion) """
	return ["1.0.0", _getFileVersion("./updater.exe")]

def _getFileVersion(filePath):
	info = win32api.GetFileVersionInfo(filePath, os.sep)
	ms = info['FileVersionMS']
	ls = info['FileVersionLS']
	version = '%d.%d.%d' % (win32api.HIWORD(ms), win32api.LOWORD(ms), win32api.HIWORD(ls))
	return version

def checkUpdate():
	""" アップデートダイアログを表示する """
	globalVars.update = update()
	globalVars.update.update()

class update(threading.Thread):
	def __init__(self):
		super().__init__()
		self.log=getLogger("%s.%s" % (constants.LOG_PREFIX,"update"))
		self.log.info("update initialized")
		self.needStop = False
		self.reserve = False

	def update(self, auto=False):
		self.log.info("called update auto = %s" % str(auto))
		if not hasattr(sys, "frozen"):
			self.log.info("update is unavailable reason: not supported")
			if not auto:
				simpleDialog.winDialog(_("アップデート"), _("このバージョンではアップデートを使用できません。"))
			return
		# アップデータチェック
		updaterCheck = False
		try:
			if getUpdaterVersion()[0] == getUpdaterVersion()[1]: updaterCheck = True
		except: pass
		if not updaterCheck:
			self.log.info("update is unavailable reason: updater not found")
			simpleDialog.winDialog(_("アップデート"), _("アップデータが利用できません。お手数ですが、再度ソフトウェアをダウンロードしてください。"))
			return
		self.log.info("starting to check update...")
		params = {
			"name": constants.APP_NAME,
			"updater_version": constants.UPDATER_VERSION,
			"version": constants.APP_VERSION
		}
		timeout = globalVars.app.config.getint("general", "timeout", 3)
		try:
			response = requests.get(constants.UPDATE_URL, params, timeout = timeout)
		except requests.exceptions.ConnectTimeout:
			if not auto:
				self.log.info("failed to check update reason: connection timed out")
				simpleDialog.winDialog(_("アップデート"), _("サーバーへの通信がタイムアウトしました。"))
			return
		except requests.exceptions.ConnectionError as e:
			print(e)
			self.log.info("failed to check update reason: connection is not successful")
			if not auto:
				simpleDialog.winDialog(_("アップデート"), _("サーバーへの接続に失敗しました。インターネット接続などをご確認ください"))
			return
		except:
			traceback.print_exc()
			self.log.info("an error has occurred.")
			if not auto:
				simpleDialog.errorDialog(_("サーバーとの通信中に不明なエラーが発生しました。"))
			return
		if not response.status_code == 200:
			self.log.info("failed to check update reason: the server returned invalid status code %d" % (response.status_code))
			if not auto:
				simpleDialog.winDialog(_("アップデート"), _("サーバーとの通信に失敗しました。"))
			return
		self.log.info("checking update succeeded. analyzing the response from the server...")
		self.info = response.json()
		code = self.info["code"]
		if code == errorCodes.UPDATER_LATEST:
			self.log.info("update was not done reason: this is the latest version")
			if not auto:
				simpleDialog.winDialog(_("アップデート"), _("現在のバージョンが最新です。アップデートの必要はありません。"))
			return
		elif code == errorCodes.UPDATER_BAD_PARAM:
			self.log.info("update was not done reason: Request parameter is invalid")
			if not auto:
				simpleDialog.winDialog(_("アップデート"), _("リクエストパラメーターが不正です。開発者まで連絡してください"))
			return
		elif code == errorCodes.UPDATER_NOT_FOUND:
			self.log.info("update was not done reason: not registered")
			if not auto:
				simpleDialog.winDialog(_("アップデート"), _("アップデーターが登録されていません。開発者に連絡してください。"))
			return
		elif code == errorCodes.UPDATER_NEED_UPDATE or errorCodes.UPDATER_VISIT_SITE:
			self.log.info("opening update dialog...")
			self.dialog = updateDialog.updateDialog()
			self.dialog.Initialize()
			self.dialog.Show()
		return

	def open_site(self):
		webbrowser.open(self.info["URL"])
		return

	def runUpdate(self):
		if not self.reserve: return #予約されていないアップデートはできない
		if os.path.exists("updater.exe"):
			self.log.info("executing updater...")
			pid = os.getpid()
			subprocess.Popen(("updater.exe", sys.argv[0], constants.UPDATER_WAKE_WORD, self._file_name, self.info["updater_hash"], str(pid)))
		else:
			self.log.info("updater not found")
			os.remove(self._file_name)			
			self.dialog.updater_notFound()
		

	def run(self):
		self.log.info("downloading update file...")
		url = self.info["updater_url"]
		self._file_name = "update_file.zip"
		response = requests.get(url, stream = True)
		total_size = int(response.headers["Content-Length"])
		wx.CallAfter(self.dialog.gauge.SetRange, (total_size))
		now_size = 0
		broken = False
		with open(self._file_name, mode="wb") as f:
			for chunk in response.iter_content(chunk_size = 1024):
				if self.needStop:
					broken = True
					print("broken!")
					break
				f.write(chunk)
				now_size += len(chunk)
				wx.CallAfter(self.dialog.gauge.SetValue, (now_size))
				wx.YieldIfNeeded()
		if broken:
			self.log.info("downloading update file has canceled by user")
			os.remove(self._file_name)
			wx.CallAfter(self.dialog.end)
			return
		self.log.info("update file downloaded")
		wx.CallAfter(self.dialog.end)
		self.reserve = True
		simpleDialog.winDialog(_("アップデート"), _("ダウンロードが完了しました。\nソフトウェア終了時に、自動でアップデートされます。"))
		return

	def exit(self):
		self.needStop = True
		return
