# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Command Line Interface(CLI), entry points of console_scripts.
'''

import os
import sys
import time
import argparse

from .glogger import logfile, getGLogger
from .processors import processor_names, alias_processor_names, get_processor
from . import __version__ as gdpy3_version

__all__ = ['cli_script']

log = getGLogger('G')


def print_version():
    print('gdpy3 version %s' % gdpy3_version)
    print('Copyright (C) %s shmilee' % time.strftime('%Y'))


def get_parser_top():
    '''Create top-level parser.'''
    parser = argparse.ArgumentParser(
        prog='gdpy3',
        description="A tiny script that converts and plots data.",
        epilog="For more log details, please see: %s" % logfile,
        add_help=False,
    )
    subparsers = parser.add_subparsers(title='subcommands', dest='subcmd')
    optgrp = parser.add_argument_group('options')
    optgrp.add_argument('-l', '--list', action='store_true',
                        help='List available processors and exit')
    optgrp.add_argument('-h', '--help', action='store_true',
                        help='Show this help message and exit')
    optgrp.add_argument('-V', '--version', action='store_true',
                        help='Print version and exit')
    return parser, subparsers


def get_parser_base():
    '''Create parent parser for sub-commands.'''
    parser = argparse.ArgumentParser(
        description="parent parser for sub-commands",
        add_help=False,
    )
    arggrp = parser.add_argument_group('arguments')
    arggrp.add_argument('casepath', nargs='*', type=str,
                        help='Case data path(s)')
    optgrp = parser.add_argument_group('common options')
    _pnames = processor_names + list(alias_processor_names.keys())
    optgrp.add_argument('--processor', type=str, metavar='ProcessorName',
                        choices=_pnames, default=_pnames[0],
                        help="Assign processor to work, "
                        "(default: %(default)s)")
    optgrp.add_argument('-h', '--help', action='store_true',
                        help='Show this help message and exit')
    return parser


def get_parser_convert(subparsers, parents=[]):
    '''Create the parser for the "convert" sub-command.'''
    parser = subparsers.add_parser(
        'convert',
        usage='%(prog)s [options]... casepath...',
        description="Script that converts raw data to "
                    "a .npz, .hdf5 file beside raw data.",
        add_help=False,
        parents=parents,
    )
    optgrp = parser.add_argument_group('convert options')
    optgrp.add_argument('--add_desc', type=str, metavar='Desc',
                        help='Additional description of raw data')
    optgrp.add_argument('--filenames_filter', type=eval, metavar='Filter',
                        help='Function(str) to filter filenames in raw data')
    optgrp.add_argument('--savetype', type=str,
                        choices=['.npz', '.hdf5'], default='.npz',
                        help="Extension of savefile, (default: %(default)s)")
    optgrp.add_argument('--overwrite', action='store_true',
                        help='Overwrite existing savefile')
    return parser


def get_parser_plot(subparsers, parents=[]):
    '''Create the parser for the "plot" sub-command.'''
    parser = subparsers.add_parser(
        'plot',
        usage='%(prog)s [options]... casepath...',
        description="Script that plots pickled data in .npz, .hdf5 file to "
                    "figures in a directory beside pickled data. "
                    "It also accepts 'convert options', "
                    "as subcommand 'plot' is beyond 'convert'.",
        add_help=False,
        parents=parents,
    )
    optgrp = parser.add_argument_group('plot options')
    optgrp.add_argument(
        '--datagroups_filter', type=eval, metavar='Filter',
        help='Function(str) to filter datagroups in pickled data')
    optgrp.add_argument('--select', type=str,
                        action='append', metavar='Pattern',
                        help="Patterns for selecting figures to plot")
    optgrp.add_argument('--style', type=str,
                        action='append', metavar='Style',
                        help="Style name of figures")
    optgrp.add_argument('--figext', type=str, default='png',
                        choices=['png', 'pdf', 'ps', 'eps', 'svg', 'jpg'],
                        help="Extension of saved figures, "
                        "(default:  %(default)s)")
    return parser


def get_parser():
    '''Assemble top-level parser and sub-command parsers.'''
    top, subparsers = get_parser_top()
    base = get_parser_base()
    convert = get_parser_convert(subparsers, parents=[base])
    plot = get_parser_plot(subparsers, parents=[convert])
    return {'top': top, 'convert': convert, 'plot': plot}


def cli_script():
    '''Entry point for gdpy3'''
    parserlib = get_parser()
    args = parserlib['top'].parse_args()
    log.debug("Get input arguments: %s" % args)

    if args.list:
        print("Available Processors:")
        for i, n in enumerate(processor_names):
            print("%s%s" % (' ' * 4, n))
        print("Alias Processors:")
        for i, apn in enumerate(alias_processor_names):
            print("%s%10s -> %s" % (' ' * 4, apn, alias_processor_names[apn]))
        sys.exit()
    if args.help:
        if args.subcmd:
            parserlib[args.subcmd].print_help()
        else:
            parserlib['top'].print_help()
        sys.exit()
    if args.version:
        print_version()
        sys.exit()

    if args.subcmd:
        if not args.casepath:
            log.info("Please set at least one case data path!")
            parserlib[args.subcmd].print_help()
            sys.exit()
    else:
        parserlib['top'].print_help()
        sys.exit()

    gdp = get_processor(args.processor)
    log.info("Using %s ..." % gdp.name)
    if args.subcmd == 'plot':
        if not args.select:
            _YN = input("Select all figures to plot! Continue(y/n)? ")
            if _YN.lower() in ('y', 'yes'):
                args.select = ['.*']
            else:
                sys.exit()
        plot_style = None

    N = len(args.casepath)
    for i, path in enumerate(args.casepath, 1):
        log.info("Case(%d/%d) path: %s" % (i, N, path))
        try:
            if args.subcmd == 'convert':
                gdp.pick(
                    path,
                    add_desc=args.add_desc,
                    filenames_filter=args.filenames_filter,
                    savetype=args.savetype,
                    overwrite=args.overwrite,
                    Sid=True,
                )
                if (gdp.pcksaver is None
                        or not os.path.isfile(gdp.pcksaver.path)):
                    log.error("Failed to convert %s!" % path)
            elif args.subcmd == 'plot':
                gdp.pick(
                    path,
                    add_desc=args.add_desc,
                    filenames_filter=args.filenames_filter,
                    savetype=args.savetype,
                    overwrite=args.overwrite,
                    Sid=False,
                    datagroups_filter=args.datagroups_filter,
                    add_plotter=True,
                )
                if gdp.pckloader is None or gdp.plotter is None:
                    log.error("Failed to plot %s!" % path)
                    continue
                # plot figures
                figurelabels = set()
                for select in args.select:
                    figurelabels.update(gdp.refind(select))
                if len(figurelabels) == 0:
                    continue
                if plot_style is None:
                    if args.style:
                        plot_style = gdp.plotter.check_style(args.style)
                    else:
                        plot_style = []
                if plot_style:
                    gdp.plotter.style = plot_style
                figdir = '%s-figures-%s' % (
                    os.path.splitext(gdp.pckloader.path)[0],
                    time.strftime('%F-%H'))
                if not os.path.isdir(figdir):
                    os.mkdir(figdir)
                M = len(figurelabels)
                for j, flabel in enumerate(sorted(figurelabels), 1):
                    log.info("Case(%d/%d), Figure(%d/%d): %s"
                             % (i, N, j, M, flabel))
                    fname = '%s.%s' % (flabel.replace('/', '-'), args.figext)
                    try:
                        gdp.plot(flabel, show=False)
                        gdp.plotter.save_figure(
                            flabel, os.path.join(figdir, fname))
                    except Exception:
                        continue
                    gdp.plotter.close_figure(flabel)
            else:
                pass
        except Exception:
            log.error("Failed to pick up case %s!" % path, exc_info=1)
    sys.exit()
