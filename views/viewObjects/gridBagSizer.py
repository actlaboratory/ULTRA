#GridBagSizer
#Copyright (C) 2020 yamahubuki <itiro.ishino@gmail.com>

import wx
from views.viewObjectBase.viewObjectUtil import *


class GridBagSizer(wx.GridBagSizer):
	"""
		FlexGridSizer互換の引数で初期化及びAdd()が利用できるよう改造したGridBagSizer
		Insertは使えないので注意！
	"""

	def __init__(self,vgap=0,hgap=0,p3=None):
		if p3==None:
			if type(hgap)!=wx.Size:	#GridBagSizer標準を利用
				super().__init__(vgap,hgap)
				self.SetCols(2)
			elif type(hgap)==wx.Size:	#FlexGridSizer互換の(cols,gap)を利用
				super().__init__(hgap.width,hgap.height)
				self.SetCols(vgap)
			else:
				raise ValueError
		else:					#FlexGridSizer互換の(cols,vgap,hgap)を利用
			super().__init__(hgap,p3)
			self.SetCols(vgap)
		
	def Add(self,*args,**kwargs):
		kwargs.pop("proportion",None)
		if isset(args,kwargs,0,"item",wx.GBSizerItem):
			super().Add(self,*args,**kwargs)
		elif isset(args,kwargs,1,"pos",wx.GBPosition):
			super().Add(self,*args,**kwargs)
		elif isset(args,kwargs,2,"pos",wx.GBPosition):
			super().Add(self,*args,*kwargs)
		elif isset(args,kwargs,0,"item",wx.SizerItem):
			raise TypeError
		elif isset(args,kwargs,0,"window",wx.Window) or isset(args,kwargs,0,"sizer",wx.Sizer):
			if len(args)==2 and len(kwargs)==0:
				super().Add(args[0],self.getNextPos(),wx.GBSpan(),flag=args[1])
			elif len(args)>=3:
				super().Add(args[0],self.getNextPos(),wx.GBSpan(),*(args[2:]),**kwargs)
			else:
				super().Add(args[0],self.getNextPos(),wx.GBSpan(),**kwargs)
		else:
			raise NotImplementedError
				#Add (self, width, height, proportion=0, flag=0, border=0, userData=None)
				#Add (self, width, height, flags)
				#Add (self, size, proportion=0, flag=0, border=0, /Transfer/=None)
				#Add (self, size, flags)

	def SetItemSpan(self,*args,**kwargs):
		"""
			標準の引数に加えて、(window,col=int)でも設定できるよう拡張
		"""
		if isset(args,kwargs,1,None,int):
			super().SetItemSpan(args[0],wx.GBSpan(1,args[1]))
		else:
			super().SetItemSpan(*args,*kwargs)

	def getNextPos(self):
		if self.GetItemCount()==0:			#最初のアイテム
			return wx.GBPosition(0,0)
		lastItem=self.GetChildren()[self.GetItemCount()-1]
		row,col=lastItem.GetEndPos()
		col+=1
		if col==self.GetCols():
			col=0
			row+=1
		return wx.GBPosition(row,col)
