# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import logging
import numpy

__all__ = ['DataBlock']

log = logging.getLogger('gdc')


def _setpathname(pathname, ext):
    '''if pathname extension is not ``ext``, change it's extension
    '''
    if os.path.splitext(pathname)[1] != ext:
        return pathname + ext
    else:
        return pathname


class DataBlock(object):
    '''Base DataBlock class of Data1d, GtcOut, History, Snapshot, etc.

    1) save DataBlock.data to a numpy compressed .npz file, or
    2) save DataBlock.data to a matlab .mat file, or
    3) save DataBlock.data to a h5py .hdf5 file

    Attributes
    ----------
        file: str of
            File name of GTC .out to convert
        name: str of data name
        datakeys: tuple
            data keys of physical quantities in the .out file
        data: dict of converted data
    '''
    __slots__ = ['file', 'name', 'datakeys', 'data']

    def __init__(self, file=None, name='exampledata'):
        self.file = file
        self.name = name
        self.datakeys = ('example_int', 'example_pi', 'example_array')
        self.data = dict(description='example data dict',
                         example_int=666,
                         example_pi=3.14159265358979,
                         example_array=numpy.array([2.0, 4.0, 6.0]))

    def convert(self):
        '''Read GTC .out file to self.data as a dict.
        Define this function in derived class.
        '''
        log.error('Define this function in derived class.')
        raise

    def save2npz(self, npzfile, additional=[]):
        '''save DataBlock.data to a numpy compressed .npz file

        Parameters
        ----------
        npzfile: str
            File name of ``.npz`` file which the data is saved.
        additional: list
            additional data in a list of (name, data) tuple.
            example: [(name1, data1), (name2, data2)]

        Returns
        -------
        None

        Raises
        ------
        IOError
            If the .npz file does exist, but cannot be load.
        ValueError
            additional list isn't a list of (name, data) tuple

        Examples
        --------
        >>> import datablock
        >>> db = datablock.DataBlock()
        >>> db.save2npz('/tmp/test.npz')
        >>> name1 = 'name1'
        >>> data1 = {'a': 1, 'b': 2}
        >>> name2 = 'name2'
        >>> data2 = {'a': 4, 'b': 6}
        >>> db.save2npz('/tmp/test123.npz', additional=[
        ...             (name1, data1), (name2, data2)])

        Notes
        -----
        Q: How to read data from npz?
        A: npzf['name/datakey']
        >>> npzf = numpy.load('/tmp/test.npz')
        >>> name = 'name1/'
        >>> npzf[name + 'a']
        '''
        # https://docs.scipy.org/doc/numpy/reference/generated/numpy.savez_compressed.html

        tempdict = dict()
        npzfile = _setpathname(npzfile, '.npz')
        if os.path.isfile(npzfile):
            try:
                log.debug("Read existent data from file %s." % npzfile)
                tempf = numpy.load(npzfile)
                for key in tempf.files:
                    tempdict.update({key: tempf[key]})
            except (IOError, ValueError):
                log.error("Failed to read file %s." % npzfile)
                raise
            finally:
                if 'tempf' in dir():
                    tempf.close()

        additional.append((self.name, self.data))
        try:
            for name, data in additional:
                for key, val in data.items():
                    if name not in ('/', ''):
                        key = name + '/' + key
                    tempdict.update({key: val})
        except ValueError:
            log.error("``additional`` must be a list of (name, data) tuple")
            raise

        try:
            numpy.savez_compressed(npzfile, **tempdict)
        except IOError:
            log.error("Failed to create file %s." % npzfile)
            raise

    def save2hdf5(self, hdf5file, additional=[]):
        '''save DataBlock.data to a h5py .hdf5 file

        Parameters
        ----------
        hdf5file: str
            File name of ``.hdf5`` file which the data is saved.
        additional: list
            additional data in a list of (name, data) tuple.

        Raises
        ------
        ImportError
            Cannot import h5py
        IOError
            Cannot read or create the .hdf5 file.
        ValueError
            additional list isn't a list of (name, datadict) tuple

        Notes
        -----
        Q: How to read data from hdf5?
        A: h5f['name/datakey'].value
        >>> h5f = h5py.File('/tmp/data1d.hdf5', 'r')
        >>> name = 'data1d/'
        >>> print(h5f[name + 'description'][()])
        >>> h5f[name + 'mpsi+1'].value
        >>> h5f[name + 'field00-phi'][...]
        '''

        try:
            from . import wraphdf5 as hdf5
        except ImportError:
            log.error("Failed to import 'wraphdf5'!")
            raise

        hdf5file = _setpathname(hdf5file, '.hdf5')
        h5f = hdf5.open(hdf5file)

        additional.append((self.name, self.data))
        try:
            for name, data in additional:
                hdf5.write(h5f, name, data)
        except ValueError:
            log.error("``additional`` must be a list of (name, data) tuple. "
                      "``data`` must be a dict.")
            raise
        finally:
            hdf5.close(h5f)

    def save2mat(self, matfile, additional=[]):
        '''save DataBlock.data to a matlab .mat file

        Parameters
        ----------
        matfile: str
            File name of ``.mat`` file which the data is saved.
        additional: list
            additional data in a list of (name, data) tuple.
        '''

        try:
            import scipy
        except ImportError:
            log.error('If you want to save data in a .mat file, '
                      'please install scipy.')
            raise

        matfile = _setpathname(matfile, '.mat')
        # TODO(nobody): scipy.io.savemat, share data with matlab

    savez = save2npz
    saveh5 = save2hdf5
