"""Конфигурация приложения и централизованные пути."""

from pathlib import Path  # Импортируем Path для кроссплатформенных путей.


class AppConfig:  # Описываем единый источник настроек приложения.
    """Хранит константы и пути приложения."""

    APP_NAME: str = "DeGhost With AI"  # Название приложения.
    APP_VERSION: str = "0.1.0"  # Текущая версия приложения.
    BASE_DIR: Path = Path(__file__).resolve().parent.parent  # Корень проекта.
    DATA_DIR: Path = BASE_DIR / "data"  # Папка данных.
    SYNTHETIC_DIR: Path = DATA_DIR / "synthetic"  # Папка синтетики.
    SYNTHETIC_MEMMAP_DIR: Path = SYNTHETIC_DIR / "memmap"  # Папка memmap.
    SYNTHETIC_OUTPUT_DIR: Path = SYNTHETIC_DIR / "output"  # Папка результата.
    PROJECTS_DIR: Path = DATA_DIR / "projects"  # Папка проектов.
    CHECKPOINTS_DIR: Path = BASE_DIR / "models" / "checkpoints"  # Чекпоинты.
    DEFAULT_WINDOW_SIZE: tuple[int, int] = (1280, 800)  # Размер окна.
    MIN_WINDOW_SIZE: tuple[int, int] = (1024, 700)  # Минимальный размер.
    SYNTHETIC_GEO_STUB_SHAPE: tuple[int, int, int] = (96, 96, 96)  # Размер stub.
    SYNTHETIC_RESULT_SHAPE: tuple[int, int] = (128, 128)  # Размер результата.
    SYNTHETIC_FDTD_STUB_DELAY_SEC: int = 3  # Задержка FDTD-заглушки.
    DEFAULT_WAVELET_FREQUENCY_HZ: str = "40"  # Частота импульса.
    DEFAULT_ACQUISITION_SHOTS: str = "100"  # Число источников.
    DEFAULT_ACQUISITION_RECEIVERS: str = "200"  # Число приёмников.
    MAX_RECENT_PROJECTS: int = 10  # Максимум последних проектов.
    SERVER_TIMEOUT_SEC: int = 3  # Таймаут проверки сервера.
    SERVER_CHECK_INTERVAL: int = 30  # Интервал проверки сервера.
    SUPPORTED_PROVIDERS: list[str] = ["runpod", "colab", "kaggle"]  # Серверы.
    SUPPORTED_FORMATS: list[str] = [".h5", ".hdf5", ".segy", ".sgy"]  # Форматы.

    def ensure_dirs(self) -> None:  # Создаём обязательные директории.
        """Создаёт рабочие папки приложения."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)  # Создаём data.
        self.SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)  # Создаём synthetic.
        self.SYNTHETIC_MEMMAP_DIR.mkdir(parents=True, exist_ok=True)  # Memmap.
        self.SYNTHETIC_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)  # Output.
        self.PROJECTS_DIR.mkdir(parents=True, exist_ok=True)  # Создаём projects.
        self.CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)  # Создаём models.
