# RFC — Foundation
**Фундамент: MainWindow, LaunchScreen, AppController, ModeTabBar**

## Статус: ГОТОВ К РЕАЛИЗАЦИИ

## Цель
Создать полностью рабочий каркас:
- Логика запуска (есть проекты / нет проектов)
- MainWindow с пустым QStackedWidget
- LaunchScreen как QDialog
- Кастомный ModeTabBar в toolbar
- AppController как владелец режимов и задач

## Файлы к созданию

### config/app_config.py
- APP_NAME = "DeGhost With AI"
- APP_VERSION = "0.1.0"
- Все пути через pathlib.Path:
  BASE_DIR, DATA_DIR, SYNTHETIC_DIR,
  PROJECTS_DIR, CHECKPOINTS_DIR
- DEFAULT_WINDOW_SIZE = (1280, 800)
- MIN_WINDOW_SIZE = (1024, 700)
- MAX_RECENT_PROJECTS = 10
- SERVER_TIMEOUT_SEC = 3
- SERVER_CHECK_INTERVAL = 30
- SUPPORTED_PROVIDERS = ["runpod", "colab", "kaggle"]
- SUPPORTED_FORMATS = [".h5", ".hdf5", ".segy", ".sgy"]
- ensure_dirs() — создать все папки при старте
- Никаких импортов PyQt6

### main.py
- Создать AppConfig → ensure_dirs()
- Создать QApplication
- Создать MainWindow(config)
- MainWindow сам решает что показать при старте
- window.show() → app.exec()
- Максимум 25 строк

### app/app_controller.py
- Владелец активных режимов:
  self._active_modes: dict[str, QWidget] = {}
  Максимум 4 ключа: "training","processing","synthetic","testing"
- Владелец всех фоновых QThread задач
- open_mode(mode: str) → QWidget:
  Если режим есть → вернуть существующий виджет
  Если нет → создать lazy → сохранить → вернуть
- close_mode(mode: str) → None:
  Удалить из _active_modes
  НЕ останавливать QThread фоновой задачи
- has_unsaved_changes(mode: str) → bool

### ui/main_window.py
- QMainWindow
- centralWidget: QStackedWidget (начинается ПУСТЫМ)
- Toolbar: ModeTabBar + статус сервера справа
- При старте вызвать _check_startup()
- _check_startup():
  Если SessionManager.has_projects() → RecentProjectsDialog
  Иначе → LaunchScreen(config).exec()
- switch_to_mode(mode: str):
  widget = AppController.open_mode(mode)
  Если не в стеке → stack.addWidget(widget)
  stack.setCurrentWidget(widget)
  ModeTabBar.add_tab(mode)
- close_mode(mode: str):
  Проверить has_unsaved_changes
  Показать диалог если нужно
  stack.removeWidget(widget)
  AppController.close_mode(mode)
  ModeTabBar.remove_tab(mode)

### ui/launch_screen.py
- QDialog (НЕ QWidget)
- Загружает ui/forms/launch_screen_ui.py
- Сигнал: mode_selected = pyqtSignal(str)
- 4 кнопки → emit режима → self.accept()
- Вызывается из MainWindow._check_startup()
  и при создании нового проекта

### ui/widgets/mode_tab_bar.py
- Кастомный QWidget для toolbar
- Показывает только активные вкладки
- Максимум 4 вкладки
- Кнопка × на каждой вкладке
- Сигнал: tab_clicked = pyqtSignal(str)
- Сигнал: tab_closed = pyqtSignal(str)
- add_tab(mode: str) — добавить если нет
- remove_tab(mode: str) — удалить
- set_active(mode: str) — выделить активную

## Архитектурные ограничения
- QStackedWidget начинается ПУСТЫМ (нет placeholder)
- LaunchScreen — QDialog, не в стеке
- QThread живёт в AppController, не в виджете
- Все пути через AppConfig
- Нет глобальных переменных
- Максимум 4 режима одновременно

## Критерий готовности
- uv run main.py → MainWindow открывается
- Нет проектов → LaunchScreen появляется модально
- Клик на режим → вкладка в ModeTabBar, виджет в стеке
- Повторный клик на тот же режим → переключение без дублирования
- Клик × → диалог → вкладка исчезает
- Фоновый QThread не останавливается при закрытии вкладки