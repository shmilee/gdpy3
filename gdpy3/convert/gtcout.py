# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

'''
Source fortran code:

v110922
-------

skip
'''

import os
import re
import numpy
from .block import Block, log

__all__ = ['GtcOutV110922']


class GtcOutV110922(Block):
    '''
    gtc.out parameters

    INPUT_PARAMETERS, PHYSICAL_PARAMETERS, KEY_PARAMETERS, etc.

    Original can be get by
    `numpy.ndarray.tostring(self.data['backup-gtcout']).decode()`

    Attributes
    ----------
    file: str
        File path of GTC ``gtc.out`` to convert
    group: str of data group
    datakeys: tuple
        data keys of physical quantities in ``gtc.out``
    data: dict of converted data
    '''
    __slots__ = []
    _Datakeys = ('set by function convert',)

    def convert(self, additionalpats=[]):
        '''Read gtc.out parameters

        convert the gtc.out data to self.data as a dict,
        save list in data dict as numpy.array.

        Parameters
        ----------
        additionalpats: list
            list of additional patterns to get parameters
            re.search(pattern, datastring, re.M)

        Examples
        --------
        >>> numpat = r'[-+]?\d+[\.]?\d*[eE]?[-+]?\d*'
        >>> mypats=[r'\*{6}\s+k_r\*rhoi=\s*?(?P<krrhoi>' + numpat + r'?)\s*?,'
        ... + r'\s+k_r\*rho0=\s*?(?P<krrho0>' + numpat + r'?)\s+?\*{6}',
        ... r'\*{5}\s+k_r\*dlt_r=\s*?(?P<krdltr>' + numpat + r'?)\s+?\*{5}']
        >>> gtcout.convert(additionalpats=mypats)
        '''
        with open(self.file, 'r') as f:
            log.ddebug("Read file '%s'." % self.file)
            outdata = f.readlines()

        sd = self.data

        # http://stackoverflow.com/a/29581287
        numpat = r'[-+]?\d+[\.]?\d*[eE]?[-+]?\d*'
        pickpara = re.compile(
            r'^\s*?(?P<key>\w+?)\s*?=\s*?(?P<val>' + numpat + '?)\s*?,?\s*?$')
        for line in outdata:
            mline = pickpara.match(line)
            if mline:
                key, val = mline.groups()
                if val.isdigit():
                    val = int(val)
                else:
                    val = float(val)
                    # if int(val) - val == 0:
                    #    val = int(val)
                log.ddebug("Filling datakey: %s=%s ..." % (key.lower(), val))
                sd.update({key.lower(): val})
        log.debug("Filled datakeys: %s ..." % str(tuple(sd.keys())))

        # search other parameters, one by one
        otherparapats = [
            r'npartdom=\s*?(?P<npartdom>\d+?)\s+?and\s+?.+',
            r',\s+?psiw=\s*?(?P<psiw>' + numpat + r'?)$',
            r'nue_eff=\s*?(?P<nue_eff>' + numpat + r'?)'
            + r'\s+?nui_eff=\s*?(?P<nui_eff>' + numpat + r'?)$',
            r'rg0=\s*?(?P<rg0>' + numpat + r'?)'
            + r'\s+?rg1=\s*?(?P<rg1>' + numpat + r'?)\s+?',
            r'a_minor=\s*?(?P<a_minor>' + numpat + r'?)\s+$',
            r'\s*?nmodes=(?P<nmodes>(\s*?\d+)+)\s*$',
            r'\s*?mmodes=(?P<mmodes>(\s*?\d+)+)\s*$',
            r'TIME USAGE \(in SEC\):$\s*.+$\s*total\s*$\s*(?P<cputime>(\s*?'
            + numpat + r'){8})\s*$',
            r'Program starts at DATE=(?P<start_date>' + numpat + r'?)'
            + r'\x00{2}\s+TIME=(?P<start_time>' + numpat + r'?)$',
            r'Program ends at   DATE=(?P<end_date>' + numpat + r'?)'
            + r'\x00{2}\s+TIME=(?P<end_time>' + numpat + r'?)$',
        ]
        outdata = ''.join(outdata)
        debugkeys = []
        # TODO: additionalpats, val is a array of integer or float
        # val is a number -> len(val.split()) == 1
        for pat in otherparapats + additionalpats:
            mdata = re.search(pat, outdata, re.M)
            if mdata:
                for key, val in mdata.groupdict().items():
                    if key in ('nmodes', 'mmodes'):
                        val = numpy.array([int(n) for n in val.split()])
                    elif key in ('cputime',):
                        val = numpy.array([float(t) for t in val.split()])
                    elif val.isdigit():
                        val = int(val)
                    else:
                        val = float(val)
                    log.ddebug("Filling datakey: %s=%s ..." % (key, val))
                    debugkeys.append(key)
                    sd.update({key: val})
        log.debug("Filled datakeys: %s ..." % str(debugkeys))

        # only residual zonal flow(zf) case, second occurence match
        pat = (r'\*{6}\s+k_r\*rhoi=\s*?(?P<zfkrrhoi>' + numpat + r'?)\s*?,'
               + r'\s+k_r\*rho0=\s*?(?P<zfkrrho0>' + numpat + r'?)\s+?\*{6}$'
               + r'\s*istep=\s*?(?P<zfistep>' + numpat + r'?)\s*.+$'
               + r'\s*\*{5}\s+k_r\*dlt_r=\s*?(?P<zfkrdltr>'
               + numpat + r'?)\s+?\*{5}')
        mdata = [m.groupdict() for m in re.finditer(pat, outdata, re.M)]
        if len(mdata) == 2 and len(mdata[1]) == 4:
            log.debug("Filling datakeys: %s ..." %
                      str([key for key, val in mdata[1].items()]))
            sd.update({key: int(val) if val.isdigit() else float(val)
                       for key, val in mdata[1].items()})

        # backup gtc.out
        log.ddebug("Filling datakey: %s ..." % 'backup-gtcout')
        sd.update({'backup-gtcout': numpy.fromfile(self.file)})

        self.datakeys = tuple(sd.keys())
