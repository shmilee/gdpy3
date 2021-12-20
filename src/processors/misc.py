# -*- coding: utf-8 -*-

# Copyright (c) 2020-2021 shmilee

"""
Module for miscellaneous functions and methods.
"""

import os
import re
import numpy as np

from ..glogger import getGLogger
from ..loaders import get_pckloader
from ..savers import get_pcksaver

__all__ = [
    'change_v04x_pickled_data', 'change_pckdata_ext',
    'slim_v060_digged_data']
plog = getGLogger('P')


def change_v04x_pickled_data(path):
    '''
    change gdpy3-pickled-data-xxx.npz -> (>=0.5) gtcv3-xxx.converted.npz

    Parameters
    ----------
    path: path of pickled data
    '''
    if not os.path.isfile(path):
        plog.error("Path %s not found!" % path)
        return
    rootdir = os.path.dirname(path)
    root, ext = os.path.splitext(os.path.basename(path))
    if ext in ['.npz', '.hdf5'] and root.startswith('gdpy3-pickled-data-'):
        plog.info("This is a pickled data path %s!" % path)
    else:
        plog.error("This is not a pickled data path %s!" % path)
        return
    oldloader = get_pckloader(path)
    ver = oldloader.get('version') if 'version' in oldloader else None
    if ver in ['110922', 'GTCV110922', 'GTCV3.14-22']:
        plog.info("Find version '%s'" % ver)
        # gdpy3-pickled-data-8aad8b6725
        saltstr = root[-10:][:6]
        # gtcv3-8aad8b.converted
        newroot = 'gtcv3-%s.converted%s' % (saltstr, ext)
        newpath = os.path.join(rootdir, newroot)
        if os.path.isfile(newpath):
            plog.error("Converted data file exists: %s! pass" % newpath)
        else:
            plog.info("Rename %s -> %s" % (path, newpath))
            os.rename(path, newpath)
    else:
        plog.error("This is a invalid pickled data!")


def change_pckdata_ext(path, ext):
    '''
    yy-xxxxxx.{converted,digged}.npz <-> yy-xxxxxx.{converted,digged}.hdf5

    Parameters
    ----------
    path: path of converted or digged data
    ext: extension of out path, like '.npz', '.hdf5'
    '''
    if not os.path.isfile(path):
        plog.error("Path %s not found!" % path)
        return
    root, ext1 = os.path.splitext(path)
    root, ext2 = os.path.splitext(root)
    if (ext2, ext1) in [('.converted', '.npz'), ('.converted', '.hdf5')]:
        plog.info("This is a converted data path %s!" % path)
    elif (ext2, ext1) in [('.digged', '.npz'), ('.digged', '.hdf5')]:
        plog.info("This is a digged data path %s!" % path)
    else:
        plog.error("This is not a converted or digged data path %s!" % path)
        return
    if ext not in ['.npz', '.hdf5']:
        plog.error("Unsupported extension %s!" % ext)
        return
    if ext1 == ext:
        plog.warning("Old extension is %s, nothing to change!" % ext)
        return
    newpath = '%s%s%s' % (root, ext2, ext)
    if os.path.exists(newpath):
        plog.warning("Data file %s exists! Nothing to do!" % newpath)
        return
    oldloader = get_pckloader(path)
    info = {'processor': oldloader['processor']}
    if ext2 == '.converted':
        info['description'] = oldloader['description']
        info['saltstr'] = oldloader['saltstr']
    with get_pcksaver(newpath) as newsaver:
        newsaver.write('/',  info)
        for grp in oldloader.datagroups:
            results = oldloader.get_by_group(grp)
            plog.info("Copy: %s" % grp)
            newsaver.write(grp, results)
    plog.info("Done. %s -> %s." % (path, os.path.basename(newpath)))


