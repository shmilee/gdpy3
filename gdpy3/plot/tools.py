# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import logging
import numpy as np
import matplotlib.style.core as score
import gdpy3.read as gdr

from matplotlib import rcParams

__all__ = ['is_dictobj', 'in_dictobj',
           'mplstyle_available', 'mplstylelib', 'mplcmap',
           'colorbar_revise_function',
           'max_subarray', 'fitline', 'argrelextrema',
           'fft', 'savgol_golay_filter', 'findflat',
           ]

log = logging.getLogger('gdp')


# 1. dictobj

def is_dictobj(dictobj):
    '''
    Check if *dictobj* is a instance of :class:`gdpy3.read.readnpz.ReadNpz`.
    '''
    if isinstance(dictobj, gdr.ReadNpz):
        return True
    else:
        return False


def in_dictobj(dictobj, *keys):
    '''
    Check if all the *keys* are in *dictobj*.
    '''
    result = True
    for key in keys:
        if key not in dictobj.datakeys:
            log.warn("Key '%s' not in %s!" % (key, dictobj.file))
            result = False
    return result


# 2. mplstyle

__mplstylepath = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'mpl-stylelib')
mplstyle_available = score.available


def __update_gdpy3_mplstyle_library():
    global mplstyle_available
    for path, name in score.iter_style_files(__mplstylepath):
        mplstyle_available.append(name)
__update_gdpy3_mplstyle_library()


def mplstylelib(style=None):
    '''
    Filter the *style*.
    If the name starts with 'gdpy3-', change it to absolute path.
    Return str of mplstyle.
    '''
    if style not in mplstyle_available:
        log.warn("'%s' not found in the style library! Use 'default'!" % style)
        return 'default'
    # start with 'gdpy3-'
    if style.startswith('gdpy3-'):
        return os.path.join(__mplstylepath, style + '.mplstyle')
    # score.available
    return style


def mplcmap(figurestyle):
    '''
    Return using cmap, for Axes3D
    '''
    if 'image.cmap' in rcParams:
        with score.context(figurestyle):
            return rcParams['image.cmap']
    else:
        return 'jet'


# 3. FigureStructure, revise function

def colorbar_revise_function(label, grid_alpha=0.3, **kwargs):
    '''
    Return a colorbar `revise function` for FigureStructure.

    Parameters
    ----------
    label: label of mappable which the colorbar applies
    keyword arguments: kwargs passed to colorbar
        *cax*, *ax*, *fraction*, *pad*, *ticks*, etc.
    '''
    def revise_func(figure, axes):
        axes.grid(alpha=grid_alpha)
        mappable = None
        for child in axes.get_children():
            if child.get_label() == label:
                mappable = child
        if mappable:
            figure.colorbar(mappable, **kwargs)
    return revise_func


# 4 . math, numpy, etc.

def max_subarray(A):
    '''
    Maximum subarray problem
    '''
#    region_len = 0
#    thissum = 0
#    for a in A:
#        thissum += a
#        if thissum < 0:
#            thissum = 0
#        if thissum > region_len:
#            region_len = thissum
    max_ending_here = max_so_far = A[0]
    for x in A[1:]:
        max_ending_here = max(x, max_ending_here + x)
        max_so_far = max(max_so_far, max_ending_here)
    return max_so_far


def fitline(X, Y, deg, info=''):
    '''
    One-dimensional polynomial fit
    '''
    fitresult = np.polyfit(X, Y, deg, full=True)
    log.debug("Fitting line '%s' result:" % info)
    log.debug("%s" % (fitresult,))
    fit_p = np.poly1d(fitresult[0])
    return fitresult, fit_p(X)


def argrelextrema(X, m='both'):
    '''
    Index of relative extrema
    '''
    tmp = np.diff(np.sign(np.gradient(X)))
    if m == 'max':
        index = (tmp < 0).nonzero()[0]
    elif m == 'min':
        index = (tmp > 0).nonzero()[0]
    else:
        index = tmp.nonzero()[0]
    # recheck
    if m == 'max':
        for j, i in enumerate(index):
            if i == 0 or i == (len(X) - 1):
                continue
            if X[i] < X[i + 1]:
                index[j] = i + 1
            if X[i] < X[i - 1]:
                index[j] = i - 1
    if m == 'min':
        for j, i in enumerate(index):
            if i == 0 or i == (len(X) - 1):
                continue
            if X[i] > X[i + 1]:
                index[j] = i + 1
            if X[i] > X[i - 1]:
                index[j] = i - 1
    if m == 'both':
        for j, i in enumerate(index):
            if i in [0, 1, (len(X) - 2), (len(X) - 1)]:
                continue
            if (X[i] - X[i + 1]) * (X[i] - X[i - 1]) < 0:
                if (X[i + 1] - X[i + 2]) * (X[i + 1] - X[i]) > 0:
                    index[j] = i + 1
                    continue
                if (X[i - 1] - X[i]) * (X[i - 1] - X[i - 2]) > 0:
                    index[j] = i - 1
    return index


def fft(dt, signal):
    '''
    FFT in one dimension
    '''
    if isinstance(dt, float) and isinstance(signal, np.ndarray):
        size = signal.size
        tf = 2 * np.pi / dt * np.linspace(-0.5, 0.5, size)
        af = np.fft.fftshift(np.fft.fft(signal))
        pf = np.sqrt(np.power(af.real, 2) + np.power(af.imag, 2))
        return tf, af, pf
    else:
        log.error("'dt' must be 'float', 'signal' must be 'np.ndarray'!")
        return None, None, None


def savgol_golay_filter(x, window_size, polyorder, deriv=0, delta=1.0,
                        axis=-1, mode='interp', cval=0.0, rate=1,
                        nodebug=False, info='data'):
    '''
    Try to import `scipy.signal.savgol_filter`.
    If failed, use an old Savitzky-Golay filter:
    http://scipy-cookbook.readthedocs.io/items/SavitzkyGolay.html?highlight=Savitzky#Sample-Code
    '''
    try:
        from scipy.signal import savgol_filter
        newfilter = True
    except ImportError:
        newfilter = False

    if newfilter:
        if not nodebug:
            log.debug("Use 'scipy.signal.savgol_filter' to smooth %s." % info)
        return savgol_filter(x, window_size, polyorder, deriv=deriv,
                             delta=delta, axis=axis, mode=mode, cval=cval)

    if not nodebug:
        log.debug("Use an old Savitzky-Golay filter to smooth %s." % info)
    from math import factorial
    try:
        window_size = np.abs(np.int(window_size))
        order = np.abs(np.int(polyorder))
    except ValueError:
        raise ValueError("window_size and polyorder have to be of type int")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    order_range = range(order + 1)
    half_window = (window_size - 1) // 2
    # precompute coefficients
    b = np.mat([[k**i for i in order_range]
                for k in range(-half_window, half_window + 1)])
    m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = x[0] - np.abs(x[1:half_window + 1][::-1] - x[0])
    lastvals = x[-1] + np.abs(x[-half_window - 1:-1][::-1] - x[-1])
    x = np.concatenate((firstvals, x, lastvals))
    return np.convolve(m[::-1], x, mode='valid')


def findflat(X, upperlimit):
    '''
    Return flat region: start, len. *upperlimit* limits abs(gradient)
    '''
    Xg = np.abs(np.gradient(savgol_golay_filter(X, 51, 3, nodebug=True)))
    Xg = [1 if g < upperlimit else -X.size for g in Xg]
    _len = max_subarray(Xg)
    for _start in range(X.size):
        if sum(Xg[_start:_start + _len]) == _len:
            break
    return _start, _len
