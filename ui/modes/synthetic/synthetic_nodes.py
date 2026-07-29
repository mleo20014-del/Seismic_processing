"""Ноды NodeGraphQt для режима синтетических данных."""

from __future__ import annotations  # Включаем отложенную обработку типов.

import time  # Импортируем sleep для FDTD-заглушки.
from pathlib import Path  # Импортируем Path для путей memmap.
from typing import Any  # Импортируем Any для временных структур.
from uuid import uuid4  # Импортируем uuid для уникальных файлов memmap.

import numpy as np  # Импортируем NumPy для массивов и memmap.
from NodeGraphQt import BaseNode  # Импортируем базовый класс ноды.
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot  # Qt-потоки.

from app.cache_manager import SyntheticCacheManager  # Менеджер memmap-кэша.
from app.node_context import get_context  # Импортируем общий контекст нод.
from config.app_config import AppConfig  # Импортируем централизованные пути.
from core.synthetic.geo_stub import GeologicalModel, create_stub_model  # Геология.


STATUS_COLORS: dict[str, tuple[int, int, int]] = {  # Цвета состояний нод.
    "idle": (80, 80, 80),  # Серый цвет ожидания.
    "editing": (180, 140, 20),  # Жёлтый цвет редактирования.
    "ready": (40, 130, 60),  # Зелёный цвет готовности.
    "computing": (30, 100, 200),  # Синий цвет вычисления.
    "error": (180, 40, 40),  # Красный цвет ошибки.
}  # Завершаем словарь цветов.


class WaveletParams(dict[str, Any]):  # Словарь параметров импульса.
    """Хранит параметры импульса как словарь-заглушку."""


class NodeSignalBridge(QObject):  # QObject-мост сигналов в главный поток.
    """Передаёт сигналы worker в поток, где создана нода."""

    result_ready = pyqtSignal(object)  # Сигнал готового результата.
    error_occurred = pyqtSignal(str)  # Сигнал ошибки.

    @pyqtSlot(object)  # Принимаем результат из worker-потока.
    def forward_result(self, result: object) -> None:  # Пересылаем результат.
        """Передаёт результат дальше уже через QObject главного потока."""
        self.result_ready.emit(result)  # Отправляем результат подписчику.

    @pyqtSlot(str)  # Принимаем ошибку из worker-потока.
    def forward_error(self, message: str) -> None:  # Пересылаем ошибку.
        """Передаёт ошибку дальше уже через QObject главного потока."""
        self.error_occurred.emit(message)  # Отправляем текст ошибки.


class StatusNode(BaseNode):  # Общая базовая нода проекта.
    """Базовая нода с общей цветовой индикацией статуса."""

    __identifier__ = "deghost.synthetic"  # Общий namespace нод синтетики.

    def __init__(self) -> None:  # Инициализируем базовую ноду.
        """Инициализирует базовую ноду и ставит статус ожидания."""
        super().__init__()  # Инициализируем BaseNode.
        self._status: str = "idle"  # Храним строковый статус ноды.
        self._cache_manager: SyntheticCacheManager | None = None  # Кэш.
        self._cache_paths: set[Path] = set()  # Файлы, созданные этой нодой.
        self.set_status("idle")  # Ставим начальный статус.

    def set_status(self, status: str) -> None:  # Меняем состояние ноды.
        """Меняет цвет ноды по строковому статусу."""
        self._status = status  # Сохраняем статус для программной логики.
        color = STATUS_COLORS.get(status, (80, 80, 80))  # Берём цвет.
        self.set_color(*color)  # Применяем цвет через NodeGraphQt.

    def get_status(self) -> str:  # Возвращаем строковый статус.
        """Возвращает текущий строковый статус ноды."""
        return self._status  # Возвращаем сохранённое состояние.

    def set_cache_manager(self, cache_manager: SyntheticCacheManager) -> None:
        """Подключает менеджер временных memmap-файлов."""
        self._cache_manager = cache_manager  # Сохраняем менеджер кэша.

    def _register_cache_path(self, path: Path) -> None:  # Регистрируем файл.
        """Регистрирует memmap-файл, созданный этой нодой."""
        if self._cache_manager is None:  # Проверяем наличие менеджера.
            return  # Без менеджера регистрация невозможна.

        self._cache_manager.register(path)  # Регистрируем файл в общем кэше.
        self._cache_paths.add(path)  # Запоминаем файл за текущей нодой.

    def _release_cache_paths(self) -> None:  # Освобождаем файлы ноды.
        """Удаляет старые memmap-файлы этой ноды перед пересчётом."""
        if self._cache_manager is None:  # Проверяем наличие менеджера.
            self._cache_paths.clear()  # Сбрасываем локальные пути.
            return  # Выходим без удаления.

        for path in list(self._cache_paths):  # Копируем пути для обхода.
            self._cache_manager.release(path)  # Удаляем файл через менеджер.
        self._cache_paths.clear()  # Очищаем локальный набор.


