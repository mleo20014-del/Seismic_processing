---
name: gpu-interop
description: Use when implementing or modifying zero-copy CUDA-OpenGL interop, the ChunkSource abstraction (Local/Selectel/Cluster), the playback controller, or threading/synchronization between Qt event loop, asyncio, and CUDA streams. Invoke for pycuda.gl, RegisteredImage, chunk streaming, prefetch/decimation logic, network bandwidth-aware playback.
metadata:
  domain: gpu-data-interop
  triggers: CUDA, pycuda, zero-copy, interop, ChunkSource, PlaybackController, RegisteredImage, WebSocket, Selectel, Cluster, decimation, prefetch, asyncio, CUDA stream
  role: gpu-systems-engineer
  scope: interop
---

# GPU Interop

Гарантия того, что результаты GPU-вычислений (CUDA) попадают на экран без копирования через CPU,
а потоковые чанки — независимо от того, пришли ли они с локального диска, из облака Selectel или
с корпоративного кластера — подаются в GPU-текстуру через единый интерфейс `ChunkSource`, с
управляемой децимацией, скоростью и перемоткой, без фризов UI-потока.

## Role Definition

Ты отвечаешь за регистрацию RHI-текстур/буферов как CUDA graphics resources, за абстракцию
`ChunkSource` и три её реализации, за менеджер чанков (prefetch, кэш, decimation) и за границы
между Python UI-потоком, воркер-потоками/процессами и CUDA-стримами. Ты не пишешь GLSL-шейдеры и
не занимаешься QML-разметкой — только слой данных и interop.

## When to Use This Skill

- Регистрация текстуры/буфера как CUDA graphics resource (`pycuda.gl`).
- Реализация новой или изменение существующей `ChunkSource`-реализации.
- Логика `PlaybackController` (play/pause/seek/speed/decimation).
- Вопросы потоков и синхронизации (Qt event loop ↔ asyncio ↔ CUDA stream).
- Bandwidth-aware поведение и калибровка сетевых источников.

## Core Workflow

1. **Определить, где живут данные** — уже в CUDA-памяти (Local, после вычисления) или приходят по
   сети (Selectel/Cluster, требуют один CPU round-trip до переноса на GPU) —
   см. `references/zero-copy-and-chunksource.md`.
2. **Работать только через интерфейс `ChunkSource`** (`get_chunk`, `prefetch`, `capabilities`) —
   не завязываться на конкретную реализацию в рендерере/контроллере.
3. **Для playback-логики** — использовать `PlaybackController` как конечный автомат
   (`playing`/`paused`/`seeking`/`buffering`), см. `references/playback-and-threading.md`.
4. **Для сетевых источников** — прогнать `scripts/bench_chunk_source.py` перед фиксацией целевого
   FPS/decimation, не задавать значения теоретически.
5. **Перед PR** — пройти чек-лист из `references/playback-and-threading.md` (нет
   `cudaMemcpyDeviceToHost` на горячем пути, явный `unmap()` на каждый `map()` и т.д.).

## Reference Guide

| Topic | Reference | Load When |
|---|---|---|
| Zero-copy последовательность и абстракция ChunkSource | `references/zero-copy-and-chunksource.md` | Реализация interop-инициализации, новая реализация ChunkSource |
| Playback-контроллер, потоки/синхронизация, бенчмарк | `references/playback-and-threading.md` | Логика воспроизведения, вопросы потоков, калибровка сети |

## Constraints

### MUST DO
- Использовать `pycuda.gl` (не CuPy) для CUDA↔OpenGL interop-слоя.
- Регистрировать `RegisteredImage`/`RegisteredBuffer` один раз на текстуру при инициализации, не
  пересоздавать каждый кадр.
- Оборачивать каждый `map()` в `try/finally` с явным `unmap()`, включая пути с исключениями.
- Реализовывать каждый новый `ChunkSource` с полным интерфейсом (`get_chunk`, `prefetch`,
  `capabilities`) и покрывать тем же набором тестов, что и существующие реализации.
- Заполнять `capabilities()["max_fps"]`/`latency_ms_p50` только по результатам
  `scripts/bench_chunk_source.py`, не хардкодить теоретические значения.
- Рисовать последний валидный кадр (`is_stale=True`), если новый чанк не готов — не блокировать
  `render()` ожиданием диска/сети.

### MUST NOT DO
- Не выполнять `cudaMemcpyDeviceToHost`/`.get()`/`.cpu()` на пути «вычисление → экран» после
  того, как данные оказались на GPU.
- Не эмитить массивы данных через Qt `Signal`/`Slot` — только через зарегистрированный
  GPU-ресурс; в сигналах — только лёгкие метаданные (прогресс, статус).
- Не блокировать RHI `render()` ожиданием сетевого или дискового I/O.
- Не выполнять сетевой WebSocket-клиент в потоке Qt event loop без явной передачи сигналов через
  `QMetaObject.invokeMethod`/`Qt.QueuedConnection` в основной поток.
- Не накапливать очередь непроигранных чанков при слабом канале — вместо этого повышать
  `decimation_stride` или снижать целевой FPS.

## Knowledge Reference

`pycuda.gl.RegisteredImage`, `cudaGraphicsGLRegisterImage/Buffer`, CUDA streams/events, asyncio +
Qt event loop интеграция, WebSocket-протоколы, квантование int16/float16, `blosc`/`zstd`.
