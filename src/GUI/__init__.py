# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
This subpackage provides GUI support for gdpy3, entry points of gui_scripts.
'''

import sys
import argparse

__all__ = ['gui_script']


def gui_script():
    '''Entry point for gdpy3'''
    parser = argparse.ArgumentParser(
        prog='gdpy3-gui',
        description="A tiny application that converts and plots data.",
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
                        help='If no casepath given, first ask a sftp path')
    optgrp.add_argument('-h', '--help', action='store_true',
                        help='Show this help message and exit')

    args = parser.parse_args()

    if args.help:
        parser.print_help()
        sys.exit()

    if args.backend == 'tk':
        from .tk import GTkApp
        GTkApp(path=args.casepath, ask_sftp=args.ask_sftp)
    else:
        pass
