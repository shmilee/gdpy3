# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

import os
import time
import tempfile
import getpass
import tkinter
from tkinter import ttk, simpledialog, filedialog, messagebox
from tkinter.constants import *
from distutils.version import LooseVersion

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
        img = tkinter.PhotoImage(file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'icon', 'main_128.gif'))
        root.tk.call('wm', 'iconphoto', root._w, "-default", img)
        root.protocol("WM_DELETE_WINDOW", root.destroy)
        style = ttk.Style()
        font = ('Microsoft YaHei', 10)
        width = 0
        style.configure('.', font=font)
        main = ttk.Frame(root, relief=RIDGE, borderwidth=2)
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
        # 3 - VerticalScrolledFrame
        w_kw_out_frame = ttk.Frame(w_frame_panel)
        w_kw_scrollbar = ttk.Scrollbar(w_kw_out_frame, orient=VERTICAL)
        w_kw_scrollbar.pack(fill=Y, side=RIGHT, expand=0)
        w_kw_canvas = tkinter.Canvas(
            w_kw_out_frame, bd=0, highlightthickness=0,
            yscrollcommand=w_kw_scrollbar.set, width=0, height=160)
        w_kw_canvas.pack(side=LEFT, fill=BOTH, anchor=W, expand=1)
        w_kw_scrollbar.config(command=w_kw_canvas.yview)
        w_kw_canvas.xview_moveto(0)
        w_kw_canvas.yview_moveto(0)
        w_kw_in_frame = ttk.Frame(w_kw_canvas)
        w_kw_canvas.create_window(0, 0, window=w_kw_in_frame, anchor=NW)

        def _configure_canvas_interiorframe(event):
            w_kw_canvas.update_idletasks()
            w_kw_canvas.configure(scrollregion=w_kw_canvas.bbox("all"))
        w_kw_in_frame.bind('<Configure>', _configure_canvas_interiorframe)

        def _on_mousewheel(event):
            number = 0
            # Linux wheel event: event.delta = 0, event.num = 4 or 5
            # Windows wheel event: event.delta = -120 or 120 ?
            if event.num == 5 or event.delta == -120:
                number = 1  # down
            if event.num == 4 or event.delta == 120:
                number = -1  # up
            # print(number)
            w_kw_canvas.yview_scroll(number, "units")
        w_kw_canvas.bind("<MouseWheel>", _on_mousewheel)
        w_kw_canvas.bind("<Button-4>", _on_mousewheel)
        w_kw_canvas.bind("<Button-5>", _on_mousewheel)
        w_kw_out_frame.pack(in_=w_frame_panel, side=TOP,
                            expand=1, fill=X, padx=5, pady=5)
        w_plot = ttk.Button(
            w_frame_panel, text='Plot', width=8, command=self.after_plot)
        w_plot.pack(in_=w_frame_panel, side=BOTTOM, anchor=E, padx=5, pady=5)
        w_frame_panel.grid(row=2, column=0, padx=10, pady=5, sticky=W+E)
        # 4 - bottom
        w_info = tkinter.Label(
            main, relief=RIDGE, borderwidth=1, anchor=E, font=(font[0], 8),
            text="Version %s\t© %s shmilee\t" % (
                gdpy3_version, time.strftime('%Y')))
        w_info.grid(row=3, column=0, sticky=W+E)
        # X - for share
        self.root = root
        self.center(root)
        self.processor_name = w_str_proc
        self.figlabel_filter = w_str_filter
        self.figlabels = w_list_fig
        self.figlistbox = w_listbox_fig
        self.figkwframe = w_kw_in_frame
        self.path = path
        self.processor = None
        self.figkwslib = {}  # all figure kwargs widgets, key is figlabel
        self.figkws = {}  # kwargs widgets mapped in panel
        self.windows = {}  # all plotted figure windows, key is figlabel
        # X - events
        w_select_proc.bind("<<ComboboxSelected>>", self.after_processor_name)
        w_entry_filter.bind("<Return>", self.after_filter)
        w_listbox_fig.bind("<<ListboxSelect>>", self.after_figlabel)
        # X - start
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

    def reset_panel(self, clear_lib=False):
        for n, w in self.figkws.items():
            w.grid_forget()
            w.pack_forget()
            w.place_forget()
        self.figkws = {}
        if clear_lib:
            for figlabel in self.figkwslib:
                for n, w in self.figkwslib[figlabel].items():
                    w.destroy()
            self.figkwslib = {}

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
                self.reset_panel(clear_lib=True)
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
            self.reset_panel()
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
                        len(self.windows), self.path, master=self.root,
                        class_='gdpy3-gui')
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
        self.reset_panel(clear_lib=True)
        # close fig windows

    def after_figlabel(self, event):
        if self.figlistbox.curselection():
            figlabel = self.figlabels.get()[self.figlistbox.curselection()[0]]
            # update panel
            self.reset_panel()
            if figlabel in self.figkwslib:
                print("Use old widgets")
                for n, w in self.figkwslib[figlabel].items():
                    w.pack()
            else:
                print("Gen new widgets")
                self.figkwslib[figlabel] = {}
                for i in range(len(figlabel)):  # TODO
                    self.figkwslib[figlabel][i] = ttk.Button(
                        self.figkwframe, text="Button " + str(i))
                    self.figkwslib[figlabel][i].pack()
            self.figkws = self.figkwslib[figlabel]
            print(self.figkws[len(figlabel) - 1])


class MplFigWindow(tkinter.Toplevel):
    '''
    Embed a Matplotlib figure to Tkinter GUI.
    '''

    def __init__(self, fig, figlabel, index, path, master=None, cnf={}, **kw):
        super(MplFigWindow, self).__init__(master=master, cnf=cnf, **kw)
        import matplotlib
        import matplotlib.backends.backend_tkagg as tkagg
        if LooseVersion(matplotlib.__version__) <= LooseVersion('2.1.2'):
            # print('Recommand matplotlib>=2.2.0')
            tkagg.NavigationToolbar2Tk = tkagg.NavigationToolbar2TkAgg
        from matplotlib.backend_bases import key_press_handler
        # matplotlib.use('TkAgg', warn=False, force=True)
        self.title('%s - %d - %s' % (figlabel, index, path))
        if fig:
            canvas = tkagg.FigureCanvasTkAgg(fig, master=self)
            canvas.draw()
            # canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
            toolbar = tkagg.NavigationToolbar2Tk(canvas, self)
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
