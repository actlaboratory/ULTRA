#controlBase for ViewCreator
#Copyright (C) 2019-2020 Hiroki Fujii <hfujii@hisystron.com>
#Copyright (C) 2020 yamahubuki <itiro.ishino@gmail.com>

import ctypes
import wx

class controlBase():
	def AcceptsFocusFromKeyboard(self):
		return self.focusFromKbd

	def hideScrollBar(self, orient=wx.VERTICAL):
		assert orient in (wx.VERTICAL, wx.HORIZONTAL, wx.VERTICAL | wx.HORIZONTAL)
		if orient & wx.VERTICAL==wx.VERTICAL:
			ctypes.windll.user32.ShowScrollBar(self.GetHandle(),1,0)
		if orient & wx.HORIZONTAL==wx.HORIZONTAL:
			ctypes.windll.user32.ShowScrollBar(self.GetHandle(),0,0)

	def PopupMenu(self,menu,p2,p3=None):
		if isinstance(p2,int):
			return super().PopupMenu(menu,p2,p3)		#menu,x,y
		elif isinstance(p2,wx.Point):
			return super().PopupMenu(menu,p2)			#menu,point
		else:
			pos=wx.DefaultPosition
			if type(p2)==wx.ContextMenuEvent:
				pos=p2.GetPosition()
			if pos==wx.DefaultPosition:
				pos=self.getPopupMenuPosition()
			else:
				pos=p2.GetEventObject().ScreenToClient(pos)
			return super().PopupMenu(menu,pos)

	#ポップアップメニューの表示位置をクライアント座標のwx.Pointで返す
	#デフォルトではウィンドウ中央
	def getPopupMenuPosition(self):
		return wx.Point(self.GetSize().x/2,self.GetSize().y/2)
