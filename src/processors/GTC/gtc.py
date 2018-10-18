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
from ..core import DigCore, log

__all__ = ['GtcDigCoreV110922']


class GtcDigCoreV110922(DigCore):
    '''
    gtc.out parameters

    INPUT_PARAMETERS, PHYSICAL_PARAMETERS, KEY_PARAMETERS, etc.

    Original can be get by
    `numpy.ndarray.tostring(outdict['backup-gtcout']).decode()`
    '''
    __slots__ = []
    itemspattern = ['^(?P<section>gtc)\.out$', '.*/(?P<section>gtc)\.out$']
    default_section = 'gtc'
    _datakeys = ('get by function :meth:`_convert`',)

    def _convert(self):
        '''Read 'gtc.out' parameters.'''
        with self.rawloader.get(self.files) as f:
            log.debug("Read file '%s'." % self.files)
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
                log.debug("Filling datakey: %s=%s ..." % (key.lower(), val))
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
            # TODO me,trapped fraction
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
                    log.debug("Filling datakey: %s=%s ..." % (key, val))
                    debugkeys.append(key)
                    sd.update({key: val})
        log.debug("Filled datakeys: %s ..." % str(debugkeys))

        # search array parameters
        arraypats = [
            r'nue_eff=\s*?' + numpat + r'?\s+?nui_eff=\s*?' + numpat + r'?$'
            + r'(?P<arr1>.*)$'
            + r'\s*?rg0=\s*?' + numpat + r'?\s+?rg1=\s*?' + numpat + r'?\s+?',
            r'a_minor=\s*?' + numpat + r'?\s+$'
            + r'(?P<arr2>.*)$'
            + r'\s*?nmodes=(\s*?\d+)+\s*$',
            r'poisson solver=(\s*?' + numpat + r'){4}\s*$'
            + r'(?P<arr3>.*)$'
            + r'\s*CPU TIME USAGE \(in SEC\):$',
        ]
        debugkeys = []
        for pat in arraypats:
            mdata = re.search(re.compile(
                pat, re.MULTILINE | re.DOTALL), outdata)
            if mdata:
                for key, val in mdata.groupdict().items():
                    if key in ('arr3',):
                        val = val.strip().split('\n')
                        val = numpy.array([
                            [float(n) for n in li.split()]
                            for li in val
                            if not li.startswith(' write to restart_dir')
                        ])
                    else:
                        val = val.strip().split('\n')
                        val = numpy.array(
                            [[float(n) for n in li.split()] for li in val])
                    log.debug("Filling datakey: %s=%s ..." % (key, val))
                    debugkeys.append(key)
                    sd.update({key: val})
        log.debug("Filled datakeys: %s ..." % str(debugkeys))

        # backup gtc.out, broken with archive loader
        # log.debug("Filling datakey: %s ..." % 'backup-gtcout')
        # with self.rawloader.get(self.file) as f:
        #     sd.update({'backup-gtcout': numpy.fromfile(f)})

        return sd
