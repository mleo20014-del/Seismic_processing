# Zero-copy interop и абстракция ChunkSource

## Почему PyCUDA, а не CuPy для interop

CuPy не предоставляет официальных биндингов OpenGL-interop уровня `cudaGraphicsGLRegisterImage`.
PyCUDA имеет модуль `pycuda.gl` с прямым доступом к этому CUDA Runtime API. Поэтому:

- Тяжёлые вычисления (FDTD, свёртки, обучение) остаются на существующем стеке
  (CuPy/PyTorch/CUDA-kernels).
- **Только слой interop с рендерером** — через `pycuda.gl`, как тонкий мост между вычислительным
  результатом (уже в CUDA-памяти, в любом фреймворке) и OpenGL-текстурой, созданной RHI.
- Это единственная нативная зависимость, требующая скомпилированного расширения — она изолирована
  в одном модуле (`interop/`) и не тянет за собой пересборку остального приложения.

## Принцип zero-copy (эталонная последовательность, сценарий Local)

1. **Инициализация (один раз при старте вьюера):**
   - RHI создаёт `QRhiTexture` (3D для объёма, 2D для графиков) с нужным форматом (например
     `R32F` для амплитуды или `RGBA16F` при необходимости фазы+амплитуды одновременно).
   - Через low-level handle текстуры (native OpenGL texture id, доступный из `QRhiTexture`
     бэкенда) вызывается `pycuda.gl.RegisteredImage(int(gl_texture_id), gl_target, cuda_flags)`.
   - Получаем `RegisteredImage`, который переиспользуется на все последующие кадры — регистрация
     делается один раз, не на каждый кадр.

2. **На каждое обновление кадра (новый timestep / новый чанк):**

```python
mapping = registered_image.map()
cuda_array = mapping.array(0, 0)          # CUDA array, указывающий на ту же память, что OpenGL-текстура
cuda_kernel_write_wavefield(cuda_array, chunk_gpu_buffer, decimation_stride)  # CUDA-кернел пишет напрямую
mapping.unmap()
```

Никакого `cudaMemcpyDeviceToHost`/`cudaMemcpyHostToDevice` в этом пути. `chunk_gpu_buffer` — это
данные чанка, уже перенесённые на GPU на этапе загрузки, не читаемые повторно с CPU.

## Абстракция `ChunkSource` — единый интерфейс независимо от развёртывания

Рендерер и playback-контроллер работают только с этим интерфейсом. Реализация выбирается на
старте приложения (CLI-флаг/конфиг), без изменения кода потребителей.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np

@dataclass
class ChunkRequest:
    timestep: int
    decimation_stride: int          # шаг прореживания сетки (управляется пользователем)
    lod: int = 0                    # уровень детализации, если источник поддерживает mip-подобные уровни

@dataclass
class ChunkResult:
    timestep: int
    gpu_buffer: "pycuda.driver.DeviceAllocation"   # данные уже на GPU клиента к моменту возврата
    shape: tuple[int, int, int]
    dtype: np.dtype
    is_stale: bool = False           # True, если это последний валидный кадр, а не запрошенный

class ChunkSource(ABC):
    @abstractmethod
    async def get_chunk(self, request: ChunkRequest) -> ChunkResult: ...

    @abstractmethod
    async def prefetch(self, timesteps: list[int]) -> None: ...

    @abstractmethod
    def capabilities(self) -> dict:
        """Например: {"max_fps": 24, "supports_lod": True, "latency_ms_p50": 12}"""
        ...
```

### Реализация 1 — `LocalChunkSource`
- Читает чанк из `np.memmap`/Zarr напрямую с локального диска либо принимает буфер, уже
  посчитанный локальным CUDA-кернелом (FDTD-шаг на GPU ноутбука/десктопа).
- CPU-путь присутствует только при первой загрузке с диска: `np.memmap` → `cuda.mem_alloc` +
  `memcpy_htod`. Если данные уже результат локального CUDA-вычисления — копирования вообще нет,
  буфер передаётся по указателю.
- `capabilities()["max_fps"]` ограничен только производительностью локального GPU/диска.

### Реализация 2 — `SelectelChunkSource`
- Держит персистентное WebSocket-соединение с облачным инстансом Selectel (принятый паттерн
  проекта — persistent request/response, не HTTP polling).
- Протокол сообщения: бинарный фрейм `{header: {timestep, shape, dtype, codec}, payload: bytes}`.
  Рекомендуемый формат данных — **float16** или **квантованный int16 + scale/offset** (не
  float32) — вдвое-четверо меньше трафика при приемлемой потере точности для визуализации (не
  для расчётов).
- Опционально — сжатие payload (`blosc`/`zstd`) поверх квантования, если профилирование сети
  показывает, что CPU на распаковку дешевле, чем лишний трафик.
- После получения фрейма: `payload` → `np.frombuffer` (CPU, неизбежно) → **немедленно**
  `cuda.mem_alloc` + `memcpy_htod` → с этого момента буфер живёт на GPU клиента и участвует в
  zero-copy пути наравне с Local-сценарием.
- `prefetch()` заранее запрашивает N будущих timestep'ов у сервера, чтобы скрыть сетевую задержку
  при обычном воспроизведении (не при резком скачке/seek).
- `capabilities()["max_fps"]` и `latency_ms_p50` заполняются по результатам
  `scripts/bench_chunk_source.py` — не задаются заранее теоретически.

### Реализация 3 — `ClusterChunkSource`
- Наследует `SelectelChunkSource` (или использует общий `RemoteWebSocketChunkSourceBase`),
  меняется только endpoint, схема авторизации (например, корпоративный токен/VPN вместо
  API-ключа Selectel) и, возможно, формат сериализации, если на кластере уже есть свой пайплайн
  выдачи результатов.
- Если кластер в будущем перейдёт на headless server-side рендеринг (сервер сам рисует кадр и
  шлёт видеопоток) — это **не** `ChunkSource`, а отдельный `VideoStreamSource`, потребляемый
  другим, более простым QML-компонентом (`VideoOutput` + декодер), не raymarching-шейдером. Не
  проектируется заранее без отдельного запроса (см. `AGENTS.md`, раздел «Не делать без явного
  запроса»).
