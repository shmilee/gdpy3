# -*- coding: utf-8 -*-

# Copyright (c) 2022 shmilee

import tkinter
from tkinter import ttk
from tkinter.constants import *


class Slider(ttk.Frame):
    '''Float/Int RangeSlider'''  # TODO

    def __init__(self, master,
                 min_val=0, max_val=1, init_val=None, step=None, val_type=float,
                 desc=None, length=200, show_value=True, style=None):
        super(Slider, self).__init__(master)
        self.max_val = max_val
        self.min_val = min_val
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
        if desc:
            self.desc = tkinter.Label(self, text=desc, bg='green')
            self.desc.grid(in_=self, row=0, column=0, padx=5, pady=5, sticky=W)
        if show_value:
            self.textvariable = tkinter.StringVar(self)
            self.textvariable.set(min_val)
            self.vlabel = tkinter.Label(
                self, textvariable=self.textvariable, bg='yellow')
            self.vlabel.grid(in_=self, row=0, column=1,
                             padx=5, pady=5, sticky=E)

        self.canvas = tkinter.Canvas(
            self, bg='red', bd=0, width=length+2*self.BAR_RADIUS, height=2*self.BAR_RADIUS+4)
        self.canvas.grid(in_=self, row=1, column=0,
                         columnspan=2, padx=5, pady=5, sticky=W+E)
        self.line = self.canvas.create_line(
            self.BAR_RADIUS, self.BAR_RADIUS+2, length+self.BAR_RADIUS, self.BAR_RADIUS+2,
            fill=self.LINE_COLOR, width=self.LINE_WIDTH)


if __name__ == '__main__':
    root = tkinter.Tk()
    slider = Slider(
        root,
        min_val=110, max_val=1000, init_val=(120, 400), step=10,
        desc='Test:', length=100)
    slider.pack(side=LEFT, padx=2)
    root.title("Slider Widget")
    root.mainloop()
