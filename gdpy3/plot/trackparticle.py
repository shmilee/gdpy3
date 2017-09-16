# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
Particle orbit figures
----------------------

This module needs tracking particle data in group 'trackp' get by gdc.

This module provides the :class:`TrackParticleFigureV110922`.
'''

import types
import numpy as np

from . import tools
from .gfigure import GFigure, log

__all__ = ['TrackParticleFigureV110922']


class TrackParticleFigureV110922(GFigure):
    '''
    A class for figures of Particle Orbit
    '''
    __slots__ = []
    _FigGroup = 'trackp'
    _OrbitFigInfo = {
        'orbit_%s_%s' % (dim, s): dict(
            dimension=dim,
            species=s,
            track='trackp/%s-' % s,
            key=[GFigure._paragrp + 'r0'])
        for s in ['ion', 'electron']  # , 'fastion']
        for dim in ['2d', '3d']
    }
    _FigInfo = dict(_OrbitFigInfo)

    def __init__(self, dataobj, name,
                 group=_FigGroup, figurestyle=['gdpy3-notebook']):
        if name not in self._FigInfo.keys():
            raise ValueError("'%s' not found in group '%s'!" % (name, group))
        info = self._FigInfo[name]
        super(TrackParticleFigureV110922, self).__init__(
            dataobj, name, group, info, figurestyle=figurestyle)

    def calculate(self, **kwargs):
        '''
        Get the FigureStructure and calculation results.
        Save them in *figurestructure*, *calculation*.

        Notes
        -----
        2d, 3d orbit kwargs:
            key: key function for `sorted`,
                 or str 'increase', 'in-', 'decrease', 'de-', 'random',
                 default 'increase'.
            index: list of sorted particles in self.dataobj,
                   len(index) must be 9,
                   default range(9)
        '''
        log.debug("Get FigureStructure, calculation of '%s' ..." % self.Name)
        self.figurestructure = {
            'Style': self.figurestyle,
            'AxesStructures': [],
        }
        self.calculation = {}

        if self.name in self._OrbitFigInfo:
            return _set_orbit_axesstructures(self, **kwargs)
        else:
            return False


def _set_orbit_axesstructures(self, **kwargs):
    '''
    Set particle 2d or 3d orbit axesstructures, calculation
    '''
    dim = self.figureinfo['dimension']
    species = self.figureinfo['species']
    r0 = self.dataobj[self.figureinfo['key'][0]]
    particles = self.dataobj.find(self.figureinfo['track'])
    total = len(particles)
    log.parm("Total number of tracked %s particles: %d." % (species, total))
    # sorted key function
    if 'key' not in kwargs:
        kwargs['key'] = 'increase'
    if isinstance(kwargs['key'], types.FunctionType):
        skey = kwargs['key']
    elif kwargs['key'] in ('in-', 'increase'):
        def skey(n): return int(n.split('-')[1] * 10 + n.split('-')[2])
    elif kwargs['key'] in ('de-', 'decrease'):
        def skey(n): return -int(n.split('-')[1] * 10 + n.split('-')[2])
    elif kwargs['key'] == 'random':
        def skey(n): return np.random.random()
    else:
        log.warn("Invalid `sorted` key for tracked particles. Use 'random'.")

        def skey(n): return np.random.random()
    sortedparticles = sorted(particles, key=skey)
    # index of sorted particles
    if 'index' not in kwargs:
        index = range(9)
    else:
        if isinstance(kwargs['index'], (range, list, tuple)):
            ilen = len(kwargs['index'])
            if ilen == 9:
                index = kwargs['index']
            else:
                log.warn("Too many indices, slicing [:9].")
                index = kwargs['index'][:9]
        else:
            index = range(9)
    # get axes
    for n, idx in enumerate(index):
        number = int("33%s" % str(n + 1))
        log.debug("Getting Axes %d ..." % number)
        if idx + 1 > total:
            log.error("Failed to get Axes %d ..." % number)
            continue
        try:
            pdata = self.dataobj[sortedparticles[idx]]
            pname = sortedparticles[idx].replace(self.figureinfo['track'], '')
            R = pdata[:, 1] * r0
            Z = pdata[:, 2] * r0
            if dim == '2d':
                drmax = 1.1 * max(abs(np.max(R) - r0), np.max(Z),
                                  abs(r0 - np.min(R)), abs(np.min(Z)))
                axes = {
                    'data': [
                            [1, 'plot', (R, Z), dict()],
                            [2, 'set_aspect', ('equal',), dict()],
                    ],
                    'layout': [
                        number, dict(
                            title=pname,
                            xlim=[r0 - drmax, r0 + drmax],
                            ylim=[-drmax, drmax],
                            **{'xlabel': 'R(cm)' if n in (6, 7, 8) else ''},
                            **{'ylabel': 'Z(cm)' if n in (0, 3, 6) else ''})
                    ],
                }
                if species == 'ion':
                    # find dr = |Rmax-Rmin| while z=0
                    fR = []
                    for t in range(0, len(R) - 1):
                        if Z[t] * Z[t + 1] < 0:
                            fR.append((R[t] + R[t + 1]) / 2)
                    Rmin = sum(fR[::2]) / len(fR[::2])
                    Rmax = sum(fR[1::2]) / len(fR[1::2])
                    dr = abs(Rmax - Rmin)
                    # theta M
                    mpoints = np.array(sorted(zip(R, Z),
                                              key=lambda p: p[0])[:4])
                    minR = np.average(mpoints[:, 0])
                    minZ = np.average(np.abs(mpoints[:, 1]))
                    minvec = [minR - r0, minZ]
                    costhetaM = np.inner([r0, 0], minvec) / r0 / \
                        np.sqrt(np.inner(minvec, minvec))
                    thetaM = np.arccos(costhetaM) * 180 / np.pi
                    axes['data'] = [
                        [1, 'plot', (R, Z),
                         dict(label='$\Delta R$ = %.3f' % dr)],
                        [2, 'plot', ([Rmin, Rmin],
                                     [-0.6 * drmax, 0.6 * drmax]),
                         dict(label='R=%.3f' % Rmin)],
                        [3, 'plot', ([Rmax, Rmax],
                                     [-0.6 * drmax, 0.6 * drmax]),
                         dict(label='R=%.3f' % Rmax)],
                        [4, 'plot', ([r0, r0 + drmax], [0, 0], 'k'), {}],
                        [5, 'plot', ([r0, minR], [0, minZ]), {}],
                        [6, 'text', (r0 + 1, 0 + 1,
                                     r'$\theta$ = %.2f' % thetaM), {}],
                        [7, 'legend', (), dict()],
                        [8, 'set_aspect', ('equal',), dict()],
                    ]
                    self.calculation.update(
                        {'%s-dr' % pname: dr, '%s-theta' % pname: thetaM})
            elif dim == '3d':
                zeta = pdata[:, 3]
                X = R * np.cos(zeta)
                Y = R * np.sin(zeta)
                rmax = 1.05 * np.max(R)
                scale = [-rmax, rmax]
                axes = {
                    'data': [
                        [1, 'plot', (X, Y, Z), dict(linewidth=1)],
                        [2, 'set_aspect', ('equal',), dict()],
                        [3, 'auto_scale_xyz', (scale, scale, scale), dict()],
                    ],
                    'layout': [
                        number, dict(
                            title=pname, projection='3d',
                            **{'xlabel': 'X(cm)' if n in (6, 7, 8) else ''},
                            **{'ylabel': 'Y(cm)' if n in (6, 7, 8) else ''},
                            **{'zlabel': 'Z(cm)' if n in (2, 5, 8) else ''})
                    ],
                }
            else:
                pass
            # suptitle
            if n == 0:
                order = len(axes['data']) + 1

                def addsuptitle(fig, ax, art): return fig.suptitle(
                    "%s orbits of %s (9/%d)" % (dim.upper(), species, total))
                axes['data'].append([order, 'revise', addsuptitle, dict()])
        except Exception:
            log.error("Failed to get data of '%s' from %s!"
                      % (species + ':' + pname, self.dataobj.file), exc_info=1)
        else:
            self.figurestructure['AxesStructures'].append(axes)
    return True
