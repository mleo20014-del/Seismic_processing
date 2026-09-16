# seismic.spec — PyInstaller spec (Фаза 0, proof-of-concept; финальный — Фаза 6)
# Упаковщик: PyInstaller (D001 — решение зафиксировано, не переоткрывать)
# Платформы: Linux, Windows, macOS (D010)
#
# ОБЯЗАТЕЛЬНЫЕ datas:
#   - build/shaders/*.qsb  — без них рендерер не работает (AGENTS.md §5 MUST DO)
#   - ui/qml/**/*.qml      — QML-движок не загрузится без файлов
#   - i18n/*.qm            — переводы (D004/D011, i18n с Фазы 0)
#   - config/*.yaml        — конфигурации ChunkSource
#
# Запуск: uv run pyinstaller seismic.spec
# Проверка бандлинга: dist/SeismicProcessing/SeismicProcessing --log-level DEBUG

import sys
from pathlib import Path

PROJECT_ROOT = Path(".").resolve()
IS_MACOS = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"

# Нативные библиотеки pycuda (только Linux/Windows — нет CUDA на macOS)
_pycuda_binaries = []
if not IS_MACOS:
    try:
        import site

        for sp in site.getsitepackages():
            driver_so = Path(sp) / "pycuda" / "_driver.cpython-313-x86_64-linux-gnu.so"
            if driver_so.exists():
                _pycuda_binaries.append((str(driver_so), "pycuda"))
                break
    except Exception:
        pass  # На CI без CUDA — не критично для proof-of-concept

a = Analysis(
    [str(PROJECT_ROOT / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=_pycuda_binaries,
    datas=[
        # QML-файлы
        (str(PROJECT_ROOT / "ui" / "qml"), "ui/qml"),
        # Скомпилированные шейдеры .qsb (AGENTS.md §5 MUST DO)
        (str(PROJECT_ROOT / "build" / "shaders"), "build/shaders"),
        # Переводы Qt Linguist (D004/D011 — i18n с Фазы 0)
        (str(PROJECT_ROOT / "i18n"), "i18n"),
        # YAML конфигурации ChunkSource
        (str(PROJECT_ROOT / "config"), "config"),
    ],
    hiddenimports=[
        "PySide6.QtQuick",
        "PySide6.QtQml",
        "PySide6.QtGui",
        "PySide6.QtCore",
        "PySide6.QtOpenGL",
        "PySide6.QtQuickControls2",
        # pycuda (только не-macOS; на macOS импорт защищён в interop/)
        "pycuda",
        "pycuda.gl",
        "pycuda.driver",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Не включаем PyVista/VTK — только offline QA (AGENTS.md §3)
        "vtk",
        "pyvista",
        "matplotlib",
        "IPython",
        "jupyter",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SeismicProcessing",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # macOS: иконка добавляется в Фазе 2 (assets/icon.icns)
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="SeismicProcessing",
)

# macOS App Bundle (только при сборке на macOS)
if IS_MACOS:
    app = BUNDLE(
        coll,
        name="SeismicProcessing.app",
        icon=None,  # assets/icon.icns добавляется в Фазе 2
        bundle_identifier="com.seismicproject.processing",
        info_plist={
            "NSHighResolutionCapable": True,  # HiDPI/Retina (D006)
            "CFBundleShortVersionString": "0.1.0",
        },
    )
