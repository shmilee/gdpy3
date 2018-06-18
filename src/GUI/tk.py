# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

import os
import time
import tempfile
import getpass
import tkinter
from tkinter import ttk, simpledialog, filedialog, messagebox
from tkinter.constants import *

from .. import __version__ as gdpy3_version
from ..processors import get_processor, processor_names

__all__ = ['GTkApp']


class GTkApp(object):
    '''
    GUI(Graphical User Interface) made by tkinter.
    '''
    recent_path = os.path.join(tempfile.gettempdir(),
                               'gdpy3_%s_recent_path' % getpass.getuser())

    def __init__(self, path=None, ask_sftp=False):
        '''
        Parameters
        ----------
        path: str
            case path
        ask_sftp: bool
            if no path given, first ask a sftp path or not
        '''
        root = tkinter.Tk(className='gdpy3-gui')
        img = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'icon', 'main_128.gif')
        root.tk.call('wm', 'iconphoto', root._w, tkinter.PhotoImage(file=img))
        root.protocol("WM_DELETE_WINDOW", root.destroy)
        style = ttk.Style()
        font = ('Microsoft YaHei', 10)
        width = 0
        style.configure('.', font=font)
        main = tkinter.Frame(root, relief=RIDGE, borderwidth=2)
        main.pack(fill=BOTH, expand=1)
        # 1
        w_frame_proc = ttk.Labelframe(main, text='1. Processor:', width=width)
        w_str_proc = tkinter.StringVar()
        w_select_proc = tkinter.ttk.Combobox(
            w_frame_proc, values=processor_names, font=font,
            textvariable=w_str_proc, state='readonly')
        w_select_proc.grid(in_=w_frame_proc, row=0, column=0, padx=5, pady=5)
        w_pick = ttk.Button(
            w_frame_proc, text="Pick", width=0, command=self.after_pick)
        w_pick.grid(in_=w_frame_proc, row=0, column=1, padx=5, pady=5)
        w_frame_proc.grid(row=0, column=0, padx=10, pady=5, sticky=W+E)
        # 2
        w_frame_fig = ttk.Labelframe(main, text='2. Figure:', width=width)
        w_str_filter = tkinter.StringVar(value='^.*/.*$')
        w_entry_filter = ttk.Entry(
            w_frame_fig, font=font, textvariable=w_str_filter)
        w_entry_filter.grid(in_=w_frame_fig, row=0, column=0, padx=5, pady=5)
        w_filter = ttk.Button(
            w_frame_fig, text='Filter', width=0, command=self.after_filter)
        w_filter.grid(in_=w_frame_fig, row=0, column=1, padx=5, pady=5)
        w_list_fig = tkinter.Variable(value=[])
        w_listbox_fig = tkinter.Listbox(
            w_frame_fig, selectmode=SINGLE, font=font,
            listvariable=w_list_fig, state='normal')
        w_scrollbar_fig = ttk.Scrollbar(
            w_frame_fig, orient="vertical", command=w_listbox_fig.yview)
        w_listbox_fig.config(yscrollcommand=w_scrollbar_fig.set)
        w_listbox_fig.grid(in_=w_frame_fig, row=1, columnspan=2,
                           sticky=W+E, padx=5, pady=5)
        w_scrollbar_fig.grid(in_=w_frame_fig, row=1, column=1,
                             sticky=E+N+S, padx=5, pady=5)
        w_frame_fig.grid(row=1, column=0, padx=10, pady=5, sticky=W+E)
        # 3
        w_frame_panel = ttk.Labelframe(main, text='3. Panel:', width=width)
        w_plot = ttk.Button(
            w_frame_panel, text='Plot', width=0, command=self.after_plot)
        w_plot.pack(in_=w_frame_panel, side=RIGHT, padx=5, pady=5)
        w_frame_panel.grid(row=2, column=0, padx=10, pady=5, sticky=W+E)
        # bottom
        w_info = tkinter.Label(
            main, relief=RIDGE, borderwidth=1, anchor=E, font=(font[0], 8),
            text="Version %s\t© %s shmilee\t" % (
                gdpy3_version, time.strftime('%Y')))
        w_info.grid(row=3, column=0, sticky=W+E)
        # for share
        self.root = root
        self.center(root)
        self.processor_name = w_str_proc
        self.figlabel_filter = w_str_filter
        self.figlabels = w_list_fig
        self.figlistbox = w_listbox_fig
        self.path = path
        self.processor = None
        self.windows = {}
        # event
        w_select_proc.bind("<<ComboboxSelected>>", self.after_processor_name)
        w_entry_filter.bind("<Return>", self.after_filter)
        w_listbox_fig.bind("<<ListboxSelect>>", self.after_figlabel)
        # start
        if not self.path and ask_sftp:
            self.path = simpledialog.askstring(
                "Input sftp path",
                "Directory in SSH server, format: "
                "'sftp://username@host[:port]##remote/path'",
                parent=root)
        if not self.path:
            if os.path.isfile(self.recent_path):
                with open(self.recent_path, 'r') as recf:
                    old_path = recf.readline().strip()
                    while not self.path:
                        self.path = filedialog.askopenfilename(
                            parent=self.root,
                            initialdir=os.path.dirname(old_path))
            else:
                while not self.path:
                    self.path = filedialog.askopenfilename(parent=root)
        if not self.path.startswith('sftp://'):
            with open(self.recent_path, 'w') as recf:
                recf.write(self.path)
        self.root.title('gdpy3 - %s' % self.path)
        self.root.mainloop()

    def center(self, win):
        win.update_idletasks()
        width = win.winfo_width()
        height = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def after_pick(self):
        if self.processor_name.get():
            gdp = get_processor(self.processor_name.get())
            if self.path.startswith('sftp://'):
                def _passwd_CALLBACK(prompt):
                    return simpledialog.askstring(
                        "Input Password", "SSH Server Password: ",
                        show='*', parent=self.root)
                from ..getpasswd import GetPasswd
                GetPasswd.CALLBACK = _passwd_CALLBACK
            if self.path.endswith(gdp.pcksaltname):
                self.path = self.path[:-len(gdp.pcksaltname)]
            gdp.pick(self.path)
            self.root.title('gdpy3 - %s' % self.path)
            if gdp.pckloader:
                self.processor = gdp
                self.figlabel_filter.set('^.*/.*$')
                self.figlabels.set(gdp.figurelabels)
                self.figlistbox.selection_clear(0, END)
                # reset panel
                # close fig windows
            else:
                messagebox.showerror(message='Failed to get processor!')
        else:
            messagebox.showwarning(message='Select processor first!')

    def after_filter(self, *args):
        if self.processor:
            self.figlabels.set(self.processor.refind(
                self.figlabel_filter.get()))
            self.figlistbox.selection_clear(0, END)
            # reset panel
        else:
            messagebox.showwarning(message='Pick processor first!')

    def after_plot(self):
        if self.figlistbox.curselection():
            figlabel = self.figlabels.get()[self.figlistbox.curselection()[0]]
            self.processor.plot(figlabel, show=False)
            if self.processor.plotter.name.startswith('mpl::'):
                if self.windows.get(figlabel, None) is None:
                    self.windows[figlabel] = MplFigWindow(
                        self.processor.plotter.get_figure(figlabel), figlabel,
                        len(self.windows), self.path, master=self.root)
                else:
                    self.windows.get(figlabel).wm_deiconify()
            else:
                messagebox.showerror(message='%s not supported with Tk!'
                                     % self.processor.plotter.name)
        else:
            messagebox.showwarning(message='Select a figure first!')

    def after_processor_name(self, event):
        self.figlabel_filter.set('^.*/.*$')
        self.figlabels.set([])
        self.figlistbox.selection_clear(0, END)
        # reset panel
        # close fig windows

    def after_figlabel(self, event):
        if self.figlistbox.curselection():
            figlabel = self.figlabels.get()[self.figlistbox.curselection()[0]]
            # update panel


