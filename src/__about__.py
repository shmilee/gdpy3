# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

VERSION = (0, 4, 1)

__description__ = "Gyrokinetic Toroidal Code Data Processing tools written in python3"
__url__ = "https://github.com/shmilee/gdpy3.git"
__version__ = '.'.join(map(str, VERSION))
__status__ = "alpha"
__author__ = "shmilee"
__email__ = "shmilee.zju@gmail.com"
__license__ = "MIT"
__copyright__ = 'Copyright (c) 2018 shmilee'


def _get_data_path(name):
    '''Get the path to *name*.'''
    import os
    import sys

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    if os.path.isdir(path):
        return path

    # pyinstaller frozen check
    if getattr(sys, 'frozen', None):
        path = os.path.join(sys._MEIPASS, name)
        if os.path.isdir(path):
            return path

        path = os.path.join(os.path.dirname(sys.executable), name)
        if os.path.isdir(path):
            return path

        path = os.path.join(sys.path[0], name)
        if os.path.isdir(path):
            return path

    raise RuntimeError("Can't find the %s files!" % name)


__data_path__ = _get_data_path('gdpy3-data')
__icon_name__ = 'gdpy3_128'
