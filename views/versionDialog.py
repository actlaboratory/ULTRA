# versionDialog
# Copyright (C) 2020 Hiroki Fujii <hfujii@hisystron.com>

import wx
import constants, update
from views import baseDialog, ViewCreator


def versionDialog():
    d = dialog()
    d.Initialize()
    d.Show()


class dialog(baseDialog.BaseDialog):
    def __init__(self):
        super().__init__("versionInfoDialog")

    def Initialize(self):
        self.log.debug("created")
        super().Initialize(self.app.hMainView.hFrame,_("バージョン情報"))
        self.InstallControls()
        return True

    def InstallControls(self):
        """いろんなwidgetを設置する。"""
        versionCreator = ViewCreator.ViewCreator(self.viewMode, self.panel, self.sizer, wx.VERTICAL, 10, style=wx.ALL, margin=20)
        textList = []
        textList.append(str(constants.APP_FULL_NAME) + " (" + constants.APP_NAME + ")")
        textList.append(_("ソフトウェアバージョン") + ": " + str(constants.APP_VERSION))
        try: textList.append(_("アップデータバージョン") + ": " + update.getUpdaterVersion()[1])
        except: pass
        textList.append(_("ライセンス") + ": " + constants.APP_LICENSE)
        textList.append(_("開発元") + ": %s - %s" %(constants.APP_DEVELOPERS, constants.APP_DEVELOPERS_URL))
        textList.append(_("ソフトウェア詳細情報") + ": " + constants.APP_DETAILS_URL)
        textList.append("")
        textList.append(_("ライセンス/著作権情報については、同梱の license.txt を参照してください。"))
        textList.append("")
        textList.append(constants.APP_COPYRIGHT_MESSAGE)

        self.info, dummy = versionCreator.inputbox("", defaultValue="\r\n".join(textList), style=wx.TE_MULTILINE|wx.TE_READONLY | wx.TE_NO_VSCROLL | wx.BORDER_RAISED, sizerFlag=wx.EXPAND, x=750, textLayout=None)
        f = self.info.GetFont()
        f.SetPointSize(f.GetPointSize() * (2/3))
        self.info.SetFont(f)
        self.info.SetMinSize(wx.Size(750,240))

        # フッター
        footerCreator = ViewCreator.ViewCreator(self.viewMode, self.panel, self.sizer, style=wx.ALIGN_RIGHT | wx.ALL, margin=20)
        self.closeBtn = footerCreator.closebutton(_("閉じる"))
        self.closeBtn.SetDefault()
