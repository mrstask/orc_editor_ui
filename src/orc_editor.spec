from PyInstaller.utils.hooks import collect_data_files
import os
import pytz

block_cipher = None

# Add timezone data
timezone_data = []
tzdata_dir = os.path.join(os.path.dirname(pytz.__file__), 'zoneinfo')
for root, _, files in os.walk(tzdata_dir):
    for file in files:
        full_path = os.path.join(root, file)
        rel_path = os.path.relpath(full_path, tzdata_dir)
        timezone_data.append((full_path, os.path.join('pytz', 'zoneinfo', rel_path)))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=timezone_data,  # Add timezone data here
    hiddenimports=[
        'tkinter',
        'pandas',
        'numpy',
        'pyarrow',
        'pyarrow.orc',
        'pyarrow.lib',
        'pytz',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ORC_Editor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ORC_Editor'
)