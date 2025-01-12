# ClearSlider
#Copyright (C) 2020 yamahubuki <itiro.ishino@gmail.com>

import wx
from views.viewObjectBase import sliderBase, toolTipBase

def unsupported(*pArg, **kwargs):
    raise NotImplementedError("ClearSlider is not support this function.")

class clearSlider(sliderBase.slider):
    """
        見やすいスライダ。
        Sliderの派生だが、メモリ表示をサポートしていないので注意すること。

        また、SliderEventではマウスクリックによるスライダーの移動を検知しないことにも注意を要する。
        あらゆる方法でのスライダーの移動を検知するには、setScrollCallBack(func)でコールバック関数を登録しておくとよい。
    """

    # 上下左右の枠の太さ(上＋下、左＋右の２本分の値を偶数で指定)
    BORDER_WIDTH = 6

    def __init__(self, *pArg, **kwargs):
        #非対応のスタイルの設定はエラーにする
        style = 0
        if "style" in kwargs:
            style = kwargs["style"]
            kwargs["style"] |= wx.FULL_REPAINT_ON_RESIZE
        elif len(pArg)>=8:
            style = pArg[7]
            pArg[7] |= wx.FULL_REPAINT_ON_RESIZE
        else:        #ないなら作る
            kwargs["style"] = wx.FULL_REPAINT_ON_RESIZE
        if style!=0:
            if ((style & wx.SL_VERTICAL == wx.SL_VERTICAL) or (style & wx.SL_AUTOTICKS == wx.SL_AUTOTICKS) 
                    or (style & wx.SL_MIN_MAX_LABELS == wx.SL_MIN_MAX_LABELS) or (style & wx.SL_VALUE_LABEL == wx.SL_VALUE_LABEL) 
                    or (style & wx.SL_LEFT == wx.SL_LEFT) or (style & wx.SL_RIGHT == wx.SL_RIGHT) 
                    or (style & wx.SL_TOP == wx.SL_TOP) or (style & wx.SL_BOTTOM == wx.SL_BOTTOM) 
                    or (style & wx.SL_BOTH == wx.SL_BOTH) or (style & wx.SL_SELRANGE == wx.SL_SELRANGE)):
                raise ValueError("ClearSlider is not support tick, label, and Lange style.")

        super().__init__(*pArg, **kwargs)
        self.Bind(wx.EVT_PAINT, self.paintEvent)
        self.Bind(wx.EVT_SLIDER, self.sliderEvent)
        self.Bind(wx.EVT_LEFT_DOWN, self.mouseClickEvent)
        self.Bind(wx.EVT_ENTER_WINDOW, self.onMouseMotion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.onMouseLeave)
        self.Bind(wx.EVT_MOTION, self.onMouseMotion)
        self.enableToolTip = False #ツールチップ
        self.callBack = None

    def setScrollCallBack(self,func):
        self.callBack = func

    def paintEvent(self,event):
        dc = wx.PaintDC(self)

        ellipseWidth = dc.GetSize().GetHeight() / 2

        # はみ出た円を消すために背景色で塗る
        dc.SetPen(wx.Pen(self.GetBackgroundColour(), self.BORDER_WIDTH, wx.PENSTYLE_SOLID))
        dc.SetBrush(wx.Brush(self.GetBackgroundColour(), wx.BRUSHSTYLE_SOLID))
        dc.DrawRectangle(0, 0, dc.GetSize().GetWidth(), dc.GetSize().GetHeight())

        # 枠描画のため背景色で塗る
        dc.SetPen(wx.Pen(wx.Colour(0, 102, 204), self.BORDER_WIDTH, wx.PENSTYLE_SOLID))
        dc.DrawRectangle((int)(self.getLeftMargin()), 0, (int)(dc.GetSize().GetWidth() - self.getLeftMargin() - self.getRightMargin()), (int)(dc.GetSize().GetHeight()))

        # 現在のパーセンテージまで塗る
        dc.SetBrush(wx.Brush(wx.Colour(0, 102, 204), wx.BRUSHSTYLE_SOLID))
        dc.SetPen(wx.Pen(wx.Colour(0, 102, 204), 1, wx.PENSTYLE_SOLID))
        dc.DrawRectangle((int)(ellipseWidth / 2), 0, (int)(self.getValueBarLength()), (int)(dc.GetSize().GetHeight()))

        # 現在の位置に円を描画
        dc.SetBrush(wx.Brush(wx.Colour(255, 100, 0), wx.BRUSHSTYLE_SOLID))
        dc.SetPen(wx.Pen(wx.Colour(255, 100, 0), 1, wx.PENSTYLE_SOLID))
        dc.DrawEllipse((int)(self.BORDER_WIDTH / 2 + self.getValueBarLength() - self.BORDER_WIDTH / 2), 0, int(ellipseWidth), int(dc.GetSize().GetHeight()))

    #ウィンドウ内座標xからその位置のvalueの値を計算する
    def pos2value(self, x):
        # 0除算対策
        if (self.GetMax() - self.GetMin() == 0) or self._getVarLength()==0:
            return 0

        #Value 1あたりの幅を計算
        v = self._getVarLength() / (self.GetMax() - self.GetMin())

        return (x - self.getLeftMargin()) / v


    # スタートから塗る長さを返す
    # スライダーが最小値の時0、最大値の時にウィンドウ幅-左右マージンとなる
    def getValueBarLength(self):
        # 0除算対策
        if (self.GetMax() - self.GetMin() == 0) or self._getVarLength()==0:
            return 0

        #Value 1あたりの幅を計算
        v = self._getVarLength() / (self.GetMax() - self.GetMin())

        return v * (self.GetValue() - self.GetMin())

    # 描画されるバーの長さを返す
    def _getVarLength(self):
        return self.GetSize().GetWidth() - self.getLeftMargin() - self.getRightMargin()

    def getLeftMargin(self):
        return self.GetSize().GetHeight() / 2 / 2

    def getRightMargin(self):
        return self.GetSize().GetHeight() / 2 / 2

    def sliderEvent(self,event):
        self.Refresh()
        event.Skip()
        if self.callBack:
            self.callBack()

    def setToolTip(self, labelFunction):
        """
            ラベル生成関数とともにツールチップをセット。

            :param function labelFunction: str <= labelFunction(sliderValue)
        """
        self.tipLabelFunction = labelFunction
        if self.enableToolTip == False:
            self.enableToolTip = True
            self.toolTip = None

    def onMouseMotion(self, evt):
        if self.enableToolTip:
            if round(self.pos2value(evt.GetX()))<self.GetMin() or round(self.pos2value(evt.GetX()))>self.GetMax():
                if self.toolTip != None:
                    self.toolTip.destroy()
                    self.toolTip = None
                return
            val = self.tipLabelFunction(self.pos2value(evt.GetX()))
            if self.toolTip != None:
                self.toolTip.refresh(self.ClientToScreen(evt.GetPosition()), val)
            else:
                self.toolTip = toolTipBase.toolTip(self, self.ClientToScreen(evt.GetPosition()), val, self.GetBackgroundColour(), self.GetForegroundColour(), self.GetFont())
        if evt.Dragging():
            self.mouseClickEvent(evt)

    def onMouseLeave(self, evt):
        if self.enableToolTip and self.toolTip != None:
            self.toolTip.destroy()
            self.toolTip = None

    def SetValue(self,value):
        super().SetValue(int(value))
        self.Refresh()

    def mouseClickEvent(self,event):
        self.SetValue(self.pos2value(event.GetX()))
        self.SetFocus()
        if self.callBack:
            self.callBack()

    #描画の関係でサポートできない関数の呼び出しを例外にする
    GetTickFreq = unsupported
    SetTickFreq = unsupported
    SetTick = unsupported
    GetSelEnd = unsupported
    SetSelEnd = unsupported
    GetRange = unsupported
    SetSelection = unsupported
