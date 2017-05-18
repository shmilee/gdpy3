#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import logging
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib import cm
import gdpy3.read as gdr
import gdpy3.plot.enginelib as elib

log0 = logging.getLogger('test')
log1 = logging.getLogger('gdr')
log2 = logging.getLogger('gdp')

if __name__ == '__main__':
    log0.setLevel(10)
    log1.setLevel(20)
    log2.setLevel(10)

    case = gdr.read('/home/IFTS_shmilee/2017-D/obo-4T-50dots-0.04/')
    grid = GridSpec(3, 3, wspace=0.2, hspace=0.1)
    testax1 = {
        'layout': [
            grid[0, :2],
            dict(
                title=r'field00-phi, time=301,600$\Delta t$',
                xlabel='r',
                ylabel=r'$\phi$'
            )
        ],
        'data': [
            [1, 'plot', (case['data1d/field00-phi'][:, 300], 'rs-'),
             dict(label='time=301$\Delta t$', linewidth=1)],
            [2, 'plot', (case['data1d/field00-phi'][:, 599], 'go-'),
             dict(label='time=600$\Delta t$')],
            [3, 'legend', (), dict()],
        ],
        'style': ['ggplot', 'errortest', {'axes.grid': False}],
    }
    testax2 = {
        'layout': [
            grid[0, 2:],
            dict(
                title=r'field00-phi, r=101,126$\Delta r$',
                xlabel='time',
                xlim=[300, 700],
                ylim=[-0.2, 0.4],
            )
        ],
        'data': [
            [1, 'plot', (case['data1d/field00-phi'][100, :], '-'),
             dict(label='r=100', linewidth=1)],
            [2, 'plot', (case['data1d/field00-phi'][125, :], '-'),
             dict(label='r=126')],
            [3, 'legend', (), dict(loc='upper left')],
        ],
    }

    # surface
    field = case['data1d/field00-phi']
    y, x = field.shape
    x = np.linspace(0, x - 1, x)
    y = np.linspace(1, y, y)
    x, y = np.meshgrid(x, y)

    def revise_surface(fig, ax):
        surf = None
        for child in ax.get_children():
            if child.get_label() == 'phi00':
                surf = child
        if surf:
            fig.colorbar(surf)
    testax3 = {
        'layout': [
            [0.33, 0, 0.66, 0.33],
            dict(
                projection='3d',
                zlim3d=(np.min(field), np.max(field)),
            )
        ],
        'data': [
            [1, 'plot_surface', (x, y, field),
                dict(cmap=cm.jet,
                     rstride=1, cstride=1, linewidth=1,
                     antialiased=True,
                     label='phi00'
                     )
             ],
        ],
        'revise': revise_surface,
    }

    zline = np.linspace(0, 15, 1000)
    xline = np.sin(zline)
    yline = np.cos(zline)
    zdata = 15 * np.random.random(100)
    xdata = np.sin(zdata) + 0.1 * np.random.randn(100)
    ydata = np.cos(zdata) + 0.1 * np.random.randn(100)
    testax4 = {
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

    mu, sigma = 100, 15
    x = mu + sigma * np.random.randn(10000)
    testax5 = {
        'layout': [
            337,
            dict(
                title=r'$\mathrm{Histogram of IQ: }\mu=100, \sigma=15$',
                xlabel='Smarts', ylabel='Probability',
                # xticklabels='',
            )
        ],
        'data': [
            [1, 'hist', (x, 50), dict(normed=1, label='H')],
            [2, 'legend', (), dict()],
        ],
        'style': ['default'],
    }

    # together
    testfigstruct = {
        'Style': [
            'seaborn-paper',
            {
                'figure.figsize': (10, 8),
                'figure.dpi': 80,
                'figure.subplot.wspace': 0.2,
                'figure.subplot.hspace': 0.2,
            }
        ],
        'AxesStructures': [
            testax1, testax2, testax3, testax4, testax5,
            {
                'layout': [336, dict()],
                'data':[
                    [1, 'plot', (range(20),), dict(label='line')],
                    [2, 'axvspan', (8, 14), dict(alpha=0.5, color='red')],
                    [3, 'legend', (), dict(loc='best')],
                ],
            }
        ],
    }
    fig = elib.get_figure_factory('mpl')(testfigstruct)
    print(fig)
    fig.show()
    input()
