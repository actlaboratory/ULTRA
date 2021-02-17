#virtualListCtrlBase for ViewCreator
#Copyright (C) 2019-2020 Hiroki Fujii <hfujii@hisystron.com>


import wx
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
        return super().__init__(*lPArg, **kArg)

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
    # ビュー部分
    # 
    def OnGetItemText(self, item, column):
        obj = self.lst[item]
        if hasattr(obj, '__iter__'): return str(obj[column]) # イテレーション可能なオブジェクト
        else: return obj.getListTuple()[column] # getListTupleを実装するオブジェクト




    #
    # リスト部分
    #
    def append(self, object):
        self.lst.append(object)
        super().SetItemCount(len(self.lst))
        self.RefreshItem(len(self.lst)-1)


    def clear(self):
        self.lst.clear()
        self.Select(-1, 0)
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

    def pop(self, index):
        l = self.GetSelectedItems()
        self.DeleteItem(index)
        ret = self.lst.pop(index)
        self.RefreshItems(index, len(self.lst)-1)
        return ret

    def remove(self, value):
        index = self.lst.index(value)
        l = self.GetSelectedItems()
        self.lst.remove(value)
        self.DeleteItem(index)
        self.RefreshItems(index, len(self.lst)-1)
        self.__setSelectionFromList(l)

    def reverse(self):
        self.lst.reverse()
        self.RefreshItems(0, len(self.lst)-1)

    def sort(self):
        self.lst.sort()
        self.RefreshItems(0, len(self.lst)-1)

    
    # 拡張比較
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
            self.DeleteItem(key)
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
                self.DeleteItem(i)
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
