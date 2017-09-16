# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import numpy
import zipfile
import tempfile

from ..glogger import getGLogger

__all__ = ['NpzSaver', 'Hdf5Saver', 'NpzLoader', 'Hdf5Loader']

log = getGLogger('C')


class NpzSaver(object):
    # https://docs.scipy.org/doc/numpy/reference/generated/numpy.savez_compressed.html
    # /usr/lib/python3.x/site-packages/numpy/lib/npyio.py, funtion _savez
    '''
    Save GTC data to the NumPy compressed ``.npz`` data archive.

    Attributes
    ----------
    file: str
        Path of ``.npz`` file
    fobj: ZipFile instance
        The compressed ZipFile object
    fobj_on: bool
        The ZipFile object initialized or not

    Parameters
    ----------
    file : str
        The string containing the path to the archive to open.
    '''
    __slots__ = ['file', 'fobj', 'fobj_on']
    _extension = '.npz'

    def __init__(self, file):
        file = self._setpathname(file, self._extension)
        if os.access(os.path.dirname(file), os.W_OK):
            self.file = file
        else:
            raise IOError(
                "Can't access directory '%s'!" % os.path.dirname(file))
        self.fobj = None
        self.fobj_on = False

    @staticmethod
    def _setpathname(pathname, ext):
        '''
        If pathname extension is not ``ext``, change it's extension
        '''
        if os.path.splitext(pathname)[1] != ext:
            return pathname + ext
        else:
            return pathname

    def _open_append(self):
        return numpy.lib.npyio.zipfile_factory(
            self.file, mode="a", compression=zipfile.ZIP_DEFLATED)

    def _open_new(self):
        return numpy.lib.npyio.zipfile_factory(
            self.file, mode="w", compression=zipfile.ZIP_DEFLATED)

    def iopen(self):
        '''
        Initialize file object.
        Open ``file`` if exists, create otherwise.

        Returns
        -------
        bool: ``fobj`` initialized or not
        '''

        if self.fobj_on:
            log.warn("The ZipFile object has been initialized.")
            return True
        file = self.file
        fobj = None
        if os.path.isfile(file):
            try:
                log.debug("Open file '%s' to append data." % file)
                fobj = self._open_append()
            except Exception:
                log.error("Failed to open file '%s'." % file, exc_info=1)
                raise
        else:
            try:
                log.debug("Create file '%s' to store data." % file)
                fobj = self._open_new()
            except Exception:
                log.error("Failed to create file '%s'." % file, exc_info=1)
                raise
        if fobj:
            self.fobj = fobj
            self.fobj_on = True
            return True
        else:
            return False

    def _write(self, group, data):
        file_dir, file_prefix = os.path.split(self.file)
        fd, tmpfile = tempfile.mkstemp(
            prefix=file_prefix, dir=file_dir, suffix='-numpy.npy')
        os.close(fd)
        log.ddebug("Using tempfile: %s" % tmpfile)
        try:
            for key, val in data.items():
                if group in ('/', ''):
                    fname = key + '.npy'
                else:
                    fname = group + '/' + key + '.npy'
                fid = open(tmpfile, mode='wb')
                try:
                    numpy.lib.format.write_array(fid, numpy.asanyarray(val),
                                                 allow_pickle=True,
                                                 pickle_kwargs=None)
                    fid.close()
                    fid = None
                    log.ddebug("Writting %s ..." % fname)
                    self.fobj.write(tmpfile, arcname=fname)
                except Exception:
                    log.error("Failed to write %s." % fname, exc_info=1)
                finally:
                    if fid:
                        fid.close()
        except Exception:
            log.error("Failed to save data of '%s'!" % group, exc_info=1)
        finally:
            os.remove(tmpfile)

    def write(self, group, data):
        '''
        Write dict ``data`` in group ``group`` to file object ``fobj``.

        Parameters
        ----------
        group: str, group name
        data: dict data in this group
        '''

        if not self.fobj_on:
            log.error("``fobj`` is not initialized!")
            return False
        if not (isinstance(group, str) and isinstance(data, dict)):
            log.error("``group`` is not str, or ``data`` is not dict!")
            return False
        self._write(group, data)

    def close(self):
        '''
        Close initialized file object ``fobj``.
        '''
        if self.fobj_on:
            log.debug("Close initialized file '%s'." % self.file)
            self.fobj.close()
        self.fobj = None
        self.fobj_on = False


