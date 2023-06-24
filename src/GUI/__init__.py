# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020 shmilee

'''
This subpackage provides GUI support for gdpy3, entry points of gui_scripts.
'''
import os
import sys
import ctypes
import argparse
from ..__about__ import __gversion__, __author__
from ..glogger import logfile, getGLogger
from ..savers import pcksaver_types

__all__ = ['gui_script']
log = getGLogger('G')


def gui_script():
    '''Entry point for gdpy3'''
    parser = argparse.ArgumentParser(
        prog='gdpy3-gui',
        description="A tiny application that converts and plots data.",
        epilog="For more log details, please see: %s" % logfile,
        add_help=False,
    )
    arggrp = parser.add_argument_group('arguments')
    arggrp.add_argument('casepath', nargs='?', type=str,
                        help='Case data path, support types: '
                        'local or sftp directory, tarfile, zipfile '
                        'or %s file.' % ', '.join(pcksaver_types[1:]))
    optgrp = parser.add_argument_group('options')
    optgrp.add_argument('--backend', type=str,  default='tk',
                        choices=['tk'],
                        help="Set GUI backend, (default:  %(default)s)")
    optgrp.add_argument('--ask_sftp', action='store_true',
                        help='If no casepath given, '
                             'ask for a sftp directory, not local path.')
    optgrp.add_argument('--parallel', type=str,
                        choices=['off', 'multiprocess'],  # 'mpi4py'],
                        default='multiprocess',
                        help="Parallel processing or not, "
                        "(default: %(default)s)")
    optgrp.add_argument('--tk_scaling', nargs='?', type=float, metavar='float',
                        help='Set scaling factor used by Tk')
    optgrp.add_argument('-h', '--help', action='store_true',
                        help='Show this help message and exit')

    args = parser.parse_args()
    log.debug('Accept args: %s' % args)

    if args.help:
        parser.print_help()
        sys.exit()

    if os.name == 'nt':
        AppID = 'io.%s.%s.v%s' % (__author__, __name__, __gversion__)
        log.debug('Set AppUserModelID %s for Windows.' % AppID)
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(AppID)
        if args.tk_scaling:
            # ref: ttkbootstrap/utility.py, enable_high_dpi_awareness
            ctypes.windll.user32.SetProcessDPIAware()

    if args.backend == 'tk':
        from .tk import GTkApp
        GTkApp(path=args.casepath,
               ask_sftp=args.ask_sftp, parallel=args.parallel,
               scaling=args.tk_scaling)
    else:
        pass
