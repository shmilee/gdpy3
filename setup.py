# -*- coding: utf-8 -*-

# Copyright (c) 2018 shmilee

import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
about = {}
with open(os.path.join(here, 'src', '__about__.py'), encoding='utf-8') as f:
    about['__file__'] = f.name
    exec(f.read(), about)
data_dir = os.path.basename(about['__data_path__'])
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

packages = ['gdpy3']
subpackages = find_packages(where='src', exclude=('*tests',))
packages.extend(['gdpy3.%s' % p for p in subpackages])

setup(
    name='gdpy3',
    version=about['__version__'],
    description=about['__description__'],
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author=about['__author__'],
    author_email=about['__email__'],
    url=about['__url__'],
    license=about['__license__'],
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
        'pck.hdf5': ['h5py>=2.6.0'],
        'raw.ssh': ['paramiko>=2.4.1'],
        'core.tools': ['scipy>=0.14.0'],
        'gui.ipynb': ['ipython[notebook]', 'ipywidgets'],
    },
    package_data={
        'gdpy3': ['%s/%s' % (data_dir, f) for f in [
            '*-stylelib/gdpy3-*.*style',
            '*-stylelib/readme.txt',
            'icon/*',
            'ipynb_scrollbar/*'
        ]],
    },
    data_files=[],
    entry_points={
        'console_scripts': [
            'gdpy3 = gdpy3.cli:cli_script',
        ],
        'gui_scripts': [
            'gdpy3-gui = gdpy3.GUI:gui_script',
        ],
    },
)
