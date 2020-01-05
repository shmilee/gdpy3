# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee


class RawLoader(object):
    path = 'test/rawlodaer'
    filenames = [
        'g.out', 'eq.out', 's0.out', 's2.out', 's4.out',
        'p/s0_t0.out', 'p/s0_t1.out', 'p/s0_t2.out',
        'p/s2_t0.out', 'p/s2_t1.out', 'p/s2_t2.out',
    ]

    def key_location(self, f):
        return '%s/%s' % ('test/rawlodaer', f)


class PckLoader(object):
    path = 'test/pcklodaer'
    datakeys = [
        'g/c',
        'da/i-p-f', 'da/i-m-f', 'da/e-p-f', 'da/e-m-f',
        'his/i', 'his/e', 'his/n',
        's0/p', 's0/a', 's0/x', 's0/y',
        's2/p', 's2/a', 's2/x', 's2/y',
        'tp/i-1', 'tp/i-2', 'tp/i-3',
        'tp/e-1', 'tp/e-2', 'tp/e-3',
    ]
