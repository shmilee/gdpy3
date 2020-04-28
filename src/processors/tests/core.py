# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

from ...cores.converter import Converter, clog
from ...cores.digger import Digger, dlog

_all_Converters = ['TestConverter']
_all_Diggers = ['TestDigger']
__all__ = _all_Converters + _all_Diggers


class TestConverter(Converter):
    __slots__ = []
    nitems = '?'
    itemspattern = ['^(?P<section>test)\.out$',
                    '.*/(?P<section>test)\.out$']

    def _convert(self):
        with self.rawloader.get(self.files) as f:
            clog.debug("Read file '%s'." % self.files)
            outdata = f.readlines()

        sd = {}
        for i, key in enumerate(['m', 'n', 'p', 'q']):
            sd.update({key: int(outdata[i].strip())})
        return sd


class TestDigger(Digger):
    __slots__ = []
    nitems = '+'
    itemspattern = [r'^(?P<section>test)/m$', r'^(?P<section>test)/n$',
                    r'^(?P<section>test)/p$', r'^(?P<section>test)/q$']
    post_template = 'tmpl_line'

    def _set_fignum(self, numseed=None):
        self._fignum = 'mnpq'

    def _dig(self, kwargs):
        m, n, p, q = self.pckloader.get_many(*self.srckeys)
        x = [i for i in range(m, n)]
        y = [i for i in range(p, q)]
        return dict(x=x, y=y, title='(%s,%s,%s,%s)' % (m, n, p, q)), {}

    def _post_dig(self, results):
        r = results
        return dict(LINE=[(r['x'], r['y'])], title=r['title'],
                    xlabel=r'$m->n$', ylabel=r'$p->q$', aspect='equal')
