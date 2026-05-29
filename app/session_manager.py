"""Менеджер сохранённых проектов."""

from pathlib import Path  # Импортируем Path для путей проектов.

from config.app_config import AppConfig  # Импортируем конфигурацию приложения.


class SessionManager:  # Объявляем менеджер проектных сессий.
    """Проверяет наличие сохранённых проектов."""

    def __init__(self, config: AppConfig) -> None:  # Принимаем конфигурацию.
        """Инициализирует менеджер сессий."""
        self.config = config  # Сохраняем конфиг через dependency injection.

    def has_projects(self) -> bool:  # Проверяем наличие проектов.
        """Возвращает True, если есть сохранённые проекты."""
        return any(self.config.PROJECTS_DIR.glob("*.json"))  # Ищем JSON-проекты.

    def get_recent_projects(self) -> list[Path]:  # Получаем список проектов.
        """Возвращает последние проекты в пределах лимита."""
        projects = sorted(  # Сортируем проекты по времени изменения.
            self.config.PROJECTS_DIR.glob("*.json"),  # Берём JSON-файлы.
            key=self._get_modified_time,  # Используем метод получения mtime.
            reverse=True,  # Сначала самые новые проекты.
        )  # Завершаем сортировку проектов.
        return projects[: self.config.MAX_RECENT_PROJECTS]  # Ограничиваем список.

    def _get_modified_time(self, path: Path) -> float:  # Читаем mtime файла.
        """Возвращает время изменения файла проекта."""
        return path.stat().st_mtime  # Возвращаем timestamp изменения файла.
