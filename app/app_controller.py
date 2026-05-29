"""Контроллер приложения и активных режимов."""

from PyQt6.QtCore import QThread  # Импортируем QThread для будущих задач.
from PyQt6.QtWidgets import QWidget  # Импортируем QWidget как тип экранов.

from config.app_config import AppConfig  # Импортируем конфигурацию приложения.
from ui.modes.processing.processing_view import ProcessingView  # Режим обработки.
from ui.modes.synthetic.synthetic_view import SyntheticView  # Режим синтетики.
from ui.modes.testing.testing_view import TestingView  # Режим тестирования.
from ui.modes.training.training_view import TrainingView  # Режим обучения.


class AppController:  # Объявляем владельца режимов и фоновых задач.
    """Управляет активными режимами и будущими QThread задачами."""

    def __init__(self, config: AppConfig) -> None:  # Принимаем конфигурацию.
        """Инициализирует контроллер приложения."""
        self.config = config  # Сохраняем конфиг через dependency injection.
        self._active_modes: dict[str, QWidget] = {}  # Храним открытые режимы.
        self._tasks: dict[str, QThread] = {}  # Храним будущие фоновые задачи.

    def open_mode(self, mode: str) -> QWidget:  # Открываем или возвращаем режим.
        """Возвращает существующий или лениво созданный виджет режима."""
        if mode in self._active_modes:  # Проверяем, открыт ли режим раньше.
            return self._active_modes[mode]  # Возвращаем существующий виджет.

        widget = self._create_mode_widget(mode)  # Создаём виджет режима.
        self._active_modes[mode] = widget  # Сохраняем единственный экземпляр.
        return widget  # Возвращаем созданный виджет режима.

    def close_mode(self, mode: str) -> None:  # Закрываем активный режим.
        """Удаляет режим из активных без остановки фоновой задачи."""
        widget = self._active_modes.pop(mode, None)  # Забираем виджет режима.
        if widget is not None:  # Проверяем, был ли режим открыт.
            widget.deleteLater()  # Планируем безопасное удаление виджета.

    def has_unsaved_changes(self, mode: str) -> bool:  # Проверяем изменения.
        """Возвращает признак несохранённых изменений режима."""
        return False  # На этапе foundation изменений ещё нет.

    def get_mode_widget(self, mode: str) -> QWidget | None:  # Ищем виджет.
        """Возвращает активный виджет режима или None."""
        return self._active_modes.get(mode)  # Возвращаем виджет из словаря.

    def _create_mode_widget(self, mode: str) -> QWidget:  # Создаём режим.
        """Создаёт виджет режима по строковому идентификатору."""
        if mode == "training":  # Проверяем режим обучения.
            return TrainingView(self.config)  # Создаём виджет обучения.
        if mode == "processing":  # Проверяем режим обработки.
            return ProcessingView(self.config)  # Создаём виджет обработки.
        if mode == "synthetic":  # Проверяем режим синтетики.
            return SyntheticView(self.config)  # Создаём виджет синтетики.
        if mode == "testing":  # Проверяем режим тестирования.
            return TestingView(self.config)  # Создаём виджет тестирования.

        raise ValueError(f"Неизвестный режим: {mode}")  # Сообщаем об ошибке.
