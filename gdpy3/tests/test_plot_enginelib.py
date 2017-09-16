# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import unittest
import tempfile
import numpy as np

from matplotlib.gridspec import GridSpec

from .. import glogger
from ..plot import enginelib

glogger.getGLogger('P').handlers[0].setLevel(60)

fielddata = np.array([[np.sin(m / 20) * np.cos(n / 20) for m in range(100)]
                      for n in range(66)])
zline = np.linspace(0, 15, 1000)
xline = np.sin(zline)
yline = np.cos(zline)
zdata = 15 * np.random.random(100)
xdata = np.sin(zdata) + 0.1 * np.random.randn(100)
ydata = np.cos(zdata) + 0.1 * np.random.randn(100)
mu, sigma = 100, 15
dist = mu + sigma * np.random.randn(10000)


def get_testfigstructure(engine):
    figstyle = [
        'seaborn-paper',
        {
            'figure.figsize': (10, 8),
            'figure.dpi': 80,
            'figure.subplot.wspace': 0.2,
            'figure.subplot.hspace': 0.2,
        },
        'gdpy3-notebook',
    ]
    grid = GridSpec(3, 3, wspace=0.2, hspace=0.1)
    ax1 = {
        'layout': [
            grid[0, :2],
            dict(
                title=r'field data, time=30,60$\Delta t$',
                xlabel='r',
                ylabel=r'$\phi$'
            )
        ],
        'data': [
            [1, 'plot', (fielddata[30, :], 'rs-'),
             dict(label='time=30$\Delta t$', linewidth=1)],
            [2, 'plot', (fielddata[60, :], 'go-'),
             dict(label='time=60$\Delta t$')],
            [3, 'legend', (), dict()],
        ],
        'style': ['ggplot', 'errortest', {'axes.grid': False}],
    }
    ax2 = {
        'layout': [
            grid[0, 2:],
            dict(
                title=r'field data, r=10,72$\Delta r$',
                xlabel='time',
                xlim=[0, 70],
            )
        ],
        'data': [
            [1, 'plot', (fielddata[:, 10], '-'),
             dict(label='r=10', linewidth=1)],
            [2, 'plot', (fielddata[:, 72], '-'),
             dict(label='r=72')],
            [3, 'legend', (), dict(loc='upper left')],
        ],
    }
    x, y = np.meshgrid(*[np.arange(0, x) for x in fielddata.T.shape])

    def mess_colorbar(fig, ax, art, **kwargs):
        fig.colorbar(art[1], ax=fig.get_axes()[:2])
    ax3 = {
        'layout': [
            [0.33, 0, 0.66, 0.33],
            dict(
                projection='3d',
                zlim3d=(np.min(fielddata), np.max(fielddata)),
            )
        ],
        'data': [
            [1, 'plot_surface', (x, y, fielddata),
             dict(rstride=1, cstride=1, linewidth=1,
                  antialiased=True,
                  cmap=engine.tool['get_style_param'](
                      figstyle, 'image.cmap'),
                  label='field'
                  )
             ],
            [2, 'revise', lambda fig, ax, art: fig.colorbar(art[1]), {}],
            [3, 'revise', mess_colorbar, {}],
        ],
    }
    ax4 = {
        'style': ['classic'],
        'layout': [
            335,
            dict(
                title='line3D',
                xlabel='X', ylabel='Y',
                projection='3d',
            )
        ],
        'data': [
            [1, 'plot3D', (xline, yline, zline), dict(label='line3d')],
            [2, 'scatter3D', (xdata, ydata, zdata), dict()],
        ],
    }
    ax5 = {
        'layout': [
            337,
            dict(
                title=r'$\mathrm{Histogram of IQ: }\mu=100, \sigma=15$',
                xlabel='Smarts', ylabel='Probability',
                # xticklabels='',
            )
        ],
        'data': [
            [1, 'hist', (dist, 50), dict(normed=1, label='H')],
            [2, 'legend', (), dict()],
        ],
        'style': ['default'],
    }
    ax6 = {
        'layout': [334, dict(ylabel='line1')],
        'data': [
            [1, 'plot', (zline, xline), dict(label='line1')],
            [2, 'axvspan', (6, 8), dict(
                alpha=0.5, ymin=0.6, ymax=0.9, color='red')],
            [3, 'legend', (), dict(loc='upper left')],
            [4, 'twinx', (), dict(nextcolor=2)],
            [5, 'plot', (zline, yline),
             dict(label='line2')],
            [6, 'set_ylabel', ('line2',), dict()],
            [7, 'legend', (), dict(loc='center right')],
        ],
    }
    return {
        'Style': figstyle,
        'AxesStructures': [ax1, ax2, ax3, ax4, ax5, ax6],
    }


class TestMplEngine(unittest.TestCase):
    '''
    Test class matplotlib Engine
    '''

    def setUp(self):
        self.engine = enginelib.get_engine('matplotlib')
        self.tmpfile = tempfile.mktemp(suffix='-mplfigure')

    def tearDown(self):
        for ext in ['.jpg', '.png', '.pdf']:
            tmpfile = self.tmpfile + ext
            if os.path.isfile(tmpfile):
                os.remove(tmpfile)

    def test_mplengine_style(self):
        self.assertTrue('gdpy3-notebook' in self.engine.style_available)

    def test_mplengine_tool_get_style_param(self):
        get_style_param = self.engine.tool['get_style_param']
        cmap = get_style_param('gdpy3-notebook', 'image.cmap')
        self.assertEqual(cmap, 'jet')
        cmap = get_style_param(
            ['gdpy3-notebook', {'image.cmap': 'hot'}], 'image.cmap')
        self.assertEqual(cmap, 'hot')

    def test_mplengine_z_figure_factory(self):
        fig = self.engine(get_testfigstructure(self.engine))
        for ext in ['.jpg', '.png', '.pdf']:
            tmpfile = self.tmpfile + ext
            fig.savefig(tmpfile)
        # fig.show()
        input("[I]nterrupt, to see figure in %s." % tmpfile)
        self.engine.close(fig)
