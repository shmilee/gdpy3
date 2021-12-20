# -*- coding: utf-8 -*-

# Copyright (c) 2020-2021 shmilee

try:
    import gdpy3
    from gdpy3 import get_processor, get_visplter, get_imcat
    print("[pre-import] module 'gdpy3'")
except Exception:
    pass

try:
    import numpy as np
    print("[pre-import] module 'numpy' as 'np'")
except Exception:
    pass

def fix_mpl_backend(backend):
    from gdpy3.visplters.mplvisplter import MatplotlibVisplter
    MatplotlibVisplter.subprocess_fix_backend_etc(mpl_backend=backend)
