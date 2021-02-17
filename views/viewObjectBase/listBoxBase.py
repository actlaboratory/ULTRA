#listBoxBase for ViewCreator
#Copyright (C) 2019-2020 Hiroki Fujii <hfujii@hisystron.com>
#Copyright (C) 2020 yamahubuki <itiro.ishino@gmail.com>


import wx
from views.viewObjectBase import viewObjectUtil, controlBase

class listBox(controlBase.controlBase, wx.ListBox):
	def __init__(self, *pArg, **kArg):
		self.focusFromKbd = viewObjectUtil.popArg(kArg, "enableTabFocus", True) #キーボードフォーカスの初期値
		return super().__init__(*pArg, **kArg)

	#ポップアップメニューの表示位置をクライアント座標のwx.Pointで返す
	def getPopupMenuPosition(self):
		x,y=self.GetSize()
		h=y//self.GetCountPerPage()-1
		c=-1
		for i in range(0,self.GetCountPerPage()):
			if self.IsSelected(self.GetTopItem()+i):
				c=i
		if c!=-1:
			return wx.Point(x/2,h*c-h//2)
		else:
			return super().getPopupMenuPosition()

	#右クリック時に呼ぶと、その時のマウス座標位置を強制的にクリックする
	def setCursorOnMouse(self,event):
		item=self.HitTest(self.ScreenToClient(wx.GetMousePosition()))
		if item!=wx.NOT_FOUND and (not self.IsSelected(item)):
			self.SetSelection(wx.NOT_FOUND)
			self.SetSelection(item)
		event.Skip()	#コンテキストメニュー表示の為Skip必須
