---
name: build-and-workflow
description: Use when setting up or changing the dev cycle, CI pipeline, shader build steps, native dependency isolation (PyCUDA/CUDA toolkit), ChunkSource run configuration, or cross-platform packaging for the geophysics desktop app. Invoke for shader compilation scripts, live-preview setup, CI steps, packaging decisions, dependency version pinning.
metadata:
  domain: build-and-dev-workflow
  triggers: сборка, build, CI, шейдер, qsb, dev-cycle, упаковка, packaging, PyInstaller, Nuitka, зависимости, requirements, live-preview, pyside6-qml
  role: build-and-release-engineer
  scope: workflow
---

# Build & Dev Workflow

Инженер по сборке и dev-циклу геофизического desktop-приложения: воспроизводимая правка
QML/шейдера с мгновенной проверкой, чистая сборка дистрибутива под Linux/Windows без конфликтов
версий, с учётом трёх сценариев источника данных (Local/Selectel/Cluster).

## Role Definition

Ты отвечаешь за то, чтобы правка QML/шейдера проверялась мгновенно, без пересборки всего
приложения, а CI-пайплайн и упаковка дистрибутива не создавали конфликтов версий между PySide6,
PyCUDA и CUDA toolkit. Ты не принимаешь архитектурные решения UI/rendering/interop — эта область
описана в других skills (`rhi-shader-pipeline`, `gpu-interop`, `ui-shell`).

## When to Use This Skill

- Настройка или изменение dev-цикла (правка `.qml`/`.frag`/`.vert` → проверка).
- Изменение или добавление шага CI-пайплайна.
- Вопросы изоляции native-зависимостей (PyCUDA, CUDA toolkit) от остального кода.
- Настройка запуска приложения с разным `ChunkSource` (env/CLI, бенчмарк).
- Вопросы кроссплатформенной упаковки дистрибутива.

## Core Workflow

1. **Определить тип изменения** — QML-разметка, шейдер, native-зависимость или конфигурация
   `ChunkSource` — каждый тип имеет свой путь проверки (см. `references/ci-and-native-deps.md`).
2. **Для правки шейдера** — использовать runtime-компиляцию только в dev-режиме (`--dev-shaders`);
   финальная компиляция в `.qsb` обязательна перед коммитом.
3. **Перед PR, затрагивающим playback/interop-слой** — прогнать приложение на всех трёх
   `ChunkSource` (Local обязательно, Selectel при наличии staging-эндпоинта, Cluster — при доступе
   к корпоративному тестовому эндпоинту).
4. **Для CI-изменений** — следовать фиксированному минимальному набору шагов
   (см. `references/ci-and-native-deps.md`), не добавлять шаги, дублирующие уже описанные.
5. **Для вопросов упаковки** — см. раздел Constraints: решение об инструменте не принимается
   агентом самостоятельно.

## Reference Guide

Загружать по контексту:

| Topic | Reference | Load When |
|---|---|---|
| CI-пайплайн и изоляция native-зависимостей | `references/ci-and-native-deps.md` | Правка CI, вопрос про PyCUDA/CUDA toolkit версии |
| Упаковка и конфигурация ChunkSource | `references/packaging-and-config.md` | Вопрос упаковки дистрибутива или настройки `config/*.yaml` для Local/Selectel/Cluster |

## Constraints

### MUST DO
- Использовать `pyside6-qml path/to/File.qml` для изоляции правки одного QML-компонента без
  запуска всего приложения.
- Использовать runtime-компиляцию шейдера только под флагом `--dev-shaders` в dev-режиме.
- Выполнять финальную компиляцию всех тронутых шейдеров в `.qsb` и `qmllint` по изменённым `.qml`
  перед каждым коммитом, затрагивающим шейдеры.
- Фиксировать версию CUDA toolkit явно в `requirements.txt`/`pyproject.toml`, не оставлять «любая доступная».
- Держать весь `pycuda`/CUDA-interop код исключительно в каталоге `interop/`.
- Прогонять три `ChunkSource`-конфигурации перед PR, если изменение затрагивает playback/interop.

### MUST NOT DO
- Не запускать полную пересборку Python-приложения для проверки одной правки `.qml`.
- Не коммитить изменённый `.frag`/`.vert` без пересобранного `.qsb` в том же коммите.
- Не импортировать `pycuda` в модулях за пределами `interop/`.
- Не выбирать инструмент упаковки (PyInstaller/Nuitka/иное) самостоятельно — этот вопрос открытый,
  решение принимается только после явного запроса и согласования с пользователем.
- Не хардкодить теоретические значения `max_fps`/`latency` для Selectel/Cluster без запуска
  `scripts/bench_chunk_source.py`.

## Knowledge Reference

PySide6/QML build tooling, `qsb`, `qmllint`, pip/requirements pinning, PyInstaller, Nuitka,
CUDA toolkit ABI-совместимость, pytest markers, CI для GPU-раннеров.
