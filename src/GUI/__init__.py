# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
This subpackage provides GUI support for gdpy3, entry points of gui_scripts.
'''
import os
import sys
import ctypes
import argparse
from ..__about__ import __version__, __author__
from ..glogger import logfile, getGLogger

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
                        'local or sftp directory, '
                        'tar, zip, npz or hdf5 file.')
    optgrp = parser.add_argument_group('options')
    optgrp.add_argument('--backend', type=str,  default='tk',
                        choices=['tk'],
                        help="Set GUI backend, (default:  %(default)s)")
    optgrp.add_argument('--ask_sftp', action='store_true',
                        help='If no casepath given, '
                             'ask for a sftp directory, not local path.')
    optgrp.add_argument('-h', '--help', action='store_true',
                        help='Show this help message and exit')

    args = parser.parse_args()
    log.debug('Accept args: %s' % args)

    if args.help:
        parser.print_help()
        sys.exit()

    if os.name == 'nt':
        AppID = 'io.%s.%s.v%s' % (__author__, __name__, __version__)
        log.debug('Set AppUserModelID %s for Windows.' % AppID)
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(AppID)

    if args.backend == 'tk':
        from .tk import GTkApp
        GTkApp(path=args.casepath, ask_sftp=args.ask_sftp)
    else:
        pass