class Hdf5Saver(NpzSaver):
    # http://docs.h5py.org/en/latest/index.html
    '''
    Save GTC data to ``.hdf5`` file.

    Attributes
    ----------
    file: str
        Path of ``.hdf5`` file
    fobj: HDF5 file object
    fobj_on: bool
        The HDF5 file object initialized or not

    Parameters
    ----------
    file : str
        The string containing the path to the ``.hdf5`` file to open.
    '''
    __slots__ = ['h5py']
    _extension = '.hdf5'

    def __init__(self, file):
        try:
            import h5py
        except ImportError:
            log.error('If you want to save data in a .hdf5 file, '
                      'please install h5py(python bindings for HDF5).')
            raise
        self.h5py = h5py
        super(Hdf5Saver, self).__init__(file)

    def _open_append(self):
        return self.h5py.File(self.file, 'r+')

    def _open_new(self):
        return self.h5py.File(self.file, 'w-')

    def _write(self, group, data):
        try:
            if group in ('/', ''):
                fgrp = self.fobj
                for key in data.keys():
                    if key in self.fobj:
                        log.ddebug("Delete dataset '/%s'." % key)
                        self.fobj.__delitem__(key)
            else:
                if group in self.fobj:
                    log.ddebug("Delete group '/%s'." % group)
                    self.fobj.__delitem__(group)
                log.ddebug("Create group '/%s'." % group)
                fgrp = self.fobj.create_group(group)
            for key, val in data.items():
                log.ddebug("Create dataset '%s/%s'." % (fgrp.name, key))
                if isinstance(val, (list, numpy.ndarray)):
                    fgrp.create_dataset(key, data=val, chunks=True,
                                        compression='gzip',
                                        compression_opts=9)
                else:
                    fgrp.create_dataset(key, data=val)
            self.fobj.flush()
        except Exception:
            log.error("Failed to save data of '%s'!" % group, exc_info=1)


