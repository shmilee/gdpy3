# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

import numpy

__all__ = ['Trans_r_psi']


class Trans_r_psi(object):
    ''' r, r/a <-> psi, psi/psiw'''
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
        return numpy.sqrt(r2)

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
        roots = numpy.roots([q3/3.0, q2/2.0, q1, - r**2 / (2*self.psiw)])
        for npsi in roots:
            if npsi.imag == 0:
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
        A = numpy.mat([
            [1.0, q_p1[0], q_p1[0]**2.0],
            [1.0, q_p2[0], q_p2[0]**2.0],
            [1.0, q_p3[0], q_p3[0]**2.0],
        ])
        b = numpy.mat([q_p1[1], q_p2[1], q_p3[1]]).T
        q = numpy.linalg.solve(A, b)
        q1, q2, q3 = q[0, 0], q[1, 0], q[2, 0]
        psiw = a**2.0/2.0/(q1+q2/2.0+q3/3.0)
        return (q1, q2, q3), psiw
