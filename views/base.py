# -*- coding: utf-8 -*-
#views base class
#Copyright (C) 2019 Yukio Nozawa <personal@nyanchangames.com>
#Copyright (C) 2020-2021 yamahubuki <itiro.ishino@gmail.com>

import _winxptheme
import wx

import constants
import defaultKeymap
import errorCodes
import globalVars
import keymap
import menuItemsDic
import menuItemsStore
import views.ViewCreator

from logging import getLogger
from simpleDialog import dialog


class BaseView(object):
	"""ビューの基本クラス。"""
	def __init__(self,identifier):
		self.identifier=identifier
		self.log=getLogger("%s.%s" % (constants.LOG_PREFIX,self.identifier))
		self.shortcutEnable=True
		self.viewMode=views.ViewCreator.ViewCreator.config2modeValue(
			globalVars.app.config.getstring("view","colorMode","white",("white","dark")),
			globalVars.app.config.getstring("view","textWrapping","off",("on","off"))
		)
		self.app=globalVars.app

	def Initialize(self, ttl, x, y,px,py,style=wx.DEFAULT_FRAME_STYLE,space=0):
		"""タイトルとウィンドウサイズとポジションを指定して、ウィンドウを初期化する。"""
		self.hFrame=wx.Frame(None,wx.ID_ANY,ttl, size=(x,y),pos=(px,py),name=ttl,style=style)
		_winxptheme.SetWindowTheme(self.hFrame.GetHandle(),"","")
		self.hFrame.Bind(wx.EVT_MOVE_END,self.events.WindowMove)
		self.hFrame.Bind(wx.EVT_SIZE,self.events.WindowResize)
		self.hFrame.Bind(wx.EVT_MAXIMIZE,self.events.WindowResize)
		self.hFrame.Bind(wx.EVT_CLOSE,self.events.OnExit)
		self.MakePanel(space)

	def MakePanel(self,space=0):
		self.hPanel=views.ViewCreator.makePanel(self.hFrame)
		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.hPanel,None, wx.VERTICAL,style=wx.ALL,space=space)
		self.hFrame.Layout()

	def Clear(self, space=0):
		self.hFrame.DestroyChildren()
		self.MakePanel(space)

	def Show(self):
		self.creator.GetPanel().Layout()
		self.hFrame.Show()
		self.app.SetTopWindow(self.hFrame)
		return True

	def InstallMenuEvent(self,menu,event):
		"""メニューを作り、指定されたイベント処理用オブジェクトと結びつける。"""
		menu.parent=self			#下位互換の為ここで渡すしかない。applyで必要。
		menu.Apply(self.hFrame)
		self.menu=menu

		#ショートカット無効状態の時に表示するダミーのメニューバー
		#これがないとメニューバーの高さ分画面がずれてしまうために必要
		self.hDisableMenuBar=wx.MenuBar()
		self.hDisableSubMenu=wx.Menu()
		self.hDisableMenuBar.Append(self.hDisableSubMenu,_("現在メニューは操作できません"))
		self.SetShortcutEnabled(True)

		self.hFrame.Bind(wx.EVT_MENU,event)

	def SetShortcutEnabled(self,en):
		"""
			ショートカットキーの有効/無効を切り替える。
			AcceleratorTableとメニューバーのそれぞれに登録されているので、両方の対策が必要。
		"""
		return self._SetShortcutEnabled(en,self.hFrame)

	def _SetShortcutEnabled(self,en,target):
		self.shortcutEnable=en
		if en:
			#通常のメニューバーに戻す
			self.hFrame.SetMenuBar(self.menu.hMenuBar)
		else:
			self.hFrame.SetMenuBar(self.menu.hDisableMenuBar)
		#SetMenuBarの後に呼び出しが必要
		self.creator.GetSizer().Layout()

		t=self.menu.acceleratorTable if en else wx.AcceleratorTable()
		target.SetAcceleratorTable(t)


