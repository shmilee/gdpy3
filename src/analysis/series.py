# -*- coding: utf-8 -*-

# Copyright (c) 2023 shmilee

'''
Function, class to compare different cases.
'''

import os
import json
import numpy as np
from ..processors import get_processor
from .._json import dumps as json_dumps
from ..glogger import getGLogger

__all__ = ['get_label_ts_data', 'LabelInfoSeries']
log = getGLogger('G.a')


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
        change path in results for each case
    name_replace: function
        change name in results for each case, default: basename of its path
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
        name = os.path.basename(os.path.realpath(path))
        if name_replace and callable(name_replace):
            name = name_replace(name)
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
            dict(path=path, name=name, label=label) for each case,
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
    def merge_ls_jsons(*jsonfiles, savepath=None):
        ''' jsonfiles: path of Label Studio json results '''
        ls_ts_list = []
        i = 1
        for file in jsonfiles:
            with open(file, 'r') as f1:
                reslist = json.loads(f1.read())
            ls_ts_list.extend([
                dict(id=i, data=data)
                for i, data in enumerate(reslist, i)
            ])
            i += len(reslist)
        if savepath:
            with open(savepath, 'w') as f2:
                f2.write(json_dumps(ls_ts_list, indent=2, indent_limit=8))
        else:
            return ls_ts_list


class CaseSeries(obejct):
    '''
    GTC parameter series cases.

    Attributes
    ----------
    paths: list of (realpath, key) pairs for each case
        same order as input real paths *casepaths*
    cases: dict
        key is path, name or saltstr; value is gdpy3 processor for each case
    labelinfo: LabelInfoSeries instance
        label information of these cases
    '''

    def __init__(self, casepaths, key_type='saltstr', key_replace=None,
                 skip_lost=True, labelinfo=None):
        '''
        Parameters
        ----------
        casepaths: list
            real cases paths of GTC parameter series
        key_type: str
            use name, path or saltstr(default) as key for :attr:`cases`
        key_replace: function
            change key string for :attr:`cases`, when key_type is name or path
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
            if key_type in ('name', 'path'):
                if key_type == 'name':
                    key = os.path.basename(os.path.realpath(path))
                else:
                    key = path
                if key_replace and callable(key_replace):
                    key = key_replace(key)
            else:
                key = gdp.saltstr
            self.paths.append((path, key))
            if key in self.cases:
                log.warning("key '%s' collision, path '%s'!" % (key, path))
            self.cases[key] = gdp
        if isinstance(labelinfo, LabelInfoSeries):
            self.labelinfo = labelinfo
        else:
            self.labelinfo = None

    def dig_chi_D(self, particle, gyroBohm=True, Ln=None):
        '''
        Get chi and D of particle.

        Parameters
        ----------
        particle: str
            ion, electron or fastion
        gyroBohm: bool
            use gyroBohm unit. rho0/Ln*(Bohm unit)
        Ln: float
            Set R0/Ln for gyroBohm unit. Ln=1.0/2.22 when R0/Ln=2.22
            If Ln=None, use a_minor as default Ln.
        '''
        if particle in ('ion', 'electron', 'fastion'):
            figlabel = 'history/%s_flux' % particle
        else:
            raise ValueError('unsupported particle: %s ' % particle)
        time_chi, time_D = {}, {}
        time_chi_sat, time_D_sat = {}, {}
        for k, v in self.cases.items():
            a, b, c = v.dig(figlabel, post=False)
            time = b['time']
            chi, D = b['energy'], b['particle']
            if gyroBohm:
                Ln = v.pckloader['gtc/a_minor'] if Ln is None else Ln
                rho0 = v.pckloader['gtc/rho0']
                chi, D = chi*Ln/rho0, D*Ln/rho0
            time_chi[k] = (time, chi)  # TODO saturation
            time_D[k] = (time, D)
            if self.sat_time and self.paths[k] in self.sat_time:
                start, end = self.sat_time[self.paths[k]]
                start, end = np.where(time > start)[
                    0][0], np.where(time > end)[0]
                end = end[0] if len(end) > 0 else len(time)
            else:
                start, end = len(time)*7//10, len(time)
            sat_x = np.linspace(time[start], time[end-1], 2)
            chi_sat = np.mean(chi[start:end])
            D_sat = np.mean(D[start:end])
            # sat_std = np.std(chi[start:end])
            time_chi_sat[k] = (sat_x, np.linspace(chi_sat, chi_sat,  2))
            time_D_sat[k] = (sat_x, np.linspace(D_sat, D_sat,  2))
        return time_chi, time_D, time_chi_sat, time_D_sat
