#virtualListCtrlBase for ViewCreator
#Copyright (C) 2019-2020 Hiroki Fujii <hfujii@hisystron.com>
#Copyright (C) 2020-2021 yamahubuki <itiro.ishino@gmail.com>

import wx

import globalVars

from views.viewObjectBase import viewObjectUtil, listCtrlBase

class virtualListCtrl(listCtrlBase.listCtrl):
    # listの機能を組み込み
    def __init__(self, *pArg, **kArg):
        lPArg = list(pArg)
        if "style" in kArg: kArg["style"] = kArg["style"] | wx.LC_REPORT | wx.LC_VIRTUAL
        elif len(lPArg) >= 5: lPArg[4] = lPArg[4] | wx.LC_REPORT | wx.LC_VIRTUAL
        else: kArg["style"] = wx.LC_REPORT | wx.LC_VIRTUAL
        self.lst = []
        self.focusFromKbd = viewObjectUtil.popArg(kArg, "enableTabFocus", True)
        self.columns = []
        self.bindFunctions = {}    #カラム関係のイベントのバインドを保存する辞書
        self.printColumn = True
        super().__init__(*lPArg, **kArg)
        super().Bind(wx.EVT_LIST_END_LABEL_EDIT,self.onLabelEditEnd)
        super().Bind(wx.EVT_LIST_COL_END_DRAG,self.onColumnDragEnd)

    def RefreshItems(self, first, end):
        super().RefreshItems(first, end)
        wx.YieldIfNeeded()

    def getList(self):
        return self.copy()

    def setList(self, lst):
        lstLen = len(lst)
        self.lst = lst
        super().SetItemCount(lstLen)
        if lstLen > 0: self.RefreshItems(0, lstLen)

    #
    #    listCtrl互換
    #
    def Append(self,object):
        self.append(object)
        return self.GetItemCount()-1

    def InsertItem(self,index,label=None):
        if label==None or type(label)!=str:
            raise NotImplementedError
        return self.insert(index,[label])

    def SetItem(self,index,column=0,label=None,imageId=-1):
        if type(index)!=int or label==None or type(label)!=str or imageId!=-1:
            raise NotImplementedError
        if column<0:
            raise ValueError
        obj=self.lst[index]
        while(len(obj)<=column):
            obj.append("")
        obj[column]=label
        self.RefreshItem(index)
        return True

    def DeleteAllItems(self):
        self.lst=[]
        return super().DeleteAllItems()

    def DeleteItem(self,index):
        self.pop(index)
        return True

    def GetItemBackgroundColour(self,index,colour):
        raise NotImplementedError

    def SetItemBackgroundColour(self,index,colour):
        raise NotImplementedError

    def SetItemImage(self,item,image, selImage=-1):
        raise NotImplementedError


    #
    # ビュー部分
    # 
    def OnGetItemText(self, item, column):
        tmp = self.getColFromWx(column)
        column = tmp.col
        obj = self.lst[item]
        if len(obj)<=column:
            return ""
        return str(obj[column]) # イテレーション可能なオブジェクト

    def OnGetItemAttr(self,item):
        return None

    def OnGetItemImage(self,item):
        return -1

    def onLabelEditEnd(self,event):
        if wx.wxEVT_LIST_END_LABEL_EDIT in self.bindFunctions:
            self.bindFunctions[wx.wxEVT_LIST_END_LABEL_EDIT](event)
        if (not event.IsEditCancelled()) and event.IsAllowed():
            self.lst[self.GetFocusedItem()][self.getColFromWx(0).col]=self.GetEditControl().GetLineText(0)

    def onColumnDragEnd(self,event):
        event.SetColumn(self.getColFromWx(event.GetColumn()).col)
        if wx.wxEVT_LIST_COL_END_DRAG in self.bindFunctions:
            self.bindFunctions[wx.wxEVT_LIST_COL_END_DRAG](event)
        if event.IsAllowed():
            self.getCol(event.GetColumn()).width=super().GetColumnWidth(self.getCol(event.GetColumn()).wx_col)

    #
    # 非対応関数
    #
    def SortItems(self,fnSortCallBack):
        raise NotImplementedError


    #
    # リスト部分
    #
    def append(self, object):
        self.lst.append(object)
        super().SetItemCount(len(self.lst))
        self.RefreshItem(len(self.lst)-1)


    def clear(self):
        self.lst.clear()
        super().SetItemCount(0)

    def copy(self):
        return self.lst.copy()

    def count(self, value):
        return self.lst.count(value)

    def extend(self, iterable):
        self.lst.extend(iterable)
        newLen = len(self.lst)
        super().SetItemCount(newLen)
        if len(iterable) > 0: self.RefreshItems(newLen-len(iterable), newLen-1)

    def index(self, *pArg, **kArg):
        return self.lst.index(*pArg, *kArg)

    def insert(self, index, object):
        self.lst.insert(index, object)
        super().SetItemCount(len(self.lst))
        self.RefreshItems(index, len(self.lst)-1)
        return index

    def pop(self, index):
        l = self.GetSelectedItems()
        super().DeleteItem(index)
        ret = self.lst.pop(index)
        self.RefreshItems(index, len(self.lst)-1)
        return ret

    def remove(self, value):
        index = self.lst.index(value)
        l = self.GetSelectedItems()
        self.lst.remove(value)
        super().DeleteItem(index)
        self.RefreshItems(index, len(self.lst)-1)
        self.__setSelectionFromList(l)

    def reverse(self):
        self.lst.reverse()
        self.RefreshItems(0, len(self.lst)-1)

    def sort(self):
        self.lst.sort()
        self.RefreshItems(0, len(self.lst)-1)


    #
    # 拡張比較
    #
    def __lt__(self, other):
        return self.lst.__lt__(other)

    def __le__(self, other):
        return self.lst.__le__(other)

    def __eq__(self, other):
        return self.lst.__eq__(other)

    def __ne__(self, other):
        return self.lst.__ne__(other)

    def __gt__(self, other):
        return self.lst.__gt__(other)

    def __ge__(self, other):
        return self.lst.__ge__(other)

    
    def __hash__(self):
        return self.lst.__hash__()


    # to do
    # def __init_subclass(cls):


    # 
    def __len__(self):
        return self.lst.__len__()

    def __mul__(self, other):
        return self.lst.__mul__(other)

    def __getitem__(self, key):
        return self.lst.__getitem__(key)

    def __setitem__(self, key, value):
        self.lst.__setitem__(key, value)
        self.RefreshItem(key)

    def __delitem__(self, key):
        if len(self.lst[key]) >= 500: #大量処理の高速化
            self.Show(False)
            l = self.GetSelectedItems()
            previousL = self.lst[0:self.GetFirstSelected() + 1]
            fId = self.GetFocusedItem()
            if self.GetFocusedItem() >= 0: f = self.lst[self.GetFocusedItem()]
            else: f = None
            top = self.GetTopItem()
            self.Focus(0)
            self.lst.__delitem__(key)
            super().SetItemCount(len(self.lst))
            self.RefreshItems(0, len(self.lst)-1)
            self.__setFocus(f, fId, top, l, previousL)
            self.__setSelectionFromList(l)
            self.Show()
            self.SetFocus()
        elif type(key) == int:
            super().DeleteItem(key)
            self.lst.pop(key)
            self.RefreshItems(0, len(self.lst)-1)
        else:
            l = self.GetSelectedItems()
            previousL = self.lst[0:self.GetFirstSelected() + 1]
            fId = self.GetFocusedItem()
            if self.GetFocusedItem() >= 0: f = self.lst[self.GetFocusedItem()]
            else: f = None
            top = self.GetTopItem()
            self.Focus(0)
            for o in reversed(self.lst[key]):
                i = self.lst.index(o)
                super().DeleteItem(i)
                self.lst.pop(i)
            self.RefreshItems(0, len(self.lst)-1)
            self.__setFocus(f, fId, top, l, previousL)
            self.__setSelectionFromList(l)

    def __iter__(self):
        return self.lst.__iter__()

    def __reversed__(self):
        return self.lst.__reversed__()
    
    def __contains__(self, item):
        return self.lst.__contains__(item)


    # 数値型エミュレート
    def __add__(self, value):
        self.lst.__add__(value)
        return self

    def __rmul__(self, other):
        self.lst.__rmul__(other)
        return self

    def __iadd__(self, other):
        oldLen = len(self.lst)
        self.lst.__iadd__(other)
        newLen = len(self.lst)
        super().SetItemCount(newLen)
        if oldLen < newLen: self.RefreshItems(oldLen, newLen-1)
        return self
        
    def __imul__(self, other):
        oldLen = len(self.lst)
        self.lst.__imul__(other)
        newLen = len(self.lst)
        super().SetItemCount(newLen)
        if oldLen < newLen: self.RefreshItems(oldLen, newLen-1)
        return self

    def GetSelectedItems(self):
        s = self.GetFirstSelected()
        if s < 0: return None
        else:
            ret = [self.lst[s]]
            while True:
                s = self.GetNextSelected(s)
                if s < 0: break
                else: ret.append(self.lst[s])
            return ret

    def __setSelectionFromList(self, lst):
        self.Select(-1, 0)
        for t in lst:
            if t in self.lst: self.Select(self.lst.index(t))
        if self.GetSelectedItemCount() == 0: self.Select(0)

    def __setFocus(self, obj, fId, topItem, selection, previousL):
        """ フォーカス更新（オブジェクト, フォーカスID, トップID, 選択リスト、選択領域直前までのリスト）"""
        self.Focus(0)
        if obj in self.lst:
            self.Focus(self.lst.index(obj))
        else:
            for o in reversed(previousL):
                if o in self.lst:
                    self.Focus(self.lst.index(o))
                    break
        if self.GetFocusedItem() == len(self.lst) - 1: newFocus = self.GetFocusedItem()
        else: newFocus = self.GetFocusedItem() + 1
        newTop = topItem - (fId - newFocus) + self.GetCountPerPage() - 1
        if newTop >= len(self.lst): self.Focus(len(self.lst) - 1)
        else: self.Focus(newTop)
        self.Focus(newFocus)

    #
    #    カラムの操作
    #
    def DeleteAllColumns(self):
        self.columns=[]
        super().DeleteAllColumns()

    def getCol(self, col):
        tmp = [i for i in self.columns if i.col == col]
        if len(tmp) == 0: return
        return tmp[0]

    #表示・非表示に関わらず、追加されているカラム数を返す
    def GetColumnCount(self):
        return len(self.columns)

    #画面に表示されているカラムの数を返す
    def GetShowingColumnCount(self):
        ret = 0
        for col in self.columns:
            if col.display:
                ret+=1
        return ret

    def getColFromWx(self, wx_col):
        tmp = [i for i in self.columns if i.wx_col == wx_col]
        if len(tmp) == 0: return
        return tmp[0]

    def isPrintColumn(self):
        return self.printColumn

    def setPrintColumn(self, v):
        assert type(v)==bool
        self.printColumn = v

    def loadColumnInfo(self,section,key):
        self.printColumn = self._needSaveColumnInfo and globalVars.app.config.getboolean(self.sectionName,self.keyName+"_print_column_name",True)
        super().loadColumnInfo(section,key)

    def saveColumnInfo(self):
        super().saveColumnInfo()
        globalVars.app.config[self.sectionName][self.keyName+"_print_column_name"] = self.printColumn

    def AppendColumn(self, heading, format=wx.LIST_FORMAT_LEFT, width=-1):
        if self.isPrintColumn():
            result = super().AppendColumn(heading, format, width)
        else:
            result = super().AppendColumn("", format, width)
        ret = Column(len(self.columns), result, super().GetColumnOrder(result), format, width, heading)
        self.columns.append(ret)
        return ret.col

    def InsertColumn(self, col, heading, format=wx.LIST_FORMAT_LEFT, width=wx.LIST_AUTOSIZE):
        if col == 0:
            next = self.getCol(col)
            if next != None:
                insertedColumn = Column(col, next.wx_col - 1, next.disp_col - 1, format, width, heading)
            else:
                insertedColumn = Column(0, 0, 0, format, width, heading)
        elif col <= self.GetColumnCount():
            prev = self.getCol(col - 1)
            insertedColumn = Column(col, prev.wx_col + 1, prev.disp_col + 1, format, width, heading)
        else:
            insertedColumn = Column(self.GetColumnCount(), GetShowingColumnCount(), GetShowingColumnCount(), format, width, heading)
        for i in [j for j in self.columns if j.col >= insertedColumn.col]: i.col += 1
        for i in [j for j in self.columns if j.wx_col >= insertedColumn.wx_col]: i.wx_col += 1
        for i in [j for j in self.columns if j.disp_col >= insertedColumn.disp_col]: i.disp_col += 1
        if self.isPrintColumn():
            super().InsertColumn(insertedColumn.wx_col, heading, format, width)
        else:
            super().InsertColumn(insertedColumn.wx_col, "", format, width)
        self.columns.append(insertedColumn)
        for i in self.lst: i.insert(insertedColumn.col, "")
        return insertedColumn.col

    def DeleteColumn(self, col):
        removedColumn = self.getCol(col)
        for i in [j for j in self.columns if j.col > removedColumn.col]: i.col -= 1
        for i in [j for j in self.columns if j.wx_col > removedColumn.wx_col]: i.wx_col -= 1
        for i in [j for j in self.columns if j.disp_col > removedColumn.disp_col]: i.disp_col -= 1
        for i in self.lst: del i[col]
        result = super().DeleteColumn(removedColumn.wx_col)
        self.columns.remove(removedColumn)
        return result

    def GetColumn(self,col):
        info = wx.ListItem()
        info.SetText(self.getCol(col).heading)
        info.SetWidth(self.getCol(col).width)
        info.SetAlign(self.getCol(col).format)
        info.SetColumn(col)
        return info

    def SetColumnsOrder(self, orders):
        super().DeleteAllColumns()
        tmp = list(range(len(self.columns)))
        counter = 0
        for i in orders:
            data = self.getCol(i)
            data.wx_col = super().AppendColumn(data.heading, data.format, data.width)
            data.disp_col = counter
            data.display = True
            counter += 1
            tmp.remove(i)
        for i in tmp:
            data = self.getCol(i)
            data.wx_col = -1
            data.disp_col = -1
            data.display = False
        self.RefreshItems(0, self.GetItemCount())

        # カラム名の表示・非表示を切替
        if self._needSaveColumnInfo:
            for i in list(range(len(self.columns))):
                col = self.getCol(i)
                if not col.display:
                    continue
                wxCol = self.GetColumn(i)
                if self.isPrintColumn():
                    wxCol.SetText(col.heading)
                else:
                    wxCol.SetText("")
                self.SetColumn(col.wx_col,wxCol)


    def GetColumnsOrder(self):
        ret = []
        tmp = super().GetColumnsOrder()
        for i in tmp:
            data = self.getColFromWx(i)
            ret.append(data.col)
        return ret

    def GetColumnWidth(self, col):
        tmp = self.getCol(col)
        return tmp.width

    def SetColumnWidth(self, col, width):
        tmp = self.getCol(col)
        tmp.width = width
        if tmp.wx_col < 0: return
        return super().SetColumnWidth(tmp.wx_col, width)

    def Bind(self, event, handler, source=None, id=wx.ID_ANY, id2=wx.ID_ANY):
        if type(event)!=wx.PyEventBinder or  source!=None or id!=wx.ID_ANY or id2!=wx.ID_ANY:
            raise NotImplementedError
        if event in (wx.EVT_LIST_COL_CLICK, wx.EVT_LIST_COL_RIGHT_CLICK, wx.EVT_LIST_COL_BEGIN_DRAG, wx.EVT_LIST_COL_DRAGGING):
            self.bindFunctions[event.typeId]=handler
            return super().Bind(event, self.columnEvent, source=source, id=id, id2=id2)
        if event in (wx.EVT_LIST_END_LABEL_EDIT,wx.EVT_LIST_COL_END_DRAG):
            self.bindFunctions[event.typeId]=handler
            #別途self内の関数をBind済み
            return            #wx標準でも戻り値はNoneである
        return super().Bind(event, handler, source=source, id=id, id2=id2)

    def columnEvent(self,event):
        if self.bindFunctions[event.GetEventType()]:
            event.SetColumn(self.getColFromWx(event.GetColumn()).col)
            self.bindFunctions[event.GetEventType()](event)
        else:
            event.Skip()

    def GetItemText(self, item, col):
        return self.lst[item][col]

if __name__ == "__main__":
    app = wx.App()
    frame = wx.Frame()
    obj = virtualListCtrl(frame)
    l = []
    for i in range(100000):
        l.append(i)
    print("ok")
    print(obj)
    obj += l
    print(obj)
    print("ok")
    obj.RefreshItems(0, 100000)
    print("ok")    
    print(len(obj))


class Column:
    def __init__(self, col, wx_col, disp_col, format, width, heading):
        self.col = col
        self.wx_col = wx_col
        self.disp_col = disp_col
        self.format = format
        self.width = width
        self.heading = heading
        self.display = disp_col >= 0

    def __repr__(self):
        """デバッグ用"""
        return str(self.__dict__)
