"""Контроллер приложения и активных режимов."""

from PyQt6.QtWidgets import QWidget  # Импортируем QWidget как тип экранов.

from app.cache_manager import SyntheticCacheManager  # Импортируем менеджер кэша.
from app.task_manager import TaskManager  # Импортируем менеджер фоновых задач.
from config.app_config import AppConfig  # Импортируем конфигурацию приложения.
from ui.modes.processing.processing_view import ProcessingView  # Режим обработки.
from ui.modes.synthetic.node_edit_canvas import NodeEditCanvas  # Canvas синтетики.
from ui.modes.testing.testing_view import TestingView  # Режим тестирования.
from ui.modes.training.training_view import TrainingView  # Режим обучения.


class AppController:  # Объявляем владельца активных режимов.
    """Управляет активными режимами и делегирует задачи TaskManager."""

    def __init__(  # Принимаем зависимости контроллера.
        self,
        config: AppConfig,
        task_manager: TaskManager,
        cache_manager: SyntheticCacheManager,
    ) -> None:
        """Инициализирует контроллер приложения."""
        self.config = config  # Сохраняем конфиг через dependency injection.
        self.task_manager = task_manager  # Сохраняем менеджер фоновых задач.
        self.cache_manager = cache_manager  # Сохраняем менеджер memmap-кэша.
        self._active_modes: dict[str, QWidget] = {}  # Храним открытые режимы.

    def open_mode(self, mode: str) -> QWidget:
        """Возвращает существующий или созданный виджет режима."""
        if mode in self._active_modes:  # Проверяем, открыт ли режим раньше.
            return self._active_modes[mode]  # Возвращаем существующий виджет.

        widget = self._create_mode_widget(mode)  # Создаём виджет режима.
        self._active_modes[mode] = widget  # Сохраняем единственный экземпляр.
        self.task_manager.subscribe(mode, widget)  # Подписываем виджет режима.
        return widget  # Возвращаем созданный виджет режима.

    def close_mode(self, mode: str) -> None:  # Закрываем активный режим.
        """Удаляет режим из активных без остановки фоновой задачи."""
        widget = self._active_modes.pop(mode, None)  # Забираем виджет режима.
        if widget is not None:  # Проверяем, был ли режим открыт.
            self.task_manager.unsubscribe(mode, widget)  # Отписываем от задач.
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
            return NodeEditCanvas(  # Создаём canvas синтетики.
                self.config,  # Передаём конфигурацию.
                self.cache_manager,  # Передаём менеджер кэша.
            )  # Завершаем создание canvas.
        if mode == "testing":  # Проверяем режим тестирования.
            return TestingView(self.config)  # Создаём виджет тестирования.

        raise ValueError(f"Неизвестный режим: {mode}")  # Сообщаем об ошибке.
