"""Панель вкладок активных режимов."""

from PyQt6.QtCore import Qt, QObject, pyqtSignal  # Импортируем Qt и сигналы.
from PyQt6.QtWidgets import (  # Импортируем виджеты для панели вкладок.
    QHBoxLayout,  # Используем горизонтальное размещение вкладок.
    QToolButton,  # Используем QToolButton для вкладки и закрытия.
    QWidget,  # Используем QWidget как контейнер вкладки.
)  # Завершаем импорт виджетов.


class ModeTabBar(QWidget):  # Объявляем виджет панели вкладок.
    """Показывает активные режимы и отправляет сигналы вкладок."""

    tab_clicked = pyqtSignal(str)  # Сигнал клика по вкладке режима.
    tab_closed = pyqtSignal(str)  # Сигнал закрытия вкладки режима.

    def __init__(self) -> None:  # Инициализируем панель вкладок.
        """Создаёт пустую панель активных режимов."""
        super().__init__()  # Инициализируем QWidget.
        self._mode_titles = self._create_mode_titles()  # Создаём подписи режимов.
        self._tab_widgets: dict[str, QWidget] = {}  # Храним контейнеры вкладок.
        self._tab_buttons: dict[str, QToolButton] = {}  # Храним кнопки вкладок.
        self._close_buttons: dict[str, QToolButton] = {}  # Храним кнопки закрытия.
        self._active_mode: str | None = None  # Храним активный режим.
        self._layout = QHBoxLayout(self)  # Создаём горизонтальный layout.
        self._layout.setContentsMargins(0, 0, 0, 0)  # Убираем внешние отступы.
        self._layout.setSpacing(4)  # Задаём расстояние между вкладками.
        self._layout.setAlignment(  # Задаём выравнивание вкладок.
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop  # Вправо вверх.
        )  # Завершаем настройку выравнивания.

    def add_tab(self, mode: str) -> None:  # Добавляем вкладку режима.
        """Добавляет вкладку режима, если её ещё нет."""
        if mode in self._tab_widgets:  # Проверяем существование вкладки.
            self.set_active(mode)  # Активируем уже созданную вкладку.
            return  # Завершаем метод без дублирования.

        if len(self._tab_widgets) >= 4:  # Проверяем лимит активных режимов.
            raise RuntimeError("Открыто максимальное число режимов")  # Ошибка.

        tab_widget = QWidget(self)  # Создаём контейнер одной вкладки.
        tab_layout = QHBoxLayout(tab_widget)  # Создаём layout внутри вкладки.
        tab_layout.setContentsMargins(0, 0, 0, 0)  # Настраиваем отступы вкладки.
        tab_layout.setSpacing(4)  # Настраиваем расстояние внутри вкладки.
        tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Прижимаем вверх.

        tab_button = QToolButton(tab_widget)  # Создаём кнопку выбора вкладки.
        tab_button.setText(self._mode_titles[mode])  # Устанавливаем имя режима.
        tab_button.setCheckable(True)  # Разрешаем визуально отмечать вкладку.
        tab_button.setMinimumHeight(17)  # Задаём минимальную высоту кнопки.
        tab_button.setMaximumHeight(17)  # Задаём максимальную высоту кнопки.
        tab_button.setProperty("mode", mode)  # Сохраняем режим в свойстве.
        tab_button.clicked.connect(self._on_tab_clicked)  # Подключаем клик.

        close_button = QToolButton(tab_widget)  # Создаём кнопку закрытия.
        close_button.setText("×")  # Устанавливаем символ закрытия вкладки.
        close_button.setMinimumHeight(17)  # Задаём минимальную высоту кнопки.
        close_button.setMaximumHeight(17)  # Задаём максимальную высоту кнопки.
        close_button.setProperty("mode", mode)  # Сохраняем режим в свойстве.
        close_button.clicked.connect(self._on_close_clicked)  # Подключаем закрытие.

        tab_layout.addWidget(tab_button)  # Добавляем кнопку вкладки.
        tab_layout.addWidget(close_button)  # Добавляем кнопку закрытия.
        self._layout.addWidget(tab_widget)  # Добавляем вкладку на панель.

        self._tab_widgets[mode] = tab_widget  # Запоминаем контейнер вкладки.
        self._tab_buttons[mode] = tab_button  # Запоминаем кнопку вкладки.
        self._close_buttons[mode] = close_button  # Запоминаем кнопку закрытия.
        self.set_active(mode)  # Делаем добавленную вкладку активной.

    def remove_tab(self, mode: str) -> None:  # Удаляем вкладку режима.
        """Удаляет вкладку режима с панели."""
        tab_widget = self._tab_widgets.pop(mode, None)  # Забираем контейнер.
        self._tab_buttons.pop(mode, None)  # Удаляем кнопку вкладки.
        self._close_buttons.pop(mode, None)  # Удаляем кнопку закрытия.

        if tab_widget is not None:  # Проверяем наличие контейнера.
            self._layout.removeWidget(tab_widget)  # Убираем виджет из layout.
            tab_widget.deleteLater()  # Планируем безопасное удаление вкладки.

        if self._active_mode == mode:  # Проверяем удаление активной вкладки.
            self._active_mode = None  # Сбрасываем активный режим.

    def set_active(self, mode: str) -> None:  # Выделяем активную вкладку.
        """Выделяет активную вкладку режима."""
        self._active_mode = mode  # Сохраняем активный режим.

        for tab_mode, button in self._tab_buttons.items():  # Обходим кнопки.
            is_active = tab_mode == mode  # Проверяем активность вкладки.
            button.setChecked(is_active)  # Записываем состояние кнопки.
            button.setStyleSheet(self._get_button_style(is_active))  # Ставим стиль.

    def _on_tab_clicked(self, checked: bool = False) -> None:  # Обрабатываем клик.
        """Отправляет сигнал выбранной вкладки."""
        _ = checked  # Явно игнорируем флаг checkable-кнопки.
        sender = self.sender()  # Получаем объект-источник сигнала.
        mode = self._get_mode_from_sender(sender)  # Извлекаем режим из sender.
        self.tab_clicked.emit(mode)  # Отправляем сигнал выбора вкладки.

    def _on_close_clicked(self, checked: bool = False) -> None:  # Закрываем.
        """Отправляет сигнал закрытия вкладки."""
        _ = checked  # Явно игнорируем флаг checkable-кнопки.
        sender = self.sender()  # Получаем объект-источник сигнала.
        mode = self._get_mode_from_sender(sender)  # Извлекаем режим из sender.
        self.tab_closed.emit(mode)  # Отправляем сигнал закрытия вкладки.

    def _get_mode_from_sender(self, sender: QObject | None) -> str:  # Читаем режим.
        """Возвращает режим из свойства объекта-источника сигнала."""
        if sender is None:  # Проверяем отсутствие источника сигнала.
            raise RuntimeError("Не найден источник сигнала вкладки")  # Ошибка.

        mode = sender.property("mode")  # Получаем свойство режима.
        if not isinstance(mode, str):  # Проверяем тип свойства режима.
            raise RuntimeError("Некорректный режим вкладки")  # Ошибка.

        return mode  # Возвращаем строковый код режима.

    def _get_button_style(self, is_active: bool) -> str:  # Формируем стиль.
        """Возвращает стиль кнопки вкладки."""
        if is_active:  # Проверяем активное состояние.
            return "font-weight: 600; background: #e3d4c2;"  # Активный стиль.

        return "background: #f4f1ec;"  # Обычный стиль вкладки.

    def _create_mode_titles(self) -> dict[str, str]:  # Создаём подписи.
        """Возвращает русские названия режимов."""
        return {  # Возвращаем словарь подписей.
            "training": "Обучение",  # Подпись режима обучения.
            "processing": "Обработка",  # Подпись режима обработки.
            "synthetic": "Синтетика",  # Подпись режима синтетики.
            "testing": "Тесты",  # Подпись режима тестирования.
        }  # Завершаем словарь подписей.
