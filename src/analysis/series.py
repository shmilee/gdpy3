# -*- coding: utf-8 -*-

# Copyright (c) 2023 shmilee

'''
Function, class to compare different cases.
'''

import os
import re
import shutil
import json
import numpy as np
from ..loaders import get_rawloader
from ..processors import get_processor
from ..visplters import get_visplter
from .._json import dumps as json_dumps
from ..glogger import getGLogger

__all__ = [
    'get_selected_converted_data',
    'get_label_ts_data', 'LabelInfoSeries',
]
log = getGLogger('G.a')


def get_selected_converted_data(pathsmap, parallel='off', **kwargs):
    '''
    Get selected GTC raw data from original directory (like sftp://xxx),
    then convert and save to a new directory (like local path).
    Return a list of failed cases.

    Parameters
    ----------
    pathsmap: list of 3-tuple
        casepaths to do, format (original, newpath, filenames_exclude), like,

        .. code::

            pathsmap = [(
                'sftp://u1@a.b.c.d##scan-2023/P1P2', './GTC-scan-2023/P1P2',
                ['phi_dir/.*out',  # pattern, exclude
                 r'(?!^(?:gtc|history)\.out|gtc-input.*lua$)']  # ?! selected
            ), next case, ...]

    parallel: str, 'off' or 'multiprocess'
        'sftp://xxx' case needs parallel='off'.
    kwargs: other parameters passed to :meth:`processors.get_processor`

    Notes
    -----
    1. Use :meth:`utils.GetPasswd.set` to set password of sftp.
    '''
    for k in list(kwargs.keys()):
        if k in ('path', 'parallel', 'filenames_exclude', 'Sid'):
            remove = kwargs.pop(k)
    if 'name' in kwargs:
        gdpcls = get_processor(name=kwargs.get('name'), parallel='off')
    else:
        gdpcls = get_processor(parallel='off')
    failed = []
    N = len(pathsmap)
    for i, pmap in enumerate(pathsmap, 1):
        try:
            print('', flush=True)
            print('-'*16, '%d/%d' % (i, N), '-'*16, flush=True)
            path, dest, exclude = pmap
            if os.path.exists(dest):
                test = get_rawloader(dest)
                if (test.refind('%s-.*converted.*' % gdpcls.__name__.lower())
                        and test.refind(gdpcls.saltname)):
                    log.warning('Skip path %s that has converted data!' % dest)
                    continue
            else:
                log.info('Create directory: %s' % dest)
                os.mkdir(dest)
            gdp = get_processor(
                path, parallel=parallel, filenames_exclude=exclude, Sid=True,
                **kwargs)
            converted = gdp.pcksaver.path
            idx = converted.rfind(gdp.name.lower() + '-')
            file = os.path.join(dest, converted[idx:])
            log.info('Move converted data: %s -> %s' % (converted, file))
            shutil.move(converted, file)
            # copy gtc.out, gtc-input.lua
            todo = [gdp.saltname]
            todo.extend(gdp.rawloader.refind('gtc-\d+\.out'))
            todo.extend(gdp.rawloader.refind('gtc-input.*\.lua'))
            for file1 in todo:
                file2 = os.path.join(dest, file1)
                if os.path.exists(file2):
                    log.warning('Skip file: %s' % file2)
                    continue
                log.info('Copy file: %s -> %s' % (file1, file2))
                with gdp.rawloader.get(file1) as f1:
                    with open(file2, 'w') as f2:
                        f2.write(f1.read())
        except Exception as e:
            log.error('%s failed: %s' % (pmap[0], e), exc_info=1)
            failed.append(pmap)
    return failed