class NpzLoader(object):
    '''
    Load pickled data in ``.npz`` file. Return a dictionary-like object.

    Attributes
    ----------
    file: str
        path of the .npz file
    datakeys: tuple
        keys of physical quantities in the .npz file
    datagroups: tuple
        groups of datakeys
    desc: str
        description of the .npz file
    description: alias desc
    cache: dict
        cached keys from .npz file

    Parameters
    ----------
    file: str
        path of the .npz file to open

    Notes
    -----
    Q: How to read data from .npz file?
    A: npzfile[datakey]
    >>> npzfile = numpy.load('/tmp/test.npz')
    >>> datakey = 'group/key'
    >>> npzfile[datakey]
    '''
    __slots__ = ['file', 'datakeys', 'datagroups',
                 'desc', 'description', 'cache',
                 '_speciallib']

    def _set_speciallib(self):
        self._speciallib = numpy

    def _special_openfile(self):
        return self._speciallib.load(self.file)

    def _special_closefile(self, tempf):
        tempf.close()

    def _special_getkeys(self, tempf):
        return tempf.files

    def _special_getitem(self, tempf, key):
        value = tempf[key]
        if value.size == 1:
            value = value.item()
        return value

    def __init__(self, file):
        if os.path.isfile(file):
            self.file = file
        else:
            raise IOError("Failed to find file %s." % file)
        self._set_speciallib()
        try:
            log.debug("Open file %s." % self.file)
            tempf = self._special_openfile()
            log.debug("Getting datakeys from %s ..." % self.file)
            self.datakeys = tuple(self._special_getkeys(tempf))
            self.datagroups = tuple(
                os.path.dirname(k) for k in self.datakeys
                if k.endswith('/description'))
            self.desc = str(self._special_getitem(tempf, 'description'))
            self.description = self.desc
        except (IOError, ValueError):
            log.critical("Failed to read file %s." % self.file, exc_info=1)
            raise
        finally:
            if 'tempf' in dir():
                log.debug("Close file %s." % self.file)
                self._special_closefile(tempf)
        self.cache = {}

    def keys(self):
        return self.datakeys

    def __getitem__(self, key):
        if key not in self.datakeys:
            raise KeyError("%s is not in '%s'" % (key, self.file))
        if key in self.cache:
            return self.cache[key]
        try:
            log.debug("Open file %s." % self.file)
            tempf = self._special_openfile()
            log.debug("Getting key '%s' from %s ..." % (key, self.file))
            value = self._special_getitem(tempf, key)
            self.cache[key] = value
        except (IOError, ValueError):
            log.critical("Failed to get '%s' from %s!" %
                         (key, self.file), exc_info=1)
            raise
        finally:
            if 'tempf' in dir():
                log.debug("Close file %s." % self.file)
                self._special_closefile(tempf)
        return value

    get = __getitem__

    def find(self, *keys):
        '''
        Find the datakeys which contain ``keys``
        '''
        result = self.datakeys
        for key in keys:
            key = str(key)
            result = tuple(
                filter(lambda k: True if key in k else False, result))
        return tuple(result)

    def get_many(self, *keys):
        '''
        Get values by ``keys``. Return a tuple of values.
        '''
        result = [self.cache[k] if k in self.cache else None for k in keys]
        idxtodo = [i for i, k in enumerate(result) if k is None]
        if len(idxtodo) == 0:
            return tuple(result)
        try:
            log.debug("Open file %s." % self.file)
            tempf = self._special_openfile()
            for i in idxtodo:
                key = keys[i]
                log.debug("Getting key '%s' from %s ..." % (key, self.file))
                value = self._special_getitem(tempf, key)
                result[i] = value
                self.cache[key] = value
        except (IOError, ValueError):
            if 'key' in dir():
                log.critical("Failed to get '%s' from %s!" %
                             (key, self.file), exc_info=1)
            else:
                log.critical("Failed to open '%s'!" % self.file, exc_info=1)
            raise
        finally:
            if 'tempf' in dir():
                log.debug("Close file %s." % self.file)
                self._special_closefile(tempf)
        return tuple(result)


class Hdf5Loader(NpzLoader):
    '''
    Load datasets in ``.hdf5`` file. Return a dictionary-like object.

    Attributes
    ----------
    file: str
        path of the .hdf5 file
    datakeys: tuple
        keys of physical quantities in the .hdf5 file
    datagroups: tuple
        groups of datakeys
    desc: str
        description of the .hdf5 file
    description: alias desc
    cache: dict
        cached keys from .hdf5 file

    Parameters
    ----------
    file: str
        path of the .hdf5 file to open

    Notes
    -----
    Q: How to read data from .hdf5 file?
    A: h5file[datakey].value
    >>> h5file = h5py.File('/tmp/test.hdf5', 'r')
    >>> datakey = 'group/key'
    >>> h5file[datakey].value
    >>> h5file[datakey][()]
    >>> h5file[datakey][...]
    '''
    __slots__ = []

    def _set_speciallib(self):
        try:
            import h5py
        except ImportError:
            log.error('If you want to load data in a .hdf5 file, '
                      'please install h5py(python bindings for HDF5).')
            raise
        self._speciallib = h5py

    def _special_openfile(self):
        return self._speciallib.File(self.file, 'r')

    def _special_closefile(self, tempf):
        tempf.close()

    def _special_getkeys(self, tempf):
        mykeys = []
        tempf.visititems(
            lambda name, obj: mykeys.append(name)
            if isinstance(obj, self._speciallib.Dataset) else None)
        return mykeys

    def _special_getitem(self, tempf, key):
        return tempf[key].value
