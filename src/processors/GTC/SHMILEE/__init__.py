# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
User SHMILEE's Processors and Cores.

1. GTC Residual Zonal Flow Processor V110922.
   GTC .out files should be named as: gtc.out, data1d.out, history.out,
   so they can be auto-detected.
'''

from .. import (
    data1d,
    history,
    GTCProcessorV110922,
)

from . import rzf

__all__ = ['GTCSHMILEERZF110922']


class GTCSHMILEERZF110922(GTCProcessorV110922):
    __slots__ = []
    DigCores = [
        rzf.RZFGtcDigCoreV110922,
        data1d.Data1dDigCoreV110922,
        history.HistoryDigCoreV110922,
    ]
    LayCores = [
        rzf.RZFData1dLayCoreV110922,
        history.HistoryLayCoreV110922,
    ]
    pckversion = 'GTCSHMILEERZF110922'
