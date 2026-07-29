"""Общее хранилище данных для нод синтетического графа."""

from __future__ import annotations  # Включаем отложенную обработку типов.

from dataclasses import dataclass  # Импортируем dataclass для контейнера.
from typing import Any  # Импортируем Any для временных объектов нод.

import numpy as np  # Импортируем NumPy для типа результата синтетики.


@dataclass  # Автоматически создаём init и хранение полей.
class NodeContext:  # Объявляем общий контекст данных графа.
    """Хранит результаты работы нод без передачи тяжёлых данных через порты."""

    wavelet: Any | None = None  # Храним параметры импульса.
    geology: Any | None = None  # Храним геологическую модель.
    geometry: Any | None = None  # Храним геометрию съёмки.
    synthetic_result: np.ndarray | None = None  # Храним результат синтетики.


_instance: NodeContext | None = None  # Храним единственный экземпляр контекста.


def get_context() -> NodeContext:  # Возвращаем общий контекст нод.
    """Возвращает единый контекст данных для всех нод графа."""
    global _instance  # Разрешаем создание singleton в модуле.
    if _instance is None:  # Проверяем, создан ли контекст.
        _instance = NodeContext()  # Создаём контекст при первом обращении.
    return _instance  # Возвращаем общий экземпляр.
