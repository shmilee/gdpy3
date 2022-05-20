# -*- coding: utf-8 -*-

# Copyright (c) 2022 shmilee

'''
Extend the matplotlib Axes3D class.

ref
---
1. https://gist.github.com/WetHat/1d6cd0f7309535311a539b42cccca89c
2. mpl_toolkits.mplot3d.art3d.Text3D
'''

from matplotlib.text import Annotation
from matplotlib.patches import FancyArrowPatch
from matplotlib.artist import allow_rasterization
from mpl_toolkits.mplot3d.proj3d import proj_transform
from matplotlib import cbook
from matplotlib.axes import Axes
from mpl_toolkits.mplot3d.axes3d import Axes3D


class Annotation3D(Annotation):
    '''
    Annotation object with 3D position.
    '''

    def __str__(self):
        return "Annotation3D(%g, %g, %g, %r)" % (
            self.xy[0], self.xy[1], self.xyz[2], self._text)

    def __init__(self, text, xyz, xyztext=None, **kwargs):
        xy = xyz[:2]
        xytext = None if xyztext is None else xyztext[:2]
        Annotation.__init__(self, text, xy, xytext=xytext, **kwargs)
        self.set_3d_properties(xyz, xyztext=xyztext)

    def set_3d_properties(self, xyz, xyztext=None):
        self.xyz = xyz
        self._z = xyz[2] if xyztext is None else xyztext[2]
        self.stale = True

    @allow_rasterization
    def draw(self, renderer):
        xy = proj_transform(*self.xyz, self.axes.M)[:2]
        _x, _y, _ = proj_transform(self._x, self._y, self._z, self.axes.M)
        with cbook._setattr_cm(self, xy=xy, _x=_x, _y=_y):
            Annotation.draw(self, renderer)
        self.stale = False


def annotate3D(self, text, xyz, xyztext=None, **kwargs):
    '''
    Add anotation `text` to an `Axes3d` instance.

    Parameters
    ----------
    text: str
        The text of the annotation.
    xyz: (float, float, float)
        The point *(x, y, z)* to annotate.
    xyztext : (float, float, float), default: *xyz*
        The position *(x, y, z)* to place the text at.
    **kwargs
        Additional kwargs are passed to Axes.annotate.
    '''
    xy = xyz[:2]
    xytext = None if xyztext is None else xyztext[:2]
    annotation = super(Axes3D, self).annotate(
        text, xy, xytext=xytext, **kwargs)
    annotation.__class__ = Annotation3D
    annotation.set_3d_properties(xyz, xyztext=xyztext)
    return annotation


setattr(Axes3D, 'annotate3D', annotate3D)
setattr(Axes3D, 'annotate2D', Axes.annotate)
setattr(Axes3D, 'annotate', annotate3D)


class FancyArrowPatch3D(FancyArrowPatch):
    '''
    A fancy arrow patch with 3D positions.
    '''

    def __str__(self):
        (x1, y1, z1), (x2, y2, z2) = self._posA_posB_3D
        return f"{type(self).__name__}(({x1:g}, {y1:g}, {z1:g})->({x2:g}, {y2:g}, {z2:g}))"

    def __init__(self, posA, posB, **kwargs):
        FancyArrowPatch.__init__(self, posA=posA[:2], posB=posB[:2], **kwargs)
        self.set_3d_properties(posA, posB)

    def set_3d_properties(self, posA, posB):
        self._posA_posB_3D = [posA, posB]
        self.stale = True

    def do_3d_projection(self, renderer=None):
        (x1, y1, z1), (x2, y2, z2) = self._posA_posB_3D
        xs, ys, zs = proj_transform((x1, x2), (y1, y2), (z1, z2), self.axes.M)
        return min(zs)

    @allow_rasterization
    def draw(self, renderer):
        (x1, y1, z1), (x2, y2, z2) = self._posA_posB_3D
        xs, ys, zs = proj_transform((x1, x2), (y1, y2), (z1, z2), self.axes.M)
        _posA_posB = [(xs[0], ys[0]), (xs[1], ys[1])]
        with cbook._setattr_cm(self, _posA_posB=_posA_posB):
            FancyArrowPatch.draw(self, renderer)
        self.stale = False


def arrow3D(self, posA, posB, **kwargs):
    '''
    Add an 3d `arrow` to an `Axes3d` instance.

    Parameters
    ----------
    posA, posB : (float, float, float)
        (x, y, z) coordinates of arrow tail and arrow head respectively.
    **kwargs
        Additional kwargs are passed to `~matplotlib.patches.FancyArrowPatch`.
    '''
    arrow = FancyArrowPatch3D(posA, posB, **kwargs)
    self.add_artist(arrow)
    return arrow


setattr(Axes3D, 'arrow3D', arrow3D)
setattr(Axes3D, 'arrow2D', Axes.arrow)
setattr(Axes3D, 'arrow', Axes.arrow)
