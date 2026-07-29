"""Интеграция NodeGraphQt в canvas режима синтетики."""

from __future__ import annotations  # Включаем отложенную обработку типов.

from typing import cast  # Импортируем cast для уточнения типа graph.widget.

from NodeGraphQt import BaseNode, NodeGraph  # Импортируем граф и базовую ноду.
from PyQt6.QtWidgets import QLayout, QWidget  # Импортируем типы Qt-виджетов.

from app.cache_manager import SyntheticCacheManager  # Менеджер memmap-кэша.
from ui.forms.node_edit_canvas_ui import Ui_node_canvas  # Форма canvas.
from ui.modes.synthetic.synthetic_nodes import (  # Импортируем классы нод.
    AcquisitionNode,  # Нода геометрии съёмки.
    FDTDNode,  # Нода расчёта синтетики.
    GeologyNode,  # Нода геологической модели.
    OutputNode,  # Нода выходного результата.
    WaveletNode,  # Нода импульса.
)
from ui.modes.synthetic.synthetic_viewer import SyntheticNodeViewer  # Viewer.


class SyntheticGraph:  # Объявляем интегратор NodeGraphQt.
    """Создаёт NodeGraphQt и встраивает его в готовый canvas."""

    def __init__(  # Принимаем зависимости графа.
        self,
        canvas: Ui_node_canvas,
        cache_manager: SyntheticCacheManager,
    ) -> None:
        """Инициализирует граф, ноды, связи и встраивание виджета."""
        self.canvas = canvas  # Сохраняем форму-контейнер.
        self.cache_manager = cache_manager  # Сохраняем менеджер memmap-кэша.
        self.graph = NodeGraph(viewer=SyntheticNodeViewer())  # Создаём граф.
        self.nodes: dict[str, BaseNode] = {}  # Храним созданные ноды по ключам.

        self._register_nodes()  # Регистрируем типы нод.
        self._create_nodes()  # Создаём экземпляры нод.
        self._attach_cache_manager()  # Передаём нодам менеджер кэша.
        self._connect_ports()  # Соединяем порты нод.
        self._embed_graph_widget()  # Встраиваем виджет графа в canvas.
        self.graph.node_double_clicked.connect(self._on_double_click)  # Двойной клик.

    def _register_nodes(self) -> None:  # Регистрируем классы в NodeGraphQt.
        """Регистрирует все ноды синтетического графа."""
        self.graph.register_node(WaveletNode)  # Регистрируем ноду импульса.
        self.graph.register_node(GeologyNode)  # Регистрируем ноду геологии.
        self.graph.register_node(AcquisitionNode)  # Регистрируем ноду съёмки.
        self.graph.register_node(FDTDNode)  # Регистрируем FDTD-ноду.
        self.graph.register_node(OutputNode)  # Регистрируем выходную ноду.

    def _create_nodes(self) -> None:  # Создаём и размещаем ноды.
        """Создаёт ноды и расставляет их на сцене."""
        self.nodes["wavelet"] = self.graph.create_node(  # Создаём ноду импульса.
            "deghost.synthetic.WaveletNode",  # Указываем тип ноды.
            name="Импульс",  # Задаём видимое имя.
            pos=(-300, -150),  # Размещаем слева сверху.
        )  # Сохраняем ноду импульса.
        self.nodes["geology"] = self.graph.create_node(  # Создаём ноду геологии.
            "deghost.synthetic.GeologyNode",  # Указываем тип ноды.
            name="Геологическая модель",  # Задаём видимое имя.
            pos=(0, -150),  # Размещаем сверху по центру.
        )  # Сохраняем ноду геологии.
        self.nodes["acquisition"] = self.graph.create_node(  # Создаём ноду съёмки.
            "deghost.synthetic.AcquisitionNode",  # Указываем тип ноды.
            name="Съёмка",  # Задаём видимое имя.
            pos=(300, -150),  # Размещаем справа сверху.
        )  # Сохраняем ноду съёмки.
        self.nodes["fdtd"] = self.graph.create_node(  # Создаём FDTD-ноду.
            "deghost.synthetic.FDTDNode",  # Указываем тип ноды.
            name="FDTD",  # Задаём видимое имя.
            pos=(0, 100),  # Размещаем ниже входных нод.
        )  # Сохраняем FDTD-ноду.
        self.nodes["output"] = self.graph.create_node(  # Создаём выходную ноду.
            "deghost.synthetic.OutputNode",  # Указываем тип ноды.
            name="Выход",  # Задаём видимое имя.
            pos=(0, 320),  # Размещаем внизу.
        )  # Сохраняем выходную ноду.

    def _attach_cache_manager(self) -> None:  # Назначаем кэш нодам.
        """Передаёт менеджер memmap-кэша созданным нодам."""
        for node in self.nodes.values():  # Проходим по всем нодам.
            if hasattr(node, "set_cache_manager"):  # Проверяем поддержку кэша.
                node.set_cache_manager(self.cache_manager)  # Передаём кэш.

    def _connect_ports(self) -> None:  # Соединяем цепочку данных.
        """Соединяет порты нод программно."""
        self._connect("wavelet", "wavelet", "fdtd", "wavelet")  # Импульс в FDTD.
        self._connect("geology", "geology", "fdtd", "geology")  # Геология в FDTD.
        self._connect("acquisition", "geometry", "fdtd", "geometry")  # Съёмка.
        self._connect("fdtd", "synthetic", "output", "synthetic")  # Результат.

    def _connect(
        self,
        source_node: str,
        source_port: str,
        target_node: str,
        target_port: str,
    ) -> None:  # Соединяем конкретную пару портов.
        """Соединяет один выходной порт с одним входным портом."""
        output_port = self.nodes[source_node].outputs()[source_port]  # Выход.
        input_port = self.nodes[target_node].inputs()[target_port]  # Вход.
        output_port.connect_to(input_port)  # Создаём связь между портами.

    def _embed_graph_widget(self) -> None:  # Встраиваем виджет графа.
        """Добавляет виджет графа в layout готового canvas."""
        layout = self._get_canvas_layout()  # Получаем layout canvas.
        self._remove_legacy_placeholder(layout)  # Убираем старый placeholder.
        graph_widget = cast(QWidget, self.graph.widget)  # Уточняем тип виджета.
        graph_widget.setObjectName("synthetic_node_graph")  # Задаём имя объекта.
        layout.addWidget(graph_widget)  # Добавляем NodeGraphQt в canvas.

    def _get_canvas_layout(self) -> QLayout:  # Ищем layout для графа.
        """Возвращает layout, в который нужно встроить NodeGraphQt."""
        layout = getattr(self.canvas, "verticalLayout", None)  # Берём layout формы.
        if isinstance(layout, QLayout):  # Проверяем тип layout.
            return layout  # Возвращаем найденный layout.

        raise RuntimeError("Canvas не содержит verticalLayout для NodeGraphQt")  # Ошибка.

    def _remove_legacy_placeholder(self, layout: QLayout) -> None:  # Чистим форму.
        """Удаляет старый placeholder, если он есть в форме."""
        placeholder = getattr(self.canvas, "node_canvas_synth", None)  # Ищем виджет.
        if not isinstance(placeholder, QWidget):  # Проверяем наличие placeholder.
            return  # Нечего удалять.

        layout.removeWidget(placeholder)  # Убираем placeholder из layout.
        placeholder.hide()  # Скрываем placeholder.
        placeholder.setParent(None)  # Отвязываем placeholder от родителя.

    def _on_double_click(self, node: BaseNode) -> None:  # Реагируем на двойной клик.
        """Обрабатывает двойной клик по ноде."""
        print(f"Открыть редактор: {node.name()}")  # Временно выводим имя ноды.
