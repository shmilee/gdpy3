# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

from .__about__ import __description__, __url__, __version__, __status__
from .__about__ import __author__, __email__, __license__, __copyright__

__doc__ = __description__
__all__ = [
    'get_rawloader', 'get_pckloader', 'get_pcksaver',
    'get_plotter', 'get_processor',
]

from .loaders import get_rawloader, get_pckloader
from .savers import get_pcksaver
from .plotters import get_plotter
from .processors import get_processor