class GeologyWorker(QObject):  # Worker для геологической модели.
    """Создаёт геологическую модель в отдельном потоке."""

    finished = pyqtSignal(object)  # Сигнал успешного завершения.
    failed = pyqtSignal(str)  # Сигнал ошибки с текстом.

    @pyqtSlot()  # Делаем метод Qt-слотом.
    def run(self) -> None:  # Запускаем работу worker.
        """Создаёт geo_stub и переводит тяжёлые массивы в memmap."""
        try:  # Перехватываем ошибки worker.
            nx, ny, nz = AppConfig.SYNTHETIC_GEO_STUB_SHAPE  # Размер stub.
            model = create_stub_model(  # Создаём memmap-модель напрямую.
                nx=nx,  # Передаём размер X.
                ny=ny,  # Передаём размер Y.
                nz=nz,  # Передаём размер Z.
                memmap_dir=AppConfig.SYNTHETIC_MEMMAP_DIR,  # Папка memmap.
            )  # Завершаем создание geo_stub.
            self.finished.emit(model)  # Отправляем готовую модель.
        except Exception as error:  # Обрабатываем любые сбои.
            self.failed.emit(str(error))  # Передаём текст ошибки.


class FDTDWorker(QObject):  # Worker для FDTD-заглушки.
    """Имитирует FDTD-расчёт в отдельном потоке."""

    finished = pyqtSignal(object)  # Сигнал успешного завершения.
    failed = pyqtSignal(str)  # Сигнал ошибки с текстом.

    @pyqtSlot()  # Делаем метод Qt-слотом.
    def run(self) -> None:  # Запускаем worker.
        """Ждёт три секунды и создаёт memmap-заглушку результата."""
        try:  # Перехватываем ошибки расчёта.
            time.sleep(AppConfig.SYNTHETIC_FDTD_STUB_DELAY_SEC)  # Имитируем работу.
            result = self._create_result_memmap()  # Создаём результат.
            self.finished.emit(result)  # Передаём результат наружу.
        except Exception as error:  # Обрабатываем сбой.
            self.failed.emit(str(error))  # Передаём текст ошибки.

    def _create_result_memmap(self) -> np.memmap:  # Создаём результат.
        """Создаёт небольшой memmap-массив синтетического результата."""
        memmap_dir = AppConfig.SYNTHETIC_MEMMAP_DIR  # Папка memmap.
        memmap_dir.mkdir(parents=True, exist_ok=True)  # Создаём папку.

        path = memmap_dir / f"synthetic_result_{uuid4().hex}.dat"  # Путь файла.
        result = np.memmap(  # Создаём memmap результата.
            path,  # Передаём путь файла.
            dtype=np.float32,  # Задаём тип float32.
            mode="w+",  # Открываем файл на запись и чтение.
            shape=AppConfig.SYNTHETIC_RESULT_SHAPE,  # Задаём форму результата.
        )  # Завершаем создание memmap.
        result[:] = 0.0  # Заполняем результат нулями.
        result.flush()  # Сбрасываем данные на диск.
        return result  # Возвращаем memmap-результат.


class WaveletNode(StatusNode):  # Нода импульса.
    """Создаёт параметры импульса для синтетического расчёта."""

    __identifier__ = "deghost.synthetic"  # Namespace ноды.
    NODE_NAME = "Импульс"  # Видимое имя ноды.

    def __init__(self) -> None:  # Инициализируем ноду.
        """Инициализирует ноду импульса и её свойства."""
        super().__init__()  # Инициализируем StatusNode.
        self.add_output("wavelet")  # Добавляем выход импульса.
        self.create_property(  # Создаём свойство типа импульса.
            "wavelet_type",  # Имя свойства.
            "ricker",  # Значение по умолчанию.
            items=["ricker", "ormsby", "klauder"],  # Варианты выбора.
        )  # Завершаем создание свойства.
        self.create_property(  # Создаём частоту импульса.
            "frequency_hz",  # Имя свойства частоты.
            AppConfig.DEFAULT_WAVELET_FREQUENCY_HZ,  # Значение из конфига.
        )  # Завершаем создание частоты.

    def process(self) -> None:  # Выполняем ноду.
        """Создаёт заглушку параметров импульса в NodeContext."""
        self.set_status("editing")  # Показываем редактирование.
        wavelet = WaveletParams(  # Формируем параметры импульса.
            wavelet_type=self.get_property("wavelet_type"),  # Тип импульса.
            frequency_hz=self.get_property("frequency_hz"),  # Частота.
        )  # Завершаем параметры импульса.
        get_context().wavelet = wavelet  # Сохраняем импульс в контекст.
        self.set_status("ready")  # Показываем готовность.


