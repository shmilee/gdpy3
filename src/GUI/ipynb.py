# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Contains ipynb UI class.
'''

import ipywidgets
from IPython.display import display, HTML

from ..__about__ import __data_path__
from ..processors import get_processor, processor_names

__all__ = ['IpynbUI', 'ScrollTool']


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

                def observer(change):
                    self.widgets['plot'].button_style = 'primary'
                for wi in w:
                    wi.observe(observer, 'value')
                w = [ipywidgets.HBox(w[i:i+2]) for i in range(0, len(w), 2)]
                display(ipywidgets.VBox(w))

    def get_panel_widgets(self, layout):
        controls = {}
        common_kw = dict(
            style={'description_width': 'initial'},
            layout=ipywidgets.Layout(width='40%', margin='1% 2% auto 2%'),
            disabled=False)
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
                    continuous_update=False,
                    orientation='horizontal', readout=True,
                    **common_kw)
            elif v['widget'] in ('Dropdown', 'SelectMultiple'):
                controls[k] = getattr(ipywidgets, v['widget'])(
                    options=v['options'],
                    value=v['value'],
                    description=v['description'],
                    **common_kw)
            elif v['widget'] in ('Checkbox',):
                controls[k] = getattr(ipywidgets, v['widget'])(
                    value=v['value'],
                    description=v['description'],
                    **common_kw)
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


class ScrollTool(object):
    '''
    ScrollTool.bar: scroll-head, scroll-hidecode, scroll-bottom
    '''
    __slots__ = ['html']
    _replace_keys_ = ['scroll_head_title', 'scroll_bottom_title',
                      'scroll_showcode_title', 'scroll_hidecode_title']

    def __init__(self):
        import os
        import locale
        import configparser
        lang = locale.getlocale()[0]
        config = configparser.ConfigParser(default_section='en_US')
        datapath = os.path.join(__data_path__, 'ipynb_scrollbar')
        configfile = config.read(os.path.join(datapath, 'locale'))
        with open(os.path.join(datapath, 'scroll_bar.css')) as fcss, \
                open(os.path.join(datapath, 'scroll_bar.html')) as fhtml, \
                open(os.path.join(datapath, 'scroll_bar.js')) as fjs:
            css, html, js = fcss.read(), fhtml.read(), fjs.read()
            for k in self._replace_keys_:
                if lang in config and k in config[lang]:
                    v = config[lang][k]
                else:
                    v = config['en_US'][k]
                css = css.replace('{{ %s }}' % k, v)
                html = html.replace('{{ %s }}' % k, v)
                js = js.replace('{{ %s }}' % k, v)
            self.html = HTML('%s\n%s\n%s' % (css, html, js))

    @property
    def bar(self):
        return display(self.html)
