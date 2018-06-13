# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

__name__ = "gdpy3"
__doc__ = "Gyrokinetic Toroidal Code Data Processing tools written in python3"
__author__ = "shmilee"
__version__ = "0.3.4"
__status__ = "alpha"
__license__ = "MIT"
__email__ = "shmilee.zju@gmail.com"
__uri__ = "https://github.com/shmilee/gdpy3.git"
__all__ = ['get_plotter', 'get_processor']

from .plotters import get_plotter
from .processors import get_processor
