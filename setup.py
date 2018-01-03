# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

import os
import importlib.util
from setuptools import setup, find_packages

# https://docs.python.org/3.6/library/importlib.html#importing-a-source-file-directly
spec = importlib.util.spec_from_file_location('gdpy3', './src/__init__.py')
gdpy3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gdpy3)

packages = ['gdpy3']
subpackages = find_packages(where='src', exclude=('*tests',))
packages.extend(['gdpy3.%s' % p for p in subpackages])

setup(
    name='gdpy3',
    version=gdpy3.__version__,
    description=gdpy3.__doc__,
    long_description=open(
        os.path.join(
            os.path.dirname(__file__),
            'README.rst'
        )
    ).read(),
    author=gdpy3.__author__,
    author_email=gdpy3.__email__,
    url=gdpy3.__uri__,
    license=gdpy3.__license__,
    keywords='GTC, matplotlib',
    package_dir={'gdpy3': 'src'},
    packages=packages,
    platforms=[
        'Linux',
        'MacOS X',
        'Windows',
    ],
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Plugins',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: OS Independent',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Scientific/Engineering :: Visualization'
    ),
    install_requires=[
        'numpy>=1.10.0',
        'matplotlib>=1.5.3',
    ],
    extras_require={
        'hdf5': ['h5py>=2.6.0'],
        'tools': ['scipy>=0.14.0'],
        'ipynbtool': ['ipython[notebook]'],
    },
    package_data={
        'gdpy3': ['plot/enginelib/mpl-stylelib/*.mplstyle',
                  'plot/enginelib/mpl-stylelib/readme.txt']
    },
    data_files=[],
    entry_points={
        'console_scripts': [
            'gdpy3-convert = gdpy3.main:script_convert',
            'gdpy3-plot = gdpy3.main:script_plot',
        ],
        #'gui_scripts': [
        #    'gdpy3-gui = gdpy3.gui:start',
        #],
    },
)
