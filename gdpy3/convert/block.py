# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import numpy

from .utils import NpzSaver, log

__all__ = ['Block']


class Block(object):
    '''
    Base Block class of Data1d, GtcOut, History, Snapshot, etc.

    1) save Block.data to a numpy compressed .npz file, or
    2) save Block.data to a h5py .hdf5 file

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
            log.ddebug("Get group from file name -> '%s'." % self.group)
        self.datakeys = self.get_cls_datakeys()
        cutoff = self.__doc__.index('Attributes\n')
        self.data = {
            'description': self.__doc__[:cutoff].strip(),
        }

    @classmethod
    def get_cls_datakeys(cls):
        return cls._Datakeys

    def convert(self):
        '''
        Read GTC .out file to self.data as a dict.
        Define this function in derived class.
        '''
        log.error('Define this function in derived class.')
        raise

    def save(self, saver, additional=[],
             auto_close=True, deal_with_npz='append'):
        '''
        Save Block.data to a numpy compressed .npz or h5py .hdf5 file.

        Parameters
        ----------
        additional: list
            additional data in a list of (group, data) tuple.
            example: [(group1, data1), (group2, data2)]
        auto_close: bool
            finally close ``saver`` or not
        deal_with_npz: str, 'new' or 'append', default is 'append'
            If .npz file already exists, how to deal with original data?
            1) 'new', create a new file, write fresh data,
               then append original data which isn't inclued in fresh data.
            2) 'append', use original file, and append fresh data directly.

        Raises
        ------
        IOError
            ``saver`` is not a instance of NpzSaver or Hdf5Saver
        ValueError
            ``additional`` list isn't a list of (group, data) tuple

        Examples
        --------
        >>> import gdpy3.convert.block as block
        >>> db = block.Block(file='',check_file=False)
        >>> saver = block.NpzSaver('/tmp/test.npz')
        >>> group1 = 'group1'
        >>> data1 = {'a': 1, 'b': 2}
        >>> group2 = 'group2'
        >>> data2 = {'a': 4, 'b': 6}
        >>> db.save(saver, additional=[(group1, data1), (group2, data2)])
        '''

        if not isinstance(saver, NpzSaver):
            log.error("``saver`` isn't a instance of NpzSaver or Hdf5Saver!")
            raise IOError("``saver`` is invalid!")
        if not isinstance(additional, list):
            log.error("``additional`` must be a list of (group, data) tuple.")
            raise ValueError(
                "``additional`` must be a list of (group, data) tuple.")

        # npz 'new'
        if (deal_with_npz == 'new' and saver._extension == '.npz'
                and os.path.isfile(saver.file)):
            saver.close()
            backnpz = saver.file + '-backup.npz'
            log.debug("Rename '%s' to '%s'!" % (saver.file, backnpz))
            os.rename(saver.file, backnpz)
        else:
            backnpz = None

        # open file
        if not saver.fobj_on:
            saver.iopen()
        # write data
        if saver.fobj_on:
            saver.write(self.group, self.data)
            for group, data in additional:
                saver.write(group, data)
            # npz 'new': append original data
            # npz 'new': tempdict -> {group1:data1,group2,data2}
            if backnpz:
                freshset = set(os.path.splitext(n)[0]
                               for n in saver.fobj.namelist())
                log.debug("Read data from original file %s." % backnpz)
                try:
                    backfid = numpy.load(backnpz)
                    backset = set(backfid.files)
                    # keys in backset but not freshset
                    datatodo = backset.difference(freshset)
                    # group the keys
                    tempdict = {os.path.dirname(k): {} for k in datatodo}
                    for k in datatodo:
                        tempdict[os.path.dirname(k)][
                            os.path.basename(k)] = backfid[k]
                except Exception:
                    log.error("Failed to read original file %s." %
                              backnpz, exc_info=1)
                finally:
                    if 'backfid' in dir():
                        backfid.close()
                    if 'tempdict' in dir():
                        for group, data in tempdict.items():
                            saver.write(group, data)
                    log.debug("Remove original file '%s'!" % backnpz)
                    os.remove(backnpz)
            # close file
            if auto_close:
                saver.close()
        else:
            log.error("Failed to initialize ``saver.fobj``!")
            # npz 'new'
            if backnpz:
                log.debug("Rename '%s' to '%s'!" % (backnpz, saver.file))
                os.rename(backnpz, saver.file)
