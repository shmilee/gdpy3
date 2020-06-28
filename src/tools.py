# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
Some tools for Core.
'''

import numpy as np

from .glogger import getGLogger

__all__ = ['max_subarray', 'line_fit', 'curve_fit',
           'argrelextrema', 'intersection_4points',
           'near_peak', 'high_envelope',
           'fft', 'fft2', 'savgolay_filter',
           'findflat', 'findgrowth',
           'correlation',
           ]
log = getGLogger('C')


def max_subarray(A):
    '''
    Maximum subarray problem
    '''
    max_ending_here = max_so_far = A[0]
    for x in A[1:]:
        max_ending_here = max(x, max_ending_here + x)
        max_so_far = max(max_so_far, max_ending_here)
    return max_so_far


def line_fit(X, Y, deg, fitX=None, info=None, **kwargs):
    '''
    One-dimensional polynomial fit. Return polyfit returns and fitY.

    Parameters
    ----------
    X, Y, deg, kwargs: passed to `numpy.polyfit`
    fitX: array
        new X data used to calculate fitY
    info: str
        info of line
    '''
    if 'full' not in kwargs:
        kwargs['full'] = True
    fitresult = np.polyfit(X, Y, deg, **kwargs)
    info = ("line '%s'" % info) if info else "line"
    log.debug("Fitting %s result: %s" % (info, fitresult))
    if (kwargs['full']
            or (not kwargs['full'] and kwargs['cov'])):
        fit_p = np.poly1d(fitresult[0])
    else:
        fit_p = np.poly1d(fitresult)
    newX = X if fitX is None else fitX
    return fitresult, fit_p(newX)


def curve_fit(f, X, Y, fitX=None, f_constant=None, info=None, **kwargs):
    '''
    Call `scipy.optimize.curve_fit`. Use non-linear least squares
    to fit a function, f, to data. Return popt, pcov, fitY.

    Parameters
    ----------
    f: callable or string name of preset-functions.
        'power', Y = a*X^b + c + eps
        'exp', 'exponential', Y = a*e^(b*x) + c + eps
        'ln', 'log', 'lograrithmic', Y = a*ln(x) + b + eps
        'gauss', 'gaussian', Y = a*e^(-(x-b)^2/(2*c^2)) + d + eps
    X, Y, kwargs: passed to `scipy.optimize.curve_fit`
    fitX: array
        new X data used to calculate fitY
    f_constant: number
        set preset-function's constant parameter, like 'exp' c, 'gauss' d
    info: str
        info of curve
    '''
    try:
        from scipy.optimize import curve_fit
    except ImportError:
        log.error("'%s' needs package 'scipy'!'" % 'curve_fit', exc_info=1)
        return (None,)*3
    info = ("curve '%s'" % info) if info else "curve"
    func = None
    if isinstance(f, str):
        if f == 'power':
            if f_constant is None:
                def func(x, a, b, c): return (a*np.power(x, b)+c)
            else:
                def func(x, a, b): return (a*np.power(x, b)+f_constant)
        elif f in ('exp', 'exponential'):
            if f_constant is None:
                def func(x, a, b, c): return (a*np.exp(b*x)+c)
            else:
                def func(x, a, b): return (a*np.exp(b*x)+f_constant)
        elif f in ('ln', 'log', 'lograrithmic'):
            if f_constant is None:
                def func(x, a, b): return (a*np.log(x)+b)
            else:
                def func(x, a): return (a*np.log(x)+f_constant)
        elif f in ('gauss', 'gaussian'):
            if f_constant is None:
                def func(x, a, b, c, d): return (
                    a*np.exp(-(x-b)**2/(2*c**2))+d)
            else:
                def func(x, a, b, c): return (
                    a*np.exp(-(x-b)**2/(2*c**2))+f_constant)
            if 'p0' not in kwargs:
                Ymax, Ymin = np.max(Y), np.min(Y)
                idx_Ymax = np.where(Y[:] == Ymax)[0][0]
                guess_p0 = [Ymax, X[idx_Ymax], np.std(X)]
                if f_constant is None:
                    guess_p0.append(Ymin)
                kwargs['p0'] = np.array(guess_p0)
                log.debug("Initial guess parameters for fitting 'gaussian': "
                          "p0=%s" % kwargs['p0'])
    elif callable(f):
        func = f
    if func is None:
        log.error("Invalid arg 'f', not callable or available strings!")
        return (None,)*3
    popt, pcov = curve_fit(func, X, Y, **kwargs)
    log.debug("Fitting %s result: popt=%s, pcov=%s" % (info, popt, pcov))
    newX = X if fitX is None else fitX
    fitY = np.array([func(i, *popt) for i in newX])
    return popt, pcov, fitY


def argrelextrema(X, m='both'):
    '''
    Call `scipy.signal.argrelextrema`, get indexes of relative extrema.

    Parameters
    ----------
    m: str
        'max', 'min' or 'both', default 'both'
    '''
    try:
        from scipy.signal import argrelextrema
    except ImportError:
        log.error("'%s' needs package 'scipy'!'" % 'argrelextrema',
                  exc_info=1)
        return None
    if not isinstance(X, np.ndarray):
        X = np.array(X)
    if m == 'max':
        index = argrelextrema(X, np.greater)[0]
    elif m == 'min':
        index = argrelextrema(X, np.less)[0]
    else:
        g, l = argrelextrema(X, np.greater)[0], argrelextrema(X, np.less)[0]
        index = np.sort(np.append(g, l))
    return index


def intersection_4points(P1x, P1y, P2x, P2y, P3x, P3y, P4x, P4y):
    '''Return line P1P2 and P3P4 intersection (x,y).'''
    tmp = (P1x-P2x)*(P3y-P4y)-(P1y-P2y)*(P3x-P4x)
    if tmp == 0:
        return None, None
    else:
        x = ((P1x*P2y-P1y*P2x)*(P3x-P4x)-(P3x*P4y-P3y*P4x)*(P1x-P2x))/tmp
        y = ((P1x*P2y-P1y*P2x)*(P3y-P4y)-(P3x*P4y-P3y*P4x)*(P1y-P2y))/tmp
        return x, y


def near_peak(Y, X=None, intersection=False, lowerlimit=1.0/np.e,
              select='all', greedy=False):
    '''
    Find 1D Y values >= lowerlimit * peak value, near the peak.
    Return new sub array X and Y, if no X given, use index.

    Parameters
    ----------
    intersection: bool
        add intersection in result
    select: str
        default 'all', get all peaks; others, only get the max peak
    greedy: bool
        If select not 'all' and greedy is True,
        search from edge where Y values >= lowerlimit * peak value.
    '''
    if select == 'all':
        indexs = argrelextrema(Y, m='max')
        greedy = False
    else:
        indexs = [np.argmax(Y)]
    res = []
    for idx in indexs:
        limit = lowerlimit*Y[idx]
        if select != 'all' and greedy:
            left_idx = 0
            for i in range(idx):
                if Y[i] >= limit:
                    left_idx = i
                    break
            right_idx = len(Y)-1
            for i in range(len(Y)-1, idx, -1):
                if Y[i] >= limit:
                    right_idx = i
                    break
        else:
            left_idx = idx
            for i in range(idx, -1, -1):
                if Y[i] >= limit:
                    left_idx = i
                else:
                    break
            right_idx = idx
            for i in range(idx, len(Y), 1):
                if Y[i] >= limit:
                    right_idx = i
                else:
                    break
        newY = Y[left_idx:right_idx+1]
        if X is None:
            newX = np.array(range(left_idx, right_idx+1))
        else:
            newX = X[left_idx:right_idx+1]
        # add line intersection
        if intersection:
            if Y[left_idx] > limit and left_idx > 0:
                x, y = intersection_4points(
                    X[left_idx-1], Y[left_idx-1], X[left_idx], Y[left_idx],
                    X[left_idx-1], limit, X[left_idx], limit)
                newX, newY = np.insert(newX, 0, x), np.insert(newY, 0, y)
            if Y[right_idx] > limit and right_idx < len(Y) - 1:
                x, y = intersection_4points(
                    X[right_idx], Y[right_idx], X[right_idx+1], Y[right_idx+1],
                    X[right_idx], limit, X[right_idx+1], limit)
                newX, newY = np.append(newX, x), np.append(newY, y)
        res.append((newX, newY))
    if select == 'all':
        return res
    else:
        return res[0]


def high_envelope(Y, X=None, add_indexs=[], **kwargs):
    '''
    Call `scipy.interpolate.interp1d`, return high envelope of Y.

    Parameters
    ----------
    add_indexs: list
        extend indexes of relative extrema
    kwargs: passed to `scipy.interpolate.interp1d`
        like *kind* of interpolation, *fill_value*, etc.
    '''
    try:
        from scipy.interpolate import interp1d
    except ImportError:
        log.error("'%s' needs package 'scipy'!'" % 'high_envelope',
                  exc_info=1)
        return None
    old_indexs = argrelextrema(Y, m='max')
    uadd = []
    if 0 not in add_indexs:
        add_indexs.insert(0, 0)
    if len(Y)-1 not in add_indexs:
        add_indexs.append(len(Y)-1)
    for i in add_indexs:
        if i not in old_indexs and 0 <= i <= len(Y)-1:
            uadd.append(i)
    new_indexs = np.concatenate((old_indexs, uadd))
    new_indexs.sort(kind='mergesort')
    # print(new_indexs,type(new_indexs[0]))
    if X is None:
        X = np.array(range(len(Y)))
    if 'kind' not in kwargs:
        kwargs['kind'] = 'linear'
    if 'bounds_error' not in kwargs:
        kwargs['bounds_error'] = False
    if 'fill_value' not in kwargs:
        kwargs['fill_value'] = 0.0
    Yinterp = interp1d(X[new_indexs], Y[new_indexs], **kwargs)
    return Yinterp(X)


def fft(dt, signal):
    '''
    FFT in one dimension, return tf, af, pf
    '''
    if isinstance(dt, float) and isinstance(signal, np.ndarray):
        size = signal.size
        if size % 2 == 0:
            tf = np.linspace(-0.5, 0.5, size, endpoint=False)
        else:
            tf = np.linspace(-0.5, 0.5, size, endpoint=True)
        tf = 2 * np.pi / dt * tf
        af = np.fft.fftshift(np.fft.fft(signal))
        # pf = np.sqrt(np.power(af.real, 2) + np.power(af.imag, 2))
        pf = abs(af)
        return tf, af, pf
    else:
        log.error("'dt' must be 'float', 'signal' must be 'np.ndarray'!")
        return None, None, None


def fft2(dt, dx, signal):
    '''
    FFT in two dimension, return tf, xf, af, pf
    signal.shape == (X.size, T.size)
    '''
    if (isinstance(dt, float) and isinstance(dx, float)
            and isinstance(signal, np.ndarray)
            and len(signal.shape) == 2):
        xsize, tsize = signal.shape
        if xsize % 2 == 0:
            xf = np.linspace(-0.5, 0.5, xsize, endpoint=False)
        else:
            xf = np.linspace(-0.5, 0.5, xsize, endpoint=True)
        if tsize % 2 == 0:
            tf = np.linspace(-0.5, 0.5, tsize, endpoint=False)
        else:
            tf = np.linspace(-0.5, 0.5, tsize, endpoint=True)
        xf = 2 * np.pi / dx * xf
        tf = 2 * np.pi / dt * tf
        af = np.fft.fftshift(np.fft.fft2(signal))
        pf = abs(af)
        return tf, xf, af, pf
    else:
        log.error("'dt', 'dx' must be 'float', "
                  "'signal' must be 2D 'np.ndarray'!")
        return None, None, None, None


def savgolay_filter(x, window_size=None, polyorder=None, info=None, **kwargs):
    '''
    Call `scipy.signal.savgol_filter`, return the filtered data.

    Parameters
    ----------
    window_size: int
        window length, a positive odd integer, default 51, len(x) or len(x)-1
    polyorder: int
        less than window length, default 3 or window_size-1
    info: str
        info of data x
    kwargs: passed to `scipy.signal.savgol_filter`
    '''
    try:
        from scipy.signal import savgol_filter
    except ImportError:
        log.error("'%s' needs package 'scipy'!'" % 'savgol_filter',
                  exc_info=1)
        return None
    if not window_size:
        window_size = min(51, len(x))
        if window_size % 2 == 0:
            window_size = window_size - 1
    if not polyorder:
        polyorder = min(3, window_size-1)
    if info:
        log.debug("Use 'scipy.signal.savgol_filter' to smooth %s." % info)
    return savgol_filter(x, window_size, polyorder, **kwargs)


def findflat(X, upperlimit, info=None):
    '''
    Return flat region: start, len. *upperlimit* limits abs(gradient(X))
    '''
    Xg = np.abs(np.gradient(savgolay_filter(X, info=info)))
    Xg = [1 if g < upperlimit else -X.size**2 for g in Xg]
    _len = max_subarray(Xg)
    if _len < 0:
        return 0, 0
    for _start in range(X.size):
        if sum(Xg[_start:_start + _len]) == _len:
            break
    return _start, _len


def findgrowth(X, lowerlimit, info=None):
    '''
    Return growth region: start, len. *lowerlimit* limits gradient(X)
    '''
    Xg = np.gradient(savgolay_filter(X, info=info))
    Xg = [1 if g > lowerlimit else -X.size**2 for g in Xg]
    _len = max_subarray(Xg)
    if _len < 0:
        return 0, 0
    for _start in range(X.size):
        if sum(Xg[_start:_start + _len]) == _len:
            break
    return _start, _len


def correlation(data, r0, r1, c0, c1, dr, dc,
                ruler_r=None, ruler_r_use='little',
                ruler_c=None, ruler_c_use='little'):
    '''
    Calculate correlation length or autocorrelation time
    xiao2010, POP, 17, 022302

    Parameters
    ----------
    data: 2d array, like delta_phi(zeta,psi)
    r0, r1, c0, c1: select data[r0:r1, c0:c1]
    dr, dc: correlation matrix size
    ruler_r, ruler_c: index [0,dr] [0,dc] -> value [vdr0, vdr1] [vdc0, vdc1]
        (ruler_r.size, ruler_c.size) == data.shape
    ruler_r_use, ruler_c_use: use ruler little or big endian

    Returns
    -------
    tau: correlation 2d array, tau.shape == (vdr.size, vdc.size)
    vdr: delta row array
    vdc: delta column array
    '''
    tau = np.zeros((dr, dc))
    logstep = round(dr/10)
    for i in range(dr):
        for j in range(dc):
            #tmptau, tmpinten0, tmpinten1 = 0, 0, 0
            # for m in range(c0, c1-j):
            #    for n in range(r0, r1-i):
            #        tmptau = tmptau + data[n,m]*data[n+i,m+j]
            #        tmpinten0 = tmpinten0 + data[n,m]*data[n,m]
            #        tmpinten1 = tmpinten1 + data[n+i,m+j]*data[n+i,m+j]
            #tau[i,j] = tmptau/np.sqrt(tmpinten0*tmpinten1)
            tmp = np.multiply(data[r0:r1-i, c0:c1-j], data[r0+i:r1, c0+j:c1])
            tmptau = np.sum(tmp)
            tmp = np.multiply(data[r0:r1-i, c0:c1-j], data[r0:r1-i, c0:c1-j])
            tmpinten0 = np.sum(tmp)
            tmp = np.multiply(data[r0+i:r1, c0+j:c1], data[r0+i:r1, c0+j:c1])
            tmpinten1 = np.sum(tmp)
            tau[i, j] = tmptau/np.sqrt(tmpinten0*tmpinten1)
        if (i+1) % logstep == 0 or i == 0 or i+1 == dr:
            log.info('correlation row %d/%d' % (i+1, dr))
            # print('row %d: %s' % (i, tau[i, :]))
            # print(tau[i,:])
    if ruler_r is None:
        vdr = None
    else:
        vdr = np.zeros(dr)
        for i in range(dr):
            if ruler_r_use == 'little':
                vdr[i] = ruler_r[r0+i] - ruler_r[r0]
            else:
                vdr[i] = ruler_r[r1] - ruler_r[r1-i]
    if ruler_c is None:
        vdc = None
    else:
        vdc = np.zeros(dc)
        for j in range(dc):
            if ruler_c_use == 'little':
                vdc[j] = ruler_c[c0+j] - ruler_c[c0]
            else:
                vdc[j] = ruler_c[c1] - ruler_c[c1-j]
    return tau, vdr, vdc
