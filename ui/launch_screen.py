"""Стартовый диалог выбора режима."""

from PyQt6.QtCore import pyqtSignal  # Импортируем сигнал PyQt.
from PyQt6.QtWidgets import QDialog  # Импортируем базовый класс диалога.

from config.app_config import AppConfig  # Импортируем конфигурацию приложения.
from ui.launch_screen_ui import Ui_launch_screen  # Импортируем форму.


class LaunchScreen(QDialog, Ui_launch_screen):  # Объявляем модальный диалог.
    """Диалог выбора первого режима проекта."""

    mode_selected = pyqtSignal(str)  # Создаём сигнал выбранного режима.

    def __init__(self, config: AppConfig) -> None:  # Принимаем конфигурацию.
        """Инициализирует диалог и подключает кнопки режимов."""
        super().__init__()  # Инициализируем QDialog и форму.
        self.config = config  # Сохраняем конфиг через dependency injection.
        self.selected_mode: str | None = None  # Храним выбранный режим.
        self.setupUi(self)  # Загружаем визуальную структуру из Qt Designer.
        self._setup_text()  # Обновляем динамический текст диалога.
        self._connect_signals()  # Подключаем кнопки к именованным слотам.

    def _setup_text(self) -> None:  # Настраиваем динамический текст.
        """Настраивает динамический текст диалога."""
        self.setWindowTitle(  # Устанавливаем заголовок диалога.
            f"{self.config.APP_NAME} v{self.config.APP_VERSION}"  # Текст.
        )  # Завершаем установку заголовка.

    def _connect_signals(self) -> None:  # Подключаем сигналы кнопок.
        """Подключает кнопки формы к слотам выбора режима."""
        self.btn_training.clicked.connect(self._on_training_clicked)  # Training.
        self.btn_testing.clicked.connect(self._on_testing_clicked)  # Testing.
        self.btn_synthetic.clicked.connect(self._on_synthetic_clicked)  # Synthetic.
        self.btn_processing.clicked.connect(self._on_processing_clicked)  # Processing.

    def _on_training_clicked(self) -> None:  # Обрабатываем выбор обучения.
        """Выбирает режим обучения."""
        self._select_mode("training")  # Передаём код режима.

    def _on_testing_clicked(self) -> None:  # Обрабатываем выбор тестов.
        """Выбирает режим тестирования."""
        self._select_mode("testing")  # Передаём код режима.

    def _on_synthetic_clicked(self) -> None:  # Обрабатываем выбор синтетики.
        """Выбирает режим синтетики."""
        self._select_mode("synthetic")  # Передаём код режима.

    def _on_processing_clicked(self) -> None:  # Обрабатываем выбор обработки.
        """Выбирает режим обработки."""
        self._select_mode("processing")  # Передаём код режима.

    def _select_mode(self, mode: str) -> None:  # Завершаем выбор режима.
        """Сохраняет режим, отправляет сигнал и закрывает диалог."""
        self.selected_mode = mode  # Сохраняем выбранный режим.
        self.mode_selected.emit(mode)  # Сообщаем выбранный режим наружу.
        self.accept()  # Закрываем диалог с успешным результатом.
