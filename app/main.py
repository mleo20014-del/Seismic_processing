"""
app/main.py — точка входа UI/Rendering слоя.

КРИТИЧЕСКИ ВАЖЕН ПОРЯДОК ИНИЦИАЛИЗАЦИИ:
  1. QQuickWindow.setGraphicsApi(OpenGL) — ДО создания QGuiApplication и QQmlEngine.
  2. QGuiApplication(...) — после setGraphicsApi.
  3. QTranslator — устанавливается после создания QGuiApplication, ДО создания QQmlEngine.
  4. QQmlEngine / QQmlApplicationEngine — после QGuiApplication и QTranslator.

Нарушение порядка не диагностируется на уровне отдельного модуля.
Источник: AGENTS.md §4.2, first-step.md раздел 4.

i18n (D004/D011): механизм Qt Linguist закладывается с Фазы 0.
  - Язык по умолчанию: RU.
  - Переключение EN: через настройки (Фаза 2+).
  - .qm файлы находятся в i18n/ и бандлируются через seismic.spec.
"""

import sys
from pathlib import Path

from PySide6.QtCore import QLocale, QTranslator
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface

# Каталог с .qm файлами переводов
I18N_DIR = Path(__file__).parent.parent / "i18n"


def _install_translator(app: QGuiApplication, locale: QLocale | None = None) -> QTranslator | None:
    """
    Устанавливает переводчик для заданной локали.
    Возвращает объект QTranslator (держать в памяти всё время работы приложения).
    Если перевод не найден — приложение работает на исходном языке (EN-source).
    """
    if locale is None:
        locale = QLocale.system()

    lang = locale.name()  # например "ru_RU", "en_US"
    lang_short = lang.split("_")[0]  # "ru", "en"

    # Ищем файл перевода: сначала точное совпадение (ru_RU), затем короткое (ru)
    candidates = [
        I18N_DIR / f"seismic_{lang}.qm",
        I18N_DIR / f"seismic_{lang_short}.qm",
    ]

    translator = QTranslator(app)
    for qm_path in candidates:
        if qm_path.exists() and translator.load(str(qm_path)):
            app.installTranslator(translator)
            return translator

    # Перевод не найден — не критично, работаем на source-языке
    return None


def main() -> int:
    # ── ШАГ 1: зафиксировать RHI backend на OpenGL ДО любого Qt-объекта ──────
    # ОБЯЗАТЕЛЬНО до создания QGuiApplication.
    # Источник: AGENTS.md §4.2, renderer-template.md
    QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.OpenGL)

    # ── ШАГ 2: создать QGuiApplication ──────────────────────────────────────
    app = QGuiApplication(sys.argv)
    app.setApplicationName("SeismicProcessing")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("SeismicProject")

    # ── ШАГ 3: установить переводчик (i18n, D004/D011) ───────────────────────
    # По умолчанию — системная локаль (будет RU на системах с locale=ru_RU).
    # Переключение через настройки реализуется в Фазе 2.
    _translator = _install_translator(app)

    # ── ШАГ 4: создать QML-движок и загрузить главный QML-файл ───────────────
    engine = QQmlApplicationEngine()

    qml_root = Path(__file__).parent.parent / "ui" / "qml"
    engine.addImportPath(str(qml_root))

    qml_main = qml_root / "main.qml"
    engine.load(qml_main)

    if not engine.rootObjects():
        print(
            "[ERROR] Не удалось загрузить main.qml. " "Проверьте путь и синтаксис QML-файла.",
            file=sys.stderr,
        )
        return 1

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
