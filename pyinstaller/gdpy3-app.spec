# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

# -*- mode: python -*-


def _get_gdpy3_about():
    import os
    import gdpy3.__about__

    return {
        'name': 'gdpy3-app',
        'version': gdpy3.__about__.__version__,
        'AppID': 'io.shmilee.gdpy3.app',
        'desc': gdpy3.__about__.__description__,
        'copyright': gdpy3.__about__.__copyright__,
        'icon': os.path.join(
            gdpy3.__about__.__data_path__, 'icon',
            '%s.icns' % gdpy3.__about__.__icon_name__),
    }


gdpy3_about = _get_gdpy3_about()
block_cipher = None

a = Analysis(['./gdpy3-app.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=['packaging.requirements'],
             hookspath=['.'],
             runtime_hooks=[],
             excludes=['gtk', 'gi',
                       'matplotlib.backends.backend_gtk3',
                       'matplotlib.backends.backend_gtk3agg',
                       'matplotlib.backends.backend_gtk3cairo',
                       'PyQt4',
                       'matplotlib.backends.backend_qt4agg',
                       'matplotlib.backends.backend_qt4cairo',
                       'notebook', 'tornado', 'zmq',
                       'ipywidgets', 'nbconvert', 'nbformat',
                       ],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name=gdpy3_about['name'],
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          icon=gdpy3_about['icon'],
          console=False)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name=gdpy3_about['name'])
app = BUNDLE(coll,
             name='%s.app' % gdpy3_about['name'],
             version=gdpy3_about['version'],
             icon=gdpy3_about['icon'],
             bundle_identifier=gdpy3_about['AppID'],
             info_plist={
                 'CFBundleGetInfoString': gdpy3_about['desc'],
                 'NSHumanReadableCopyright': gdpy3_about['copyright'],
             })
