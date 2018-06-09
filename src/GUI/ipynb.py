# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains ipynb UI class.
'''

import ipywidgets
from IPython.display import display
from ..processors import get_processor, processor_names


class IpynbUI(object):
    '''
    UI(User Interface) used in Jupyter notebook.
    '''
    __slots__ = ['path', 'processor', 'widgets', 'panel_widgets', 'figlabel']

    def __init__(self, path):
        self.path = path
        self.processor = None
        self.widgets = dict(
            processor=ipywidgets.Dropdown(
                options=processor_names,
                value=processor_names[0],
                description='Processor:'),
            pick=ipywidgets.Button(
                description='', disabled=False,
                button_style='primary',  # 'success', 'info', or ''
                tooltip='Pick', icon='arrow-circle-right',
                layout=ipywidgets.Layout(width='5%')),
            scope=ipywidgets.Dropdown(
                options=[None],
                value=None,
                description='Scope:'),
            figlabel=ipywidgets.Dropdown(
                options=[None],
                value=None,
                description='Figure:',
                layout=ipywidgets.Layout(left='-15px')),
            plot=ipywidgets.Button(
                description='', disabled=False,
                button_style='primary',
                tooltip='Plot', icon='paint-brush',
                layout=ipywidgets.Layout(width='5%')),
            terminal=ipywidgets.Output(),
            panel=ipywidgets.Output(),
            canvas=ipywidgets.Output(),
        )
        self.panel_widgets = {}
        self.figlabel = None

        self.widgets['processor'].observe(self.init_scope, 'value')
        self.widgets['pick'].on_click(self.update_scope)
        self.widgets['scope'].observe(self.update_figlabel, 'value')
        self.widgets['figlabel'].observe(self.update_panel, 'value')
        self.widgets['plot'].on_click(self.update_canvas)

    def init_scope(self, *args):
        self.widgets['scope'].options = [None]
        self.widgets['scope'].value = None
        self.widgets['pick'].button_style = 'primary'

    def update_scope(self, *args):
        gdp = get_processor(self.widgets['processor'].value)
        with self.widgets['terminal']:
            gdp.pick(self.path)
        if gdp.pckloader:
            self.processor = gdp
            options = sorted(gdp.layout.keys())
            self.widgets['scope'].options = options
            self.widgets['scope'].value = options[0]
            self.widgets['pick'].button_style = 'success'

    def update_figlabel(self, *args):
        options = self.processor.layout.get(
            self.widgets['scope'].value, [None])
        self.widgets['figlabel'].options = options
        self.widgets['figlabel'].value = options[0]
        self.widgets['plot'].button_style = 'primary'

    def update_panel(self, *args):
        self.widgets['plot'].button_style = 'primary'
        if self.widgets['figlabel'].value:
            self.figlabel = '%s/%s' % (
                self.widgets['scope'].value, self.widgets['figlabel'].value)
            with self.widgets['terminal']:
                figinfo = self.processor.get(self.figlabel)
        else:
            self.figlabel, figinfo = None, None
        if figinfo:
            self.panel_widgets = self.get_panel_widgets(figinfo.layout)
            self.widgets['panel'].clear_output(wait=True)
            with self.widgets['panel']:
                w = list(self.panel_widgets.values())
                w = [ipywidgets.HBox(w[i:i+2]) for i in range(0, len(w), 2)]
                display(ipywidgets.VBox(w))

    def get_panel_widgets(self, layout):
        controls = {}
        for k, v in layout.items():
            if v['widget'] in (
                    'IntSlider', 'FloatSlider',
                    'IntRangeSlider', 'FloatRangeSlider'):
                controls[k] = getattr(ipywidgets, v['widget'])(
                    value=v['value'],
                    min=v['rangee'][0],
                    max=v['rangee'][1],
                    step=v['rangee'][2],
                    description=v['description'],
                    style={'description_width': 'initial'},
                    layout=ipywidgets.Layout(width='50%'),
                    disabled=False, continuous_update=False,
                    orientation='horizontal', readout=True)
            else:
                pass
        return controls

    def update_canvas(self, *args):
        if self.figlabel:
            figkwargs = {k: v.value for k, v in self.panel_widgets.items()}
            with self.widgets['terminal']:
                figure = self.processor.plot(self.figlabel, **figkwargs)
            if figure:
                self.widgets['canvas'].clear_output(wait=True)
                with self.widgets['canvas']:
                    # print(figkwargs)
                    display(self.processor.plotter.get_figure(self.figlabel))
                self.widgets['plot'].button_style = 'success'
        else:
            self.widgets['canvas'].clear_output(wait=True)
            with self.widgets['canvas']:
                print("No figure to plot!")

    @property
    def UI(self):
        return display(ipywidgets.VBox([
            ipywidgets.HBox([
                self.widgets['processor'],
                self.widgets['pick'],
                self.widgets['scope'],
                self.widgets['figlabel'],
                self.widgets['plot'],
            ]),
            self.widgets['panel'],
            self.widgets['canvas'],
        ]))

    def clear_log(self, wait=False):
        self.widgets['terminal'].clear_output(wait=wait)

    @property
    def log(self):
        return display(self.widgets['terminal'])
