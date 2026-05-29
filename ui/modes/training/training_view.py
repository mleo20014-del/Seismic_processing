"""Виджет режима обучения."""

from PyQt6.QtCore import Qt  # Импортируем Qt для выравнивания текста.
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget  # Импортируем виджеты.

from config.app_config import AppConfig  # Импортируем конфигурацию приложения.


class TrainingView(QWidget):  # Объявляем экран режима обучения.
    """Отображает каркас режима обучения моделей."""

    def __init__(self, config: AppConfig) -> None:  # Принимаем конфигурацию.
        """Инициализирует визуальный каркас режима обучения."""
        super().__init__()  # Инициализируем QWidget.
        self.config = config  # Сохраняем конфиг через dependency injection.
        layout = QVBoxLayout(self)  # Создаём layout режима.
        label = QLabel("Режим обучения моделей U-Net", self)  # Создаём подпись.
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Центрируем подпись.
        layout.addWidget(label)  # Добавляем подпись в layout.
