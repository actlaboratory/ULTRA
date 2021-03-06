# -*- coding: utf-8 -*-
#Falcon globalKeyConfig view
#Copyright (C) 2021 yamahubuki <itiro.ishino@gmail.com>
#Note: All comments except these top lines will be written in Japanese. 

import copy
import os
import wx

import globalVars
import keymap
import views.keyConfig
import views.KeyValueSettingDialogBase

from simpleDialog import dialog,errorDialog

class Dialog(views.KeyValueSettingDialogBase.KeyValueSettingDialogBase):
	def __init__(self,keyConfig,menuIds,checkEntries=[],filter=None):
		info=[
			(_("名前"),wx.LIST_FORMAT_LEFT,350),
			(_("ショートカット"),wx.LIST_FORMAT_LEFT,370),
			(_("識別子"),wx.LIST_FORMAT_LEFT,200)
		]
		super().__init__("globalKeyConfigDialog",SettingDialog,info,keyConfig,menuIds)
		self.oldKeyConfig=copy.copy(keyConfig)
		self.checkEntries=checkEntries
		self.filter=filter
		if filter==None:
			self.filter=globalVars.app.hMainView.menu.keymap.filter

	def Initialize(self,title=_("ショートカットキーの設定")):
		super().Initialize(self.app.hMainView.hFrame,title)
		self.addButton.Hide()
		self.deleteButton.Hide()
		return

	def SettingDialogHook(self,dialog):
		dialog.SetFilter(self.filter)

	def OkButtonEvent(self,event):
		"""
			設定されたキーが重複している場合はエラーとする
		"""
		#他のビューとの重複調査
		if not views.KeyValueSettingDialogBase.KeySettingValidation(self.oldKeyConfig,self.values[0],self.log,self.checkEntries,True):
			return

		#このビュー内での重複調査
		newKeys={}
		for name,keys in self.values[0].items():
			for key in keys.split("/"):
				newKeys.setdefault(key.upper(), set()).add(name)
		for key,names in newKeys.items():
			if key==_("なし"):
				continue
			if len(names)>=2:
				entries=[]
				for name in names:
					entries.append(keymap.makeEntry(self.values[1][name],key,None,self.log))
				if not keymap.permitConfrict(entries,self.log):
					dialog(_("エラー"),_("以下の項目において、重複するキー %(key)s が設定されています。\n\n%(command)s") % {"key": key,"command": names},self.wnd)
					return
		event.Skip()

class SettingDialog(views.KeyValueSettingDialogBase.SettingDialogBase):
	"""設定内容を入力するダイアログ"""

	def __init__(self,parent,name,key,id):
		keys=key.split("/")
		for i in range(len(keys),5):
			keys.append(_("なし"))
		super().__init__(
				parent,
				((_("名前"),False),(_("ショートカット1"),False),(_("ショートカット2"),False),(_("ショートカット3"),False),(_("ショートカット4"),False),(_("ショートカット5"),False),(_("識別子"),None)),
				(None,(_("設定"),self.SetKey1),(_("設定"),self.SetKey2),(_("設定"),self.SetKey3),(_("設定"),self.SetKey4),(_("設定"),self.SetKey5),None),
				name,keys[0],keys[1],keys[2],keys[3],keys[4],id
				)

	def Initialize(self):
		return super().Initialize(_("登録内容の入力"))

	def SetKey1(self,event):
		self.keyDialog(1)

	def SetKey2(self,event):
		self.keyDialog(2)

	def SetKey3(self,event):
		self.keyDialog(3)

	def SetKey4(self,event):
		self.keyDialog(4)

	def SetKey5(self,event):
		self.keyDialog(5)

	def GetData(self):
		ret=[None]*3
		ret[0]=self.edits[0].GetLineText(0)
		ret[1]=""
		for i in range(1,6):
			if self.edits[i].GetLineText(0)!=_("なし"):
				if ret[1]!="":
					ret[1]+="/"
				ret[1]+=self.edits[i].GetLineText(0)
		if ret[1]=="":
			ret[1]=_("なし")
		ret[2]=self.edits[6].GetLineText(0)
		return ret

	def SetFilter(self,filter):
		"""
			SettingDialogHookから呼び出され、フィルタを登録する
		"""
		self.filter=filter

	def keyDialog(self,no):
		#フィルタに引っかかるものが既に設定されている場合、その変更は許さない
		before=self.edits[no].GetLineText(0)
		if before!=_("なし"):
			if not self.filter.Check(before):
				errorDialog(_("このショートカットは変更できません。"),self.wnd)
				return
		d=views.keyConfig.Dialog(self.wnd,self.filter)
		d.Initialize()
		if d.Show()==wx.ID_CANCEL:
			dialog(_("設定完了"), _("解除しました。"),self.wnd)
			self.edits[no].SetValue(_("なし"))
		else:
			dialog(_("設定完了"), _("%s に設定しました。") % (d.GetValue()),self.wnd)
			self.edits[no].SetValue(d.GetValue())
		return

	#同一パターンを２重指定している場合の処理をしてから閉じる
	def Validation(self,event):
		lst=[]
		for i in range(1,6):
			if self.edits[i].GetLineText(0)!=_("なし"):
				entry = keymap.makeEntry(self.edits[0].GetLineText(0),self.edits[i].GetLineText(0),None,self.log)
				if entry not in lst:
					lst.append(entry)
				else:
					self.edits[i].SetValue(_("なし"))
		event.Skip()
