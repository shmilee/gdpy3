# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
Some tools for Core.
'''

import numpy as np

from .glogger import getGLogger

__all__ = ['max_subarray', 'fitline', 'curve_fit',
           'argrelextrema', 'intersection_4points',
           'near_peak', 'high_envelope',
           'fft', 'fft2', 'savgol_golay_filter',
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


def fitline(X, Y, deg, info=''):
    '''
    One-dimensional polynomial fit
    '''
    fitresult = np.polyfit(X, Y, deg, full=True)
    log.debug("Fitting line '%s' result:" % info)
    log.debug("%s" % (fitresult,))
    fit_p = np.poly1d(fitresult[0])
    return fitresult, fit_p(X)


def curve_fit(f, X, Y, info=None, **kwargs):
    '''
    Call `scipy.optimize.curve_fit`. Use non-linear least squares
    to fit a function, f, to data. Return popt, pcov, fitY.

    f: callable or string name of preset-functions.
        'power', Y = a*X^b + c + eps
        'exp', 'exponential', Y = a*e^(b*x) + c + eps
        'ln', 'log', 'lograrithmic', Y = a*ln(x) + b + eps
        'gauss', 'gaussian', Y = a*e^(-(x-b)^2/(2*c^2)) + d + eps
    kwargs: passed to `scipy.optimize.curve_fit`
    '''
    try:
        from scipy.optimize import curve_fit
    except ImportError:
        log.error("'curve_fit' needs package 'scipy'!'")
        return (None,)*3
    info = ("curve '%s'" % info) if info else "curve"
    func = None
    if isinstance(f, str):
        if f == 'power':
            def func(x, a, b, c): return (a*np.power(x, b)+c)
        elif f in ('exp', 'exponential'):
            def func(x, a, b, c): return (a*np.exp(b*x)+c)
        elif f in ('ln', 'log', 'lograrithmic'):
            def func(x, a, b): return (a*np.log(x)+b)
        elif f in ('gauss', 'gaussian'):
            def func(x, a, b, c, d): return (a*np.exp(-(x-b)**2/(2*c**2))+d)
            if 'p0' not in kwargs:
                Ymax, Ymin = np.max(Y), np.min(Y)
                x_Ymax = X[np.where(Y[:] == Ymax)[0]]
                kwargs['p0'] = np.array([Ymax, x_Ymax[0], np.std(X), Ymin])
                log.debug("Initial guess parameters for fitting 'gaussian': "
                          "p0=%s" % kwargs['p0'])
    elif callable(f):
        func = f
    if func is None:
        log.error("Invalid arg 'f', not callable or available strings!")
        return (None,)*3
    popt, pcov = curve_fit(func, X, Y, **kwargs)
    log.debug("Fitting %s result: popt=%s, pcov=%s" % (info, popt, pcov))
    fitY = np.array([func(i, *popt) for i in X])
    return popt, pcov, fitY


def argrelextrema(X, m='both', recheck=False):
    '''
    Index of relative extrema
    Try to import `scipy.signal.argrelextrema`.
    If failed, use an lame one.
    '''
    try:
        from scipy.signal import argrelextrema as relextrema
        if m == 'max':
            index = relextrema(X, np.greater)[0]
        elif m == 'min':
            index = relextrema(X, np.less)[0]
        else:
            g, l = relextrema(X, np.greater)[0], relextrema(X, np.less)[0]
            index = np.sort(np.append(g, l))
    except ImportError:
        tmp = np.diff(np.sign(np.gradient(X)))
        if m == 'max':
            index = (tmp < 0).nonzero()[0]
        elif m == 'min':
            index = (tmp > 0).nonzero()[0]
        else:
            index = tmp.nonzero()[0]
    if not recheck:
        return index
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
    Find 1D Y values >= lowerlimit * peak value, near the peak
    Return new sub array X and Y, if no X given, use index.
    If select='all', get all peaks, else only get the max peak.
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


def high_envelope(Y, X=None, add_indexs=[], kind='linear'):
    '''
    Return high envelope of Y.
    Specifies the *kind* of interpolation as a string, if use scipy.
    '''
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
    try:
        from scipy.interpolate import interp1d
    except ImportError:
        return np.interp(X, X[new_indexs], Y[new_indexs])
    Yinterp = interp1d(X[new_indexs], Y[new_indexs], kind=kind,
                       bounds_error=False, fill_value=0.0)
    return Yinterp(X)


def fft(dt, signal):
    '''
    FFT in one dimension
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
    FFT in two dimension
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


def savgol_golay_filter(x, window_size=None, polyorder=None, deriv=0,
                        delta=1.0, axis=-1, mode='interp', cval=0.0,
                        rate=1, info='data'):
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

    if not window_size:
        window_size = min(51, len(x))
        if window_size % 2 == 0:
            window_size = window_size - 1
    if not polyorder:
        polyorder = min(3, window_size-1)

    if newfilter:
        log.debug("Use 'scipy.signal.savgol_filter' to smooth %s." % info)
        return savgol_filter(x, window_size, polyorder, deriv=deriv,
                             delta=delta, axis=axis, mode=mode, cval=cval)

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


def findflat(X, upperlimit, info='data'):
    '''
    Return flat region: start, len. *upperlimit* limits abs(gradient(X))
    '''
    Xg = np.abs(np.gradient(savgol_golay_filter(X, info=info)))
    Xg = [1 if g < upperlimit else -X.size**2 for g in Xg]
    _len = max_subarray(Xg)
    if _len < 0:
        return 0, 0
    for _start in range(X.size):
        if sum(Xg[_start:_start + _len]) == _len:
            break
    return _start, _len


def findgrowth(X, lowerlimit, info='data'):
    '''
    Return growth region: start, len. *lowerlimit* limits gradient(X)
    '''
    Xg = np.gradient(savgol_golay_filter(X, info=info))
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
    correlation length
    autocorrelation time
    xiao2010, POP, 17, 022302

    data: 2d array, like delta_phi(zeta,psi)
    r0, r1, c0, c1: select data[r0:r1, c0:c1]
    dr, dc: correlation matrix size
    ruler_r, ruler_c: index [0,dr] [0,dc] -> value [vdr0, vdr1] [vdc0, vdc1]
        (ruler_r.size, ruler_c.size) == data.shape
    ruler_r_use, ruler_c_use: use ruler little or big endian
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
