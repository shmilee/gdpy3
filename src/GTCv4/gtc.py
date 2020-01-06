# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
Source fortran code:

skip
'''

import re
import numpy
from ..cores.converter import Converter, clog

_all_Converters = ['GtcConverter']
_all_Diggers = []
__all__ = _all_Converters + _all_Diggers


class GtcConverter(Converter):
    '''
    Parameters in gtc.out

    INPUT_PARAMETERS, PHYSICAL_PARAMETERS, KEY_PARAMETERS, etc.
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = ['^(?P<section>gtc)\.out$', '.*/(?P<section>gtc)\.out$']

    def _convert(self):
        '''Read 'gtc.out' parameters.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
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
                clog.debug("Filling datakey: %s=%s ..." % (key.lower(), val))
                sd.update({key.lower(): val})
        clog.debug("Filled datakeys: %s ..." % str(tuple(sd.keys())))

        # search other parameters, one by one
        otherparapats = [
            r'npartdom=\s*?(?P<npartdom>\d+?)\s+?and\s+?.+',
            r',\s+?psiw=\s*?(?P<psiw>' + numpat + r'?)$',
            r'nue_eff=\s*?(?P<nue_eff>' + numpat + r'?)'
            + r'\s+?nui_eff=\s*?(?P<nui_eff>' + numpat + r'?)$',
            r'rg0,rg1=\s*?(?P<rg0>' + numpat + r'?)'
            + r'\s+?(?P<rg1>' + numpat + r'?)\s+?',
            r'a_minor=\s*?(?P<a_minor>' + numpat + r'?)\s+$',
            r'\s*?nmodes=(?P<nmodes>(\s*?\d+)+)\s*$',
            r'\s*?mmodes=(?P<mmodes>(\s*?\d+)+)\s*$',
            # TODO me,trapped fraction
            # TODO TIME USAGE
            # r'TIME USAGE \(in SEC\):$\s*.+$\s*total\s*$\s*(?P<cputime>(\s*?'
            # + numpat + r'){8})\s*$',
            r'Program starts at DATE=(?P<start_date>' + numpat + r'?)'
            + r'\s+TIME=(?P<start_time>' + numpat + r'?)$',
            r'Program ends at   DATE=(?P<end_date>' + numpat + r'?)'
            + r'\s+TIME=(?P<end_time>' + numpat + r'?)$',
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
                    clog.debug("Filling datakey: %s=%s ..." % (key, val))
                    debugkeys.append(key)
                    sd.update({key: val})
        clog.debug("Filled datakeys: %s ..." % str(debugkeys))

        # search array parameters
        arraypats = [
            r'meshte\s+?meshti\s+?meshne\s+?meshni\s*?$'
            + r'(?P<arr1>.*)$'
            + r'\s*?eq_flux at i=\s*?' + numpat + r'$',
            r'rg_sp/rg - 1,\s+?dtorpsi/q\s*?$'
            + r'(?P<arr2>.*)?$'
            + r'\s*?\*+?$'
            + r'\s*?=+?$'
            + r'\s*?No Radial Boundary Decay',
            r'poisson solver=(\s*?' + numpat + r'){4}\s*$'
            + r'(?P<arr3>.*)$'
            + r'\s+routine\s+count\s+rank0.*$',
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
                    if key == 'arr2':
                        # rg/a -> rg, GTCv3 compatibility
                        val = numpy.insert(
                            val, 1, values=val[:, 1]*sd['a_minor'], axis=1)
                    # clog.debug("Filling datakey: %s=%s ..." % (key, val))
                    debugkeys.append(key)
                    sd.update({key: val})
        clog.debug("Filled datakeys: %s ..." % str(debugkeys))

        return sd