class MplFigWindow(tkinter.Toplevel):
    '''
    Embed a Matplotlib figure to Tkinter GUI.
    '''

    def __init__(self, fig, figlabel, index, path, master=None, cnf={}, **kw):
        super(MplFigWindow, self).__init__(master=master, cnf=cnf, **kw)
        import matplotlib
        from matplotlib.backends.backend_tkagg import (
            FigureCanvasTkAgg, NavigationToolbar2Tk)
        from matplotlib.backend_bases import key_press_handler
        # matplotlib.use('TkAgg', warn=False, force=True)
        self.title('%s - %d - %s' % (figlabel, index, path))
        if fig:
            canvas = FigureCanvasTkAgg(fig, master=self)
            canvas.draw()
            # canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
            toolbar = NavigationToolbar2Tk(canvas, self)
            toolbar.update()
            canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

            def on_key_event(event):
                key_press_handler(event, canvas, toolbar)
            canvas.mpl_connect('key_press_event', on_key_event)

        x = int(0.05 * self.winfo_screenwidth())
        y = int(0.1 * self.winfo_screenheight())
        w = int(0.45 * self.winfo_screenwidth())
        h = int(0.8 * self.winfo_screenheight())
        self.geometry('{}x{}+{}+{}'.format(w, h, x + index % 2 * w, y))
        self.protocol("WM_DELETE_WINDOW", self.wm_withdraw)
