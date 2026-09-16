"""
app/main.py — точка входа UI/Rendering слоя.

КРИТИЧЕСКИ ВАЖЕН ПОРЯДОК ИНИЦИАЛИЗАЦИИ:
  1. QQuickWindow.setGraphicsApi(OpenGL) — ДО создания QGuiApplication и QQmlEngine.
  2. QGuiApplication(...) — после setGraphicsApi.
  3. QQmlEngine / QQmlApplicationEngine — после QGuiApplication.

Нарушение порядка не диагностируется на уровне отдельного модуля.
Источник: AGENTS.md §4.2, first-step.md раздел 4 (первая строка таблицы).
"""

import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface


def main() -> int:
    # ── ШАГ 1: зафиксировать RHI backend на OpenGL ДО любого Qt-объекта ──────
    # Это обязательно делать до создания QGuiApplication.
    QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.OpenGL)

    # ── ШАГ 2: создать QGuiApplication ──────────────────────────────────────
    app = QGuiApplication(sys.argv)
    app.setApplicationName("SeismicProcessing")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("SeismicProject")

    # ── ШАГ 3: создать QML-движок и загрузить главный QML-файл ───────────────
    engine = QQmlApplicationEngine()

    # Путь к QML-файлам относительно корня проекта
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
