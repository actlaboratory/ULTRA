# -*- coding: utf-8 -*-
# hotkey mapping  manager
#Copyright (C) 2019-2020 yamahubuki <itiro.ishino@gmail.com>

import wx

import keymapHandlerBase
import menuItemsStore


def hotkeyHandler(event):
	"""
		同じref_idでメニューイベントとして投げなおすイベントハンドラ
		hotkeyのイベントはwx.KeyEventでくる
		デフォルト引数にしたいので上に書いている
	"""
	newEvent=wx.CommandEvent(wx.wxEVT_MENU,event.GetId())
	wx.PostEvent(event.GetEventObject().GetEventHandler(),newEvent)
	return


class HotkeyHandler(keymapHandlerBase.KeymapHandlerBase):
	"""
		ホットキーのマッピングを管理する
	"""

	def __init__(self, dict=None, filter=None):
		super().__init__(dict, filter, permitConfrict=permitConfrict)

	def makeEntry(self,ref,key,filter,log):
		"""
			ref(String)と、/区切りでない単一のkey(String)からwx.AcceleratorEntryを生成
		"""
		if menuItemsStore.getRef(ref.upper())>49151:		#OSの仕様により0xBFFF=49151までしか利用できない
			log.warning("%s=%d is invalid hotkey ref. hotkey ref must be smaller than 49151" % (ref,menuItemsStore.getRef(ref)))
			return False
		return super().makeEntry(ref,key,filter,log)

	def Set(self,identifier,window,eventHandler=hotkeyHandler):
		"""
			指定されたウィンドウにホットキーとして登録する
			identifier で、どのビューでのテーブルを取得するかを指定する。
			windowには、登録先としてwx.windowを継承したインスタンスを指定する
			EVT_HOTKEYをeventHandlerで指定された関数にBindする(NoneでBindの省略可)
		"""
		if eventHandler:
			window.Bind(wx.EVT_HOTKEY,eventHandler)
		try:
			for entry in self.entries[identifier.upper()]:
				if not window.RegisterHotKey(entry.GetCommand(),entry.GetFlags(),entry.GetKeyCode()):
					self.log.warning("hotkey set failed. ref=%s may be confrict." % entry.GetRefName)
					self.addError(identifier,entry.GetRefName(),"N/A","register failed. may be confrict.")
		except KeyError:
			self.log.debug("hotkey set failed. identifier %s not defined." % identifier.upper())

	def UnSet(self,identifier,window):
		"""
			指定されたウィンドウに対するホットキーの登録を解除する
			identifier で、どのビューでのテーブルを取得するかを指定する。
			windowには、先にSet()で登録を行ったwindowを指定する
			イベントのバインドも削除(Noneで上書き)する
		"""
		window.Bind(wx.EVT_HOTKEY,None)
		try:
			for entry in self.entries[identifier.upper()]:
				if not window.UnregisterHotKey(entry.GetCommand()):
					self.log.warning("hotkey unset failed. ref=%s may be confrict." % entry.GetRefName)
					self.addError(identifier,entry.GetRefName(),"N/A","unregister failed.")
		except KeyError:
			self.log.debug("hotkey set failed. identifier %s not defined." % identifier.upper())


def permitConfrict(items,log):
	return False		#ホットキーではOSの仕様により重複登録できない


class HotkeyFilter(keymapHandlerBase.KeyFilterBase):
	def __init__(self):
		super().__init__()
		self.AddDisablePattern("WINDOWS")					#スタートメニューの表示

	def SetDefault(self,supportInputChar=False,isSystem=False,arrowCharKey=False):
		"""
			ホットキーなので、一般のソフトウェアの利用に支障を及ぼさないためにも引数は全て省略してFalseにすることを強く推奨。
		"""
		super().SetDefault(supportInputChar,isSystem,arrowCharKey)
		self.modifierKey.add("WINDOWS")
		return self