def get_label_ts_data(casepaths, path_replace=None, name_replace=None,
                      skip_lost=True, ts_key_ver='v1', removeNaN=True,
                      savepath=None, savefmt='ls-json'):
    '''
    Get time series data from GTC cases, save to json or other data labeling
    format.
    Return a list of dicts that contain path, name, saltstr and ts data etc.
    for each case.

    Parameters
    ----------
    casepaths: list
        real cases paths of GTC parameter series
    path_replace: function
        change path in results for each case, input: case path
    name_replace: function
        change name in results for each case, input: case path
        default: basename of case path
    skip_lost: bool
        skip these paths which have no 'gtc.out' or not(raise error)
    ts_key_ver: str, version for ts keys.
        'v1' means these 4 keys: time, chi_i, d_i, logphirms.
    removeNaN: bool
        remove NaN data, check array of chi_i etc., cut off by array index
    savepath: str, file path
        save results to savepath, then upload to your labeling platform
    savefmt: str, save format
        'ls-json' is saving to json for the Label Studio Platform
    '''
    ts_data_list = []
    for path in casepaths:
        if not os.path.exists(os.path.join(path, 'gtc.out')):
            if skip_lost:
                log.warning("Skip '%s'!" % path)
                continue
            else:
                raise IOError("Lost 'gtc.out' in '%s'!" % path)
        gdp = get_processor(path)
        if path_replace and callable(path_replace):
            path = path_replace(path)
        name = os.path.basename(os.path.realpath(path))  # a/b/ -> b
        if name_replace and callable(name_replace):
            name = name_replace(path)
        # ts_data
        if ts_key_ver == 'v1':
            a, b, c = gdp.dig('history/ion_flux', post=False)
            time = b['time']
            chi, D = b['energy'], b['particle']
            a, b, c = gdp.dig('history/phi', post=False)
            logphirms = np.log(b['fieldrms'])
            if removeNaN:
                idx = len(time)
                for arr in (chi, D, logphirms):
                    checkNaN = np.where(np.isnan(arr))[0]
                    if checkNaN.size > 0:
                        idx = min(checkNaN[0], idx)
                if idx < len(time):
                    time = time[:idx]
                    chi, D = chi[:idx], D[:idx]
                    logphirms = logphirms[:idx]
            ts_data = dict(time=time, chi_i=chi, d_i=D, logphirms=logphirms)
        else:
            log.error("Unsupported ts_key_ver: '%s'!" % ts_key_ver)
            return
        ts_data_list.append(dict(
            path=path, name=name, saltstr=gdp.saltstr, ts=ts_data))
    if savepath:
        if savefmt == 'ls-json':
            ls_ts_list = [
                dict(id=i, data=data)
                for i, data in enumerate(ts_data_list, 1)
            ]
            with open(savepath, 'w') as f1:
                f1.write(json_dumps(ls_ts_list, indent=2, indent_limit=8))
        else:
            log.error("Unsupported savefmt: '%s'!" % savefmt)
    return ts_data_list


