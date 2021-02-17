#listCtrlBase for ViewCreator
#Copyright (C) 2019-2020 Hiroki Fujii <hfujii@hisystron.com>
#Copyright (C) 2020 yamahubuki <itiro.ishino@gmail.com>

import globalVars
import json
import wx
from views.viewObjectBase import viewObjectUtil, controlBase,listCtrlBase

class listCtrl(controlBase.controlBase, wx.ListCtrl):
	def __init__(self, *pArg, **kArg):
		self._needSaveColumnInfo = False
		self.sectionName = ""
		self.keyName = ""
		return super().__init__(*pArg, **kArg)

	#ポップアップメニューの表示位置をクライアント座標のwx.Pointで返す
	def getPopupMenuPosition(self):
		if  self.GetFocusedItem()>=0:
			rect=self.GetItemRect(self.GetFocusedItem(),wx.LIST_RECT_LABEL)
			return rect.GetBottomRight()
		else:
			return super().getPopupMenuPosition()

	def loadColumnInfo(self,section,key):
		"""
			保存しておいたカラム幅およびカラムの並び順を読み込んで反映する。
			この関数の呼び出し時点で全てのカラムの生成を終えている必要がある。
			関数の呼び出し時に設定情報が存在すればその情報の復元を試み、なければ呼び出し時の状況を保存する。

			保存に利用するキー名(同じセクション内において固有)と、セクション名を引数指定する。

			保存するには、このウィンドウが破棄される前にsaveColumnInfo(引数不要)を呼ぶ必要があるので注意する。
			これは、トップレベル以外のウィンドウでは終了イベントを得る方法がないためである。
		"""
		assert type(section) == str
		assert type(key) == str
		self.sectionName = section
		self.keyName = key
		self._needSaveColumnInfo = True

		#カラムの並び替え設定を反映
		try:
			self.SetColumnsOrder(json.loads(globalVars.app.config[section][key+"_columns_order"]))
			self.Refresh()
		except (json.decoder.JSONDecodeError,TypeError):
			self.saveColumnInfo()		#configが壊れているので初期値リセット
			return

		for i in range(0,self.GetColumnCount()):
			self.SetColumnWidth(i,globalVars.app.config.getint(self.sectionName,self.keyName+"_column_width_"+str(i),100,0,1500))

	def saveColumnInfo(self):
		"""
			カラムの幅と並び替えの状態をconfigに保存する。
		"""
		value=self.GetColumnsOrder()
		if value==[]:
			return		#起動直後で、まだカラム生成前の場合など
		globalVars.app.config[self.sectionName][self.keyName+"_columns_order"]=str(value)

		for i in range(0,self.GetColumnCount()):
			width=self.GetColumnWidth(i)
			globalVars.app.config[self.sectionName][self.keyName+"_column_width_"+str(i)]=str(width)
	
	def getItemSelections(self):
		"""
		現在選択されている項目のインデックスを取得 
		:returns: 選択中インデックスのリスト
		:rtype: list
		"""
		ret = []
		i = self.GetFirstSelected()
		if i >= 0: ret.append(i)
		else: return ret
		while True:
			iTmp = i
			i = self.GetNextSelected(iTmp)
			if i >= 0: ret.append(i)
			else: return ret
