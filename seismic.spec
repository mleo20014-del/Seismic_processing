# seismic.spec — черновой PyInstaller spec (Фаза 0, proof-of-concept сборки)
# Упаковщик: PyInstaller (D001 — решение зафиксировано, не переоткрывать)
#
# Критически важно: batas включает build/shaders/*.qsb и ui/qml/**/*.qml
# Без этого дистрибутив собирается без ассетов (AGENTS.md §4, first-step.md раздел 4).
#
# Для реального дистрибутива (Фаза 6) потребуется:
# 1. Добавить native-библиотеки PyCUDA и CUDA toolkit через --add-binary
# 2. Настроить хуки для QtQuick/QML ресурсов
# 3. Проверить бандлинг через: dist/SeismicProcessing --log-level DEBUG
#
# Запуск: pyinstaller seismic.spec
# (или: uv run pyinstaller seismic.spec)

from pathlib import Path

PROJECT_ROOT = Path(".").resolve()

a = Analysis(
    [str(PROJECT_ROOT / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[
        # PyCUDA native libs добавляются здесь в Фазе 6 после установки pycuda:
        # ("/path/to/pycuda/_driver.so", "pycuda"),
        # CUDA toolkit libs:
        # ("/usr/local/cuda/lib64/libcuda.so", "."),
    ],
    datas=[
        # QML-файлы — обязательны для работы QML-движка
        (str(PROJECT_ROOT / "ui" / "qml"), "ui/qml"),
        # Скомпилированные шейдеры .qsb — ОБЯЗАТЕЛЬНЫ для рендерера
        # (AGENTS.md §5 MUST DO, first-step.md раздел 4)
        (str(PROJECT_ROOT / "build" / "shaders"), "build/shaders"),
        # YAML конфигурации ChunkSource
        (str(PROJECT_ROOT / "config"), "config"),
    ],
    hiddenimports=[
        "PySide6.QtQuick",
        "PySide6.QtQml",
        "PySide6.QtGui",
        "PySide6.QtCore",
        "PySide6.QtOpenGL",
        # pycuda добавляется в Фазе 6:
        # "pycuda",
        # "pycuda.gl",
        # "pycuda.driver",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Не включаем PyVista/VTK — только offline QA, не в дистрибутиве
        "vtk",
        "pyvista",
        "matplotlib",
        # Jupyter
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
    console=False,  # GUI-приложение — без консоли
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
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
