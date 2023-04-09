# -*- coding: utf-8 -*-

# Copyright (c) 2022 shmilee

'''
zipfile setting & helper functions.
'''

import os
import sys
import zipfile
import tempfile
from .glogger import getGLogger

__all__ = ['zipfile_factory', 'zipfile_copy', 'zipfile_delete']
log = getGLogger('G')

ZIP_LZMA = zipfile.ZIP_LZMA
ZIP_DEFLATED = zipfile.ZIP_DEFLATED
Compress_prefer = 'ZIP_LZMA'  # ZIP_DEFLATED or ZIP_LZMA
Compress_kwds = dict(allowZip64=True)
Py_version_tuple = sys.version_info[:3]
if Compress_prefer == 'ZIP_LZMA' and zipfile.lzma:
    Compress_kwds['compression'] = zipfile.ZIP_LZMA
else:
    Compress_kwds['compression'] = zipfile.ZIP_DEFLATED
    if Py_version_tuple >= (3, 7, 0):
        # Changed in version 3.7: Add the compresslevel parameter.
        Compress_kwds['compresslevel'] = 6


def zipfile_factory(file, *args, **kwargs):
    """Create a ZipFile. See: `numpy.lib.npyio.zipfile_factory`."""
    if not hasattr(file, 'read'):
        file = os.fspath(file)
    mykwargs = Compress_kwds.copy()
    mykwargs.update(kwargs)
    mykwargs['allowZip64'] = True
    return zipfile.ZipFile(file, *args, **mykwargs)


def zipfile_copy(srcpath, dstpath, remove_duplicate=True, ignore=None):
    '''
    Copy zip file from *srcpath* to *dstpath*.
    Remove duplicate filenames if needed, and the last one is retained.
    Ignore filenames in list *ignore*.
    '''
    with zipfile_factory(srcpath, mode="r") as zin:
        with zipfile_factory(dstpath, mode="w") as zout:
            zout.comment = zin.comment
            if remove_duplicate:
                infolist, filenames = [], set()
                for item in reversed(zin.infolist()):
                    if item.filename not in filenames:
                        filenames.add(item.filename)
                        infolist.append(item)
                infolist.reverse()
            else:
                infolist = zin.infolist()
            for item in infolist:
                if ignore and item.filename in ignore:
                    continue
                try:
                    zout.writestr(item, zin.read(item))
                except Exception as e:
                    log.warning("Failed to copy %s in zipfile %s!" %
                                (item.filename, srcpath))


def zipfile_delete(srcpath, files):
    '''Delete *files* from zip file *srcpath*.'''
    _dir, prefix = os.path.split(srcpath)
    fd, tmp = tempfile.mkstemp(prefix=prefix, dir=_dir, suffix='-tmp.zip')
    os.close(fd)
    log.debug("Using temp zipfile: %s" % tmp)
    try:
        zipfile_copy(srcpath, tmp, ignore=files)
    except Exception as e:
        log.error("Failed to delete files from zipfile %s!" % srcpath)
        os.remove(tmp)
        return False
    else:
        os.remove(srcpath)
        os.rename(tmp, srcpath)
        return True