class GeologyNode(StatusNode):  # Нода геологической модели.
    """Создаёт геологическую модель через QThread."""

    __identifier__ = "deghost.synthetic"  # Namespace ноды.
    NODE_NAME = "Геологическая модель"  # Видимое имя ноды.

    def __init__(self) -> None:  # Инициализируем ноду.
        """Инициализирует ноду геологической модели."""
        super().__init__()  # Инициализируем StatusNode.
        self.add_output("geology")  # Добавляем выход геологии.
        self._thread: QThread | None = None  # Храним поток worker.
        self._worker: GeologyWorker | None = None  # Храним worker.
        self._signals = NodeSignalBridge()  # Храним мост сигналов в GUI-поток.
        self._signals.result_ready.connect(self._on_finished)  # Результат.
        self._signals.error_occurred.connect(self._on_failed)  # Ошибка.

    def process(self) -> None:  # Выполняем ноду.
        """Запускает создание geo_stub в фоновом потоке."""
        if self._thread is not None and self._thread.isRunning():  # Уже работает.
            return  # Не запускаем второй поток.

        self.set_status("computing")  # Показываем вычисление.
        self._thread = QThread()  # Создаём поток.
        self._worker = GeologyWorker()  # Создаём worker.
        self._worker.moveToThread(self._thread)  # Переносим worker в поток.
        self._thread.started.connect(self._worker.run)  # Стартует worker.
        self._worker.finished.connect(self._signals.forward_result)  # Результат.
        self._worker.failed.connect(self._signals.forward_error)  # Ошибка worker.
        self._worker.finished.connect(self._worker.deleteLater)  # Удаляем worker.
        self._worker.failed.connect(self._worker.deleteLater)  # Удаляем при ошибке.
        self._worker.finished.connect(self._thread.quit)  # Останавливаем поток.
        self._worker.failed.connect(self._thread.quit)  # Останавливаем при ошибке.
        self._thread.finished.connect(self._cleanup_worker)  # Чистим ссылки.
        self._thread.finished.connect(self._thread.deleteLater)  # Удаляем поток.
        self._thread.start()  # Запускаем поток.

    def _on_finished(self, model: GeologicalModel) -> None:  # Успешное завершение.
        """Сохраняет memmap-модель в общий контекст."""
        self._release_cache_paths()  # Удаляем старые файлы этой ноды.
        self._register_cache_path(model.velocity_path)  # Регистрируем скорость.
        self._register_cache_path(model.density_path)  # Регистрируем плотность.
        get_context().geology = model  # Сохраняем геологию в контекст.
        self.set_status("ready")  # Показываем готовность.

    def _on_failed(self, message: str) -> None:  # Ошибка worker.
        """Переводит ноду в ошибку при сбое worker."""
        print(f"Ошибка геологической модели: {message}")  # Пишем диагностику.
        self.set_status("error")  # Показываем ошибку.

    def _cleanup_worker(self) -> None:  # Чистим ссылки после потока.
        """Освобождает ссылки на завершённый поток и worker."""
        self._worker = None  # Убираем ссылку на worker.
        self._thread = None  # Убираем ссылку на поток.


class AcquisitionNode(StatusNode):  # Нода схемы наблюдения.
    """Создаёт параметры схемы наблюдения."""

    __identifier__ = "deghost.synthetic"  # Namespace ноды.
    NODE_NAME = "Съёмка"  # Видимое имя ноды.

    def __init__(self) -> None:  # Инициализируем ноду.
        """Инициализирует ноду съёмки и её свойства."""
        super().__init__()  # Инициализируем StatusNode.
        self.add_output("geometry")  # Добавляем выход геометрии.
        self.create_property("n_shots", AppConfig.DEFAULT_ACQUISITION_SHOTS)  # Источники.
        self.create_property(  # Создаём число приёмников.
            "n_receivers",  # Имя свойства приёмников.
            AppConfig.DEFAULT_ACQUISITION_RECEIVERS,  # Значение из конфига.
        )  # Завершаем создание свойства.

    def process(self) -> None:  # Выполняем ноду.
        """Создаёт геометрию съёмки в NodeContext."""
        self.set_status("editing")  # Показываем редактирование.
        n_shots = int(self.get_property("n_shots"))  # Читаем число источников.
        n_receivers = int(self.get_property("n_receivers"))  # Читаем приёмники.
        geometry = {  # Создаём словарь геометрии.
            "shots": np.arange(n_shots, dtype=np.float32),  # Координаты источников.
            "receivers": np.arange(n_receivers, dtype=np.float32),  # Приёмники.
        }  # Завершаем геометрию.
        get_context().geometry = geometry  # Сохраняем геометрию в контекст.
        self.set_status("ready")  # Показываем готовность.


