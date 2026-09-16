#!/usr/bin/env python3
"""
scripts/update_translations.py — обновление и компиляция переводов Qt Linguist.

Шаг 1 (lupdate): сканирует .qml и .py исходники → обновляет .ts файлы новыми строками.
Шаг 2 (lrelease): компилирует .ts → .qm (бинарный формат, используется runtime).

Использование:
    uv run python scripts/update_translations.py           # lupdate + lrelease
    uv run python scripts/update_translations.py --release # только lrelease (compile only)
    uv run python scripts/update_translations.py --check   # проверить, что .qm актуальны

Правила (D004/D011, AGENTS.md):
    - Язык по умолчанию: RU. EN — в настройках приложения.
    - .ts файлы версионируются в git (они читаемы как XML).
    - .qm файлы версионируются вместе с .ts (аналогично .qsb/.glsl).
    - lupdate запускать при КАЖДОМ добавлении нового qsTr() в .qml/.py.

Добавление нового языка:
    1. Создать i18n/seismic_<lang>.ts (скопировать из seismic_en.ts)
    2. Добавить файл в список TRANSLATIONS ниже
    3. Запустить этот скрипт
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
I18N_DIR = PROJECT_ROOT / "i18n"

# Список языков: (ts_file, qm_file)
TRANSLATIONS = [
    (I18N_DIR / "seismic_ru.ts", I18N_DIR / "seismic_ru.qm"),
    (I18N_DIR / "seismic_en.ts", I18N_DIR / "seismic_en.qm"),
]

# Исходники для сканирования (lupdate)
SOURCE_DIRS = [
    str(PROJECT_ROOT / "ui" / "qml"),
    str(PROJECT_ROOT / "app"),
]


def find_tool(name: str) -> str | None:
    """Ищет lupdate/lrelease в PATH и рядом с PySide6."""
    if found := shutil.which(name):
        return found
    try:
        import PySide6

        candidate = Path(PySide6.__file__).parent / name
        if candidate.exists():
            return str(candidate)
    except ImportError:
        pass
    return None


def run_lupdate(lupdate_bin: str, ts_file: Path, verbose: bool) -> bool:
    """Обновляет .ts файл из исходников."""
    cmd = [lupdate_bin, "-no-obsolete"] + SOURCE_DIRS + ["-ts", str(ts_file)]
    if verbose:
        print(f"  lupdate: {ts_file.name}")
        print(f"  CMD: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] lupdate failed for {ts_file.name}:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return False
    if verbose:
        print(result.stdout.strip())
    return True


def run_lrelease(lrelease_bin: str, ts_file: Path, qm_file: Path, verbose: bool) -> bool:
    """Компилирует .ts → .qm."""
    cmd = [lrelease_bin, str(ts_file), "-qm", str(qm_file)]
    if verbose:
        print(f"  lrelease: {ts_file.name} → {qm_file.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] lrelease failed for {ts_file.name}:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return False
    if verbose:
        print(result.stdout.strip())
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Обновление и компиляция переводов Qt Linguist")
    parser.add_argument(
        "--release",
        action="store_true",
        help="Только компилировать .ts → .qm, без lupdate (сканирования исходников)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Проверить, что .qm файлы существуют (для CI). Выход 1 если нет.",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if args.check:
        missing = [ts for ts, qm in TRANSLATIONS if not qm.exists()]
        if missing:
            print(
                "[FAIL] Отсутствуют .qm файлы для: "
                + ", ".join(t.stem for t in missing)
                + "\n  Запустите: uv run python scripts/update_translations.py"
            )
            return 1
        print(f"[OK] Все .qm файлы присутствуют ({len(TRANSLATIONS)} шт.)")
        return 0

    lrelease_bin = find_tool("lrelease")
    if lrelease_bin is None:
        print("[ERROR] lrelease не найден. Убедитесь, что PySide6 установлен.", file=sys.stderr)
        return 1

    errors = 0

    if not args.release:
        lupdate_bin = find_tool("lupdate")
        if lupdate_bin is None:
            print("[ERROR] lupdate не найден. Убедитесь, что PySide6 установлен.", file=sys.stderr)
            return 1
        print("=== lupdate: обновление .ts из исходников ===")
        for ts_file, _ in TRANSLATIONS:
            if not run_lupdate(lupdate_bin, ts_file, args.verbose):
                errors += 1
            elif not args.verbose:
                print(f"  OK  {ts_file.name}")

    print("=== lrelease: компиляция .ts → .qm ===")
    for ts_file, qm_file in TRANSLATIONS:
        if not run_lrelease(lrelease_bin, ts_file, qm_file, args.verbose):
            errors += 1
        elif not args.verbose:
            print(f"  OK  {ts_file.name} → {qm_file.name}")

    if errors > 0:
        print(f"\n[FAIL] {errors} ошибок при обновлении переводов.", file=sys.stderr)
        return 1

    print(f"\n[OK] Переводы обновлены: {len(TRANSLATIONS)} языков.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