class LabelInfoSeries(object):
    '''
    Label information of GTC parameter series cases.

    Attributes
    ----------
    info: dict of annotations for each case
        key is saltstr. value is dict(path=path, name=name, label=label).
        label dict has time range for 'linear', 'nonlinear', 'saturation'.
    search_paths: dict of path=[saltstr] pairs
    search_names: dict of name=[saltstr] pairs
        if has name collision, then name=[saltstr1, saltstr2, ...]
    '''
    stages = ('linear', 'nonlinear', 'saturation')

    def __init__(self, label_list=None, ls_json=None):
        '''
        Parameters
        ----------
        label_list: list of manually built label info
            dict(path, name, saltstr, label=label) for each case,
            echo label dict has time (start, end) pairs for 'linear',
            'nonlinear', 'saturation' stage, and unit is R0/cs.
        ls_json: str, path of Label Studio json results
        '''
        if label_list:
            self.info = self._get_from_label_list(label_list)
        elif ls_json:
            self.info = self._get_from_ls_json(ls_json)
        else:
            raise ValueError('Lost label info from json file or list!')
        self.search_paths = {}
        self.search_names = {}
        for s, v in self.info.items():
            p, n = v['path'], v['name']
            if p in self.search_paths:
                self.search_paths[p].append(s)
                log.warning("path '%s' collision: '%s'!" % (p, s))
            else:
                self.search_paths[p] = [s]
            if n in self.search_names:
                log.warning("name '%s' collision: '%s'!" % (n, s))
                self.search_names[n].append(s)
            else:
                self.search_names[n] = [s]

    def __contains__(self, saltstr):
        ''' Return True if saltstr is in :attr:`info` '''
        return saltstr in self.info

    def get(self, key, stage='linear', by='saltstr'):
        '''
        Parameters
        ----------
        key: str
            name, path or saltstr of one case
        stage: str
            linear(default), nonlinear, or saturation
        by: str
            use name, path or saltstr(default) as key
        '''
        if stage not in self.stages:
            raise ValueError('Unsupported stage: %s' % stage)
        if by not in ('name', 'path', 'saltstr'):
            raise ValueError('Unsupported key type: %s' % by)
        if by == 'name':
            saltstr = self.search_names.get(key, [None])[-1]
        elif by == 'path':
            saltstr = self.search_paths.get(key, [None])[-1]
        else:
            saltstr = key
        if saltstr in self.info:
            if stage in self.info[saltstr]['label']:
                return self.info[saltstr]['label'][stage]
            else:
                log.error("Stage '%s' not labeled for '%s'!" % (stage, key))
        else:
            log.error("Key '%s' not found!" % key)
        return None, None

    def _get_from_label_list(self, label_list):
        info = {}
        for res in label_list:
            path, name, saltstr = res['path'], res['name'], res['saltstr']
            info[saltstr] = dict(path=path, name=name, label=res['label'])
        return info

    def __get_labeled_time_range(self, annresult):
        result = {}
        for ann in annresult:
            if 'timeserieslabels' in ann['value']:
                ln = ann['value']['timeserieslabels'][0]
                if ln in self.stages:
                    start, end = ann['value']['start'], ann['value']['end']
                    result[ln] = (start, end)
        return result

    def _get_from_ls_json(self, ls_json):
        info = {}
        with open(ls_json, 'r') as f1:
            reslist = json.loads(f1.read())
        for res in reslist:
            path, name = res['data']['path'], res['data']['name']
            saltstr = res['data']['saltstr']
            try:
                labeltime = self.__get_labeled_time_range(
                    res['annotations'][0]['result'])  # first one
                log.info('Get labeled %s for %s' % (labeltime.keys(), path))
                info[saltstr] = dict(path=path, name=name, label=labeltime)
            except Exception as e:
                log.warning('For %s: ' % name, e)
        return info

    @staticmethod
    def merge_ls_jsons(*jsonfiles, savepath=None,
                       result_modify=None, sort_key=None, start_id=None):
        '''
        Parameters
        ----------
        jsonfiles: str, path of Label Studio json results
        savepath: str, new path
        result_modify: function
            modify result of each case, like change case path and name
            input: case result, return: modified result
        sort_key: function, custom function to sort results
            do after result_modify, input: case result
        start_id: int, change start id in json results, >=1
        '''
        result_list = []
        for file in jsonfiles:
            with open(file, 'r') as f1:
                reslist = json.loads(f1.read())
            result_list.extend(reslist)
        if result_modify and callable(result_modify):
            result_list = list(map(result_modify, result_list))
        if sort_key and callable(sort_key):
            result_list.sort(key=sort_key)
        if isinstance(start_id, int):
            for i, result in enumerate(result_list, max(start_id, 1)):
                result['id'] = i
        if savepath:
            with open(savepath, 'w') as f2:
                f2.write(json_dumps(result_list, indent=2, indent_limit=8))
        return result_list


