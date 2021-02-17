# -*- coding: utf-8 -*-
# sample dialog

import wx
import os

import views.ViewCreator
from views.baseDialog import *

class Dialog(BaseDialog):
    def __init__(self):
        super().__init__("mkdialog")

    def Initialize(self, title,message,btnTpl):
        self.title=title
        self.message=message
        self.btnTpl=btnTpl
        self.log.debug("created")
        super().Initialize(self.app.hMainView.hFrame,self.title)
        self.btnList = [] #okとキャンセる以外のボタンハンドル
        self.InstallControls()

        return True

    def InstallControls(self):
        """いろんなwidgetを設置する。"""
        self.creator=views.ViewCreator.ViewCreator(1,self.panel,self.sizer,wx.VERTICAL,20)
        self.creator.staticText(self.message)
        self.creator=views.ViewCreator.ViewCreator(1,self.panel,self.sizer,wx.HORIZONTAL,20,"",wx.ALIGN_BOTTOM | wx.ALIGN_RIGHT)
        for s in self.btnTpl:
            if s == _("キャンセル"): self.bCancel = self.creator.cancelbutton(s, self.onButtonClick)
            else: self.btnList.append(self.creator.button(s,self.onButtonClick))

    def GetData(self):
        return self.message

    def onButtonClick(self, evt):
        if evt.GetEventObject() == self.bCancel: self.wnd.EndModal(wx.ID_CANCEL)
        for o in self.btnList:
            if evt.GetEventObject()==o:
                self.wnd.EndModal(self.btnList.index(o))
        