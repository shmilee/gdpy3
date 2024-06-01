# -*- coding: utf-8 -*-

# Copyright (c) 2019-2022 shmilee

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
         dict(label=r'time=30$\Delta t$', linewidth=1)],
        [2, 'plot', (fielddata[60, :], 'go-'),
         dict(label=r'time=60$\Delta t$')],
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
        [10, 'grid', (False,), {}],
        [11, 'revise', lambda fig, ax, art: fig.colorbar(art[1]), {}],
        [12, 'revise', lambda fig, ax, art: fig.colorbar(
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
        [3, 'revise', 'remove_spines', dict(select=('x', 'y'))],
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
        [1, 'hist', (dist, 50), dict(density=1, label='H')],
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
x = np.linspace(1, 2)
y = np.linspace(1, 1.5)
ax7 = {
    'layout': [(0.05, 0.05, 0.45, 0.9), dict()],
    'data': [
            [1, 'plot', (x, y), dict(label=r'org')],
            [2, 'plot', (x, y*2), dict(label=r'*2')],
            [3, 'plot', (x, y*3), dict()],
            [44, 'plot', (x, y*4), dict(label=r'*4')],
            [5, 'plot', (x, y*5), dict(label=r'*5')],
            [6, 'plot', (x, y*6), dict()],
            [7, 'plot', ([x, x], [-y*7, -y*7.5]), dict(label=r'*7')],
            [23, 'revise', 'center_spines', dict(
                position='zero', position_left=('data', 1.5))],
            [23, 'revise', 'multi_merge_legend', dict(
                groups=[
                    dict(index=[(1, 2), 3], labels=[None, r'*3'],
                         loc='upper left'),
                    dict(index=[(44, 5), 6, 7], labels=None,
                         loc=(0.03, 0.1), ncol=2),
                ],
                max_artists_per_handler=20,
                sep=', ',
            )],
    ]
}
ax8 = {
    'layout': [
        121,
        dict(
            title='annotate3D',
            xlabel='X', ylabel='Y', zlabel='Z',
            projection='3d',
        )
    ],
    'data': [
        [1, 'scatter', ([0, 0, 0], [0, 0, 1], [0, 1, 0]), dict(marker='o')],
        [2, 'annotate3D', ('point 1', (0, 0, 0)), dict(
            xyztext=(0.01, 0.01, 0.01))],
        [3, 'annotate', ('point 2', (0, 1, 0)), dict(
            xyztext=(-30, -30, 30), textcoords='offset points',
            arrowprops=dict(ec='black', fc='white', shrink=2.5))],
        [4, 'annotate3D', ('point 3', (0, 0, 1)), dict(
            xyztext=(0.02, 0.1, 0.3),
            bbox=dict(boxstyle="round", fc="lightyellow"),
            arrowprops=dict(arrowstyle="-|>", ec='black', fc='white', lw=5))],
    ],
}
ax9 = {
    'layout': [
        122,
        dict(
            title='arrow3D',
            xlabel='X', ylabel='Y', zlabel='Z', xlim=[0, 2],
            projection='3d',
        )
    ],
    'data': [
        [1, 'arrow3D', ((0, 0, 0), (1, 1, 1)), dict(
            mutation_scale=20, arrowstyle="-|>", linestyle='dashed')],
        [2, 'arrow3D', ((1, 0, 0), (2, 1, 1)), dict(
            mutation_scale=20, ec='green', fc='red')],
    ],
}
x = np.linspace(-np.pi, np.pi, 100)
y = 2 * np.sin(x)
ax10 = {
    'layout': [122, dict(xlabel='X', ylabel='Y')],
    'data': [
        [1, 'plot', (x, y), dict()],
        [2, 'revise', 'arrow_spines', dict(position_bottom=-1, arrow_size=8)],
        [3, 'text', (0.2, 2.2, 'arrow spines'), {}],
    ],

}
temp_contourfresults = dict(
    X=fieldx, Y=fieldy, Z=fielddata, clabel_levels=[-0.5, 0, 0.5],
    plot_method='plot_surface',
    plot_method_kwargs=dict(rstride=1, cstride=1, linewidth=1,
                            antialiased=True, label='field'),
    title='test field', xlabel='r', ylabel='time',
    plot_surface_shadow=['x', 'z'],
)
temp_lineresults = dict(
    LINE=[
        ([3, 6], [1.5, 1]),
        (np.linspace(0, 9, 31), np.sin(np.linspace(0, 9, 31)), 'sin'),
        (range(100), fielddata[30, :], r'field, time=30$\Delta t$'),
    ],
    title='test title', xlabel='X', ylabel='Y',
    xlim=[0, 30], ylabel_rotation=45, legend_kwargs=dict(loc=0),
)
temp_sharextwinxresults = dict(
    X=range(100),
    YINFO=[{
        'left': [(fielddata[20, :], r'time=20$\Delta t$'),
                 (fielddata[5, :], r'time=5$\Delta t$')],
        'right': [(fielddata[32, :], r'time=32$\Delta t$'),
                  (range(20, 81), fielddata[34, 20:81]),
                  (range(30, 71), fielddata[36, 30:71], r'time=36$\Delta t$')],
        # 'rlegend': dict(loc='best'),
        'lylabel': r'$\phi$',
    }, {
        'left': [(fielddata[40, :], r'time=40$\Delta t$')],
        'right': [],
        'lylabel': r'$\phi$',
    }, {
        'left': [(fielddata[60, :], r'time=60$\Delta t$')],
        'right': [],
        'lylabel': r'$\phi$',
    },
    ],
    title='field data',
    xlabel='R',
    xlim=[0, 90],
    ylabel_rotation=45,
)
temp_z111presults = dict(
    zip_results=[
        ('tmpl_line', 221, temp_lineresults),
        ('tmpl_contourf', 223, temp_contourfresults),
        ('tmpl_sharextwinx', 122, temp_sharextwinxresults),
    ],
    suptitle='test z111p figures'
)

temp_z111presults_merge = dict(
    zip_results=[
        ('tmpl_contourf', 211, dict(
            X=fieldx, Y=fieldy, Z=fielddata, clabel_levels=[-0.5, 0, 0.5],
            title='test field', xlabel='r', ylabel='time',
        )),
        ('tmpl_line', 211, dict(
            LINE=[
                (np.linspace(20, 80, 120), 30+10 *
                 np.sin(np.linspace(20, 80, 120)), 'sin'),
                (range(100), np.linspace(0, 65, 100), 'cross'),
            ])),
    ],
    suptitle='test z111p merge figures'
)


class TestMatplotlibVisplter(unittest.TestCase):
    '''
    Test class MatplotlibVisplter
    '''

    def setUp(self):
        from ..mplvisplter import MatplotlibVisplter
        self.visplter = MatplotlibVisplter('mpl::test')
        self.tmpfile = tempfile.mktemp(suffix='-mplfigure')

    def tearDown(self):
        for ext in ['.jpg', '.png', '.pdf']:
            if os.path.isfile(self.tmpfile + ext):
                os.remove(self.tmpfile + ext)

    def test_mplvisplter_style(self):
        self.assertTrue('ggplot' in self.visplter.style_available)
        self.assertListEqual(self.visplter.style, ['gdpy3-notebook'])
        self.assertListEqual(
            self.visplter.check_style(['ggplot', '-rm', {'figure.dpi': 80}]),
            ['ggplot', {'figure.dpi': 80}])
        libpath = self.visplter.style_ext_library['gdpy3-notebook']
        libpath = self.visplter.style_ext_library[libpath]
        self.assertListEqual(
            self.visplter.filter_style(['ggplot', 'gdpy3-notebook']),
            ['ggplot', os.path.join(libpath, 'gdpy3-notebook.mplstyle')])
        self.assertEqual(self.visplter.param_from_style('image.cmap'), 'jet')
        self.assertFalse(self.visplter.param_from_style('image.cmapNone'))
        self.visplter.style = ['gdpy3-notebook', {'image.cmap': 'hot'}]
        self.assertEqual(self.visplter.param_from_style('image.cmap'), 'hot')

    def test_mplvisplter_figure(self):
        self.visplter.create_figure('test-f1', add_style=['ggplot'])
        self.visplter.add_axes(self.visplter.get_figure('test-f1'), ax1)
        for ext in ['.jpg', '.png', '.pdf']:
            self.visplter.save_figure('test-f1', self.tmpfile + ext)
        input("[I]nterrupt, to see figure in %s." % self.tmpfile)
        self.visplter.create_figure('test-f2', ax1, ax2, ax3, ax4, ax5, ax6)
        self.visplter.show_figure('test-f2')
        input('[I]nterrupt, to see figure "%s".' % 'test-f2')
        self.assertSetEqual(set(self.visplter.figures), {'test-f1', 'test-f2'})
        self.visplter.close_figure('test-f1')
        self.assertListEqual(self.visplter.figures, ['test-f2'])
        self.visplter.close_figure('all')

        self.assertListEqual(self.visplter.figures, [])

    def test_mplvisplter_figure_extending(self):
        self.visplter.create_figure('test-extend', ax8, ax9)
        self.visplter.show_figure('test-extend')
        input('[I]nterrupt, to see figure "%s".' % 'test-extend')
        self.visplter.close_figure('all')

    def test_mplvisplter_revise_functions(self):
        self.visplter.create_figure('test-rev1', ax7, ax10)
        self.visplter.show_figure('test-rev1')
        input('[I]nterrupt, to see figure "%s".' % 'test-rev1')
        self.visplter.close_figure('all')

    def test_mplvisplter_tmpl_contourf(self):
        axstruct, sty = self.visplter.tmpl_contourf(
            temp_contourfresults)
        self.visplter.create_figure('template-f1', *axstruct, add_style=sty)
        self.visplter.show_figure('template-f1')
        input('[I]nterrupt, to see figure "%s".' % 'template-f1')
        self.visplter.close_figure('template-f1')

    def test_mplvisplter_tmpl_line(self):
        axstruct, sty = self.visplter.tmpl_line(temp_lineresults)
        self.visplter.create_figure('template-f2', *axstruct, add_style=sty)
        self.visplter.show_figure('template-f2')
        input('[I]nterrupt, to see figure "%s".' % 'template-f2')
        self.visplter.close_figure('template-f2')

    def test_mplvisplter_tmpl_sharextwinx(self):
        axstruct, sty = self.visplter.tmpl_sharextwinx(
            temp_sharextwinxresults)
        self.visplter.create_figure('template-f3', *axstruct, add_style=sty)
        self.visplter.show_figure('template-f3')
        input('[I]nterrupt, to see figure "%s".' % 'template-f3')
        self.visplter.close_figure('template-f3')

    def test_visplter_tmpl_z111p(self):
        axstruct, sty = self.visplter.tmpl_z111p(temp_z111presults)
        self.visplter.create_figure('template-fz', *axstruct, add_style=sty)
        self.visplter.show_figure('template-fz')
        input('[I]nterrupt, to see figure "%s".' % 'template-fz')
        axstruct, sty = self.visplter.tmpl_z111p(temp_z111presults_merge)
        self.visplter.create_figure('template-fzm', *axstruct, add_style=sty)
        self.visplter.show_figure('template-fzm')
        input('[I]nterrupt, to see figure "%s".' % 'template-fzm')
        self.visplter.close_figure('all')
