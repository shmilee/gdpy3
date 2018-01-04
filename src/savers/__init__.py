# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

from ..glogger import getGLogger
from .npzfile import NpzFileSaver
from .base import BaseFileSaver

log = getGLogger('S')
saver_names = ['NpzFileSaver', 'Hdf5FileSaver']


def get_saver(name):
    '''
    Given a saver name, return a saver class. Raises ValueError if not found.
    '''
    if name in saver_names:
        if name == 'NpzFileSaver':
            return NpzFileSaver
        elif name == 'Hdf5FileSaver':
            from .hdf5file import Hdf5FileSaver
            return Hdf5FileSaver
        else:
            raise ValueError('Save ha? Who am I? Why am I here?')
    else:
        raise ValueError('Unknown saver cls "%s"! Did you mean one of: "%s"?'
                         % (name, ', '.join(saver_names)))

