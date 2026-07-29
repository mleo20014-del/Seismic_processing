"""Логический виджет canvas для режима синтетики."""

from PyQt6.QtWidgets import QWidget  # Импортируем базовый QWidget.

from app.cache_manager import SyntheticCacheManager  # Импортируем менеджер кэша.
from config.app_config import AppConfig  # Импортируем конфигурацию приложения.
from ui.forms.node_edit_canvas_ui import Ui_node_canvas  # Импортируем форму canvas.
from ui.modes.synthetic.synthetic_graph import SyntheticGraph  # Импортируем граф.


class NodeEditCanvas(QWidget, Ui_node_canvas):  # Виджет режима synthetic.
    """Показывает NodeGraphQt внутри формы node_edit_canvas."""

    def __init__(  # Принимаем зависимости canvas.
        self,
        config: AppConfig,
        cache_manager: SyntheticCacheManager,
    ) -> None:
        """Инициализирует canvas и подключает граф синтетических нод."""
        super().__init__()  # Инициализируем QWidget.
        self.config = config  # Сохраняем конфиг через dependency injection.
        self.cache_manager = cache_manager  # Сохраняем менеджер memmap-кэша.
        self.setupUi(self)  # Загружаем форму canvas из ui/forms.
        self.synthetic_graph = SyntheticGraph(  # Встраиваем NodeGraphQt.
            self,  # Передаём текущий canvas.
            self.cache_manager,  # Передаём менеджер кэша.
        )  # Завершаем создание графа.
