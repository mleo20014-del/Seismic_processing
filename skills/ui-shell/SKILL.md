---
name: ui-shell
description: Use when building or modifying the QML UI shell — window/panel layout, theme (Colors.qml/Theme.qml), custom Qt Quick Controls, the node graph editor (GraphEditor), Python-to-QML bindings, or playback controls UI. Invoke for QML file structure, QAbstractItemModel bindings, ConnectionBadge/status indicators, Meshroom-style styling.
metadata:
  domain: qml-ui-shell
  triggers: QML, Qt Quick Controls, тема, Theme.qml, Colors.qml, GraphEditor, нод-граф, node graph, QAbstractItemModel, ConnectionBadge, PlaybackControls, биндинг, binding, Meshroom
  role: qml-ui-engineer
  scope: ui
---

# UI Shell

Построение и поддержка декларативного QML-каркаса приложения: окна, панели, тему, стилизованные
контролы и нод-редактор — в стиле Meshroom, полностью совместимый с Python-бэкендом и устойчивый
к смене источника данных (Local/Cloud/Cluster) без изменения самой разметки.

## Role Definition

Ты отвечаешь за структуру QML-модулей, биндинг Python-моделей/объектов в QML, визуальную часть
нод-графа, раскладку окон/панелей и индикацию состояния `ChunkSource`. Ты не пишешь GLSL-шейдеры
и CUDA-код (это `rhi-shader-pipeline`/`gpu-interop`) — только декларативную разметку и связку с
Python-объектами, которые эти скиллы предоставляют.

## When to Use This Skill

- Создание или изменение `.qml`-файлов, структуры каталога `ui/qml/`.
- Биндинг Python `QObject`/`QAbstractItemModel` в QML.
- Работа с темой/стилизацией (`Colors.qml`, `Theme.qml`, переопределение контролов).
- Визуальная часть нод-графа (`GraphEditor`).
- Плейбэк-контролы и индикация статуса `ChunkSource` (idle/connected/buffering/error).

## Core Workflow

1. **Определить, куда кладётся новый QML-файл** — по эталонной структуре каталогов
   (см. `references/directory-and-binding.md`), не создавать произвольные новые верхнеуровневые папки.
2. **Экспонировать Python-объект в QML** — по правилам биндинга (context property для
   синглтонов, `QML_ELEMENT` для переиспользуемых типов) — см. `references/directory-and-binding.md`.
3. **Для модели данных** (список нод, список каналов) — использовать `QAbstractListModel`/
   `QAbstractItemModel` с ролями, не сырые `list`/`dict` через `QVariant`.
4. **Для темы/стиля** — брать значения только из `Colors.qml`/`Theme.qml`, не хардкодить в
   компоненте (см. `references/theme-node-playback.md`).
5. **Для нод-графа и плейбэк-контролов** — вся расчётная логика остаётся в Python-модели/
   контроллере, QML только визуализирует состояние (см. `references/theme-node-playback.md`).

## Reference Guide

| Topic | Reference | Load When |
|---|---|---|
| Структура каталогов и правила биндинга Python↔QML | `references/directory-and-binding.md` | Создание нового QML-модуля, экспозиция Python-объекта/модели в QML |
| Тема, нод-граф, плейбэк-контролы | `references/theme-node-playback.md` | Работа со стилем, GraphEditor, PlaybackControls.qml |

## Constraints

### MUST DO
- Экспонировать долгоживущие синглтоны (контроллер приложения, `PlaybackController`) только через
  `engine.rootContext().setContextProperty(...)`, а переиспользуемые типы — через
  `qmlRegisterType`/`QML_ELEMENT`.
- Использовать `QAbstractListModel`/`QAbstractItemModel` с `roleNames()` для любых списковых
  данных (нод графа, каналов/трасс).
- Использовать camelCase для Python-свойств, экспонируемых в QML (`@Property(..., notify=...)`).
- Экспонировать переключение `ChunkSource` как `@Slot(str)` на контроллере приложения; сама смена
  реализации происходит в Python-фабрике.
- Брать все цвета/отступы из `Colors.qml`/`Theme.qml` (`pragma Singleton`).
- Регистрировать переопределения базовых контролов через `Controls/qmldir`.
- Прогонять `qmllint` по изменённым `.qml` перед коммитом.

### MUST NOT DO
- Не передавать массивы данных через `Signal`/`Slot` — только через GPU-ресурс, зарегистрированный
  в rhi-item (`skills/gpu-interop`).
- Не создавать и не хранить инстансы `ChunkSource` в QML — это исключительно ответственность
  Python-фабрики.
- Не писать JS-функции длиннее 5–7 строк внутри `.qml` — логика сложнее тернарного выражения
  выносится в Python.
- Не хранить «состояние правды» о нод-графе в QML — единственный источник истины — Python-модель.
- Не переопределять весь набор Qt Quick Controls 2 сразу — только реально используемые и часто
  видимые контролы.
- Не выполнять вычисления над массивами данных внутри `.qml`-файлов.

## Knowledge Reference

QML/Qt Quick, `QAbstractItemModel`/`QAbstractListModel`, `@Property`/`@Signal`/`@Slot`,
`qmlRegisterType`/`QML_ELEMENT`, `pragma Singleton`, `qmldir`, `qmllint`, паттерны Meshroom
(`Controls/`, `Utils/`, `GraphEditor/`).
