---
name: rhi-shader-pipeline
description: Use when implementing or modifying QQuickRhiItem renderers, GLSL shaders (.vert/.frag), the raymarching pipeline for the wavefield volume, or adaptive LOD logic. Invoke for custom rendering, shader compilation to .qsb, RHI backend questions, 2D/3D visualization components (SeismogramView, SliceView, WavefieldVolumeView).
metadata:
  domain: custom-gpu-rendering
  triggers: QQuickRhiItem, GLSL, шейдер, shader, raymarching, qsb, RHI, OpenGL, LOD, воксель, voxel, transfer function, WavefieldVolume, SeismogramView, SliceView
  role: graphics-rendering-engineer
  scope: rendering
---

# RHI Shader Pipeline

Реализация и поддержка собственного рендерера на `QQuickRhiItem` для 2D-графиков и 3D-объёма
волнового поля через ручные GLSL-шейдеры, компилируемые в `.qsb`, с производительностью,
достаточной для интерактивного воспроизведения десятков-сотен миллионов узлов сетки без фризов
интерфейса.

## Role Definition

Ты пишешь и поддерживаешь Python-подклассы `QQuickRhiItem`/`QQuickRhiItemRenderer` для 2D- и
3D-сцен, GLSL-шейдеры и их компиляцию в `.qsb`, raymarching-пайплайн объёма волнового поля и
адаптивный LOD. Ты не занимаешься CUDA-interop (`gpu-interop`) и не пишешь QML-разметку/тему
(`ui-shell`) — только рендер-код и шейдеры.

## When to Use This Skill

- Создание или изменение `QQuickRhiItem`-подкласса (2D или 3D).
- Написание или правка GLSL-шейдера (`.vert`/`.frag`).
- Вопросы raymarching-пайплайна объёма волнового поля.
- Настройка адаптивного уровня детализации (LOD) под разное железо.
- Вопрос выбора рендер-технологии (RHI vs VTK/PyVista/Qt3D) для продакшен-визуализации.

## Core Workflow

1. **Определить тип компонента** — 2D (сейсмограмма/срез) или 3D (объём волнового поля) — оба
   используют один и тот же `QQuickRhiItem`-механизм, но 2D не делает raymarching
   (см. `references/shader-and-raymarching.md`, раздел «2D-графики как частный случай»).
2. **Создать/изменить рендер-класс** по шаблону из `references/renderer-template.md`.
3. **Написать/изменить GLSL-исходник** в `shaders/`, следуя именованию `<назначение>.<stage>.glsl`.
4. **Скомпилировать в `.qsb`** — обязательный шаг перед коммитом
   (команда — в `skills/build-and-workflow/SKILL.md`).
5. **Для raymarching/LOD-изменений** — сверить с `references/shader-and-raymarching.md` перед
   изменением uniform-структуры буфера (порядок полей в Python и GLSL должен совпадать).

## Reference Guide

| Topic | Reference | Load When |
|---|---|---|
| Почему `QQuickRhiItem`, backend OpenGL, шаблон рендер-класса | `references/renderer-template.md` | Создание нового рендер-компонента, вопрос выбора технологии |
| Шейдерная дисциплина, raymarching, LOD, 2D-вариант | `references/shader-and-raymarching.md` | Правка/создание шейдера, вопрос по uniform-буферу или LOD |

## Constraints

### MUST DO
- Использовать `QQuickRhiItem` для любого нового кастомного рендер-компонента (2D и 3D).
- Держать RHI backend закреплённым на OpenGL (`QQuickWindow.setGraphicsApi(QRhi.OpenGL)`),
  выставляется один раз при старте приложения, до создания окна.
- Хранить GLSL-исходники в `shaders/` как отдельные файлы, никогда как инлайн-строки в Python.
- Синхронно обновлять порядок полей uniform-буфера в GLSL и в Python-структуре при добавлении
  нового uniform.
- Поддерживать минимальный профиль GLSL (`100 es`) в дополнение к десктопному.
- Регулировать скорость воспроизведения через частоту обновления `timestepIndex` в Python
  (`PlaybackController`), не через QML `Timer`/анимацию.

### MUST NOT DO
- Не использовать `QQuickFramebufferObject`, `Qt3D` или VTK/PyVista как основной рендер-движок
  для продакшен-визуализации — только `QQuickRhiItem`.
- Не смешивать логику 2D-графика и 3D-объёма в одном рендер-классе — общий код выносится в
  `RhiVisualizationRendererBase`.
- Не коммитить изменённый `.glsl` без пересобранного `.qsb` в том же коммите.
- Не оставлять runtime-компиляцию шейдера включённой вне dev-режима (`--dev-shaders`).
- Не вызывать блокирующий `glFinish`/синхронный readback внутри `render()`.
- Не менять backend на Vulkan без согласованного пересмотра слоя interop (см. `AGENTS.md`).

## Knowledge Reference

QQuickRhiItem/QQuickRhiItemRenderer API, QRhiTexture/QRhiBuffer, GLSL 100 es/120/150, `qsb`,
raymarching и transfer function (1D LUT), early ray termination, QRhiProfiler/GPU-таймеры RHI.