class BaseMenu(object):
	def __init__(self,identifier,*,keyFilter=None):
		"""メニューバー・acceleratorTable登録準備"""
		self.keymap_identifier=identifier
		self.blockCount={}				#key=intのref、value=blockCount
		self.desableItems=set()			#ブロック中のメニューのrefを格納
		self.callbacks={}				#メニュー選択時のコールバックを格納
		self.hMenuBar=wx.MenuBar()
		if keyFilter:
			self.keyFilter=keyFilter
		else:
			self.keyFilter=keymap.KeyFilter().SetDefault(False,True)
		self.InitShortcut()
		self.ApplyShortcut()

	def InitShortcut(self):
		self.keymap=keymap.KeymapHandler(None,self.keyFilter)
		if self.keymap.addFile(constants.KEYMAP_FILE_NAME)!=errorCodes.OK:
			self.keymap.addDict(defaultKeymap.defaultKeymap)
			self.keymap.SaveFile(constants.KEYMAP_FILE_NAME)
		errors=self.keymap.GetError(self.keymap_identifier)
		if errors:
			tmp=_(constants.KEYMAP_FILE_NAME+"で設定されたショートカットキーが正しくありません。キーの重複、存在しないキー名の指定、使用できないキーパターンの指定などが考えられます。以下のキーの設定内容をご確認ください。\n\n")
			for v in errors:
				tmp+=v+"\n"
			dialog(_("エラー"),tmp)

	def ApplyShortcut(self, window=None, event=None):
		"""
			キーマップ上のショートカットキーの更新を反映する
			windowが指定されていれば、そのウィンドウに更新されたショートカットキーを割り当てる
		"""
		self.acceleratorTable=self.keymap.GetTable(self.keymap_identifier)
		if window:
			self.keymap.Set(self.keymap_identifier, window, event)

	def Block(self,ref):
		"""
			メニュー項目の利用をブロックし、無効状態にする
			refはlist(str)
		"""
		for i in ref:
			try:
				self.blockCount[menuItemsStore.getRef(i)]+=1
			except KeyError:
				self.blockCount[menuItemsStore.getRef(i)]=1

			#新規にブロック
			if self.blockCount[menuItemsStore.getRef(i)]==1:
				self.hMenuBar.Enable(menuItemsStore.getRef(i),False)

	def UnBlock(self,ref):
		"""
			メニュー項目のブロック事由が消滅したので、ブロックカウントを減らす。0になったら有効化する
			refはlist(str)
		"""
		for i in ref:
			try:
				self.blockCount[menuItemsStore.getRef(i)]-=1
			except KeyError:
				self.blockCount[menuItemsStore.getRef(i)]=0

			#ブロック解除
			if self.blockCount[menuItemsStore.getRef(i)]==0 and i not in self.desableItems:
				self.hMenuBar.Enable(menuItemsStore.getRef(i),True)

	def Enable(self,ref,enable):
		"""
			メニューの有効・無効を切り替える
			ref=int
		"""
		if enable:
			self.desableItems.discard(ref)
		else:
			self.desableItems.add(ref)
		return self.hMenuBar.Enable(ref,self.blockCount[ref]==0 and ref not in self.desableItems)

	def IsEnable(self,ref):
		if type(ref)==str:
			ref=menuItemsStore.getRef(ref)
		if ref not in self.blockCount:
			self.blockCount[ref]=0
		return self.blockCount[ref]<=0 and (ref not in self.desableItems)

	def RegisterMenuCommand(self,menu_handle,ref_id,title="",subMenu=None,index=-1):
		if type(ref_id)==dict:
			for k,v in ref_id.items():
				if type(v) == str:
					self._RegisterMenuCommand(menu_handle,k,v,None,index)
				else:
					self._RegisterMenuCommand(menu_handle,k,menuItemsDic.dic[k],None,index,v)
				if index>=0:index+=1
		elif type(ref_id)!=str and hasattr(ref_id,"__iter__"):
			for k in ref_id:
				self._RegisterMenuCommand(menu_handle,k,menuItemsDic.dic[k],None,index)
				if index>=0:index+=1
		else:
			if not title:
				title=menuItemsDic.dic[ref_id]
			return self._RegisterMenuCommand(menu_handle,ref_id,title,subMenu,index)

	def _RegisterMenuCommand(self,menu_handle,ref_id,title,subMenu,index, callback=None):
		if ref_id=="" and title=="":
			if index>=0:
				menu_handle.InsertSeparator(index)
			else:
				menu_handle.AppendSeparator()
			return
		shortcut=self.keymap.GetKeyString(self.keymap_identifier,ref_id)
		s=title if shortcut is None else "%s\t%s" % (title,shortcut)
		if subMenu==None:
			if index>=0:
				menu_handle.Insert(index,menuItemsStore.getRef(ref_id),s)
			else:
				menu_handle.Append(menuItemsStore.getRef(ref_id),s)
		else:
			if index>=0:
				menu_handle.Insert(index,menuItemsStore.getRef(ref_id),s,subMenu)
			else:
				menu_handle.Append(menuItemsStore.getRef(ref_id),s,subMenu)
		if callback:
			self.callbacks[menuItemsStore.getRef(ref_id)] = callback
		self.blockCount[menuItemsStore.getRef(ref_id)]=0

	def RegisterCheckMenuCommand(self,menu_handle,ref_id,title="",index=-1):
		if type(ref_id)==dict:
			for k,v in ref_id.items():
				self._RegisterCheckMenuCommand(menu_handle,k,v,index)
				if index>=0:index+=1
		elif type(ref_id)!=str and hasattr(ref_id,"__iter__"):
			for k in ref_id:
				self._RegisterCheckMenuCommand(menu_handle,k,menuItemsDic.dic[k],index)
				if index>=0:index+=1
		else:
			if not title:
				title=menuItemsDic.dic[ref_id]
			return self._RegisterCheckMenuCommand(menu_handle,ref_id,title,index)

	def _RegisterCheckMenuCommand(self,menu_handle,ref_id,title,index=-1):
		"""チェックメニューアイテム生成補助関数"""
		shortcut=self.keymap.GetKeyString(self.keymap_identifier,ref_id)
		s=title if shortcut is None else "%s\t%s" % (title,shortcut)
		if index>=0:
			menu_handle.InsertCheckItem(index,menuItemsStore.getRef(ref_id),s)
		else:
			menu_handle.AppendCheckItem(menuItemsStore.getRef(ref_id),s)
		self.blockCount[menuItemsStore.getRef(ref_id)]=0

	def RegisterRadioMenuCommand(self,menu_handle,ref_id,title=None,index=-1):
		"""ラジオメニューアイテム生成補助関数"""
		shortcut=self.keymap.GetKeyString(self.keymap_identifier,ref_id)
		if not title:
			title=menuItemsDic.dic[ref_id]
		s=title if shortcut is None else "%s\t%s" % (title,shortcut)
		if index>=0:
			menu_handle.InsertRadioItem(index,menuItemsStore.getRef(ref_id),s)
		else:
			menu_handle.AppendRadioItem(menuItemsStore.getRef(ref_id),s)
		self.blockCount[menuItemsStore.getRef(ref_id)]=0

	def SetMenuLabel(self, ref_id, label=None):
		if not label:
			label=menuItemsDic.dic[ref_id]
		shortcut=self.keymap.GetKeyString(self.keymap_identifier,ref_id)
		s=label if shortcut is None else "%s\t%s" % (label,shortcut)
		self.hMenuBar.SetLabel(menuItemsStore.getRef(ref_id), s)

	def CheckMenu(self,ref_id,state=True):
		return self.hMenuBar.Check(menuItemsStore.getRef(ref_id),state)

	def EnableMenu(self,ref_id,enable=True):
		if type(ref_id)!=str and hasattr(ref_id,"__iter__"):
			for i in ref_id:
				self._EnableMenu(i,enable)
		else:
			self._EnableMenu(ref_id,enable)

	def _EnableMenu(self,ref_id,enable):
		if type(ref_id)==int:
			return self.Enable(ref_id,enable)
		else:
			return self.Enable(menuItemsStore.getRef(ref_id),enable)

	def getItemInfo(self):
		"""
			メニューに登録されたすべてのアイテムを[(表示名,ref)...]で返します。
		"""
		ret=[]

		if self.hMenuBar==None:
			return ret
		for menu,id in self.hMenuBar.GetMenus():
			self._addMenuItemList(menu,ret)
		return ret

	def setCallbacks(self, items):
		"""メニューバーなしのショートカットをまとめてコールバック登録する"""
		for k,v in items.items():
			self.callbacks[menuItemsStore.getRef(k)] = v

	def getCallback(self,ref_id):
		if ref_id in self.callbacks:
			return self.callbacks[ref_id]

	def _addMenuItemList(self,menu,ret):
		if type(menu)==wx.Menu:
			items=menu.GetMenuItems()
		else:
			items=menu.GetSubMenu().GetMenuItems()
		for item in items:
			if item.GetSubMenu()!=None:
				self._addMenuItemList(item,ret)
			else:
				if item.GetItemLabelText()!="":		#セパレータ対策
					ret.append((item.GetItemLabelText(),item.GetId()))