class FDTDNode(StatusNode):  # Нода синтетического расчёта.
    """Создаёт синтетический результат после проверки входных данных."""

    __identifier__ = "deghost.synthetic"  # Namespace ноды.
    NODE_NAME = "FDTD"  # Видимое имя ноды.

    def __init__(self) -> None:  # Инициализируем ноду.
        """Инициализирует FDTD-ноду с тремя входами и одним выходом."""
        super().__init__()  # Инициализируем StatusNode.
        self.add_input("wavelet")  # Добавляем вход импульса.
        self.add_input("geology")  # Добавляем вход геологии.
        self.add_input("geometry")  # Добавляем вход геометрии.
        self.add_output("synthetic")  # Добавляем выход синтетики.
        self._thread: QThread | None = None  # Храним поток worker.
        self._worker: FDTDWorker | None = None  # Храним worker.
        self._signals = NodeSignalBridge()  # Храним мост сигналов в GUI-поток.
        self._signals.result_ready.connect(self._on_finished)  # Результат.
        self._signals.error_occurred.connect(self._on_failed)  # Ошибка.

    def process(self) -> None:  # Выполняем ноду.
        """Проверяет NodeContext и запускает расчёт-заглушку."""
        context = get_context()  # Получаем общий контекст.
        inputs_ready = (  # Проверяем готовность данных в контексте.
            context.wavelet is not None  # Проверяем импульс.
            and context.geology is not None  # Проверяем геологию.
            and context.geometry is not None  # Проверяем геометрию.
        )  # Завершаем проверку входов.
        if not inputs_ready:  # Проверяем готовность входов.
            self.set_status("error")  # Показываем ошибку входов.
            return  # Останавливаем выполнение.

        if self._thread is not None and self._thread.isRunning():  # Уже работает.
            return  # Не запускаем второй поток.

        self.set_status("computing")  # Показываем вычисление.
        self._thread = QThread()  # Создаём поток.
        self._worker = FDTDWorker()  # Создаём worker.
        self._worker.moveToThread(self._thread)  # Переносим worker в поток.
        self._thread.started.connect(self._worker.run)  # Стартует worker.
        self._worker.finished.connect(self._signals.forward_result)  # Результат.
        self._worker.failed.connect(self._signals.forward_error)  # Ошибка worker.
        self._worker.finished.connect(self._worker.deleteLater)  # Удаляем worker.
        self._worker.failed.connect(self._worker.deleteLater)  # Удаляем при ошибке.
        self._worker.finished.connect(self._thread.quit)  # Останавливаем поток.
        self._worker.failed.connect(self._thread.quit)  # Останавливаем при ошибке.
        self._thread.finished.connect(self._cleanup_worker)  # Чистим ссылки.
        self._thread.finished.connect(self._thread.deleteLater)  # Удаляем поток.
        self._thread.start()  # Запускаем поток.

    def _on_finished(self, result: np.ndarray) -> None:  # Успешное завершение.
        """Сохраняет результат расчёта в общий контекст."""
        self._release_cache_paths()  # Удаляем старые файлы этой ноды.
        if isinstance(result, np.memmap):  # Проверяем memmap-результат.
            self._register_cache_path(Path(result.filename))  # Регистрируем файл.
        get_context().synthetic_result = result  # Сохраняем результат.
        self.set_status("ready")  # Показываем готовность.

    def _on_failed(self, message: str) -> None:  # Ошибка worker.
        """Переводит ноду в ошибку при сбое расчёта."""
        print(f"Ошибка FDTD: {message}")  # Пишем диагностику.
        self.set_status("error")  # Показываем ошибку.

    def _cleanup_worker(self) -> None:  # Чистим ссылки после потока.
        """Освобождает ссылки на завершённый поток и worker."""
        self._worker = None  # Убираем ссылку на worker.
        self._thread = None  # Убираем ссылку на поток.


class OutputNode(StatusNode):  # Выходная нода.
    """Проверяет готовность результата к сохранению."""

    __identifier__ = "deghost.synthetic"  # Namespace ноды.
    NODE_NAME = "Выход"  # Видимое имя ноды.

    def __init__(self) -> None:  # Инициализируем ноду.
        """Инициализирует выходную ноду и свойства сохранения."""
        super().__init__()  # Инициализируем StatusNode.
        self.add_input("synthetic")  # Добавляем вход синтетики.
        self.create_property("format", "hdf5", items=["hdf5", "segy", "npy"])  # Формат.
        self.create_property("path", str(AppConfig.SYNTHETIC_OUTPUT_DIR))  # Путь.

    def process(self) -> None:  # Выполняем ноду.
        """Проверяет наличие результата синтетики в NodeContext."""
        if get_context().synthetic_result is None:  # Проверяем результат.
            self.set_status("error")  # Показываем ошибку.
            return  # Останавливаем выполнение.

        self.set_status("ready")  # Показываем готовность.
