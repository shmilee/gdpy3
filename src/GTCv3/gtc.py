# -*- coding: utf-8 -*-

# Copyright (c) 2019-2021 shmilee

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

Ndigits_tstep = 4


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

    @staticmethod
    def _c_val_v4_cputime(val):
        '''For GTCv4 cputimeusage'''
        val = val.strip().split('\n')
        val = numpy.array([[float(n) for n in li.split()[1:]] for li in val])
        return val.T

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
            # for GTCv4 arr1 arr2 arr3 cputimeusage
            r'meshte\s+?meshti\s+?meshne\s+?meshni\s*?$'
            + r'(?P<arr1>.*)$'
            + r'\s*?eq_flux at i=\s*?' + self.numpat + r'$',
            r'rg_sp/rg - 1,\s+?dtorpsi/q\s*?$'
            + r'(?P<arr2>.*)?$'
            + r'\s*?\*+?$'
            + r'\s*?=+?$'
            + r'\s*?No Radial Boundary Decay',
            (r'poisson solver=(\s*?' + self.numpat + r'){4}\s*$'
             + r'(?P<arr3>.*)$'
             + r'\s+routine\s+count\s+rank0.*$', 'float_2d_arr3'),
            (r'CPU TIME USAGE \(in SEC\):$'
             + '(?P<cputimeusage>.*)$'
             + r'\s*?MPush/sec:\s+?' + self.numpat + '\s*?$', 'v4_cputime'),

        ]

    def _convert(self):
        '''Read 'gtc.out' parameters.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        pickpara = re.compile(r'^\s*?(?P<key>\w+?)\s*?=\s*?(?P<val>'
                              + self.numpat + '?)\s*?,?\s*?$')
        duplicate_d = {}
        for line in outdata:
            mline = pickpara.match(line)
            if mline:
                key, val = mline.groups()
                key = key.lower()
                val = self._c_val_default(val)
                if key in sd:
                    if val != sd[key]:
                        dupkey = 'duplicate_%s_arr' % key
                        if dupkey in duplicate_d:
                            duplicate_d[dupkey].append(val)
                        else:
                            duplicate_d[dupkey] = [sd[key], val]
                        clog.debug("Duplicate datakey: %s=%s ..." % (key, val))
                else:
                    clog.debug("Filling datakey: %s=%s ..." % (key, val))
                    sd.update({key: val})
        for key, val in duplicate_d.items():
            sd.update({key: numpy.array(val)})
        if 'tstep' in sd:
            val = round(sd['tstep'], Ndigits_tstep)
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
                        # clog.debug("Filling datakey: %s=%s ..." % (key, val))
                        debugkeys.append(key)
                        sd.update({key: val})
                    except Exception:
                        pass
        clog.debug("Filled datakeys: %s ..." % str(debugkeys))

        # GTCv3 GTCv4 arr2 compatibility; shape: v4(Y,6) vs v3(Y,5)
        # v3: 0 i, 1 rg,              2 q, 3 rg_sp/rg-1, 4 dtorpsi/q
        # v4: 0 i, 1 rg/a, 2 psi/ped, 3 q, 4 rg_sp/rg-1, 5 dtorpsi/q
        # =>: 0 i, 1 rg, 2 q, 3 rg_sp/rg-1, 4 dtorpsi/q; 5 psi/ped
        if 'arr2' in sd and 'a_minor' in sd:
            val, a_minor = sd['arr2'], sd['a_minor']
            if val.shape[1] == 5:  # v3
                pass
            elif val.shape[1] == 6:  # v4
                clog.debug("Update datakey 'arr2' for GTCv4 ...")
                a2val = val[:, :2]  # 01: i, rg/a
                a2val[:, 1] = val[:, 1] * a_minor  # rg/a -> rg
                a2val = numpy.append(a2val, values=val[:, 3:6], axis=1)  # 345
                a2val = numpy.insert(a2val, 5, values=val[:, 2], axis=1)  # 2
                sd['arr2'] = a2val
            else:
                clog.warning("Unexpected 'arr2' shape for GTCv3 or GTCv4!")
            if 'qiflux' not in sd or 'rgiflux' not in sd:
                self._update_qiflux_rgiflux(sd)

        return sd

    def _update_qiflux_rgiflux(self, sd):
        '''
        If no qiflux in *sd*, try to get it from arr2
        GTCv3: qiflux at iflux=mpis//2
        GTCv4: qiflux at diag_flux
        '''
        try:
            iflux = sd['diag_flux']
        except Exception:
            iflux = sd['mpsi']
        try:
            arr2 = sd['arr2']
            if int(arr2[iflux-1][0]) == iflux:
                row = arr2[iflux-1]
            else:
                for i in range(len(arr2)):
                    if int(arr2[i][0]) == iflux:
                        row = arr2[i]
                        break
            sd['rgiflux'], sd['qiflux'] = row[1], row[2]
            clog.debug("Update datakeys: 'rgiflux', 'qiflux' ...")
        except Exception:
            pass
