# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

spec_root = os.path.abspath(SPECPATH)

a = Analysis(['main.py'],
             pathex=['C:\\repos\\epJSON-Editor\\epjsoneditor', spec_root],
             binaries=[],
             datas=[('support', 'support'), ('Energy+.schema.epJSON', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='epJSON-Editor',
          debug=False,
          strip=False,
          upx=True,
          console=True )