def slim_v060_digged_data(path):
    '''
    Change (v0.6.0)figlabel/DEFAULT/{a,b,c} -> (v0.6.1)figlabel/DEFAULT/_LINK

    Parameters
    ----------
    path: path of digged data
    '''
    if not os.path.isfile(path):
        plog.error("Path %s not found!" % path)
        return
    root, ext1 = os.path.splitext(path)
    root, ext2 = os.path.splitext(root)
    if (ext2, ext1) not in [('.digged', '.npz'), ('.digged', '.hdf5')]:
        plog.error("This is not a digged data path %s!" % path)
        return
    oldloader = get_pckloader(path)
    # group diggedlabels
    figlabels = {}
    for dl in oldloader.datagroups:
        grp = os.path.dirname(dl)
        if grp in figlabels:
            figlabels[grp].append(dl)
        else:
            figlabels[grp] = [dl]
    figlabels_todo = {}
    for fl in figlabels.keys():
        default, other = None, None
        if len(figlabels[fl]) == 1:
            plog.warning("Only one diggedlabels for %s!" % fl)
            plog.warning("==> %s" % figlabels[fl])
            continue
        elif len(figlabels[fl]) == 2:
            dl1, dl2 = figlabels[fl]
            if dl1.endswith('/DEFAULT'):
                default, other = dl1, dl2
            elif dl2.endswith('/DEFAULT'):
                default, other = dl2, dl1
            else:
                plog.warning("Two diggedlabels, no one is DEFAULT!")
                plog.warning("==> %s" % figlabels[fl])
                continue
            if ('%s/_LINK' % default) in oldloader.datakeys:
                continue
        else:
            # >=3, find default other
            for dl in figlabels[fl]:
                if dl.endswith('/DEFAULT'):
                    default = dl
                    break
            if default is None:
                plog.warning(">=3 diggedlabels, no one is DEFAULT!")
                plog.warning("==> %s" % figlabels[fl])
                continue
            if ('%s/_LINK' % default) in oldloader.datakeys:
                continue
            for dl in figlabels[fl]:
                if not dl.endswith('/DEFAULT'):
                    # check data
                    allks = oldloader.refind('^%s/' % re.escape(default))
                    basekeys1 = sorted([os.path.basename(k) for k in allks])
                    allks = oldloader.refind('^%s/' % re.escape(dl))
                    basekeys2 = sorted([os.path.basename(k) for k in allks])
                    equal = False
                    if basekeys1 == basekeys2:
                        equal = True
                        for k in basekeys1:
                            v1 = oldloader.get('%s/%s' % (default, k))
                            v2 = oldloader.get('%s/%s' % (dl, k))
                            if (isinstance(v1, np.ndarray)
                                    or isinstance(v2, np.ndarray)):
                                cv = np.array_equal(v1, v2)
                            else:
                                cv = v1 == v2
                            if not cv:
                                equal = False
                                break
                    if equal:
                        other = dl
                        break
        # collect all default, other
        if default and other:
            assert os.path.dirname(default) == os.path.dirname(other)
            plog.info("TODO: %s -> %s" % (default, other))
            figlabels_todo[default] = other
    if len(figlabels_todo) == 0:
        plog.warning("No figlabel/DEFAULT to do!")
        return
    slimpath = '%s-slim%s%s' % (root, ext2, ext1)
    if os.path.isfile(slimpath):
        plog.warning("Remove old slim data file: %s!" % slimpath)
        os.remove(slimpath)
    with get_pcksaver(slimpath) as newsaver:
        newsaver.write('/', {'processor': oldloader['processor']})
        for dl in oldloader.datagroups:
            if dl in figlabels_todo:
                other = figlabels_todo[dl]
                plog.info("Link: %s -> %s" % (dl, other))
                newsaver.write(dl, dict(_LINK=other))
            else:
                results = oldloader.get_by_group(dl)
                plog.info("Copy: %s" % dl)
                newsaver.write(dl, results)
    plog.info("v060 digged data in %s is slimed: %s." % (path, slimpath))
