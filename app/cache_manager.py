"""Менеджер временных memmap-файлов синтетики."""

from pathlib import Path  # Импортируем Path для работы с путями.


class SyntheticCacheManager:  # Объявляем владельца временного кэша.
    """Управляет жизненным циклом временных memmap файлов."""

    def __init__(self, cache_dir: Path) -> None:  # Принимаем папку кэша.
        """Инициализирует директорию кэша и набор активных файлов."""
        self._dir = cache_dir  # Сохраняем директорию кэша.
        self._dir.mkdir(parents=True, exist_ok=True)  # Создаём папку кэша.
        self._active: set[Path] = set()  # Храним активные memmap-файлы.

    def register(self, path: Path) -> None:  # Регистрируем активный файл.
        """Добавляет memmap-файл в список активных."""
        self._active.add(path)  # Запоминаем путь активного файла.

    def release(self, path: Path) -> None:  # Освобождаем один файл.
        """Удаляет активный memmap-файл при пересчёте или очистке."""
        if path in self._active:  # Проверяем, зарегистрирован ли файл.
            path.unlink(missing_ok=True)  # Удаляем файл с диска.
            self._active.discard(path)  # Убираем путь из активных.

    def cleanup_all(self) -> None:  # Очищаем все активные файлы.
        """Удаляет все зарегистрированные memmap-файлы."""
        for path in list(self._active):  # Копируем пути для безопасного обхода.
            self.release(path)  # Удаляем каждый активный файл.

    def cleanup_stale(self) -> None:  # Очищаем осиротевшие файлы.
        """Удаляет memmap-файлы из прошлых сессий."""
        for path in self._dir.glob("*.dat"):  # Ищем memmap-файлы.
            if path not in self._active:  # Проверяем, что файл не активен.
                path.unlink(missing_ok=True)  # Удаляем осиротевший файл.
