#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import logging
import gdpy3.read as gdr
import gdpy3.plot as gdp

log = logging.getLogger('gdpy3')
log0 = logging.getLogger('gdc')
log1 = logging.getLogger('gdr')
log2 = logging.getLogger('gdp')

APATH = '/home/IFTS_shmilee'
#RPATH = '20170511-ITG-nonlinear'
RPATH = '20170508-ITG-nonadiabatic'

fh = logging.FileHandler(os.path.join(APATH, RPATH, 'gdpy3.log'))
formatter = logging.Formatter('[%(name)s]%(levelname)s - %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)
log0.addHandler(fh)
log1.addHandler(fh)
log2.addHandler(fh)


def skip_name(name):
    if name in ['data1d/' + n for n in [
        'ion_flux',
        #'ion_energy_flux',
        'electron_flux',
        #'electron_energy_flux',
        #'zonal_flow',
        #'phi_rms',
    ]]:
        return False
    if name in ['history/fieldmode%s_%s' % (i, f)
                for i in range(1, 9) for f in ['phi']]:
        return False

    return True

if __name__ == '__main__':
    log2.setLevel(10)

    os.chdir(APATH)
    pathdir = RPATH
    ccalf = open(os.path.join(pathdir, 'calculate.txt'), 'w')
    ccalf.write("calculateresults = {\n")
    # walk
    for root, dirs, files in os.walk(pathdir):
        if 'gtc.out' in files:
            case = root
        else:
            continue
        log.info("Case Path: %s" % case)
        figdir = os.path.join(case, 'figures')
        if not os.path.isdir(figdir):
            os.mkdir(figdir)
        try:
            dictobj = gdr.read(case, overwrite=False)
            gf = gdp.gtcfigures.GtcFigures(dictobj, engine='mpl')
        except Exception as exc:
            log.error(exc)
            ccalf.close()
            break
        for name in gf.figures:
            if skip_name(name):
                continue
            fig, cal = gf.get_figure(name, figurestyle=['gdpy3-notebook'])
            if fig:
                pdf = os.path.join(figdir, name.replace('/', '-') + '.pdf')
                log2.info("Save figure to %s ..." % pdf)
                fig.savefig(pdf)
                ccalf.write("'%s': %s,\n" % (case + '/' + name, cal))
                ccalf.flush()
                fig.clf()
    ccalf.write("}\n")
    ccalf.close()
