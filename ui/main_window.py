"""Главное окно приложения."""

from PyQt6.QtCore import Qt, QTimer  # Импортируем Qt и таймер запуска.
from PyQt6.QtWidgets import QMainWindow, QMessageBox  # Импортируем базовые окна.

from app.app_controller import AppController  # Импортируем контроллер режимов.
from app.task_manager import TaskManager  # Импортируем менеджер фоновых задач.
from config.app_config import AppConfig  # Импортируем конфигурацию приложения.
from ui.forms.main_window_ui import Ui_MainWindow  # Импортируем форму окна.
from ui.launch_screen import LaunchScreen  # Импортируем стартовый диалог.
from ui.widgets.mode_tab_bar import ModeTabBar  # Импортируем вкладки режимов.


class MainWindow(QMainWindow, Ui_MainWindow):  # Объявляем главное окно.
    """Главное окно с пустым стеком режимов и панелью вкладок."""

    def __init__(self, config: AppConfig) -> None:  # Принимаем конфиг.
        """Инициализирует главное окно и проверяет сценарий запуска."""
        super().__init__()  # Инициализируем QMainWindow и форму.
        self.config = config  # Сохраняем конфиг через dependency injection.
        self.setupUi(self)  # Загружаем визуальную структуру из Qt Designer.
        self.task_manager = TaskManager(self.config)  # Создаём менеджер задач.
        self.controller = AppController(  # Создаём контроллер режимов.
            self.config,  # Передаём конфигурацию приложения.
            self.task_manager,  # Передаём владельца фоновых задач.
        )  # Завершаем создание контроллера.
        self.mode_tab_bar = ModeTabBar()  # Создаём динамический виджет вкладок.
        self._setup_window()  # Настраиваем динамический текст окна.
        self._setup_mode_tabs()  # Вставляем вкладки в контейнер формы.
        self._connect_signals()  # Подключаем сигналы навигации.
        self._schedule_launch_screen()  # Планируем показ стартового диалога.

    def switch_to_mode(self, mode: str) -> None:  # Переключаемся на режим.
        """Открывает режим, добавляет его в стек и активирует вкладку."""
        widget = self.controller.open_mode(mode)  # Получаем виджет режима.
        if self.stackedWidget.indexOf(widget) == -1:  # Проверяем наличие в стеке.
            self.stackedWidget.addWidget(widget)  # Добавляем виджет режима.

        self.stackedWidget.setCurrentWidget(widget)  # Показываем выбранный режим.
        self.mode_tab_bar.add_tab(mode)  # Добавляем вкладку режима.
        self.mode_tab_bar.set_active(mode)  # Выделяем активную вкладку.

    def close_mode(self, mode: str) -> None:  # Закрываем вкладку режима.
        """Закрывает вкладку режима без остановки фоновых задач."""
        if self.controller.has_unsaved_changes(mode):  # Проверяем изменения.
            if not self._confirm_close_mode(mode):  # Спрашиваем подтверждение.
                return  # Отменяем закрытие вкладки.

        widget = self.controller.get_mode_widget(mode)  # Получаем виджет режима.
        if widget is not None:  # Проверяем наличие виджета.
            self.stackedWidget.removeWidget(widget)  # Удаляем виджет из стека.

        self.controller.close_mode(mode)  # Удаляем режим из контроллера.
        self.mode_tab_bar.remove_tab(mode)  # Удаляем вкладку режима.

    def _setup_window(self) -> None:  # Настраиваем окно.
        """Настраивает динамические параметры главного окна."""
        self.setWindowTitle(  # Устанавливаем заголовок окна.
            f"{self.config.APP_NAME} v{self.config.APP_VERSION}"  # Текст.
        )  # Завершаем установку заголовка.
        self.label_server_status.setText("Сервер: —")  # Обновляем статус.

    def _setup_mode_tabs(self) -> None:  # Настраиваем контейнер вкладок.
        """Добавляет ModeTabBar в контейнер, созданный в Qt Designer."""
        self.horizontalLayout_3.setAlignment(  # Задаём выравнивание контейнера.
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop  # Вправо вверх.
        )  # Завершаем настройку выравнивания.
        self.horizontalLayout_3.addWidget(  # Вставляем вкладки в layout.
            self.mode_tab_bar,  # Передаём виджет вкладок.
            0,  # Не задаём дополнительный stretch.
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,  # Вправо вверх.
        )  # Завершаем добавление виджета вкладок.

    def _connect_signals(self) -> None:  # Подключаем сигналы интерфейса.
        """Подключает сигналы вкладок к навигации."""
        self.mode_tab_bar.tab_clicked.connect(self.switch_to_mode)  # Клик вкладки.
        self.mode_tab_bar.tab_closed.connect(self.close_mode)  # Закрытие вкладки.

    def _schedule_launch_screen(self) -> None:  # Планируем стартовый диалог.
        """Планирует показ LaunchScreen после появления MainWindow."""
        QTimer.singleShot(0, self._show_launch_screen)  # Открываем после show().

    def _show_launch_screen(self) -> None:  # Показываем LaunchScreen.
        """Показывает модальный диалог выбора режима."""
        dialog = LaunchScreen(self.config)  # Создаём диалог выбора режима.
        dialog.exec()  # Показываем диалог модально.
        if dialog.selected_mode is not None:  # Проверяем выбранный режим.
            self.switch_to_mode(dialog.selected_mode)  # Открываем режим.

    def _confirm_close_mode(self, mode: str) -> bool:  # Подтверждаем закрытие.
        """Возвращает True, если пользователь подтвердил закрытие режима."""
        result = QMessageBox.question(  # Показываем диалог подтверждения.
            self,  # Указываем главное окно родителем.
            "Закрыть режим",  # Задаём заголовок диалога.
            f"Закрыть режим {mode}?",  # Задаём текст вопроса.
        )  # Получаем результат диалога.
        return result == QMessageBox.StandardButton.Yes  # Возвращаем решение.
