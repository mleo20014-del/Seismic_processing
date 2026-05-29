"""Менеджер фоновых задач приложения."""

from PyQt6.QtCore import QObject, QThread  # Импортируем базу Qt и поток.
from PyQt6.QtWidgets import QWidget  # Импортируем QWidget для подписчиков.

from config.app_config import AppConfig  # Импортируем конфигурацию приложения.


class TaskManager(QObject):  # Объявляем владельца фоновых QThread задач.
    """Хранит фоновые задачи и подписки виджетов на их сигналы."""

    def __init__(self, config: AppConfig) -> None:  # Принимаем конфигурацию.
        """Инициализирует менеджер фоновых задач."""
        super().__init__()  # Инициализируем QObject для sender() и сигналов.
        self.config = config  # Сохраняем конфиг через dependency injection.
        self._tasks: dict[str, QThread] = {}  # Храним активные потоки по режиму.
        self._subscribers: dict[str, set[QWidget]] = {}  # Храним подписчиков.

    def start_task(self, mode: str, task: QThread) -> None:  # Запускаем задачу.
        """Регистрирует и запускает фоновую задачу режима."""
        if self.has_active_task(mode):  # Проверяем уже активную задачу режима.
            raise RuntimeError(f"Задача режима уже запущена: {mode}")  # Ошибка.

        self._tasks[mode] = task  # Сохраняем поток как активную задачу режима.
        task.setProperty("mode", mode)  # Запоминаем режим внутри QObject.
        task.finished.connect(self._on_task_finished)  # Подключаем очистку.
        task.start()  # Запускаем поток задачи.

    def request_cancel(self, mode: str) -> None:  # Запрашиваем отмену задачи.
        """Запрашивает мягкую отмену активной задачи режима."""
        task = self._tasks.get(mode)  # Получаем активный поток режима.
        if task is None:  # Проверяем отсутствие активной задачи.
            return  # Нечего отменять.

        task.requestInterruption()  # Просим поток остановиться безопасно.

    def has_active_task(self, mode: str) -> bool:  # Проверяем задачу режима.
        """Возвращает True, если у режима есть работающий поток."""
        task = self._tasks.get(mode)  # Получаем поток режима.
        return task is not None and task.isRunning()  # Проверяем активность.

    def get_task(self, mode: str) -> QThread | None:  # Возвращаем задачу.
        """Возвращает активную задачу режима или None."""
        return self._tasks.get(mode)  # Возвращаем поток из словаря.

    def subscribe(self, mode: str, widget: QWidget) -> None:  # Подписываем виджет.
        """Регистрирует виджет как подписчика задачи режима."""
        subscribers = self._subscribers.setdefault(mode, set())  # Берём набор.
        subscribers.add(widget)  # Добавляем виджет в подписчики режима.

    def unsubscribe(self, mode: str, widget: QWidget) -> None:  # Отписываем виджет.
        """Удаляет виджет из подписчиков задачи режима."""
        subscribers = self._subscribers.get(mode)  # Получаем подписчиков режима.
        if subscribers is None:  # Проверяем отсутствие подписчиков.
            return  # Нечего удалять.

        subscribers.discard(widget)  # Удаляем виджет без ошибки отсутствия.
        if not subscribers:  # Проверяем пустой набор подписчиков.
            self._subscribers.pop(mode, None)  # Удаляем пустую запись режима.

    def unsubscribe_widget(self, widget: QWidget) -> None:  # Отписываем от всех.
        """Удаляет виджет из подписок всех режимов."""
        modes = list(self._subscribers)  # Копируем ключи для безопасного обхода.
        for mode in modes:  # Проходим по режимам с подписчиками.
            self.unsubscribe(mode, widget)  # Отписываем виджет от режима.

    def get_subscribers(self, mode: str) -> tuple[QWidget, ...]:  # Читаем подписки.
        """Возвращает подписчиков режима как неизменяемый кортеж."""
        subscribers = self._subscribers.get(mode, set())  # Получаем набор.
        return tuple(subscribers)  # Возвращаем копию подписчиков.

    def _on_task_finished(self) -> None:  # Обрабатываем завершение потока.
        """Удаляет завершённую задачу из реестра."""
        sender = self.sender()  # Получаем поток-источник сигнала.
        if not isinstance(sender, QThread):  # Проверяем тип источника.
            return  # Игнорируем неизвестный источник.

        mode = sender.property("mode")  # Получаем режим из свойства потока.
        if not isinstance(mode, str):  # Проверяем корректность режима.
            return  # Игнорируем поток без режима.

        if self._tasks.get(mode) is sender:  # Проверяем актуальность записи.
            self._tasks.pop(mode, None)  # Удаляем завершённую задачу.
