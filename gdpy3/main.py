# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
Define entry points functions for setup script.
'''

import os
import sys
import argparse

from .glogger import getGLogger
from . import __version__ as gdpy3_version
__all__ = []

log = getGLogger('G')


def print_version(prog):
    print('gdpy3(%s): version %s' % (prog, gdpy3_version))
    print('Copyright (C) 2017 shmilee')


def script_convert():
    '''
    Entry point for gdpy3.convert.
    '''
    from . import convert as gdc

    parser = argparse.ArgumentParser(
        prog='gdpy3-convert',
        usage='%(prog)s [options]... casedir...',
        description="A tiny script that "
                    "converts GTC results to a .npz or .hdf5 file "
                    "saved in the results directory.",
        add_help=False,
    )
    base_grp = parser.add_argument_group('arguments')
    base_grp.add_argument('casedir', nargs='*', type=str,
                          help='GTC results directory(s)')
    opt_grp = parser.add_argument_group('options')
    opt_grp.add_argument('--mode', type=str,
                         choices=['walk', 'stay'], default='walk',
                         help="How to deal with *casedir*, "
                         "(default: %(default)s)")
    opt_grp.add_argument('--salt', type=str,
                         help="Salt for name of saved file, "
                         "(default: 'gtc.out')")
    opt_grp.add_argument('--extension', type=str,
                         choices=['.npz', '.hdf5'],
                         help="Extension of saved file, (default: '.npz')")
    opt_grp.add_argument('--gtcver', type=str,
                         choices=['110922'],
                         help="GTC code version, (default: '110922')")
    opt_grp.add_argument('--description', type=str,
                         help='Additional description for the case')
    opt_grp.add_argument('--additionalpats', type=list, metavar='PATS',
                         help="Additional patterns for reading 'gtc.out'")
    opt_grp.add_argument('-V', '--version', action='store_true',
                         help='Print version and exit')
    opt_grp.add_argument('-h', '--help', action='store_true',
                         help='Show this help message and exit')
    walk_grp = parser.add_argument_group(
        'walk options',
        'Walking *casedir* to find all GTC results directories')
    walk_grp.add_argument('--overwrite', action='store_true',
                          help='Overwrite existing saved file')
    stay_grp = parser.add_argument_group(
        'stay options',
        'Only deal with the first GTC results directory found in *casedir*, '
        "and overwrite saved file if exists.")
    stay_grp.add_argument('--savefile', type=str,
                          help="Specified path of the saved file, "
                               "ignore *salt*, *extension*.")
    args = parser.parse_args()
    log.ddebug("Get input arguments: %s" % args)

    if args.help:
        parser.print_help()
        sys.exit()
    if args.version:
        print_version(parser.prog)
        sys.exit()

    if not args.casedir:
        log.error("Please set a GTC results directory!")
        parser.print_help()
        sys.exit()
    case_directories = []
    for _casedir in args.casedir:
        for _croot, _dirs, _files in sorted(os.walk(_casedir)):
            if 'gtc.out' in _files:
                case_directories.append(_croot)
                if args.mode == 'stay':
                    break
        if args.mode == 'stay' and case_directories:
            break
    if not case_directories:
        log.error("Find NO GTC results directory in %s!" % args.casedir)
        sys.exit()
    log.debug("GTC results directory(s) TODO: %s" % case_directories)

    kwargs = {}
    for option in ['salt', 'extension',
                   'gtcver', 'description', 'additionalpats']:
        if args.__getattribute__(option):
            kwargs[option] = args.__getattribute__(option)
    log.debug("Common options: %s" % kwargs)

    if args.mode == 'walk':
        if args.overwrite:
            kwargs['overwrite'] = args.overwrite
        for _casedir in case_directories:
            log.info("Case directory: %s" % _casedir)
            try:
                _case = gdc.load(_casedir, **kwargs)
            except Exception:
                log.error("Failed to convert %s!" % _casedir, exc_info=1)
    elif args.mode == 'stay':
        _casedir = case_directories[0]
        log.info("Case directory: %s" % _casedir)
        try:
            if args.savefile:
                _case = gdc.convert(_casedir,
                                    savefile=args.savefile, **kwargs)
            else:
                _case = gdc.load(_casedir, **kwargs)
        except Exception:
            log.error("Failed to convert %s!" % _casedir, exc_info=1)
    else:
        log.error("Never!")
