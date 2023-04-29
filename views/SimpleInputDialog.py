# -*- coding: utf-8 -*-
# Simple input dialog view
# Copyright (C) 2019-2020 yamahubuki <itiro.ishino@gmail.com>
# Note: All comments except these top lines will be written in Japanese. 

import enum
import re
import wx

import views.ViewCreator

from logging import getLogger
from views.baseDialog import *
import simpleDialog

DEFAULT_STYLE=wx.BORDER_RAISED

# 入力値のバリデーション、値の返却のモード
class Mode(enum.Enum):
	# 空行を飛ばしつつ、1行ずつバリデーション
	# パターンにマッチしない行が1行でもあればinvalid
	# 返却時は、空行を除く各行のデータを改行コードで繋いで返す
	EACH_LINE = enum.auto()
	# 入力値全体がパターンとマッチするかを調べる
	# 返却時は、入力されたデータを加工せずに返す
	WHOLE = enum.auto()


class Dialog(BaseDialog):
	def __init__(self,title,detail,parent=None,validationPattern=None,defaultValue="",style=0,mode=Mode.EACH_LINE):
		super().__init__("SimpleInputDialog")
		self.title=title
		self.detail=detail
		self.default=defaultValue
		if parent!=None:
			self.parent=parent
		else:
			self.parent=self.app.hMainView.hFrame
		self.validationPattern = validationPattern
		self.style=style
		self.mode=mode

	def Initialize(self):
		super().Initialize(self.parent,self.title)
		self.InstallControls()
		return True

	def InstallControls(self):
		"""いろんなwidgetを設置する。"""
		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.VERTICAL,20,style=wx.ALL|wx.EXPAND,margin=20)
		self.edit,self.static=self.creator.inputbox(self.detail,defaultValue=self.default,x=-1,style=DEFAULT_STYLE|self.style,sizerFlag=wx.EXPAND)
		self.edit.hideScrollBar(wx.HORIZONTAL)

		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.HORIZONTAL,20,style=wx.ALIGN_RIGHT)
		self.bOk=self.creator.okbutton(_("ＯＫ"),self.ok)
		self.bCancel=self.creator.cancelbutton(_("キャンセル"),None)

	def ok(self,event):
		if not self.validate():
			return
		event.Skip()

	def GetData(self):
		if self.mode == Mode.EACH_LINE:
			ret = []
			for line in self.edit.GetValue().splitlines():
				line = line.strip()
				if len(line) == 0:
					continue
				ret.append(line)
			return "\n".join(ret)
		elif self.mode == Mode.WHOLE:
			return self.edit.GetValue()

	def validate(self):
		if self.validationPattern:
			pattern = re.compile(self.validationPattern)
			if self.mode == Mode.EACH_LINE:
				exists = False
				lineNum = 0
				for line in self.edit.GetValue().splitlines():
					lineNum += 1
					line = line.strip()
					if len(line) == 0:
						continue
					if not re.fullmatch(pattern, line):
						simpleDialog.errorDialog(_("入力内容に誤りがあります。") + "\n" + _("行: %d") % lineNum, self.wnd)
						return False
					# バリデーションに成功した
					exists = True
				if not exists:
					simpleDialog.errorDialog(_("有効な値が入力されていません。"), self.wnd)
					return False
			elif self.mode == Mode.WHOLE:
				if not re.fullmatch(pattern, self.edit.GetValue()):
					simpleDialog.errorDialog(_("入力内容に誤りがあります。"), self.wnd)
					return False
		return True
