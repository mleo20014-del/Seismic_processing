"""Viewer NodeGraphQt с панорамированием через левую кнопку мыши."""

from __future__ import annotations  # Включаем отложенную обработку типов.

from NodeGraphQt.widgets.viewer import NodeViewer  # Импортируем viewer графа.
from qtpy import QtCore  # Используем тот же Qt-слой, что и NodeGraphQt.


class SyntheticNodeViewer(NodeViewer):  # Объявляем viewer режима синтетики.
    """Переназначает панорамирование пустой области на зажатую ЛКМ."""

    def __init__(self) -> None:  # Инициализируем viewer.
        """Создаёт viewer и состояние пользовательского панорамирования."""
        super().__init__()  # Инициализируем стандартный NodeViewer.
        self._left_pan_active: bool = False  # Храним флаг панорамирования.

    def mousePressEvent(self, event) -> None:  # Обрабатываем нажатие мыши.
        """Запускает панорамирование ЛКМ при клике по пустому месту."""
        if self._should_start_left_pan(event):  # Проверяем старт панорамирования.
            self._left_pan_active = True  # Включаем режим панорамирования.
            self._origin_pos = event.pos()  # Запоминаем начальную позицию.
            self._previous_pos = event.pos()  # Запоминаем предыдущую позицию.
            self.LMB_state = False  # Не даём включить rubber-band selection.
            self.MMB_state = False  # Не используем старый режим средней кнопки.
            self._rubber_band.isActive = False  # Гасим прямоугольник выбора.
            event.accept()  # Сообщаем Qt, что событие обработано.
            return  # Не вызываем падающую стандартную ветку.

        super().mousePressEvent(event)  # Передаём остальные клики NodeGraphQt.

    def mouseMoveEvent(self, event) -> None:  # Обрабатываем движение мыши.
        """Двигает область построения при активном панорамировании ЛКМ."""
        if self._left_pan_active:  # Проверяем режим панорамирования.
            previous_pos = self.mapToScene(self._previous_pos)  # Старая точка.
            current_pos = self.mapToScene(event.pos())  # Текущая точка.
            delta = previous_pos - current_pos  # Считаем сдвиг сцены.
            self._set_viewer_pan(delta.x(), delta.y())  # Сдвигаем область.
            self._previous_pos = event.pos()  # Обновляем предыдущую позицию.
            event.accept()  # Сообщаем Qt, что событие обработано.
            return  # Не запускаем rubber-band selection.

        super().mouseMoveEvent(event)  # Остальные движения отдаём NodeGraphQt.

    def mouseReleaseEvent(self, event) -> None:  # Обрабатываем отпускание мыши.
        """Завершает панорамирование ЛКМ."""
        if self._left_pan_active and event.button() == QtCore.Qt.LeftButton:
            self._left_pan_active = False  # Выключаем панорамирование.
            self.LMB_state = False  # Сбрасываем состояние ЛКМ.
            event.accept()  # Сообщаем Qt, что событие обработано.
            return  # Не вызываем стандартный release для rubber-band.

        super().mouseReleaseEvent(event)  # Остальные отпускания отдаём NodeGraphQt.

    def _should_start_left_pan(self, event) -> bool:  # Проверяем старт pan.
        """Возвращает True, если ЛКМ нажата по пустой области графа."""
        if event.button() != QtCore.Qt.LeftButton:  # Проверяем кнопку мыши.
            return False  # Панорамирование только через ЛКМ.

        if self._has_modifier(event):  # Проверяем служебные модификаторы.
            return False  # Не ломаем Shift/Ctrl/Alt сценарии NodeGraphQt.

        scene_pos = self.mapToScene(event.pos())  # Переводим позицию в сцену.
        items = self._items_near(scene_pos, None, 6, 6)  # Ищем объекты рядом.
        return not items  # Панорамируем только по пустой области.

    def _has_modifier(self, event) -> bool:  # Проверяем клавиши-модификаторы.
        """Возвращает True, если нажаты Shift, Ctrl или Alt."""
        modifiers = event.modifiers()  # Читаем модификаторы события.
        return bool(  # Возвращаем наличие любого служебного модификатора.
            modifiers & QtCore.Qt.ShiftModifier  # Проверяем Shift.
            or modifiers & QtCore.Qt.ControlModifier  # Проверяем Ctrl.
            or modifiers & QtCore.Qt.AltModifier  # Проверяем Alt.
        )  # Завершаем проверку модификаторов.