class BaseEvents(object):
	"""イベント処理のデフォルトの動作をいくつか定義してあります。"""
	def __init__(self,parent,identifier):
		self.parent=parent
		self.identifier=identifier
		self.log = getLogger("%s.%s" % (constants.LOG_PREFIX,self.identifier))

	def OnMenuSelect(self,event):
		"""メニュー項目が選択されたときのイベントハンドら。"""
		#ショートカットキーが無効状態のときは何もしない
		if not self.parent.shortcutEnable:
			event.Skip()
			return

		selected=event.GetId()		#メニュー識別子
		callback = self.parent.menu.getCallback(selected)
		if callback:
			callback(event)

	def OnExit(self,event):
		event.Skip()

	# wx.EVT_MOVE_END→wx.MoveEvent
	def WindowMove(self,event):
		#設定ファイルに位置を保存
		globalVars.app.config[self.identifier]["positionX"]=self.parent.hFrame.GetPosition().x
		globalVars.app.config[self.identifier]["positionY"]=self.parent.hFrame.GetPosition().y

	# wx.EVT_SIZE→wx.SizeEvent
	def WindowResize(self,event):
		#ウィンドウがアクティブでない時(ウィンドウ生成時など)のイベントは無視
		if self.parent.hFrame.IsActive():
			#最大化状態でなければ、設定ファイルにサイズを保存
			if not self.parent.hFrame.IsMaximized():
				globalVars.app.config[self.identifier]["sizeX"]=event.GetSize().x
				globalVars.app.config[self.identifier]["sizeY"]=event.GetSize().y

			#設定ファイルに最大化状態か否かを保存
			globalVars.app.config[self.identifier]["maximized"]=self.parent.hFrame.IsMaximized()

		#sizerを正しく機能させるため、Skipの呼出が必須
		event.Skip()
