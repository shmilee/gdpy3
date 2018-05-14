# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Command Line Interface(CLI) tools for GTC
'''

import os
import time
from hashlib import sha1

from .. import __version__ as gdpy3_version
from ..glogger import getGLogger
from ..loaders import get_rawloader, get_pckloader
from ..savers import get_pcksaver
from ..plotters import get_plotter
from ..processors import get_processor

__all__ = ['pick']
log = getGLogger('G')


def pick(path, gtcver='110922', description=None,
         filenames_filter=None, savetype='.npz', overwrite=False, Sid=False,
         datagroups_filter=None, default_plotter=True):
    '''
    Pick up GTC data in *path*, get a GTC processor.

    Parameters
    ----------
    path: str
        path of GTC .out files or pickled data to open
    gtcver: str
        GTC code version -> GTC processor, default is '110922'
    description: str
        additional description of GTC data
    filenames_filter: function
        function to filter filenames in GTC .out files when get rawloader
    savetype: '.npz' or '.hdf5'
        extension of saved file, default '.npz'
    overwrite: bool
        overwrite existing saved file or not, default False
    Sid: bool
        If Sid is True, GTC .out files will not be auto-converted and
        pckloader, plotter will not be set. Sid only takes effect when
        *path* is GTC .out files to open and pcksave's type is .npz or .hdf5.
        Default False.
    datagroups_filter: function
        function to filter datagroups in pickled data when get pckloader
    default_plotter: bool
        set default plotter ('mpl::gtc') or not, default True

    Notes
    -----
    1. GTC .out files should be named as:
       gtc.out, history.out, snap("%05d" % istep).out, trackp_dir, etc.
       so they can be auto-detected.
    2. If pickled data can't be auto-saved beside GTC .out files,
       a cache pcksave will be used.
    '''
    # rawloader.path?
    try:
        rawloader = get_rawloader(path, filenames_filter=filenames_filter)
    except Exception:
        rawloader = None
        # pckloader.path?
        try:
            pckloader = get_pckloader(
                path, datagroups_filter=datagroups_filter)
        except Exception:
            pckloader = None
    if gtcver == '110922':
        log.info("Getting GTC Processor V110922 ...")
        processor = get_processor('GTCProcessorV110922')
    else:
        raise ValueError("GTC version '%s' not supported!" % gtcver)
    # 1. path -> raw
    if rawloader:
        gtcfile = [k for k in rawloader.filenames if k.endswith('gtc.out')]
        if len(gtcfile) == 0:
            raise ValueError("Can't find 'gtc.out' in '%s'!" % path)
        elif len(gtcfile) > 1:
            raise ValueError("More than one 'gtc.out' found in '%s'!" % path)
        else:
            gtcfile = gtcfile[0]
        if rawloader.loader_type in ['sftp.directory']:
            pcksaver = get_pcksaver('sftp.directory.cache')
        else:
            if os.access(path, os.W_OK):
                try:
                    with rawloader.get(gtcfile) as f:
                        salt = sha1(f.read().encode('utf-8')).hexdigest()
                        log.debug("Get salt string: '%s'." % salt)
                except Exception:
                    log.error("Failed to read salt file '%s'!" % gtcfile)
                    pcksaver = get_pcksaver('local.path.cache')
                else:
                    if rawloader.loader_type == 'directory':
                        prefix = os.path.join(path, 'gdpy3-pickled-data')
                    elif rawloader.loader_type == 'tarfile':
                        prefix = rawloader.path[:rawloader.path.rfind('.tar')]
                    elif rawloader.loader_type == 'zipfile':
                        prefix = rawloader.path[:rawloader.path.rfind('.zip')]
                    else:
                        prefix = os.path.splitext(rawloader.path)[0]
                    if savetype not in ['.npz', '.hdf5']:
                        log.warn("Use default savetype '.npz'.")
                        savetype = '.npz'
                    savepath = '%s-%s%s' % (prefix, salt[:10], savetype)
                    log.info("Default pickled data file is %s." % savepath)
                    pcksaver = get_pcksaver(savepath)
            else:
                pcksaver = get_pcksaver('local.path.cache')
        if os.path.isfile(pcksaver.path):
            if overwrite:
                log.warn("Remove old pickled data file: %s!" % pcksaver.path)
                os.remove(pcksaver.path)
            else:
                if Sid:
                    return processor
                # use old pickled data
                processor.pckloader = get_pckloader(
                    pcksaver.get_store(), datagroups_filter=datagroups_filter)
                if default_plotter:
                    processor.plotter = get_plotter('mpl::gtc')
                return processor
        # description for GTC data #TODO -> GTCProcessorV110922
        desc = ("GTC .out data from %s '%s'.\n"
                "Created by gdpy3 v%s.\n"
                "Created on %s." %
                (rawloader.loader_type, path, gdpy3_version, time.asctime()))
        if description:
            desc = desc + '\n' + str(description)
        # convert raw data, get new pickled data and set pck loader
        processor.rawloader, processor.pcksaver = rawloader, pcksaver
        if pcksaver._extension in ['.npz', 'hdf5'] and Sid: #TODO ->ep
            return processor
        with pcksaver:
            pcksaver.write('/', {'description': desc, 'version': gtcver})
        processor.convert()
        log.info("GTC '.out' files in %s are converted to %s!"
                 % (path, pcksaver.path))
        if not Sid:
            processor.pckloader = get_pckloader(
                pcksaver.get_store(), datagroups_filter=datagroups_filter)
            if default_plotter:
                processor.plotter = get_plotter('mpl::gtc')
        return processor
    # 2. path -> pck
    elif pckloader:
        processor.pckloader = pckloader
        if default_plotter:
            processor.plotter = get_plotter('mpl::gtc')
        return processor
    # 3. path -> none
    else:
        raise ValueError("Invalid loader path '%s'!" % path)


def script_convert_gtc():
    '''
    Entry point of gdpy3-convert gtc for setup script.
    '''
    #TODO

