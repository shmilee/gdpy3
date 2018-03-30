# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

'''
Source fortran code:

v110922
-------

skip
'''

import re
import numpy
from ..basecore import BaseCore, log

__all__ = ['GtcCoreV110922']


class GtcCoreV110922(BaseCore):
    '''
    gtc.out parameters

    INPUT_PARAMETERS, PHYSICAL_PARAMETERS, KEY_PARAMETERS, etc.

    Original can be get by
    `numpy.ndarray.tostring(outdict['backup-gtcout']).decode()`
    '''
    __slots__ = []
    instructions = ['dig']
    filepatterns = ['^(?P<group>gtc)\.out$', '.*/(?P<group>gtc)\.out$']
    grouppattern = '^gtc$'
    _datakeys = ('get by function :meth:`_dig`',)

    def _dig(self):
        '''Read 'gtc.out' parameters.'''
        with self.rawloader.get(self.file) as f:
            log.ddebug("Read file '%s'." % self.file)
            outdata = f.readlines()

        sd = {}
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
        for pat in otherparapats:
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

        # backup gtc.out, broken with archive loader
        # log.ddebug("Filling datakey: %s ..." % 'backup-gtcout')
        # with self.rawloader.get(self.file) as f:
        #     sd.update({'backup-gtcout': numpy.fromfile(f)})

        return sd
