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

    # http://stackoverflow.com/a/29581287
    numpat = r'[-+]?\d+[\.]?\d*[eE]?[-+]?\d*'

    @staticmethod
    def _c_val_default(val):
        if val.isdigit():
            return int(val)
        else:
            # if int(val) - val == 0:
            #    return int(val)
            return float(val)

    @staticmethod
    def _c_val_int_arr(val):
        return numpy.array([int(n) for n in val.split()])

    @staticmethod
    def _c_val_float_arr(val):
        return numpy.array([float(n) for n in val.split()])

    @property
    def otherparapats(self):
        '''
        search other parameters, one by one

        str: pat_str, then convert_val_method='default'
        OR
        tuple: (pat_str, convert_val_method), like 'int_arr', 'float_arr'

        method: getattr(self, '_c_val_%s' % convert_val_method)
        '''
        return [
            r'npartdom=\s*?(?P<npartdom>\d+?)\s+?and\s+?.+',
            r'\s+?psiw=\s*?(?P<psiw>' + self.numpat + r'?)\s*$',
            (r'nue_eff=\s*?(?P<nue_eff>' + self.numpat + r'?)'
                + r'\s+?nui_eff=\s*?(?P<nui_eff>' + self.numpat + r'?)$'),
            (r'rg0=\s*?(?P<rg0>' + self.numpat + r'?)'  # commit ee5da784
                + r'\s+?rg1=\s*?(?P<rg1>' + self.numpat + r'?)\s+?'),
            (r'rg0,rg1=\s*?(?P<rg0>' + self.numpat + r'?)'
                + r'\s+?(?P<rg1>' + self.numpat + r'?)\s+?'),
            r'a_minor=\s*?(?P<a_minor>' + self.numpat + r'?)\s+$',
            (r'\s*?nmodes=(?P<nmodes>(\s*?\d+)+)\s*$', 'int_arr'),
            (r'\s*?mmodes=(?P<mmodes>(\s*?\d+)+)\s*$', 'int_arr'),
            (r'rzf bstep=\s*?(?P<rzf_bstep>' + self.numpat
                + r'?), izonal=(?P<rzf_izonal>' + self.numpat
                + '?), kr=\s*?(?P<rzf_kr>' + self.numpat
                + '?), r1=\s*?(?P<rzf_r1>' + self.numpat
                + '?), r2=\s*?(?P<rzf_r2>' + self.numpat
                + '?)'),  # commit f91ad696
            (r'me=\s*?(?P<me>' + self.numpat + r'?)\s*,\s+trapped fraction'
                + r'\s+?(?P<trapped_frac>' + self.numpat + r'?)\s+?'),
            (r'TIME USAGE \(in SEC\):$\s*.+$\s*total\s*$\s*(?P<cputime>(\s*?'
                + self.numpat + r'){8})\s*$', 'float_arr'),
            (r'Program starts at DATE=(?P<start_date>' + self.numpat + r'?)'
                + r'\s+TIME=(?P<start_time>' + self.numpat + r'?)\s*?$'),
            (r'Program ends at   DATE=(?P<end_date>' + self.numpat + r'?)'
                + r'\s+TIME=(?P<end_time>' + self.numpat + r'?)\s*?$'),
        ]

    @staticmethod
    def _c_val_float_2d_arr(val):
        val = val.strip().split('\n')
        return numpy.array([[float(n) for n in li.split()] for li in val])

    @staticmethod
    def _c_val_float_2d_arr3(val):
        return numpy.array([[float(n) for n in li.split()]
                            for li in val.strip().split('\n')
                            if not li.startswith(' write to restart_dir')])

    @property
    def twoDarraypats(self):
        '''
        search two dimensional array parameters
        str or tuple like :attr:`otherparapats`

        default convert_val_method = 'float_2d_arr'
        '''
        return [
            r'\s+?nui_eff=\s*?' + self.numpat + r'?$'
            + r'(?P<arr1>.*)$'
            + r'\s*?rg0=\s*?' + self.numpat + r'?\s+?rg1=\s*?' + self.numpat,
            r'a_minor=\s*?' + self.numpat + r'?\s+$'
            + r'(?P<arr2>.*)$'
            + r'\s*?nmodes=(\s*?\d+)+\s*$',
            (r'poisson solver=(\s*?' + self.numpat + r'){4}\s*$'
             + r'(?P<arr3>.*)$'
             + r'\s*CPU TIME USAGE \(in SEC\):$', 'float_2d_arr3'),
        ]

    def _convert(self):
        '''Read 'gtc.out' parameters.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        pickpara = re.compile(r'^\s*?(?P<key>\w+?)\s*?=\s*?(?P<val>'
                              + self.numpat + '?)\s*?,?\s*?$')
        for line in outdata:
            mline = pickpara.match(line)
            if mline:
                key, val = mline.groups()
                val = self._c_val_default(val)
                clog.debug("Filling datakey: %s=%s ..." % (key.lower(), val))
                sd.update({key.lower(): val})
        if 'tstep' in sd:
            val = round(sd['tstep'], 8)
            clog.debug("Round datakey: %s=%s ..." % ('tstep', val))
            sd['tstep'] = val
        clog.debug("Filled datakeys: %s ..." % str(tuple(sd.keys())))

        # search other parameters, one by one
        outdata = ''.join(outdata)
        debugkeys = []
        for pat in self.otherparapats:
            if type(pat) == tuple:
                pat, c_val_method = pat
            else:
                c_val_method = 'default'
            mdata = re.search(pat, outdata, re.M)
            if mdata:
                c_val_method = getattr(self, '_c_val_%s' % c_val_method)
                for key, val in mdata.groupdict().items():
                    try:
                        val = c_val_method(val)
                        clog.debug("Filling datakey: %s=%s ..." % (key, val))
                        debugkeys.append(key)
                        sd.update({key: val})
                    except Exception:
                        pass
        clog.debug("Filled datakeys: %s ..." % str(debugkeys))

        # search two dimensional array parameters
        debugkeys = []
        for pat in self.twoDarraypats:
            if type(pat) == tuple:
                pat, c_val_method = pat
            else:
                c_val_method = 'float_2d_arr'
            mdata = re.search(re.compile(
                pat, re.MULTILINE | re.DOTALL), outdata)
            if mdata:
                c_val_method = getattr(self, '_c_val_%s' % c_val_method)
                for key, val in mdata.groupdict().items():
                    try:
                        val = c_val_method(val)
                        #clog.debug("Filling datakey: %s=%s ..." % (key, val))
                        debugkeys.append(key)
                        sd.update({key: val})
                    except Exception:
                        pass
        clog.debug("Filled datakeys: %s ..." % str(debugkeys))

        return sd
