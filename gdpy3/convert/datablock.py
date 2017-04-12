# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import numpy

__all__ = ['DataBlock']


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
                tempf = numpy.load(npzfile)
                for key in tempf.files:
                    tempdict.update({key: tempf[key]})
            except (IOError, ValueError):
                print("Failed to read file %s." % npzfile)
                raise

        additional.append((self.name, self.data))
        try:
            for name, data in additional:
                for key, val in data.items():
                    tempdict.update({name + '/' + key: val})
        except ValueError:
            print("``additional`` must be a list of (name, data) tuple")
            raise

        try:
            numpy.savez_compressed(npzfile, **tempdict)
        except IOError:
            print("Failed to create file %s." % npzfile)
            raise

    def save2hdf5(self, hdf5file, additional=[]):
        '''save DataBlock.data to a h5py .hdf5 file

        Parameters
        ----------
        npzfile: str
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
        # http://docs.h5py.org/en/latest/index.html

        try:
            import h5py
        except ImportError:
            print('If you want to save data in a .hdf5 file, '
                  'please install h5py(python bindings for HDF5).')
            raise

        hdf5file = _setpathname(hdf5file, '.hdf5')
        if os.path.isfile(hdf5file):
            try:
                h5f = h5py.File(hdf5file, 'r+')
            except IOError:
                print("Failed to read file %s." % hdf5file)
                raise
        else:
            try:
                h5f = h5py.File(hdf5file, 'w-')
            except IOError:
                print("Failed to create file %s." % hdf5file)
                raise

        additional.append((self.name, self.data))
        try:
            for name, data in additional:
                if name in h5f:
                    h5f.__delitem__(name)
                fgrp = h5f.create_group(name)
                for key, val in data.items():
                    if isinstance(val, (list, numpy.ndarray)):
                        fgrp.create_dataset(key, data=val, chunks=True,
                                            compression='gzip',
                                            compression_opts=9)
                    else:
                        fgrp.create_dataset(key, data=val)
                h5f.flush()
        except ValueError:
            print("``additional`` must be a list of (name, data) tuple. "
                  "``data`` must be a dict.")
            raise
        h5f.close()

    def save2mat(self, matfile, additional=[]):
        '''save DataBlock.data to a matlab .mat file

        Parameters
        ----------
        npzfile: str
            File name of ``.mat`` file which the data is saved.
        additional: list
            additional data in a list of (name, data) tuple.
        '''

        try:
            import scipy
        except ImportError:
            print('If you want to save data in a .mat file, '
                  'please install scipy.')
            raise

        matfile = _setpathname(matfile, '.mat')
        # TODO(nobody): scipy.io.savemat, share data with matlab

    savez = save2npz
    saveh5 = save2hdf5
