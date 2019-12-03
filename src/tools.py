# -*- coding: utf-8 -*-

# Copyright (c) 2019 shmilee

'''
Some tools for Core.
'''

import numpy as np

from .glogger import getGLogger

__all__ = ['max_subarray', 'fitline', 'argrelextrema', 'near_peak',
           'fft', 'savgol_golay_filter', 'findflat', 'findgrowth',
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


def near_peak(X, peak_idx, lowerlimit=1/np.e):
    '''Find index of values >= lowerlimit * peak value, near the peak'''
    limit = lowerlimit*X[peak_idx]
    left_idx = peak_idx
    for i in range(peak_idx, -1, -1):
        if X[i] >= limit:
            left_idx = i
        else:
            break
    right_idx = peak_idx
    for i in range(peak_idx, len(X), 1):
        if X[i] >= limit:
            right_idx = i
        else:
            break
    return left_idx, right_idx


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
        pf = np.sqrt(np.power(af.real, 2) + np.power(af.imag, 2))
        return tf, af, pf
    else:
        log.error("'dt' must be 'float', 'signal' must be 'np.ndarray'!")
        return None, None, None


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
            print('find _start', _start)
            break
    return _start, _len


def correlation(data, r0, r1, c0, c1, dr, dc):
    '''
    correlation length
    autocorrelation time
    xiao2010, POP, 17, 022302

    r0, r1, c0, c1: select data[r0:r1, c0:c1]
    dr, dc: correlation matrix size
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
    return tau
