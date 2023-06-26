# -*- coding: utf-8 -*-

# Copyright (c) 2019-2022 shmilee

'''
Contains Exporter core class.
'''
from .base import BaseCore, AppendDocstringMeta
from ..glogger import getGLogger

__all__ = ['Exporter']
elog = getGLogger('E')


class Exporter(BaseCore, metaclass=AppendDocstringMeta):
    '''
    Assemble dig results, options and template.


    Attributes
    ----------
    template: str
        template name, like 'tmpl_line', 'tmpl_z111p', ...
    '''
    __slots__ = ['template', '_z111p_tmpls', 'visoptions']
    # :attr:`visplter.template_available`
    template_available = (
        'tmpl_contourf',
        'tmpl_line',
        'tmpl_sharextwinx',
        'tmpl_z111p',  # last one
    )

    def fmt_export(self, data, fmt):
        '''Convert *data* format from dict to *fmt*.'''
        if fmt == 'dict':
            return data
        elif fmt == 'pickle':
            import pickle
            return pickle.dumps(data)
        elif fmt == 'json':
            from .._json import JsonEncoder
            encoder = JsonEncoder(ensure_ascii=False, separators=(",", ":"))
            return encoder.encode(data)
        else:
            pass

    def __init__(self, post_tmpl):
        '''Core instances for *post_tmpl*.'''
        _z111p_tmpls = []
        if isinstance(post_tmpl, str):
            post_tmpl = [post_tmpl]
        elif isinstance(post_tmpl, tuple):
            if post_tmpl[0] != 'tmpl_z111p':
                raise ValueError(
                    "tuple post_template must start with 'tmpl_z111p', "
                    "Not '%s'!" % post_tmpl[0])
        else:
            raise ValueError('Invalid type of post_template: %s' % post_tmpl)
        for tmpl in post_tmpl:
            if tmpl not in self.template_available:
                raise ValueError('Unavailable template: %s' % tmpl)
        super(Exporter, self).__init__(
            None, ('tmpl',), post_tmpl[:1], post_tmpl[1:])
        self.template = self.items[0]
        self._z111p_tmpls = self.common
        self.visoptions = {}
        for tmpl in post_tmpl:
            self.visoptions.update(getattr(self, '_visoptions_%s' % tmpl))

    def str_export_kwargs(self, kwargs):
        '''
        Turn :meth:`export` *kwargs* to str.
        Check them in :meth:`_export_tmpl_xxx`.__doc__, and sort by key.
        Check all `tmpl_xxx` in :attr:`template` and :attr:`_z111p_tmpls`.
        Return string like, "k1=1,k2=[2],k3='abc'".
        '''
        ckkws = {}
        for tmpl in self.items + self.common:
            meth = getattr(self, '_export_%s' % tmpl)
            ckkws.update({k: (list(v) if isinstance(v, tuple) else v)
                          for k, v in kwargs.items()
                          if meth.__doc__.find('*%s*' % k) > 0})
        ckkws = ['%s=%r' % (k, v) for k, v in ckkws.items()]
        return ','.join(sorted(ckkws))

    def export(self, results, otherinfo={}, fmt='dict', **kwargs):
        '''
        Export results, template name for visplter.

        Parameters
        ----------
        otherinfo: dict
            if 'accfiglabel' in it, accfiglabel will be updated.
            'figlabel/digkwargstr' -> 'figlabel/digkwargstr,viskwargstr'
        fmt: format 'dict', 'pickle' or 'json'
        kwargs: visplter template options, like colorbar, hspace etc.
        '''
        meth = getattr(self, '_export_%s' % self.template)
        results, viskwargs = meth(results, kwargs)
        viskwargstr = self.str_export_kwargs(viskwargs)
        if viskwargstr and 'accfiglabel' in otherinfo:
            elog.debug("The viskwargstr of %s is '%s'."
                       % (otherinfo['accfiglabel'], viskwargstr))
            otherinfo['accfiglabel'] = ','.join((
                otherinfo['accfiglabel'], viskwargstr))
        return self.fmt_export(
            dict(results=results, template=self.template, **otherinfo), fmt)

    def export_options(self, digoptions, otherinfo={}, fmt='dict'):
        '''
        Export dig options and  visplter template options for GUI widgets.

        Parameters
        ----------
        otherinfo: dict
        fmt: format 'dict', 'pickle' or 'json'
        '''
        return self.fmt_export(
            dict(digoptions=digoptions,
                 visoptions=self.visoptions,
                 **otherinfo), fmt)

    _visoption_default_ylabel_rotation = dict(
        widget='IntSlider',
        rangee=(0, 360, 10),
        value=90,
        description='ylabel rotation:')
    _visoption_default_aspect = dict(
        widget='Dropdown',
        options=['auto', 'equal'],
        value='auto',
        description='aspect:')

    # 1. tmpl_contourf
    _visoptions_tmpl_contourf = dict(
        plot_method=dict(
            widget='Dropdown',
            options=['contourf', 'pcolor', 'pcolormesh', 'plot_surface'],
            value='contourf',
            description='plot method:'),
        contourf_levels=dict(
            widget='IntSlider',
            rangee=(20, 200, 20),
            value=100,
            description='contourf levels:'),
        center_norm=dict(
            widget='Checkbox',
            value=False,
            description='CenteredNorm'),
        center_norm_half_ratio=dict(
            widget='FloatSlider',
            rangee=(0, 1, 0.05),
            value=1.0,
            description='CenteredNorm half ratio:'),
        colorbar=dict(
            widget='Checkbox',
            value=True,
            description='colorbar'),
        aspect=_visoption_default_aspect.copy(),
        grid_alpha=dict(
            widget='FloatSlider',
            rangee=(0, 1, 0.1),
            value=0.5,
            description='grid alpha:'),
        plot_surface_shadow=dict(
            widget='SelectMultiple',
            options=['x', 'y', 'z'],
            value=[],
            description='plot surface shadow:')
    )

    def _export_tmpl_contourf(self, results, kwargs):
        '''
        contourf kwargs
        ---------------
        kwargs passed on to *plot_method* like :meth:`visplter.tmpl_contourf`
        *plot_method*: contour like method
        *plot_method_args*, *plot_method_kwargs*: fallback
        *contourf_levels*: int, default 100
        *center_norm*: bool, use CenteredNorm or not, default False
        *center_norm_half_ratio*: float, (0,1]
            decrease CenteredNorm halfrange by this ratio, default 1.0
        *colorbar*: bool
        *aspect*: str
        *grid_alpha*: float
        *plot_surface_shadow*: list
        '''
        if 'plot_method' not in results:
            results['plot_method'] = 'contourf'
        if 'aspect' in results:
            elog.info("Use aspect=%s set by Digger." % results['aspect'])
            kwargs['aspect'] = results['aspect']
        debug_kw = {}
        for k in ['plot_method', 'plot_method_args', 'plot_method_kwargs',
                  'contourf_levels',
                  'center_norm', 'center_norm_half_ratio', 'colorbar',
                  'aspect', 'grid_alpha', 'plot_surface_shadow']:
            if k in kwargs:
                results[k] = kwargs[k]
            if k in results:
                debug_kw[k] = results[k]
        elog.debug("Some tmpl_contourf kwargs: %s" % debug_kw)
        return results, debug_kw

    # 2. tmpl_line
    _visoptions_tmpl_line = dict(
        ylabel_rotation=_visoption_default_ylabel_rotation.copy(),
        aspect=_visoption_default_aspect.copy(),
    )

    def _export_tmpl_line(self, results, kwargs):
        '''
        line kwargs
        -----------
        kwargs passed on to :meth:`visplter.tmpl_line`
        *ylabel_rotation*: str or int
            default 'vertical'
        *aspect*: str, default 'auto'
        '''
        if 'aspect' in results:
            elog.info("Use aspect=%s set by Digger." % results['aspect'])
            kwargs['aspect'] = results['aspect']
        debug_kw = {}
        for k in self._visoptions_tmpl_line.keys():
            if k in kwargs:
                results[k] = kwargs[k]
            if k in results:
                debug_kw[k] = results[k]
        elog.debug("Some tmpl_line kwargs: %s" % debug_kw)
        return results, debug_kw

    # 3. tmpl_sharextwinx
    _visoptions_tmpl_sharextwinx = dict(
        hspace=dict(
            widget='FloatSlider',
            rangee=(0, 0.5, 0.02),
            value=0.02,
            description='hspace:'),
        ylabel_rotation=_visoption_default_ylabel_rotation.copy(),
    )

    def _export_tmpl_sharextwinx(self, results, kwargs):
        '''
        sharextwinx kwargs
        ------------------
        kwargs passed on to :meth:`visplter.tmpl_sharextwinx`
        *hspace*: float
            subplot.hspace, default 0.02
        *ylabel_rotation*: str or int
            default 'vertical'
        '''
        debug_kw = {}
        for k in ['hspace', 'ylabel_rotation']:
            if k in kwargs:
                results[k] = kwargs[k]
            if k in results:
                debug_kw[k] = results[k]
        elog.debug("Some tmpl_sharextwinx kwargs: %s" % debug_kw)
        return results, debug_kw

    # 4. tmpl_z111p, self.common
    _visoptions_tmpl_z111p = {}

    def _export_tmpl_z111p(self, results, kwargs):
        '''
        For :meth:`visplter.tmpl_z111p`.
        '''
        debug_kw = {}
        for rt in results.get('zip_results', []):
            meth = getattr(self, '_export_%s' % rt[0])
            _res, _dekw = meth(rt[2], kwargs)
            if rt[2] is not _res:
                rt[2] = _res
            debug_kw.update(_dekw)
        elog.debug("Some tmpl_z111p kwargs: %s" % debug_kw)
        return results, debug_kw
