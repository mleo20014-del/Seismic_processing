# Структура каталогов и правила биндинга Python↔QML

## Структура каталогов (эталон, по образцу Meshroom)

```
ui/qml/
  main.qml                 # точка входа, ApplicationWindow
  Homepage.qml             # стартовый экран, выбор ChunkSource (Local/Selectel/Cluster)
  WorkspaceView.qml        # рабочая область (граф + панели)
  Controls/                # переопределённые базовые контролы
    Panel.qml
    Group.qml
    ThinSlider.qml
    TabPanel.qml
    StatusBar.qml
    ConnectionBadge.qml    # индикатор статуса ChunkSource (idle/connected/buffering/error)
  Utils/
    Colors.qml             # pragma Singleton — палитра
    Theme.qml               # pragma Singleton — отступы, радиусы, типографика
  GraphEditor/
    Node.qml
    Edge.qml
    NodeLog.qml
  Viewer/                  # 2D-вьюеры (см. skills/rhi-shader-pipeline)
    SeismogramView.qml
    SliceView.qml
  Viewer3D/                # 3D-вьюеры волнового поля
    WavefieldVolumeView.qml
    PlaybackControls.qml   # скорость, децимация, play/pause/seek — биндинг к PlaybackController
```

Новый `.qml`-файл создаётся в соответствующей существующей папке; новые верхнеуровневые папки в
`ui/qml/` не создаются без явного запроса.

## Правила биндинга Python ↔ QML

1. **Экспозиция объектов** — только через `engine.rootContext().setContextProperty(...)` для
   долгоживущих синглтонов (контроллер приложения, `PlaybackController`, менеджер `ChunkSource`)
   или через `qmlRegisterType`/`QML_ELEMENT` для переиспользуемых типов, инстанцируемых из QML
   (например, `WavefieldVolumeItem` из `skills/rhi-shader-pipeline`).
2. **Модели данных** (список узлов графа, список каналов/трасс) — только через
   `QAbstractListModel`/`QAbstractItemModel` с ролями (`roleNames()`), никогда через сырые
   `list`/`dict`, передаваемые как `QVariant` на каждое обновление — это лишние копии и
   GC-нагрузка.
3. **Сигналы прогресса** — Python эмитит `Signal(float)`/`Signal(dict)` с лёгкими метаданными
   (процент, диапазон, статус источника). Массивы никогда не идут через Signal/Slot — только
   через GPU-ресурс, зарегистрированный в rhi-item (см. `skills/gpu-interop`).
4. **Именование**: Python-свойства camelCase при экспозиции в QML (`@Property(float, notify=...)`),
   чтобы естественно читаться из QML-биндингов.
5. **Переключение `ChunkSource`** — экспонируется как `@Slot(str)` на контроллере приложения
   (`appController.switchSource("selectel")`), сама смена реализации происходит в Python-фабрике,
   QML не создаёт и не хранит инстансы `ChunkSource`.
