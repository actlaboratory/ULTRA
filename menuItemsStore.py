# -*- coding: utf-8 -*-
#menu items store
#Copyright (C) 2019 Yukio Nozawa <personal@nyanchangames.com>

#wx のメニューのrefを一括管理してくれる便利な人
import win32file
import wx

class _MenuItemsStore(object):
	"""このクラスは、外からインスタンス化してはいけません。"""
	def __init__(self):
		self.refs={}

	def _getRef(self,identifier):
		identifier=identifier.upper()
		try:
			ref=self.refs[identifier]
		except KeyError:#なかったら作る
			ref=wx.NewIdRef()
			self.refs[identifier]=ref
		#end なかったから作った
		return ref.GetValue()

_store=_MenuItemsStore()

def getRef(identifier):
	"""文字列から、対応するメニューのrefを取得する。なかったら、作ってから帰す。"""
	return _store._getRef(identifier)
