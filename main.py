"""Запуск приложения."""

import sys  # Импортируем sys для завершения приложения с кодом Qt.

from PyQt6.QtWidgets import QApplication  # Импортируем QApplication.

from config.app_config import AppConfig  # Импортируем конфигурацию приложения.
from ui.main_window import MainWindow  # Импортируем главное окно.


def main() -> int:  # Запускаем приложение и возвращаем код выхода.
    """Создаёт конфигурацию, приложение Qt и главное окно."""
    config = AppConfig()  # Создаём объект конфигурации.
    config.ensure_dirs()  # Создаём обязательные папки проекта.
    app = QApplication(sys.argv)  # Создаём Qt-приложение.
    window = MainWindow(config)  # Создаём главное окно приложения.
    window.show()  # Показываем главное окно пользователю.
    return app.exec()  # Запускаем цикл событий Qt.


if __name__ == "__main__":  # Проверяем прямой запуск файла.
    sys.exit(main())  # Запускаем приложение и отдаём код выхода.
