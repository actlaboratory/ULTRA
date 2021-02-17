# -*- coding: utf-8 -*-
# dialog with embedded browser

import wx
import wx.html2
import globalVars
import views.ViewCreator
from views.baseDialog import *
import re

CANCEL=-1
RUNNING=0
SUCCESS=1
ERROR=-1

class Dialog(BaseDialog):
	def __init__(self,firstPageURL,endPageURLPtn):
		super().__init__()
		#最初はfirstPageURLを開く
		#endPageURLPtn(正規表現)に一致するページまできたら閉じる
		self.firstPageURL=firstPageURL
		self.endPageURLPtn=endPageURLPtn
		super().__init__()

	def Initialize(self):
		self.identifier="webDialog"#このビューを表す文字列
		self.log.debug("created")
		super().Initialize(self.app.hMainView.hFrame,_("googleアカウント認証")+" - "+constants.APP_NAME)
		self.InstallControls()

		#ステータスを実行中に設定
		self.status=RUNNING


	def InstallControls(self):
		#ブラウザの表示
		self.creator=views.ViewCreator.ViewCreator(1,self.panel,self.sizer,wx.VERTICAL,20)
		self.web=self.creator.webView()
		self.web.Bind(wx.html2.EVT_WEBVIEW_LOADED,self.changePage)
		self.web.Bind(wx.html2.EVT_WEBVIEW_NEWWINDOW,self.error)
		self.web.Bind(wx.html2.EVT_WEBVIEW_ERROR,self.error)

		#初期URLのページを表示
		self.log.debug("navigate firstURL:"+self.firstPageURL)
		print("navigate firstURL:"+self.firstPageURL)
		self.web.LoadURL(self.firstPageURL)

	def Destroy(self):
		self.log.debug("destroy")
		if self.status==RUNNING:
			self.status=CANCEL
		self.wnd.Destroy()

	def GetData(self):
		return lastURL

	def GetStatus(self):
		return self.status

	def error(self,event):
		print("errorEvt")
		self.lastURL=event.GetURL()
		print(self.lastURL)
		print("error")
		self.status=ERROR
		self.web.Destroy()

	def changePage(self,event):
		print("evt")
		self.lastURL=event.GetURL()
		print(self.lastURL)
		if re.search(self.endPageURLPtn,self.lastURL)!=None:
			print("break")
			self.status=SUCCESS
			self.web.Destroy()
		event.Skip()
