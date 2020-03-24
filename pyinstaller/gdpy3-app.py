# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

import os
import sys
from gdpy3.__main__ import entry_iface, log

if __name__ == "__main__":
    # get cmd by prog name
    # https://github.com/pyinstaller/pyinstaller/wiki/FAQ#gnulinux
    # 1. staticx fully-static bundled version, prog is .staticx.prog
    # 2. PyInstaller version, prog can be gdpy3-app or a link
    prog = os.path.basename(sys.argv[0])
    if prog == '.staticx.prog':
        log.info('This is a staticx fully-static bundled version. '
                 'Program name is always %s!' % prog)
    else:
        log.info('This is a PyInstaller version, not fully static. '
                 'Program name is %s!' % prog)
    entry_iface(candidates=('cli', 'gui', 'run', 'ipy'), default='cli')