class CaseSeries(object):
    '''
    GTC parameter series cases.

    Attributes
    ----------
    paths: list of (realpath, saltstr) pairs for each case
        same order as input real paths *casepaths*
    cases: dict
        key is saltstr; value is gdpy3 processor for each case
    labelinfo: LabelInfoSeries instance
        label information of these cases
    chiDresults: dict, cache of :meth:`dig_chi_D`
        key is input parameters tuple of :meth:`dig_chi_D`
        value is :meth:`dig_chi_D` return
    '''

    def __init__(self, casepaths, skip_lost=True, labelinfo=None):
        '''
        Parameters
        ----------
        casepaths: list
            real cases paths of GTC parameter series
        skip_lost: bool
            skip these paths which have no 'gtc.out' or not(raise error)
        labelinfo: LabelInfoSeries instance
        '''
        self.paths = []
        self.cases = {}
        for path in casepaths:
            if not os.path.exists(os.path.join(path, 'gtc.out')):
                if skip_lost:
                    log.warning("Skip '%s'!" % path)
                    continue
                else:
                    raise IOError("Lost 'gtc.out' in '%s'!" % path)
            gdp = get_processor(path)
            key = gdp.saltstr
            self.paths.append((path, key))
            if key in self.cases:
                log.warning("key '%s' collision, path '%s'!" % (key, path))
            self.cases[key] = gdp
        if isinstance(labelinfo, LabelInfoSeries):
            self.labelinfo = labelinfo
        else:
            self.labelinfo = None
        self.chiDresults = {}
        self.plotter = get_visplter('mpl::series')
        self.plotter.style = ['gdpy3-paper-aip']

    def dig_chi_D(self, particle, gyroBohm=True, Ln=None,
                  fallback_sat_time=(0.7, 1.0)):
        '''
        Get particle chi and D of each case.
        Return a list of tuple in order of :attr:`paths`.
        The tuple has 6 elements: time t array, chi(t) array, D(t) array,
            saturation (start-time, end-time), saturation chi, saturation D.

        Parameters
        ----------
        particle: str
            ion, electron or fastion
        gyroBohm: bool
            use gyroBohm unit. rho0/Ln*(Bohm unit)
        Ln: float
            Set R0/Ln for gyroBohm unit. Ln=1.0/2.22 when R0/Ln=2.22
            If Ln=None, use a_minor as default Ln.
        fallback_sat_time: tuple
            If saturation time not found in :attr:`labelinfo`, use this
            to set saturation (start,end) time ratio. limit: 0.0 -> 1.0
        '''
        if particle in ('ion', 'electron', 'fastion'):
            figlabel = 'history/%s_flux' % particle
        else:
            raise ValueError('unsupported particle: %s ' % particle)
        cache_key = (particle, gyroBohm, Ln, tuple(fallback_sat_time))
        if cache_key in self.chiDresults:
            return self.chiDresults[cache_key]
        chiDresult = []
        for path, key in self.paths:
            gdp = self.cases[key]
            a, b, c = gdp.dig(figlabel, post=False)
            time = b['time']
            chi, D = b['energy'], b['particle']
            if gyroBohm:
                Ln = gdp.pckloader['gtc/a_minor'] if Ln is None else Ln
                rho0 = gdp.pckloader['gtc/rho0']
                chi, D = chi*Ln/rho0, D*Ln/rho0
            if self.labelinfo:
                start, end = self.labelinfo.get(key, stage='saturation')
                if start is not None:
                    start = np.where(time > start)[0][0]
                    end = np.where(time > end)[0]
                    end = end[0] if len(end) > 0 else len(time)
            else:
                start, end = fallback_sat_time
                start, end = int(len(time)*start), int(len(time)*end)
            sat_t = np.linspace(time[start], time[end-1], 2)
            chi_sat = np.mean(chi[start:end])
            # chi_sat_std = np.std(chi[start:end])
            D_sat = np.mean(D[start:end])
            chiDresult.append((time, chi, D, sat_t, chi_sat, D_sat))
        self.chiDresults[cache_key] = chiDresult
        return chiDresult

    def plot_chi_D(self, casepaths, particles=('ion', 'electron'),
                   fignum='fig1-1', add_style=[],
                   suptitle=None, title_y=0.95, savepath=None,
                   xlim=None, ylim1=None, ylim2=None, ylim3=None, ylim4=None):
        '''
        Plot chi, D figures of particle ion and electron.

        Parameters
        ----------
        casepaths: list
            selected cases paths from :attr:`paths`, selected cases to plot
        particles: tuple, particles to plot
        ylim1: ylim for chi_i
        ylim2: ylim for D_i
        ylim3: ylim for chi_e
        ylim4: ylim for D_e
        savepath: str
            default savepath is f'./{fignum}.jpg'
        '''
        xlim_kws = {'xlim': xlim} if xlim else {}
        ylim_kws = {
            k: {'ylim': v}
            for k, v in filter(lambda kw: kw[1] is not None, [
                ('ylim1', ylim1), ('ylim2', ylim2), ('ylim3', ylim3), ('ylim4', ylim4)])
        }
        Mrow = 2
        Ncol = len(particles)
        MN = Mrow*100 + Ncol*10
        all_axes = []
        axes_idx = 1
        if 'ion' in particles:
            chiDresult = self.dig_chi_D('ion')  # TODO
            axes_chii = {
                'layout': [MN+axes_idx, dict(ylabel=r'$\chi_i$', **xlim_kws, **ylim_kws.get('ylim1', {}))],
                'data': [
                    *[[1+i, 'plot', (*self.time_chii[key], '-'), dict(color="C{}".format(i), label=r'$%s, \chi_i=%.2f$' % (key, self.time_chii_sat[key][1][0]))]
                      for i, key in enumerate(parakeys)],
                    *[[30+i, 'plot', (*self.time_chii_sat[key], 'o'), dict(color="C{}".format(i))]
                      for i, key in enumerate(parakeys)],
                    [50, 'legend', (), {}],
                    [51, 'set_xticklabels', ([],), {}],
                ],
            }
            axes_idx += 1
            axes_Di = {
                'layout': [MN+axes_idx, dict(ylabel=r'$D_i$', **xlim_kws, **ylim_kws.get('ylim2', {}))],
                'data': [
                    *[[1+i, 'plot', (*self.time_Di[key], '-'), dict(color="C{}".format(i), label=r'$%s, D_i=%.2f$' % (key, self.time_Di_sat[key][1][0]))]
                      for i, key in enumerate(parakeys)],
                    *[[30+i, 'plot', (*self.time_Di_sat[key], 'o'), dict(color="C{}".format(i))]
                      for i, key in enumerate(parakeys)],
                    [50, 'legend', (), {}],
                    [51 if Ncol != 1 else -51, 'set_xticklabels', ([],), {}],
                    [-52 if Ncol != 1 else 52, 'set_xlabel',
                     (r'$t(R_0/c_s)$',), {}],
                ],
            }
            axes_idx += 1
            all_axes.extend([axes_chii, axes_Di])
        if 'electron' in particles:
            axes_chie = {
                'layout': [MN+axes_idx, dict(ylabel=r'$\chi_e$', **xlim_kws, **ylim_kws.get('ylim3', {}))],
                'data': [
                    *[[1+i, 'plot', (*self.time_chie[key], '-'), dict(color="C{}".format(i), label=r'$%s, \chi_e=%.2f$' % (key, self.time_chie_sat[key][1][0]))]
                      for i, key in enumerate(parakeys)],
                    *[[30+i, 'plot', (*self.time_chie_sat[key], 'o'), dict(color="C{}".format(i))]
                      for i, key in enumerate(parakeys)],
                    [50, 'legend', (), {}],
                    [51 if axes_idx == 1 else -51,
                        'set_xticklabels', ([],), {}],
                    [-52 if axes_idx == 1 else 52,
                     'set_xlabel', (r'$t(R_0/c_s)$',), {}],
                ],
            }
            axes_idx += 1
            axes_De = {
                'layout': [MN+axes_idx, dict(ylabel=r'$D_e$', **xlim_kws, **ylim_kws.get('ylim4', {}))],
                'data': [
                    *[[1+i, 'plot', (*self.time_De[key], '-'), dict(color="C{}".format(i), label=r'$%s, D_e=%.2f$' % (key, self.time_De_sat[key][1][0]))]
                      for i, key in enumerate(parakeys)],
                    *[[30+i, 'plot', (*self.time_De_sat[key], 'o'), dict(color="C{}".format(i))]
                      for i, key in enumerate(parakeys)],
                    [50, 'legend', (), {}],
                    [52, 'set_xlabel', (r'$t(R_0/c_s)$',), {}],
                ],
            }
            all_axes.extend([axes_chie, axes_De])
        fig = self.plotter.create_figure(
            fignum, *all_axes, add_style=[{
                'figure.figsize': (4, 6) if Ncol == 1 else (8, 6),
                # 'figure.autolayout': False,
                'figure.subplot.hspace': 0.02,
                'legend.handlelength': 2.0,
                # 'legend.fontsize': 8,
            }] + add_style)
        fig.suptitle(suptitle or fignum, y=title_y)
        fig.savefig(savepath or './%s.jpg' % fignum)
