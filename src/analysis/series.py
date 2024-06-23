# -*- coding: utf-8 -*-

# Copyright (c) 2023 shmilee

'''
Function, class to compare different cases.
'''

import os
import re
import time
import json
import math
import random
import itertools
import numpy as np
from ..loaders import get_rawloader
from ..processors import get_processor
from ..visplters import get_visplter
from .._json import dumps as json_dumps
from ..glogger import getGLogger
from .. import tools
from ..utils import simple_parse_numpydoc, inherit_docstring

__all__ = [
    'get_selected_converted_data', 'get_label_ts_data',
    'LabelInfoSeries', 'CaseSeries',
]
log = getGLogger('G.a')


def get_selected_converted_data(pathsmap, parallel='off',
                                printETA=None, printETAweights=None,
                                **kwargs):
    r'''
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
    printETA: function
        custom function to print ETA infor and process & converted file status
        The inputs are a list of time cost, a list of file size,
        and a dict of (i=, size=, sumsize=, ETA=).
    printETAweights: list
        weights for the list of time cost of cases
    kwargs: other parameters passed to :meth:`processors.get_processor`

    Notes
    -----
    1. Use :meth:`utils.GetPasswd.set` to set password of sftp.
    '''
    for k in list(kwargs.keys()):
        if k in ('path', 'parallel', 'filenames_exclude', 'savedir', 'Sid'):
            remove = kwargs.pop(k)
    if 'name' in kwargs:
        gdpcls = get_processor(name=kwargs.get('name'), parallel='off')
    else:
        gdpcls = get_processor(parallel='off')
    failed = []
    N = len(pathsmap)
    timecost = []
    filesize = []
    for i, pmap in enumerate(pathsmap, 1):
        try:
            print('', flush=True)
            print('-'*16, '%d/%d' % (i, N), '-'*16, flush=True)
            path, dest, exclude = pmap
            log.info('Raw data directory: %s' % path)
            done = False
            if os.path.exists(dest):
                test = get_rawloader(dest)
                tc = test.refind('%s-.*converted.*' % gdpcls.__name__.lower())
                if tc and test.refind(gdpcls.saltname):
                    log.warning('Skip path %s that has converted data!' % dest)
                    timecost.append(None)
                    filesize.append(os.path.getsize(
                        os.path.join(dest, tc[0])))
                    done = True
            if not done:
                log.info('Create directory: %s' % dest)
                os.makedirs(dest, exist_ok=True)
                start = time.time()
                gdp = get_processor(
                    path, parallel=parallel, filenames_exclude=exclude,
                    savedir=dest, Sid=True, **kwargs)
                todo = [gdp.saltname]
                todo.extend(gdp.rawloader.refind(r'gtc-\d+\.out'))
                todo.extend(gdp.rawloader.refind(r'gtc-input.*\.lua'))
                for file1 in todo:
                    file2 = os.path.join(dest, file1)
                    if os.path.exists(file2):
                        log.warning('Skip file: %s' % file2)
                        continue
                    log.info('Copy file: %s -> %s' % (file1, file2))
                    with gdp.rawloader.get(file1) as f1:
                        with open(file2, 'w') as f2:
                            f2.write(f1.read())
                end = time.time()
                timecost.append(end-start)
                filesize.append(os.path.getsize(gdp.pcksaver.path))
            ETA = 0
            size, sumsize = filesize[-1], sum(filesize)
            if printETAweights:
                val = np.array(tuple(filter(
                    lambda tw: tw[0], zip(timecost, printETAweights[:i]))))
                if len(val) > 0:
                    ETA = int(np.average(val[:, 0], weights=val[:, 1])*(N-i))
            else:
                val = tuple(filter(None, timecost))
                if len(val) > 0:
                    ETA = int(np.mean(val)*(N-i))
            print('-'*8, ' Done %d/%d, %.1fM/%.1fM, ETA=%ds'
                  % (i, N, size/1024/1024, sumsize/1024/1024, ETA),
                  '-'*8, flush=True)
            if printETA and callable(printETA):
                printETA(timecost, filesize, dict(
                    i=i, size=size, sumsize=sumsize, ETA=ETA))
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
        'v2' means 3 phi00 keys: time, phi00, phi00rms
    removeNaN: bool
        remove NaN Infinity, check array of chi_i etc., cut off by array index
    savepath: str, file path
        save results to savepath, then upload to your labeling platform
    savefmt: str, save format
        'ls-json' is saving to json for the Label Studio Platform
    '''
    ts_data_list = []

    def index_nan_inf(time, *arrs):
        idx = len(time)
        for arr in arrs:
            checkNaN = np.where(np.isnan(arr))[0]
            if checkNaN.size > 0:
                idx = min(checkNaN[0], idx)
            checkInf = np.where(np.isinf(arr))[0]
            if checkInf.size > 0:
                idx = min(checkInf[0], idx)
        return idx if idx < len(time) else None

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
                idx = index_nan_inf(time, chi, D, logphirms)
                if idx:
                    time = time[:idx]
                    chi, D = chi[:idx], D[:idx]
                    logphirms = logphirms[:idx]
            ts_data = dict(time=time, chi_i=chi, d_i=D, logphirms=logphirms)
        elif ts_key_ver == 'v2':
            a, b, c = gdp.dig('history/phi', post=False)
            time = b['time']
            phi00, phi00rms = b['field00'], b['field00rms']
            if removeNaN:
                idx = index_nan_inf(time, phi00, phi00rms)
                if idx:
                    time = time[:idx]
                    phi00, phi00rms = phi00[:idx], phi00rms[:idx]
            ts_data = dict(time=time, phi00=phi00, phi00rms=phi00rms)
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

    @classmethod
    def slim_ls_json(cls, jsonfile, savepath=None, result_modify=None):
        '''
        Parameters
        ----------
        jsonfile: str, path of Label Studio json results
        savepath: str, new path
        result_modify: function
            remove some data of each case.
            input: case result, return: slimmed result
            default: remove None, [], {}, 0; delete result[data][ts]
        '''
        if not (result_modify and callable(result_modify)):
            def result_modify(result):
                for k in list(result.keys()):
                    if result[k] in [None, [], {}, 0]:
                        result.pop(k)
                for k in ['file_upload', 'created_at', 'updated_at']:
                    if k in result:
                        result.pop(k)
                if 'annotations' in result:
                    for a in result['annotations']:
                        for k in list(a.keys()):
                            if a[k] in [None, [], {}, 0]:
                                a.pop(k)
                        for k in ['unique_id', 'created_at', 'updated_at']:
                            if k in a:
                                a.pop(k)
                if 'data' in result and 'ts' in result['data']:
                    result['data'].pop('ts')
                return result
        return cls.merge_ls_jsons(
            jsonfile, savepath=savepath, result_modify=result_modify)


def _parse_pltmrow_doc(doc, **kwargs):
    ''' for _plot_mrows_chi_D_like, _plot_mrows_gamma_phi_like '''
    XXX = kwargs.pop('XXX_like', None)
    if XXX:
        doc = doc.replace('{{XXX_like}}', XXX)
    return simple_parse_numpydoc(doc)


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
        self.plotter = get_visplter('mpl::series')
        self.plotter.style = ['gdpy3-paper-aip']

    def _get_start_end(self, path, key, stage, time=None, fallback=(0.7, 1.0)):
        ''' Return t0, t1, index0, index1 '''
        if time is None:
            ndstep, tstep, ndiag = self.cases[key].pckloader.get_many(
                'history/ndstep', 'gtc/tstep', 'gtc/ndiag')
            dt = tstep * ndiag
            time = np.around(np.arange(1, ndstep+1)*dt, 8)
        if self.labelinfo:
            start, end = self.labelinfo.get(key, stage=stage)
            if start is not None:
                log.info('Get %s time: %6.2f, %6.2f for %s'
                         % (stage, start, end, path))
                index = np.where((time >= start) & (time <= end))[0]
                if index.size > 0:
                    return start, end, index[0], index[-1]
        start, end = fallback
        log.info('Use fallback %s time ratio: %.3f, %.3f for %s'
                 % (stage, start, end, path))
        idx0, idx1 = int(len(time)*start) - 1, int(len(time)*end) - 1
        return time[idx0], time[idx1], idx0, idx1

    def dig_chi_D(self, particle, gyroBohm=True, Ln=None,
                  cutpsi=None, cutra=None,
                  fallback_sat_time=(0.7, 1.0)):
        '''
        Get particle chi(t) and D(t) of each case.
        Return a list of tuple in order of :attr:`paths`.
        The tuple has 6 elements:
            1) time t array, 2) chi(t) array, 3) D(t) array,
            4) saturation time (start-time, end-time),
            5) saturation chi, 6) saturation D.

        Parameters
        ----------
        particle: str
            ion, electron or fastion
        gyroBohm: bool
            use gyroBohm unit. rho0/Ln*(Bohm unit)
        Ln: float
            Set R0/Ln for gyroBohm unit. Ln=1.0/2.22 when R0/Ln=2.22
            If Ln=None, use a_minor as default Ln.
        cutpsi: tuple of int or float, like (ipsi0, ipsi1), (0.1, 0.9)mpsi
            use data1d and select the psi grids to calculate chi, D
            for example, cut off boundary grids
        cutra: tuple of float, like (0.3, 0.7)r/a
            same as cutpsi, use r/a instead of psi grids to cut data1d
        fallback_sat_time: tuple
            If saturation time not found in :attr:`labelinfo`, use this
            to set saturation (start,end) time ratio. limit: 0.0 -> 1.0
        '''
        if particle in ('ion', 'electron', 'fastion'):
            if cutpsi or cutra:
                figlabeld = 'data1d/%s_particle_flux' % particle
                figlabele = 'data1d/%s_energy_flux' % particle
            else:
                figlabel = 'history/%s_flux' % particle
        else:
            raise ValueError('unsupported particle: %s ' % particle)
        chiDresult = []
        for path, key in self.paths:
            gdp = self.cases[key]
            if cutpsi or cutra:
                rpsi = gdp.pckloader['gtc/sprpsi']
                a_minor = gdp.pckloader['gtc/a_minor']
                mpsi = gdp.pckloader['gtc/mpsi']
                rr = rpsi / a_minor  # [0, mpsi]
                if cutra:
                    idx = np.where((rr >= cutra[0]) & (rr <= cutra[1]))[0]
                    p0, p1 = idx[0], idx[-1]
                else:
                    if cutpsi[1] < 1.0:
                        p0, p1 = [int(p*mpsi) for p in cutpsi]
                    else:
                        p0, p1 = cutpsi
                    p0 = max(1, p0)
                    p1 = min(mpsi-1, p1)
                log.info("cut-psi: [%.2f, %.2f]%d=%s, cut-r/a: [%.2f, %.2f]"
                         % (p0/mpsi, p1/mpsi, mpsi, (p0, p1), rr[p0], rr[p1]))
                a, b, c = gdp.dig(figlabeld, pcutoff=(p0, p1), post=False)
                time, D = b['X'], b['Z'].mean(axis=0)
                a, b, c = gdp.dig(figlabele, pcutoff=(p0, p1), post=False)
                chi = b['Z'].mean(axis=0)
            else:
                a, b, c = gdp.dig(figlabel, post=False)
                time = b['time']
                chi, D = b['energy'], b['particle']
            if gyroBohm:
                Ln = gdp.pckloader['gtc/a_minor'] if Ln is None else Ln
                rho0 = gdp.pckloader['gtc/rho0']
                chi, D = chi*Ln/rho0, D*Ln/rho0
            _, _, start, end = self._get_start_end(
                path, key, 'saturation', time=time, fallback=fallback_sat_time)
            sat_t = np.linspace(time[start], time[end], 2)
            sat_chi = np.mean(chi[start:end+1])
            # sat_chi_std = np.std(chi[start:end])
            sat_D = np.mean(D[start:end+1])
            chiDresult.append((time, chi, D, sat_t, sat_chi, sat_D))
        return chiDresult

    def _plot_mrows_chi_D_like(
            self, xylabel1, xylabel2, datafun1, datafun2,
            result, labels, nlines, fignum, xlims={}, ylims={},
            suptitle=None, title_y=None, add_style=[], savepath=None):
        '''
        Plot 2 quantity data array by 2 columns.

        TO-Imp-Parameters
        -----------------
        xylabel1, xylabel2: dict(xlabel=x, ylabel=x) for Axes layout
            set xlabel, ylabel for quantities in column1 and column2
        datafun1, datafun2: function
            Input: partial result and labels for this Axes
            Return: Axes data list

        Parameters
        ----------
        result: list
            result get by :meth:`dig_{{XXX_like}}`
        labels: list
            set line labels for result
        nlines: int, >=2
            number of lines in each Axes
        fignum: str
            figure num/label
        xlims, ylims: dict, set xlim, ylim for some Axes
            key is axes index
        suptitle: str
        title_y: float
            suptitle y position, 0-1
        add_style: matplotlib style list
        savepath: str
            default savepath is f'./{fignum}.png'
        '''
        nlines = max(2, int(nlines))
        Mrow = math.ceil(len(result)/nlines)
        all_axes = []
        for row in range(1, Mrow+1, 1):
            ress = result[(row-1)*nlines:row*nlines]
            lbls = labels[(row-1)*nlines:row*nlines]
            for ax_idx, xylabel, datafun in zip(
                    [2*(row-1)+1, 2*(row-1)+2],
                    [xylabel1, xylabel2],
                    [datafun1, datafun2]):
                xlim, ylim = xlims.get(ax_idx, None), ylims.get(ax_idx, None)
                xylim_kws = {'xlim': xlim} if xlim else {}
                if ylim:
                    xylim_kws['ylim'] = ylim
                all_axes.append({
                    'layout': [(Mrow, 2, ax_idx), dict(
                        title='%d/%s' % (ax_idx, Mrow*2),
                        **xylabel, **xylim_kws)],
                    'data': [*datafun(ress, lbls), [900, 'legend', (), {}]],
                })
        fig = self.plotter.create_figure(
            fignum, *all_axes, add_style=add_style)
        fig.suptitle(suptitle or fignum, y=title_y)
        fig.savefig(savepath or ('./%s.png' % fignum))

    @inherit_docstring(_plot_mrows_chi_D_like, parse=_parse_pltmrow_doc,
                       parsekwargs=dict(XXX_like='chi_D'))
    def plot_chi_D(self, particle, result, labels, nlines=2,
                   fignum='1-chi-D', xlims={}, ylims={},
                   suptitle=None, title_y=None, add_style=[], savepath=None):
        '''
        Plot chi(t), D(t) figure of particle(like ion or electron).

        Parameters
        ----------
        {Parameters}
        '''
        if particle not in ('ion', 'electron', 'fastion'):
            raise ValueError('unsupported particle: %s ' % particle)
        ief = 'i' if 'ion' == particle else (
            'e' if 'electron' in particle else 'f')
        xylabel1 = {'xlabel': r'$t(R_0/c_s)$', 'ylabel': r'$\chi_%s$' % ief}
        xylabel2 = {'xlabel': r'$t(R_0/c_s)$', 'ylabel': r'$D_%s$' % ief}

        def datafun1(ress, lbls):
            return [[1+i, 'plot', (r[0], r[1], '-'), dict(
                    color="C{}".format(i), label=r'%s, $\chi_%s=%s$' % (
                        l, ief, tools.round_str(r[4], 2)))]
                    for i, (r, l) in enumerate(zip(ress, lbls))
                    ] + [[200+i, 'plot', (r[3], [r[4], r[4]], 'o'), dict(
                        color="C{}".format(i))] for i, r in enumerate(ress)]

        def datafun2(ress, lbls):
            return [[1+i, 'plot', (r[0], r[2], '-'), dict(
                color="C{}".format(i), label=r'%s, $D_%s=%s$' % (
                    l, ief, tools.round_str(r[5], 2)))]
                    for i, (r, l) in enumerate(zip(ress, lbls))
                    ] + [[200+i, 'plot', (r[3], [r[5], r[5]], 'o'), dict(
                        color="C{}".format(i))] for i, r in enumerate(ress)]
        self._plot_mrows_chi_D_like(
            xylabel1, xylabel2, datafun1, datafun2,
            result, labels, nlines, fignum, xlims=xlims, ylims=ylims,
            suptitle=suptitle, title_y=title_y, add_style=add_style,
            savepath=savepath)

    def dig_chi_D_r(self, particle, gyroBohm=True, Ln=None,
                    bgpsi=None, bgra=None,
                    fallback_sat_time=(0.7, 1.0), **kwargs):
        '''
        Get particle chi(r) and D(r) of each case.
        Return a list of tuple in order of :attr:`paths`.
        The tuple has 4 elements:
            1) radial r array, 2) chi(r) array, 3) D(r) array,
            4) annotation r tuples {(br0, br1), (r00, r11), ...}

        Parameters
        ----------
        particle: str
            ion, electron or fastion
        gyroBohm: bool
            use gyroBohm unit. rho0/Ln*(Bohm unit)
        Ln: float
            Set R0/Ln for gyroBohm unit. Ln=1.0/2.22 when R0/Ln=2.22
            If Ln=None, use a_minor as default Ln.
        bgpsi: tuple of int or float, like (ipsi0, ipsi1), (0.1, 0.9)mpsi
            annotate the boundary grids, or selected psi grids
        bgra: tuple of float, like (0.3, 0.7)r/a
            same as bgpsi, use r/a instead of psi grids
        fallback_sat_time: tuple
            If saturation time not found in :attr:`labelinfo`, use this
            to set saturation (start,end) time ratio. limit: 0.0 -> 1.0
        kwargs: dict
            other kwargs for digging 'data1d/xx_xx_flux_mean', such as
            'use_ra'(default False), 'mean_smooth'(default False)
        '''
        if particle in ('ion', 'electron', 'fastion'):
            figlabel = 'data1d/%s_%%s_flux_mean' % particle
        else:
            raise ValueError('unsupported particle: %s ' % particle)
        chiDresult = []
        if kwargs.pop('pcutoff', None):
            log.warning("Ignore 'pcutoff' kwargs!")
        usera = kwargs.get('use_ra', False)
        for path, key in self.paths:
            gdp = self.cases[key]
            a, b, c = gdp.dig('history/%s_flux' % particle, post=False)
            time = b['time']
            start, end, _, _ = self._get_start_end(
                path, key, 'saturation', time=time, fallback=fallback_sat_time)
            a, b1, c = gdp.dig(figlabel % 'energy', post=False,
                               mean_time=[start, end], **kwargs)
            chi, r = b1['meanZ'], b1['Y']
            a, b2, c = gdp.dig(figlabel % 'particle', post=False,
                               mean_time=[start, end], **kwargs)
            D = b2['meanZ']
            if gyroBohm:
                Ln = gdp.pckloader['gtc/a_minor'] if Ln is None else Ln
                rho0 = gdp.pckloader['gtc/rho0']
                chi, D = chi*Ln/rho0, D*Ln/rho0
            bgp0p1 = set()
            mpsi = gdp.pckloader.get('gtc/mpsi')
            if bgra:
                rpsi = gdp.pckloader['gtc/sprpsi']
                a_minor = gdp.pckloader['gtc/a_minor']
                rr = rpsi / a_minor  # [0, mpsi]
                if rr[0] <= bgra[0] and bgra[1] <= rr[-1]:
                    idx = np.where((rr >= bgra[0]) & (rr <= bgra[1]))[0]
                    if len(idx) > 1:
                        bgp0p1.add((idx[0], idx[-1]))
            if bgpsi:
                if bgpsi[1] < 1.0:
                    bgp0p1.add(tuple(int(p*mpsi) for p in bgpsi))
                else:
                    bgp0p1.add(tuple(int(p) for p in bgpsi))
            # p0,p1 -> r(ipsi or r/a)
            bgann = set((r[p0], r[p1]) for p0, p1 in bgp0p1)
            if bgann:
                log.debug("Get bg grids: %s" % bgann)
            chiDresult.append((r, chi, D, bgann))
        return chiDresult

    @inherit_docstring(_plot_mrows_chi_D_like, parse=_parse_pltmrow_doc,
                       parsekwargs=dict(XXX_like='chi_D_r'))
    def plot_chi_D_r(self, particle, result, labels, nlines=2,
                     fignum='1-chi-D(r)', xlims={}, ylims={}, add_style=[],
                     suptitle=None, title_y=None, savepath=None):
        '''
        Plot chi(r), D(r) figure of particle(like ion or electron).

        Parameters
        ----------
        {Parameters}
        '''
        if particle not in ('ion', 'electron', 'fastion'):
            raise ValueError('unsupported particle: %s ' % particle)
        ief = 'i' if 'ion' == particle else (
            'e' if 'electron' in particle else 'f')
        xylabel1 = {'xlabel': r'$r/a$', 'ylabel': r'$\chi_%s$' % ief}
        xylabel2 = {'xlabel': r'$r/a$', 'ylabel': r'$D_%s$' % ief}

        def get_datafun(idx):  # idx=1 for chi, 2 for D
            def datafun(ress, lbls):
                data = [
                    [1+i, 'plot', (r[0], r[idx], '-'), dict(
                        color="C{}".format(i), label=l)]
                    for i, (r, l) in enumerate(zip(ress, lbls))
                ]
                ls = itertools.cycle(['--', '-.', ':'])
                bgannotate = set()  # same bgann, just plot one in this axes
                for i, r in enumerate(ress):
                    for j, r0r1 in enumerate(r[3]):
                        if r0r1 not in bgannotate:
                            bgannotate.add(r0r1)
                            data.append([
                                100+10*i+j, 'axvspan', r0r1, dict(
                                    color="C{}".format(i+j),
                                    ls=next(ls), lw=1.0, fill=False)])
                return data
            return datafun
        self._plot_mrows_chi_D_like(
            xylabel1, xylabel2, get_datafun(1), get_datafun(2),
            result, labels, nlines, fignum, xlims=xlims, ylims=ylims,
            suptitle=suptitle, title_y=title_y, add_style=add_style,
            savepath=savepath)

    def dig_gamma_phi(self, R0Ln=None, fallback_growth_time='auto'):
        '''
        Get phi-RMS linear growth rate of each case.
        Return a list of tuple in order of :attr:`paths`.
        The tuple has 5 elements:
            1) time t array, 2) log(phirms)(t) array,
            3) linear growth time (start-time t0, end-time t1),
            4) associated log(phirms) (log(phirms)(t0), log(phirms)(t1)),
            5) linear growth rate.

        Parameters
        ----------
        R0Ln: float
            Set R0/Ln for normlization, use Cs/Ln as unit.
            If R0Ln=None, use Cs/R0.
        fallback_growth_time: tuple of float, or 'auto'
            If linear growth time not found in :attr:`labelinfo`, use this
            to set growth (start,end) time ratio. limit: 0.0 -> 1.0
            'auto', use :func:`tools.findgrowth` to find growth time
        '''
        gammaresult = []
        removeNaN = True
        for path, key in self.paths:
            gdp = self.cases[key]
            a, b, c = gdp.dig('history/phi', post=False)
            time = b['time']
            logphirms = np.log(b['fieldrms'])
            if removeNaN:
                idx = len(time)
                checkNaN = np.where(np.isnan(logphirms))[0]
                if checkNaN.size > 0:
                    idx = min(checkNaN[0], idx)
                if idx < len(time):
                    time = time[:idx]
                    logphirms = logphirms[:idx]
            start, end = None, None
            if self.labelinfo:
                start, end = self.labelinfo.get(key, stage='linear')
            if start is not None:
                log.info('Get growth time: %6.2f, %6.2f for %s'
                         % (start, end, path))
                start = np.where(time > start)[0][0]
                end = np.where(time > end)[0]
                end = end[0] if len(end) > 0 else len(time)
            else:
                if fallback_growth_time == 'auto':
                    start, region_len = tools.findgrowth(logphirms, 1e-4)
                    if region_len == 0:
                        start, region_len = 0, max(len(time) // 4, 2)
                    end = start + region_len
                    log.info(
                        "Find growth time: [%s,%s], index: [%s,%s], for %s"
                        % (time[start], time[end-1], start, end-1, path))
                else:
                    start, end = fallback_growth_time
                    log.info(
                        'Use fallback growth time ratio: %.1f, %.1f for %s'
                        % (start, end, path))
                    start, end = int(len(time)*start), int(len(time)*end)
            growth_time = np.linspace(time[start], time[end-1], 2)
            growth_logphi = np.linspace(logphirms[start], logphirms[end-1], 2)
            # polyfit growth line
            resparm, fitya = tools.line_fit(
                time[start:end], logphirms[start:end], 1,
                info='%s growth rate' % path)
            growth = resparm[0][0]
            log.info("Get growth rate: %.6f for %s" % (growth, path))
            gammaresult.append((
                time, logphirms, growth_time, growth_logphi, growth))
        return gammaresult

    @inherit_docstring(_plot_mrows_chi_D_like, parse=_parse_pltmrow_doc)
    def _plot_mrows_gamma_phi_like(
            self, xylabel, datafun,
            result, labels, nlines, ncols, fignum, xlims={}, ylims={},
            suptitle=None, title_y=None, add_style=[], savepath=None):
        '''
        Plot one quantity data array by any columns.

        TO-Imp-Parameters
        -----------------
        xylabel: dict(xlabel=x, ylabel=x) for Axes layout
            set xlabel, ylabel for the quantity
        datafun: function
            Input: partial result and labels for this Axes
            Return: Axes data list

        Parameters
        ----------
        {Parameters}
        ncols: int, >=1
            number of columns in this figure
        '''
        nlines, ncols = max(2, int(nlines)), max(1, int(ncols))
        Mrow = math.ceil(len(result)/nlines/ncols)
        all_axes = []
        for row in range(1, Mrow+1, 1):
            for col in range(1, ncols+1, 1):
                ax_idx = ncols*(row-1) + col  # ax, 1, 2, ...
                ress = result[(ax_idx-1)*nlines:ax_idx*nlines]
                lbls = labels[(ax_idx-1)*nlines:ax_idx*nlines]
                xlim, ylim = xlims.get(ax_idx, None), ylims.get(ax_idx, None)
                xylim_kws = {'xlim': xlim} if xlim else {}
                if ylim:
                    xylim_kws['ylim'] = ylim
                all_axes.append({
                    'layout': [
                        (Mrow, ncols, ax_idx), dict(
                            title='%d/%s' % (ax_idx, Mrow*ncols),
                            **xylabel, **xylim_kws)],
                    'data': [*datafun(ress, lbls), [900, 'legend', (), {}]],
                })
        fig = self.plotter.create_figure(
            fignum, *all_axes, add_style=add_style)
        fig.suptitle(suptitle or fignum, y=title_y)
        fig.savefig(savepath or ('./%s.png' % fignum))

    @inherit_docstring(_plot_mrows_gamma_phi_like, parse=_parse_pltmrow_doc,
                       parsekwargs=dict(XXX_like='gamma_phi'))
    def plot_gamma_phi(self, result, labels, nlines=2, ncols=1,
                       fignum='1-phi', xlims={}, ylims={}, add_style=[],
                       suptitle=None, title_y=None, savepath=None):
        '''
        Plot figure of phi-RMS and its growth range.

        Parameters
        ----------
        {Parameters}
        '''
        xylabel = dict(xlabel=r'$t(R_0/c_s)$', ylabel=r'$log(\phi_{RMS})$')

        def datafun(ress, lbls):
            return [[1+i, 'plot', (r[0], r[1], '-'), dict(
                color="C{}".format(i),
                label=r'%s, $\gamma_{\phi}=%.2f$' % (l, r[4]))]
                for i, (r, l) in enumerate(zip(ress, lbls))
            ] + [[200+i, 'plot', (r[2], r[3], 'o'), dict(
                color="C{}".format(i))] for i, r in enumerate(ress)]
        self._plot_mrows_gamma_phi_like(
            xylabel, datafun, result, labels, nlines, ncols, fignum,
            xlims=xlims, ylims=ylims, suptitle=suptitle, title_y=title_y,
            add_style=add_style, savepath=savepath)

    def dig_phirms_r(self, fallback_sat_time=(0.7, 1.0), **kwargs):
        '''
        Get phi-RMS(r) of each case.
        Return a list of tuple in order of :attr:`paths`.
        The tuple has 2 elements:
            1) radial r array, 2) phi-RMS(r) array

        Parameters
        ----------
        fallback_sat_time: tuple
            If saturation time not found in :attr:`labelinfo`, use this
            to set saturation (start,end) time ratio. limit: 0.0 -> 1.0
        kwargs: dict
            other kwargs for digging 'data1d/phi_rms_mean', such as
            'use_ra'(default False), 'mean_smooth'(default False)
        '''
        figlabel = 'data1d/phi_rms_mean'
        phiresult = []
        for path, key in self.paths:
            gdp = self.cases[key]
            start, end, _, _ = self._get_start_end(
                path, key, 'saturation', fallback=fallback_sat_time)
            a, b, c = gdp.dig(figlabel, post=False,
                              mean_time=[start, end], **kwargs)
            phirms, r = b['meanZ'], b['Y']
            phiresult.append((r, phirms))
        return phiresult

    @inherit_docstring(_plot_mrows_gamma_phi_like, parse=_parse_pltmrow_doc,
                       parsekwargs=dict(XXX_like='phirms_r'))
    def plot_phirms_r(self, result, labels, nlines=2, ncols=1,
                      fignum='1-phirms(r)', xlims={}, ylims={}, add_style=[],
                      suptitle=None, title_y=None, savepath=None):
        '''
        Plot phi-RMS(r) figure.

        Parameters
        ----------
        {Parameters}
        '''
        xylabel = dict(xlabel=r'$r/a$', ylabel=r'$\phi_{RMS}$')

        def datafun(ress, lbls):
            return [[1+i, 'plot', (r[0], r[1], '-'), dict(
                color="C{}".format(i), label=l)]
                for i, (r, l) in enumerate(zip(ress, lbls))]
        self._plot_mrows_gamma_phi_like(
            xylabel, datafun, result, labels, nlines, ncols, fignum,
            xlims=xlims, ylims=ylims, suptitle=suptitle, title_y=title_y,
            add_style=add_style, savepath=savepath)

    def dig_phiktheta_r(self, stage='saturation', fallback_time=(0.7, 1.0),
                        **kwargs):
        '''
        Get phi-ktheta(r) in xxx stage time of each case. Need snapshots!
        Return a list of tuple in order of :attr:`paths`.
        The tuple has 2 elements:
            1) radial r array, 2) ktheta-rho0(r) array

        Parameters
        ----------
        stage: str
            linear, nonlinear, or saturation(default)
        fallback_time: tuple
            If xxx stage time not found in :attr:`labelinfo`, use this
            to set (start,end) time ratio. limit: 0.0 -> 1.0
        kwargs: dict
            other kwargs for digging 'snapxxxxx/phi_mktheta', such as
            'm_max'(default mtheta//5), 'mean_weight_order'(default 2)
        '''
        result = []
        for path, key in self.paths:
            gdp = self.cases[key]
            start, end, _, _ = self._get_start_end(
                path, key, stage, fallback=fallback_time)
            step = [int(fl[4:9]) for fl in gdp.refind('snap.*/phi_m')]
            tstep = gdp.pckloader['gtc/tstep']
            time = np.array([round(i*tstep, 3) for i in step])
            index = np.where((time >= start) & (time <= end))[0]
            if index.size > 0:
                idx0, idx1 = index[0], index[-1]
            else:
                log.error('No snap time: %s <= t <= %s!' % (start, end))
                result.append(([], []))
                continue
            ktrho0_rt = []
            for i in step[idx0:idx1]:
                a, data, c = gdp.dig(
                    'snap%05d/phi_mktheta' % i, post=False, **kwargs)
                ktrho0_rt.append(data['ktrho0'])
            ktrho0_rt = np.array(ktrho0_rt).T
            r = data['rr']
            ktheta_r = np.average(ktrho0_rt, axis=1)
            result.append((r, ktheta_r))
        return result

    @inherit_docstring(_plot_mrows_gamma_phi_like, parse=_parse_pltmrow_doc,
                       parsekwargs=dict(XXX_like='phiktheta_r'))
    def plot_phiktheta_r(self, result, labels, nlines=2, ncols=1,
                         fignum='1-phiktheta(r)', xlims={}, ylims={},
                         suptitle=None, title_y=None,
                         add_style=[], savepath=None):
        '''
        Plot phi-ktheta(r) figure.

        Parameters
        ----------
        {Parameters}
        '''
        xylabel = dict(xlabel=r'$r/a$',
                       ylabel=r'$k_{\theta}\rho_0$')

        def datafun(ress, lbls):
            return [[1+i, 'plot', (r[0], r[1], '-'), dict(
                color="C{}".format(i), label=l)]
                for i, (r, l) in enumerate(zip(ress, lbls))]
        self._plot_mrows_gamma_phi_like(
            xylabel, datafun, result, labels, nlines, ncols, fignum,
            xlims=xlims, ylims=ylims, suptitle=suptitle, title_y=title_y,
            add_style=add_style, savepath=savepath)

    def dig_phi_spectrum(self, stage='saturation', fallback_time=(0.7, 1.0),
                         **kwargs):
        '''
        Get phi-spectrum in xxx stage time of each case. Need snapshots!
        Return a list of tuple in order of :attr:`paths`.
        The tuple has 5 elements:
            1) omega array, 2) power array, 3) Lorentzian fitting array,
            4) fitting omega-r, 5) fitting gamma

        Parameters
        ----------
        stage: str
            linear, nonlinear, or saturation(default)
        fallback_time: tuple
            If xxx stage time not found in :attr:`labelinfo`, use this
            to set (start,end) time ratio. limit: 0.0 -> 1.0
        kwargs: dict
            other kwargs for digging 'snap/phi_poloi_time_fft', such as
            'ipsi'(default mpsi//2), 'nearby'(default 1),
            'fit_wlimit'(default 0,0)
        '''
        result = []
        for path, key in self.paths:
            gdp = self.cases[key]
            figlabel = 'snap/phi_poloi_time_fft'
            if figlabel not in gdp.availablelabels:
                continue
            start, end, _, _ = self._get_start_end(
                path, key, stage, fallback=fallback_time)
            a, b, c = gdp.dig(figlabel, fft_tselect=(start, end),
                              post=False, **kwargs)
            result.append((b['tf'], b['Pomega'], b['fitPomega'],
                           b['Cauchy_mu1'], b['Cauchy_gamma1']))
        return result

    @inherit_docstring(_plot_mrows_gamma_phi_like, parse=_parse_pltmrow_doc,
                       parsekwargs=dict(XXX_like='phi_spectrum'))
    def plot_phi_spectrum(self, result, labels, nlines=2, ncols=1,
                          fignum='1-phiomega', xlims={}, ylims={},
                          suptitle=None, title_y=None,
                          add_style=[], savepath=None):
        '''
        Plot phi-spectrum figure.

        Parameters
        ----------
        {Parameters}
        '''
        xylabel = dict(xlabel=r'$\omega(c_s/R_0)$', ylabel=r'power')

        def datafun(ress, lbls):
            return [[1+i, 'plot', (r[0], r[1], '-'), dict(
                color="C{}".format(i),
                label=r'%s, $\omega_{rn}=%.4f, \gamma_n=%.4f$'
                % (l, r[3], r[4]))]
                for i, (r, l) in enumerate(zip(ress, lbls))
            ] + [[200+i, 'plot', (r[0], r[2], '--'), dict(
                color="C{}".format(i))] for i, r in enumerate(ress)]
        self._plot_mrows_gamma_phi_like(
            xylabel, datafun, result, labels, nlines, ncols, fignum,
            xlims=xlims, ylims=ylims, suptitle=suptitle, title_y=title_y,
            add_style=add_style, savepath=savepath)

    def dig_phi_spectrum_r(self, stage='saturation', select_psi=None,
                           fallback_time=(0.7, 1.0), **kwargs):
        '''
        Get phi-spectrum(r) in xxx stage time of each case. Need snapshots!
        Return a list of tuple in order of :attr:`paths`.
        The tuple has 3 elements:
            1) radial r array, 2) Lorentzian fitting omega-real array,
            3) fitting gamma array

        Parameters
        ----------
        stage: str
            linear, nonlinear, or saturation(default)
        select_psi: list of int
            only select some 'ipsi' for digging 'snap/phi_poloi_time_fft'
            default None -> range(nearby*2, mpsi-nearby, nearby)
        fallback_time: tuple
            If xxx stage time not found in :attr:`labelinfo`, use this
            to set (start,end) time ratio. limit: 0.0 -> 1.0
        kwargs: dict
            other kwargs for digging 'snap/phi_poloi_time_fft', such as
            'nearby'(default 5), 'fit_wlimit'(default 0,0)
        '''
        result = []
        nearby = kwargs.pop('nearby', 1)
        for path, key in self.paths:
            gdp = self.cases[key]
            figlabel = 'snap/phi_poloi_time_fft'
            if figlabel not in gdp.availablelabels:
                continue
            start, end, _, _ = self._get_start_end(
                path, key, stage, fallback=fallback_time)
            rpsi, a_minor, mpsi = gdp.pckloader.get_many(
                'gtc/sprpsi', 'gtc/a_minor', 'gtc/mpsi')
            ra = rpsi / a_minor  # [0, mpsi]
            r, wr, gamma = [], [], []
            if select_psi is None:
                select_psi = range(nearby*2, mpsi-nearby, nearby)
            for ipsi in select_psi:
                a, b, c = gdp.dig(figlabel,
                                  fft_tselect=(start, end),
                                  ipsi=ipsi, nearby=nearby,
                                  post=False, **kwargs)
                r.append(ra[ipsi])
                wr.append(b['Cauchy_mu1'])
                gamma.append(b['Cauchy_gamma1'])
            result.append((np.array(r), np.array(wr), np.array(gamma)))
        return result

    @inherit_docstring(_plot_mrows_chi_D_like, parse=_parse_pltmrow_doc,
                       parsekwargs=dict(XXX_like='phi_spectrum_r'))
    def plot_phi_spectrum_r(self, result, labels, nlines=2,
                            fignum='1-phiomega(r)', xlims={}, ylims={},
                            suptitle=None, title_y=None, add_style=[],
                            savepath=None):
        '''
        Plot phi-spectrum(r) figure.

        Parameters
        ----------
        {Parameters}
        '''
        xylabel1 = {'xlabel': r'$r/a$', 'ylabel': r'$\omega_r(c_s/R_0)$'}
        xylabel2 = {'xlabel': r'$r/a$', 'ylabel': r'$\gamma(c_s/R_0)$'}

        def datafun1(ress, lbls):
            return [[1+i, 'plot', (r[0], r[1], '-'), dict(
                color="C{}".format(i), label=l)]
                for i, (r, l) in enumerate(zip(ress, lbls))]

        def datafun2(ress, lbls):
            return [[1+i, 'plot', (r[0], r[2], '-'), dict(
                color="C{}".format(i), label=l)]
                for i, (r, l) in enumerate(zip(ress, lbls))]
        self._plot_mrows_chi_D_like(
            xylabel1, xylabel2, datafun1, datafun2,
            result, labels, nlines, fignum, xlims=xlims, ylims=ylims,
            suptitle=suptitle, title_y=title_y, add_style=add_style,
            savepath=savepath)

    def dig_phi_kparallel(self, ipsi=None, time_sample=0,
                          fallback_sat_time=(0.7, 1.0), **kwargs):
        '''
        Get phi-kparallel(t) of each case. Need snapshots or flux3d!
        Return a list of tuple in order of :attr:`paths`.
        The tuple has 5 elements:
            1) time t array, 2) average kparallel array,
            3) fitting kparallel-gamma array,
            4) saturation time (start-time, end-time),
            5) time averaged kparallel in saturation stage,
            6) time averaged fitting kparallel-gamma in saturation stage

        Parameters
        ----------
        ipsi: int
            select flux surfece at 'ipsi', default None -> mpsi//2
        time_sample: int
            select N random time points, <=0: select all. default 0
        fallback_sat_time: tuple
            If saturation stage not found in :attr:`labelinfo`, use this
            to set (start,end) time ratio. limit: 0.0 -> 1.0
        kwargs: dict
            other kwargs for digging 'snapxxxxx/phi_fluxa_tile_fft', such as
            'N'(default 3), 'fft_mean_kzlimit'(default [0, mtoroidal/2]),
            'fft_mean_order'(default 2).
        '''
        result = []
        for path, key in self.paths:
            gdp = self.cases[key]
            mpsi = gdp.pckloader['gtc/mpsi']
            ipsi = mpsi//2 if ipsi is None else ipsi
            figlabel = None
            if ipsi == mpsi//2:  # try snapshot first
                step = [int(k[4:9]) for k in gdp.refind('snap.*/phi_fluxa$')]
                if step:
                    figlabel = 'snap%05d/phi_fluxa_tile_fft'
            if figlabel is None:  # fallback flux3d
                step = [int(k[6:11]) for k in gdp.refind(
                    'flux3d.*/phi_%03da$' % ipsi)]
                if step:
                    figlabel = 'flux3d%%05d/phi_%03da_tile_fft' % ipsi
            if figlabel is None:
                log.error('No snap(or 3d) fluxdata for ipsi=%s!' % ipsi)
                result.append(([], []))
                continue
            if time_sample > 0 and len(step) > time_sample:
                log.info('Select %s of %s random time points!'
                         % (time_sample, len(step)))
                step = sorted(random.sample(step, time_sample))
            start, end, _, _ = self._get_start_end(
                path, key, 'saturation', fallback=fallback_sat_time)
            tstep = gdp.pckloader['gtc/tstep']
            time = np.array([round(i*tstep, 3) for i in step])
            index = np.where((time >= start) & (time <= end))[0]
            if index.size > 0:
                idx0, idx1 = index[0], index[-1]
            else:
                log.error('No snap(or 3d): %s <= time <= %s!' % (start, end))
                idx0, idx1 = 0, time.size-1
            sat_t = np.linspace(time[idx0], time[idx1], 2)
            meank, fitkgamma = [], []  # for average k//, k//-fitgamma
            for i in step:
                a, b, c = gdp.dig(figlabel % i, post=False, **kwargs)
                meank.append(b['mean_kpara'])
                fitkgamma.append(b['Cauchy_gamma1'])
            meank, fitkgamma = np.array(meank), np.array(fitkgamma)
            result.append((time, meank, fitkgamma, sat_t,
                           np.mean(meank[idx0:idx1+1]),
                           np.mean(fitkgamma[idx0:idx1+1])))
        return result

    @inherit_docstring(_plot_mrows_chi_D_like, parse=_parse_pltmrow_doc,
                       parsekwargs=dict(XXX_like='phi_kparallel'))
    def plot_phi_kparallel(self, result, labels, nlines=2,
                           fignum='1-kparallel', xlims={}, ylims={},
                           suptitle=None, title_y=None, add_style=[],
                           savepath=None):
        '''
        Plot phi-kparallel(t) figure.

        Parameters
        ----------
        {Parameters}
        '''
        xylabel1 = {'xlabel': r'$t(R_0/c_s)$',
                    'ylabel': r'$\langle k_{\parallel}R_0\rangle$'}
        xylabel2 = {'xlabel': r'$t(R_0/c_s)$',
                    'ylabel': r'$k_{\parallel}R_0$, half width'}

        def datafun1(ress, lbls):
            return [[1+i, 'plot', (r[0], r[1], '-'), dict(
                color="C{}".format(i),
                label=r'%s, saturation=%.2f' % (l, r[4]))]
                for i, (r, l) in enumerate(zip(ress, lbls))
            ] + [[200+i, 'plot', (r[3], [r[4], r[4]], 'o'), dict(
                color="C{}".format(i))]
                for i, r in enumerate(ress)]

        def datafun2(ress, lbls):
            return [[1+i, 'plot', (r[0], r[2], '-'), dict(
                color="C{}".format(i),
                label=r'%s, saturation=%.2f' % (l, r[5]))]
                for i, (r, l) in enumerate(zip(ress, lbls))
            ] + [[200+i, 'plot', (r[3], [r[5], r[5]], 'o'), dict(
                color="C{}".format(i))] for i, r in enumerate(ress)]
        self._plot_mrows_chi_D_like(
            xylabel1, xylabel2, datafun1, datafun2,
            result, labels, nlines, fignum, xlims=xlims, ylims=ylims,
            suptitle=suptitle, title_y=title_y, add_style=add_style,
            savepath=savepath)

    def dig_phi00(self, residual=False, norm=False,
                  fallback_sat_time='auto', fallback_auto_limit=5e-4,
                  **kwargs):
        '''
        Get phi00rms(t) and phi00(t) of each case.
        Return a list of tuple in order of :attr:`paths`.
        The tuple has 6 elements:
            1) (time, phi00rms(t) array), 2) (time, phi00(t) array),
            3) saturation time (start-time, end-time),
            4) saturation phi00rms, 5) saturation phi00,
            6) residual info {krrho0, max, smooth residual level, level rmse}.

        Parameters
        ----------
        residual: bool
            Use phi00 from 'history/residual_zf' phi00(r,t)
            and return more residual level info. default False
        norm: bool
            normalize phi00rms, phi00 by the maximum or not, default False
        fallback_sat_time: tuple of float, or 'auto'
            If saturation time not found in :attr:`labelinfo`, use this
            to set saturation (start,end) time ratio. limit: 0.0 -> 1.0.
            'auto', use :func:`tools.findflat` with normalized phi00rms(t)
            to find saturation time
        fallback_auto_limit: float or function
            set upperlimit for :func:`tools.findflat`, default 5e-4
            float: upperlimit=fallback_auto_limit*1.0
            function: upperlimit=fallback_auto_limit(path, normalized-phi00rms)
        kwargs: dict
            other kwargs for digging 'history/residual_zf', such as
            'ipsi'(default mpsi//2), 'nside'(default 1)
        '''
        result = []
        _ = kwargs.pop('res_time', None)
        kwargs.update(post=False, use_ra=True, p00rms=False, norm=norm)
        for path, key in self.paths:
            gdp = self.cases[key]
            # history phi00rms
            a, b1, c = gdp.dig('history/phi', post=False)
            time1, phi00rms = b1['time'], b1['field00rms']
            argmax = phi00rms.argmax()
            if norm:
                phi00rms = phi00rms/phi00rms[argmax]
            fallback_time = fallback_sat_time
            if fallback_sat_time == 'auto':
                normrms = phi00rms if norm else phi00rms/phi00rms[argmax]
                if callable(fallback_auto_limit):
                    upperlimit = fallback_auto_limit(path, normrms)
                else:
                    upperlimit = fallback_auto_limit*1.0
                start, length = tools.findflat(normrms[argmax:], upperlimit)
                if length == 0:
                    start = (6*len(time1)+4*argmax)//10
                    end = (9*len(time1)+argmax)//10
                else:
                    start += argmax
                    end = start + length
                fallback_time = start/len(time1), min(1.0, end/len(time1))
                log.info(
                    "Auto-fallback-time: [%s,%s], ratio: [%.3f,%.3f], for %s"
                    % (time1[start], time1[end-1], *fallback_time, path))
            t0, t1, start, end = self._get_start_end(
                path, key, 'saturation', time=time1, fallback=fallback_time)
            sat_time = (t0, t1)
            sat_phi00rms = phi00rms[start:end].mean()
            # rzf?
            figlabel = 'history/residual_zf'
            if residual and figlabel in gdp.availablelabels:
                a, b2, c = gdp.dig(figlabel, res_time=sat_time, **kwargs)
                time2, phi00 = b2['time'], b2['s1dzf']
                sat_phi00 = b2['s1dres']
                residual_info = {_k: b2[k] for k, _k in zip(
                    ['krrho0', 'ipsi', 'ir', 's1dresflt', 'Yd1dresrmse'],
                    ['krrho0', 'ipsi', 'ir', 'rzf', 'rmse'])}  # if k in b2}
            else:
                time2, phi00, residual_info = time1, b1['field00'], {}
                if norm:
                    phi00 = phi00/phi00.max()
                sat_phi00 = phi00[start:end].mean()
            residual_info['absmaxphi00'] = phi00[abs(phi00).argmax()]
            result.append(((time1, phi00rms), (time2, phi00),
                           sat_time, sat_phi00rms, sat_phi00, residual_info))
        return result

    @inherit_docstring(_plot_mrows_chi_D_like, parse=_parse_pltmrow_doc,
                       parsekwargs=dict(XXX_like='phi00'))
    def plot_phi00(self, result, labels, nlines=2,
                   fignum='1-phi00', xlims={}, ylims={},
                   suptitle=None, title_y=None, add_style=[], savepath=None):
        '''
        Plot phi00rms(t), phi00(t) figure.

        Parameters
        ----------
        {Parameters}
        '''
        xylabel1 = {'xlabel': r'$t(R_0/c_s)$', 'ylabel': r'$\phi_{00}RMS$'}
        xylabel2 = {'xlabel': r'$t(R_0/c_s)$', 'ylabel': r'$\phi_{00}$'}

        def residual_info(res):
            info = r'\phi_{00}=%s' % tools.round_str(res[4], 2)
            if 'rmse' in res[5]:
                info += r', R_{ZF}(r=%.1fa)=%s\pm%s' % (
                    res[5]['ir'],
                    tools.round_str(res[5]['rzf'], 2),
                    tools.round_str(res[5]['rmse'], 2))
            return r'$%s$' % info

        def datafun1(ress, lbls):
            return [[1+i, 'plot', r[0], dict(
                color="C{}".format(i), linestyle='-',
                label=r'%s, $\phi_{00}RMS=%s$' % (
                    l, tools.round_str(r[3], 2)))]
                    for i, (r, l) in enumerate(zip(ress, lbls))
                    ] + [[200+i, 'plot', (r[2], [r[3], r[3]], 'o'), dict(
                        color="C{}".format(i))] for i, r in enumerate(ress)]

        def datafun2(ress, lbls):
            return [[1+i, 'plot', r[1], dict(
                color="C{}".format(i), ls='-',
                label=r'%s, %s' % (l, residual_info(r)))]
                for i, (r, l) in enumerate(zip(ress, lbls))
            ] + [[200+i, 'plot', (r[2], [r[4], r[4]], 'o'), dict(
                color="C{}".format(i))] for i, r in enumerate(ress)]
        self._plot_mrows_chi_D_like(
            xylabel1, xylabel2, datafun1, datafun2,
            result, labels, nlines, fignum, xlims=xlims, ylims=ylims,
            suptitle=suptitle, title_y=title_y, add_style=add_style,
            savepath=savepath)
