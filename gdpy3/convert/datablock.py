# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import logging
import numpy

__all__ = ['DataBlock']

log = logging.getLogger('gdc')


class DataBlock(object):
    '''
    Base DataBlock class of Data1d, GtcOut, History, Snapshot, etc.

    1) save DataBlock.data to a numpy compressed .npz file, or
    2) save DataBlock.data to a h5py .hdf5 file

    Attributes
    ----------
    file: str
        File path of GTC .out to convert
    group: str of data group
    datakeys: tuple
        data keys of physical quantities in the .out file
    data: dict of converted data
    '''
    __slots__ = ['file', 'group', 'datakeys', 'data']
    _Datakeys = ('description',)

    def __init__(self, file, group=None, check_file=True):
        if not isinstance(file, str):
            raise ValueError("Data file path must be str!")
        if check_file:
            if os.path.isfile(file):
                self.file = file
            else:
                raise IOError("Can't find data file: '%s'!" % file)
        else:
            self.file = file
        if group:
            if not isinstance(group, str):
                raise ValueError("Data group must be str!")
            self.group = group
        else:
            self.group = os.path.basename(os.path.splitext(file)[0])
        self.datakeys = self.get_cls_datakeys()
        cutoff = self.__doc__.index('Attributes\n')
        self.data = {
            'description': self.__doc__[:cutoff].strip(),
        }

    @classmethod
    def get_cls_datakeys(cls):
        return cls._Datakeys

    def convert(self):
        '''Read GTC .out file to self.data as a dict.
        Define this function in derived class.
        '''
        log.error('Define this function in derived class.')
        raise

    @staticmethod
    def _setpathname(pathname, ext):
        '''if pathname extension is not ``ext``, change it's extension
        '''
        if os.path.splitext(pathname)[1] != ext:
            return pathname + ext
        else:
            return pathname

    def save2npz(self, npzfile, additional=[]):
        '''save DataBlock.data to a numpy compressed .npz file

        Parameters
        ----------
        npzfile: str
            File name of ``.npz`` file which the data is saved.
        additional: list
            additional data in a list of (group, data) tuple.
            example: [(group1, data1), (group2, data2)]

        Returns
        -------
        None

        Raises
        ------
        IOError
            If the .npz file does exist, but cannot be load.
        ValueError
            additional list isn't a list of (group, data) tuple

        Examples
        --------
        >>> import datablock
        >>> db = datablock.DataBlock()
        >>> db.save2npz('/tmp/test.npz')
        >>> group1 = 'group1'
        >>> data1 = {'a': 1, 'b': 2}
        >>> group2 = 'group2'
        >>> data2 = {'a': 4, 'b': 6}
        >>> db.save2npz('/tmp/test123.npz', additional=[
        ...             (group1, data1), (group2, data2)])

        Notes
        -----
        Q: How to read data from npz?
        A: npzf['group/datakey']
        >>> npzf = numpy.load('/tmp/test.npz')
        >>> group = 'group1/'
        >>> npzf[group + 'a']
        '''

        try:
            from . import wrapnpz as wrapfile
        except ImportError:
            log.error("Failed to import 'wrapnpz'!")
            raise

        # open file
        npzfile = self._setpathname(npzfile, '.npz')
        if os.path.isfile(npzfile):
            backnpz = npzfile + '-backup.npz'
            log.debug("Rename '%s' to '%s'!" % (npzfile, backnpz))
            os.rename(npzfile, backnpz)
        else:
            backnpz = None
        npzfid = wrapfile.iopen(npzfile)

        # write data
        try:
            for group, data in [(self.group, self.data)] + additional:
                wrapfile.write(npzfid, group, data)
        except ValueError:
            log.error("``additional`` must be a list of (group, data) tuple. "
                      "``data`` must be a dict.")
            raise
        finally:
            wrapfile.close(npzfid)
        # close file

        # append original data
        # tempdict -> {group1:data1,group2,data2}
        if backnpz:
            npzfid = wrapfile.iopen(npzfile)
            npzfnset = set(os.path.splitext(n)[0] for n in npzfid.namelist())
            log.debug("Read existent data from original file %s." % backnpz)
            try:
                backfid = numpy.load(backnpz)
                bckfnset = set(backfid.files)
                # keys in bckfnset but not npzfnset
                datatodo = bckfnset.difference(npzfnset)
                # group the keys
                tempdict = {os.path.dirname(k): dict() for k in datatodo}
                for k in datatodo:
                    tempdict[os.path.dirname(k)][
                        os.path.basename(k)] = backfid[k]
            except (IOError, ValueError) as exc:
                log.error("Failed to read original file %s: %s" %
                          (backnpz, exc))
            finally:
                if 'backfid' in dir():
                    backfid.close()
                if 'tempdict' in dir():
                    for group, data in tempdict.items():
                        wrapfile.write(npzfid, group, data)
                wrapfile.close(npzfid)
                log.debug("Remove original file '%s'!" % backnpz)
                os.remove(backnpz)

    def save2hdf5(self, hdf5file, additional=[]):
        '''save DataBlock.data to a h5py .hdf5 file

        Parameters
        ----------
        hdf5file: str
            File name of ``.hdf5`` file which the data is saved.
        additional: list
            additional data in a list of (group, data) tuple.

        Raises
        ------
        ImportError
            Cannot import h5py
        IOError
            Cannot read or create the .hdf5 file.
        ValueError
            additional list isn't a list of (group, datadict) tuple

        Notes
        -----
        Q: How to read data from hdf5?
        A: h5fid['group/datakey'].value
        >>> h5fid = h5py.File('/tmp/data1d.hdf5', 'r')
        >>> group = 'data1d/'
        >>> print(h5fid[group + 'description'][()])
        >>> h5fid[group + 'mpsi+1'].value
        >>> h5fid[group + 'field00-phi'][...]
        '''

        try:
            from . import wraphdf5 as wrapfile
        except ImportError:
            log.error("Failed to import 'wraphdf5'!")
            raise

        hdf5file = self._setpathname(hdf5file, '.hdf5')
        h5fid = wrapfile.iopen(hdf5file)

        try:
            for group, data in [(self.group, self.data)] + additional:
                wrapfile.write(h5fid, group, data)
        except ValueError:
            log.error("``additional`` must be a list of (group, data) tuple. "
                      "``data`` must be a dict.")
            raise
        finally:
            wrapfile.close(h5fid)

    savez = save2npz
    saveh5 = save2hdf5
