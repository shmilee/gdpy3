# -*- coding: utf-8 -*-

# Copyright (c) 2020-2021 shmilee

import numpy as np
from .. import tools

__all__ = ['Analytic_r_psi', 'Numerical_r_psi']


class Analytic_r_psi(object):
    ''' r, r/a <-> psi, psi/psiw for analytic equilibrium'''
    __slots__ = ['q', 'psiw', 'a']

    def __init__(self, q=(0.85, 1.04, 1.0), psiw=0.0381):
        self.q = q
        self.psiw = psiw
        self.a = self.rnpsi(1.0)

    def rnpsi(self, npsi):
        '''
        Input npsi=psi/psiw: [0, 1]
        Return r=nr*a: [0, a]
        '''
        q1, q2, q3 = self.q
        r2 = 2*(q1*npsi+q2*npsi*npsi/2.0+q3*npsi*npsi*npsi/3.0)*self.psiw
        return np.sqrt(r2)

    def nrnpsi(self, npsi):
        '''
        Input npsi=psi/psiw: [0, 1]
        Return nr=r/a: [0, 1]
        '''
        return self.rnpsi(npsi)/self.a

    def npsir(self, r):
        '''
        Input r=nr*a: [0, a]
        Return npsi=psi/psiw: [0, 1]
        '''
        q1, q2, q3 = self.q
        # q1*psi+q2*psi*psi/2.0+q3*psi*psi*psi/3.0 - r**2 / (2*psiw) = 0
        roots = np.roots([q3/3.0, q2/2.0, q1, - r**2 / (2*self.psiw)])
        for npsi in roots:
            if npsi.imag == 0 and npsi.real >= 0:
                return npsi.real
        return None

    def npsinr(self, nr):
        '''
        Input nr=r/a: [0, 1]
        Return npsi=psi/psiw: [0, 1]
        '''
        return self.npsir(nr*self.a)

    def qnpsi(self, npsi):
        '''
        Input npsi=psi/psiw: [0, 1]
        Return q(npsi)
        '''
        q1, q2, q3 = self.q
        return q1 + q2*npsi + q3*npsi*npsi

    def qnr(self, nr):
        '''
        Input nr=r/a: [0, 1]
        Return q(nr)
        '''
        return self.qnpsi(self.npsinr(nr))

    @staticmethod
    def cal_q_psiw(q_p1, q_p2, q_p3, a):
        '''
        Input q(npsi) 3 points and a
        Return (q1, q2, q3), psiw
        '''
        A = np.mat([
            [1.0, q_p1[0], q_p1[0]**2.0],
            [1.0, q_p2[0], q_p2[0]**2.0],
            [1.0, q_p3[0], q_p3[0]**2.0],
        ])
        b = np.mat([q_p1[1], q_p2[1], q_p3[1]]).T
        q = np.linalg.solve(A, b)
        q1, q2, q3 = q[0, 0], q[1, 0], q[2, 0]
        psiw = a**2.0/2.0/(q1+q2/2.0+q3/3.0)
        return (q1, q2, q3), psiw


class Numerical_r_psi(object):
    ''' r, r/a <-> psi, psi/psiw for numerical equilibrium'''
    __slots__ = ['r', 'a', 'psi', 'psiw']

    def __init__(self, r=None, psi=None, gdp=None):
        if r and psi:
            self.r, self.psi = np.array(r), np.array(psi)
        elif gdp:
            a, b, c = gdp.dig('equilibrium/r(psi)', post=False)
            self.r, self.psi = b['Y'], b['X']
        else:
            raise ValueError('Input r, psi together or just a GTC processor!')
        if self.r.size != self.psi.size:
            raise ValueError('Array r.size != psi.size !')
        self.a = self.r[-1]
        self.psiw = self.psi[-1]

    def __fit_coeffs(self, X, Y, deg):
        c, fy = tools.line_fit(X, Y, deg)
        std1 = np.std(Y - fy)
        std2 = np.std((Y[1:] - fy[1:]) / Y[1:])  # skip [0] zero
        print('fit residual error: %f, relative: %.3f%%' % (std1, std2*100))
        return c[0]

    def rpsi_fit_coeffs(self, x='r', deg=10):
        '''
        x: str, 'r' or 'psi'
        Return polynomial coefficients, highest power first.
        '''
        X = self.psi if x == 'psi' else self.r
        Y = self.r if x == 'psi' else self.psi
        return self.__fit_coeffs(X, Y, deg)

    def nrnpsi_fit_coeffs(self, x='nr', deg=10):
        '''
        x: str, 'nr'(r/a) or 'npsi'(psi/psiw)
        Return polynomial coefficients, highest power first.
        '''
        X = self.psi/self.psiw if x == 'npsi' else self.r/self.a
        Y = self.r/self.a if x == 'npsi' else self.psi/self.psiw
        return self.__fit_coeffs(X, Y, deg)

    @staticmethod
    def string_polynomial(coeffs1d, x='r'):
        ''' x: str symbol'''
        p1d = ''
        for c in coeffs1d:
            if p1d:
                p1d = '(%s*%s %+.8e)' % (p1d, x, c)
            else:
                p1d = '%.8e' % c
        return p1d
