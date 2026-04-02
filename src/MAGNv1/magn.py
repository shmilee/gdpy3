# -*- coding: utf-8 -*-

# Copyright (c) 2026 shmilee

'''
Source fortran code:

skip
'''

import re
import numpy
from ..cores.converter import Converter, clog

_all_Converters = ['MagnConverter']
_all_Diggers = []
__all__ = _all_Converters + _all_Diggers


class MagnConverter(Converter):
    '''
    Parameters in magn.out
    '''
    __slots__ = []
    nitems = '?'
    itemspattern = [r'^(?P<section>magn)\.out$', r'.*/(?P<section>magn)\.out$']

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
            (r'rax0, zax0:\s*?(?P<rax0>' + self.numpat + r'?)'
                + r'\s*?(?P<zax0>' + self.numpat + r'?)$'),
        ]

    def _convert(self):
        '''Read 'magn.out' parameters.'''
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        pickpara = re.compile(r'^\s*?(?P<key>\w+?)\s*?:\s*?(?P<val>'
                              + self.numpat + r'?)\s*?,?\s*?$')
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

        return sd
