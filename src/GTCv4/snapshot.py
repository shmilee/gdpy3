# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
GTCv3.snapshot -> GTCv4.snapshot

* patterns: v3, snap\d{5,7} -> v4, snap\d{7}
'''

from ..GTCv3 import snapshot as snapv3
from ..cores.base import AppendDocstringMeta

_all_Converters = snapv3._all_Converters
_all_Diggers = snapv3._all_Diggers
__all__ = _all_Converters + _all_Diggers


class ModifyPattern527(AppendDocstringMeta):
    """
    Modify itemspattern, commonpattern, neededpattern
    """
    _todo_pattern = ['itemspattern', 'commonpattern', 'neededpattern']

    def __new__(meta, name, bases, attrs):
        for attr_name in meta._todo_pattern:
            base = bases[0]  # v3 class
            original = getattr(base, attr_name, None)
            if original:
                # print('using parent', base, attr_name)
                if attr_name == 'neededpattern' and original == 'ALL':
                    attrs[attr_name] = 'ALL'
                    continue
                v4pattern = []
                for pat in original:
                    if r'snap\d{5,7}' in pat:
                        v4pattern.append(
                            pat.replace(r'snap\d{5,7}', r'snap\d{7}'))
                    else:
                        v4pattern.append(pat)
                attrs[attr_name] = v4pattern
        # OR Modify property group, preserve _group
        # group: v3, snap\d{5} -> v4, snap\d{7} -> v4, snap\d{5}
        # attrs['group'] = property(
        #    fget=lambda self: self._group.replace('snap00', 'snap'))
        return super(ModifyPattern527, meta).__new__(meta, name, bases, attrs)


class SnapshotConverter(snapv3.SnapshotConverter,
                        metaclass=ModifyPattern527):
    pass


class SnapshotProfilePdfDigger(snapv3.SnapshotProfilePdfDigger,
                               metaclass=ModifyPattern527):
    pass


class SnapshotFieldFluxDigger(snapv3.SnapshotFieldFluxDigger,
                              metaclass=ModifyPattern527):
    pass


class SnapshotFieldPoloidalDigger(snapv3.SnapshotFieldPoloidalDigger,
                                  metaclass=ModifyPattern527):
    pass


class SnapshotFieldSpectrumDigger(snapv3.SnapshotFieldSpectrumDigger,
                                  metaclass=ModifyPattern527):
    pass


class SnapshotFieldProfileDigger(snapv3.SnapshotFieldProfileDigger,
                                 metaclass=ModifyPattern527):
    pass


class SnapshotFieldmDigger(snapv3.SnapshotFieldmDigger,
                           metaclass=ModifyPattern527):
    pass
