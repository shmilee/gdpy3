#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import logging
import gdpy3.plot as gdp

log = logging.getLogger('gdpy3')
log0 = logging.getLogger('gdc')
log1 = logging.getLogger('gdr')
log2 = logging.getLogger('gdp')

APATH = '/home/IFTS_shmilee'
#RPATH = '20170511-ITG-nonlinear'
#RPATH = '20170508-ITG-nonadiabatic'
RPATH = '20170603-ITG-adiabatic'

fh = logging.FileHandler(os.path.join(APATH, RPATH, 'gdpy3.log'))
formatter = logging.Formatter('[%(name)s]%(levelname)s - %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)
log0.addHandler(fh)
log1.addHandler(fh)
log2.addHandler(fh)

default_enable = [
    'data1d/ion_flux',
    #'data1d/ion_energy_flux',
    #'data1d/electron_flux',
    #'data1d/electron_energy_flux',
    'data1d/zonal_flow',
    'data1d/residual_zonal_flow',
    r'history/fieldmode\d_phi',
    # r'history/fieldmode\d_apara',
    # r'history/fieldmode\d_fluidne',
]


if __name__ == '__main__':
    log2.setLevel(10)

    os.chdir(APATH)
    ccalf = open(os.path.join(RPATH, 'calculate.txt'), 'w')
    ccalf.write("calculateresults = {\n")
    # walk
    for croot, dirs, files in os.walk(RPATH):
        if 'gtc.out' not in files:
            continue
        log.info("Case Path: %s" % croot)
        figdir = os.path.join(croot, 'figures')
        if not os.path.isdir(figdir):
            os.mkdir(figdir)
        try:
            case = gdp.plot(croot, default_enable=default_enable)
        except Exception as exc:
            log.error("Case %s, Skip: %s" % (croot, exc))
        else:
            for name in sorted(case.gfigure_enabled):
                case.plot(name, show=False, figurestyle=[
                    #'gdpy3-notebook',
                    #'seaborn',
                    'ggplot', {'figure.figsize': (10.0, 8.0)}
                ])
                gf = case[name]
                if gf.figure and gf.engine == 'matplotlib':
                    pdf = os.path.join(figdir, name.replace('/', '-') + '.pdf')
                    log2.info("Save figure to %s ..." % pdf)
                    gf.figure.savefig(pdf)
                if gf.calculation:
                    ccalf.write("'%s': %s,\n"
                                % (croot + '/' + name, gf.calculation))
                    ccalf.flush()
                case.disable(name)
        # break
    ccalf.write("}\n")
    ccalf.close()
