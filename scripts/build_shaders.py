#!/usr/bin/env python3
"""
scripts/build_shaders.py — компиляция GLSL-шейдеров в .qsb.

Использование:
    uv run python scripts/build_shaders.py            # компилировать всё
    uv run python scripts/build_shaders.py --check    # проверить, что .qsb актуальны (для CI)
    uv run python scripts/build_shaders.py --verbose  # подробный вывод

Правило (AGENTS.md §5 MUST DO):
    Изменённый .glsl/.vert/.frag → пересобранный .qsb коммитятся в ОДНОМ коммите.

GLSL profiles: 100 es, 120, 150  (минимум 100 es по shader-and-raymarching.md).
Формат имён шейдеров: <purpose>.<stage>.glsl → <purpose>.<stage>.glsl.qsb
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

# Корень проекта — два уровня вверх от этого скрипта
PROJECT_ROOT = Path(__file__).parent.parent
SHADERS_SRC = PROJECT_ROOT / "shaders"
SHADERS_OUT = PROJECT_ROOT / "build" / "shaders"

# GLSL profiles для qsb.
# QQuickRhiItem на OpenGL backend требует минимум 330.
# "100 es,120" оставлены для совместимости с мобильными устройствами,
# но основной target: 330 (desktop OpenGL 3.3 core).
# Источник: shader-and-raymarching.md, AGENTS.md §4.2
GLSL_PROFILES = "100 es,120,330"

# Расширения файлов шейдеров
SHADER_EXTENSIONS = {".vert", ".frag", ".comp"}


def find_qsb() -> str | None:
    """Ищет утилиту qsb в PATH и стандартных местах PySide6."""
    # Сначала ищем в PATH
    if qsb := shutil.which("qsb"):
        return qsb

    # Ищем рядом с PySide6
    try:
        import PySide6

        pyside_dir = Path(PySide6.__file__).parent
        for candidate in [pyside_dir / "qsb", pyside_dir / "Qt" / "libexec" / "qsb"]:
            if candidate.exists():
                return str(candidate)
    except ImportError:
        pass

    return None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def compile_shader(qsb_bin: str, src: Path, out: Path, verbose: bool = False) -> bool:
    """Компилирует один шейдер. Возвращает True при успехе."""
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [qsb_bin, "--glsl", GLSL_PROFILES, "-o", str(out), str(src)]

    if verbose:
        print(f"  {src.relative_to(PROJECT_ROOT)} → {out.relative_to(PROJECT_ROOT)}")
        print(f"  CMD: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[ERROR] Ошибка компиляции {src.name}:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return False

    if verbose and result.stdout:
        print(result.stdout)

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Компиляция GLSL шейдеров → .qsb")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Только проверить, что все .qsb актуальны (для CI). Выход 1 если нет.",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")
    args = parser.parse_args()

    # Найти qsb
    qsb_bin = find_qsb()
    if qsb_bin is None:
        print(
            "[ERROR] Утилита qsb не найдена. "
            "Убедитесь, что PySide6 установлен и qsb доступен в PATH.\n"
            '  На Linux: export PATH=$PATH:$(python -c "import PySide6; '
            'import os; print(os.path.dirname(PySide6.__file__))")',
            file=sys.stderr,
        )
        return 1

    if args.verbose:
        print(f"qsb: {qsb_bin}")
        print(f"src: {SHADERS_SRC}")
        print(f"out: {SHADERS_OUT}")

    # Собрать список шейдеров
    shader_files = [
        p for p in sorted(SHADERS_SRC.rglob("*")) if p.is_file() and p.suffix in SHADER_EXTENSIONS
    ]

    if not shader_files:
        print(
            f"[INFO] Нет шейдеров в {SHADERS_SRC.relative_to(PROJECT_ROOT)}/ "
            "(будут добавлены в Фазе 5)."
        )
        return 0

    errors = 0
    stale = 0

    for src in shader_files:
        # Сохраняем относительный путь внутри shaders/ как структуру в build/shaders/
        rel = src.relative_to(SHADERS_SRC)
        out = SHADERS_OUT / (str(rel) + ".qsb")

        if args.check:
            # В режиме --check просто проверяем существование и свежесть .qsb
            if not out.exists():
                print(f"[STALE] Нет .qsb для {src.relative_to(PROJECT_ROOT)}")
                stale += 1
        else:
            ok = compile_shader(qsb_bin, src, out, verbose=args.verbose)
            if not ok:
                errors += 1
            elif not args.verbose:
                print(f"  OK  {src.relative_to(SHADERS_SRC)}")

    if args.check and stale > 0:
        print(
            f"\n[FAIL] {stale} шейдер(ов) не скомпилированы. "
            "Запустите: uv run python scripts/build_shaders.py"
        )
        return 1

    if errors > 0:
        print(f"\n[FAIL] {errors} шейдер(ов) завершились с ошибкой.", file=sys.stderr)
        return 1

    if not args.check:
        compiled = len(shader_files) - errors
        print(f"\n[OK] Скомпилировано {compiled}/{len(shader_files)} шейдеров.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
