# -*- coding: utf-8 -*-

# Copyright (c) 2020 MenxLi
# source: https://github.com/MenxLi/tkSliderWidget
# Copyright (c) 2022 shmilee

from tkinter import *
from tkinter.ttk import *


class Slider(Frame):
    '''Float/Int RangeSlider'''

    def __init__(self, master,
                 min_val=0, max_val=1, init_val=None, step=None, val_type=float,
                 desc=None, width=300, height=60, show_value=True, style=None):
        super(Slider, self).__init__(master)
        self.max_val = max_val
        self.min_val = min_val
        # TODO add step support
        if init_val == None:
            init_val = [min_val]
        self.init_val = init_val
        self.val_type = val_type
        self.show_value = show_value
        style = style or {}
        self.LINE_COLOR = style.get('LINE_COLOR', "#476b6b")
        self.LINE_WIDTH = style.get('LINE_WIDTH', 2)
        self.BAR_COLOR_INNER = style.get('BAR_COLOR_INNER', "#5c8a8a")
        self.BAR_COLOR_OUTTER = style.get('BAR_COLOR_OUTTER', "#c2d6d6")
        self.BAR_RADIUS = style.get('BAR_RADIUS', 8)
        self.BAR_RADIUS_INNER = style.get('BAR_RADIUS_INNER', 4)
        if val_type == int:
            self.NDIGITS = style.get('NDIGITS', None)
        else:
            # for showing in canvas & converting value
            self.NDIGITS = style.get('NDIGITS', 1)
        self.canv_H = height
        self.canv_W = width
        if not show_value:
            self.slider_y = self.canv_H/2  # y pos of the slider
        else:
            self.slider_y = self.BAR_RADIUS + 2
        self.slider_x = self.BAR_RADIUS  # x pos of the slider (left side)

        self.bars = []
        self.selected_idx = None  # current selection bar index
        for value in self.init_val:
            pos = (value-min_val)/(max_val-min_val)
            ids = []
            bar = {"Pos": pos, "Ids": ids, "Value": self._convertValue(value)}
            self.bars.append(bar)

        self.canv = Canvas(self, height=self.canv_H, width=self.canv_W)
        self.canv.pack()
        self.canv.bind("<Motion>", self._mouseMotion)
        self.canv.bind("<B1-Motion>", self._moveBar)

        self.__addTrack(self.slider_x, self.slider_y,
                        self.canv_W-self.slider_x, self.slider_y)
        for bar in self.bars:
            bar["Ids"] = self.__addBar(bar["Pos"])

    def _convertValue(self, value):
        if self.val_type == int:
            return int(value)
        else:
            return round(float(value), self.NDIGITS)

    def getValues(self):
        values = [bar["Value"] for bar in self.bars]
        return sorted(values)

    def _mouseMotion(self, event):
        x = event.x
        y = event.y
        selection = self.__checkSelection(x, y)
        if selection[0]:
            self.canv.config(cursor="hand2")
            self.selected_idx = selection[1]
        else:
            self.canv.config(cursor="")
            self.selected_idx = None

    def _moveBar(self, event):
        x = event.x
        y = event.y
        if self.selected_idx == None:
            return False
        pos = self.__calcPos(x)
        idx = self.selected_idx
        self.__moveBar(idx, pos)

    def __addTrack(self, startx, starty, endx, endy):
        id1 = self.canv.create_line(startx, starty, endx, endy,
                                    fill=self.LINE_COLOR,
                                    width=self.LINE_WIDTH)
        return id1

    def __addBar(self, pos):
        """@ pos: position of the bar, ranged from (0,1)"""
        if pos < 0 or pos > 1:
            raise Exception("Pos error - Pos: "+str(pos))
        R = self.BAR_RADIUS
        r = self.BAR_RADIUS_INNER
        L = self.canv_W - 2*self.slider_x
        y = self.slider_y
        x = self.slider_x+pos*L
        id_outer = self.canv.create_oval(
            x-R, y-R, x+R, y+R, fill=self.BAR_COLOR_OUTTER, width=2, outline="")
        id_inner = self.canv.create_oval(
            x-r, y-r, x+r, y+r, fill=self.BAR_COLOR_INNER, outline="")
        if self.show_value:
            y_value = y+self.BAR_RADIUS+8
            value = pos*(self.max_val - self.min_val)+self.min_val
            anchor = W if x - self.slider_x <= L/2 else E
            id_value = self.canv.create_text(
                x, y_value, anchor=anchor,
                text=format(self._convertValue(value)))
            return [id_outer, id_inner, id_value]
        else:
            return [id_outer, id_inner]

    def __moveBar(self, idx, pos):
        ids = self.bars[idx]["Ids"]
        for id in ids:
            self.canv.delete(id)
        self.bars[idx]["Ids"] = self.__addBar(pos)
        self.bars[idx]["Pos"] = pos
        self.bars[idx]["Value"] = self._convertValue(
            pos * (self.max_val - self.min_val)+self.min_val)

    def __calcPos(self, x):
        """calculate position from x coordinate"""
        pos = (x - self.slider_x)/(self.canv_W-2*self.slider_x)
        if pos < 0:
            return 0
        elif pos > 1:
            return 1
        else:
            return pos

    def __checkSelection(self, x, y):
        """
        To check if the position is inside the bounding rectangle of a Bar
        Return [True, bar_index] or [False, None]
        """
        for idx in range(len(self.bars)):
            id = self.bars[idx]["Ids"][0]
            bbox = self.canv.bbox(id)
            if bbox[0] < x and bbox[2] > x and bbox[1] < y and bbox[3] > y:
                return [True, idx]
        return [False, None]


if __name__ == '__main__':
    root = Tk()
    label = Label(root, text='Test:')
    label.pack(side=LEFT, padx=2)
    slider = Slider(
        root,
        min_val=110, max_val=1000, init_val=(120, 400),
        width=300, height=50)
    slider.pack(side=LEFT, padx=2)
    root.title("Slider Widget")
    root.mainloop()
    print(slider.getValues())
