# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

import os
import unittest
import tempfile
import numpy as np
from matplotlib.gridspec import GridSpec

fielddata = np.array([[np.sin(m / 20) * np.cos(n / 20) for m in range(100)]
                      for n in range(66)])
fieldx, fieldy = np.meshgrid(*[np.arange(0, x) for x in fielddata.T.shape])
zline = np.linspace(0, 15, 1000)
xline = np.sin(zline)
yline = np.cos(zline)
zdata = 15 * np.random.random(100)
xdata = np.sin(zdata) + 0.1 * np.random.randn(100)
ydata = np.cos(zdata) + 0.1 * np.random.randn(100)
mu, sigma = 100, 15
dist = mu + sigma * np.random.randn(10000)
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
    'axstyle': ['ggplot', 'errortest', {'axes.grid': False}],
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
ax3 = {
    'layout': [
        [0.33, 0, 0.66, 0.33],
        dict(
            projection='3d',
            zlim3d=(np.min(fielddata), np.max(fielddata)),
        )
    ],
    'data': [
        [1, 'plot_surface', (fieldx, fieldy, fielddata),
         dict(rstride=1, cstride=1, linewidth=1,
              antialiased=True, cmap='jet', label='field')],
        [2, 'revise', lambda fig, ax, art: fig.colorbar(art[1]), {}],
        [3, 'revise', lambda fig, ax, art: fig.colorbar(
            art[1], ax=fig.get_axes()[:2]), {}],
    ],
}
ax4 = {
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
    'axstyle': ['classic'],
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
    'axstyle': ['default'],
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


class TestMatplotlibPlotter(unittest.TestCase):
    '''
    Test class MatplotlibPlotter
    '''

    def setUp(self):
        from ..mplplotter import MatplotlibPlotter
        self.plotter = MatplotlibPlotter('mpl::test')
        self.tmpfile = tempfile.mktemp(suffix='-mplfigure')

    def tearDown(self):
        for ext in ['.jpg', '.png', '.pdf']:
            if os.path.isfile(self.tmpfile + ext):
                os.remove(self.tmpfile + ext)

    def test_mplplotter_style(self):
        self.assertTrue('seaborn' in self.plotter.style_available)
        self.assertListEqual(self.plotter.style, ['gdpy3-notebook'])
        self.assertListEqual(
            self.plotter.check_style(['seaborn', '-rm', {'figure.dpi': 80}]),
            ['seaborn', {'figure.dpi': 80}])
        self.assertListEqual(
            self.plotter.filter_style(['seaborn', 'gdpy3-notebook']),
            ['seaborn', os.path.join(
                self.plotter._MatplotlibPlotter__STYLE_LIBPATH,
                'gdpy3-notebook.mplstyle')])
        self.assertEqual(self.plotter.param_from_style('image.cmap'), 'jet')
        self.assertFalse(self.plotter.param_from_style('image.cmapNone'))
        self.plotter.style = ['gdpy3-notebook', {'image.cmap': 'hot'}]
        self.assertEqual(self.plotter.param_from_style('image.cmap'), 'hot')

    def test_mplplotter_figure(self):
        self.plotter.create_figure('test-f1', add_style=['seaborn'])
        self.plotter.add_axes(self.plotter.get_figure('test-f1'), ax1)
        self.plotter.show_figure('test-f1')
        input('[I]nterrupt, to see figure "%s".' % 'test-f1')
        self.plotter.create_figure('test-f2', ax1, ax2, ax3, ax4, ax5, ax6)
        for ext in ['.jpg', '.png', '.pdf']:
            self.plotter.save_figure('test-f2', self.tmpfile + ext)
        input("[I]nterrupt, to see figure in %s." % self.tmpfile)
        self.assertSetEqual(set(self.plotter.figures), {'test-f1', 'test-f2'})
        self.plotter.close_figure('test-f1')
        self.assertListEqual(self.plotter.figures, ['test-f2'])
        self.plotter.close_figure('all')
        self.assertListEqual(self.plotter.figures, [])
