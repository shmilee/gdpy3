# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import scipy

__all__ = ['ReadMat']


class ReadMat(object):
    '''Read data from matlab .mat file.
    Return a dictionary-like object.

    Attributes
    ----------
    file: str
        path of .mat file
    datakeys: tuple
        keys of physical quantities in the .mat file
    desc: str
        description of the .mat file
    description: alias desc

    Parameters
    ----------
    matfile: str
        the .mat file to open
    '''

    def __init__(self, matfile):
        if os.path.isfile(matfile):
            self.file = matfile
        else:
            raise IOError("Failed to find file %s." % matfile)
        # TODO(nobody): get datakeys
