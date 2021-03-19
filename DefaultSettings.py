# -*- coding: utf-8 -*-
#default config

from ConfigManager import *


class DefaultSettings:
	def get():
		config = ConfigManager()
		config["general"]={
			"language": "ja-JP",
			"fileVersion": "100",
			"locale": "ja-JP",
			"autoHide": False,
			"minimizeOnExit": True,
		}
		config["view"]={
			"font": "bold 'ＭＳ ゴシック' 22 windows-932",
			"colorMode":"normal"
		}
		config["speech"]={
			"reader" : "AUTO"
		}
		config["mainView"]={
			"sizeX": "800",
			"sizeY": "600",
		}
		config["notification"] = {
			"baloon": True,
			"record": True,
			"openBrowser": False,
			"sound": False,
			"soundFile": "",
		}
		config["twitcasting"] = {
			"enable": False,
			"saveComments": False,
		}
		config["record"] = {
			"dir": "output\\%source%",
			"createSubDir": True,
			"subDirName": "%user%",
			"fileName": "%user%_%year%%month%%day%_%hour%%minute%%second%",
			"extension": "ts",
		}
		config["proxy"] = {
			"useManualSetting": False,
			"server": "",
			"port": 8080
		}
		return config

initialValues={}
"""
	この辞書には、ユーザによるキーの削除が許されるが、初回起動時に組み込んでおきたい設定のデフォルト値を設定する。
	ここでの設定はユーザの環境に設定ファイルがなかった場合のみ適用され、初期値として保存される。
"""
