# Упаковка и конфигурация ChunkSource

## Конфигурация запуска (Local vs Selectel vs Cluster)

Выбор `ChunkSource` — параметр запуска, не код:

```yaml
# config/local.yaml
chunk_source: local
data_path: /mnt/data/wavefields

# config/selectel.yaml
chunk_source: selectel
ws_endpoint: wss://<selectel-host>/wavefield
codec: quantized_int16      # или float16
prefetch_window: 8          # количество timestep'ов, запрашиваемых заранее

# config/cluster.yaml
chunk_source: cluster
ws_endpoint: wss://<cluster-host>/wavefield
auth: corporate_token
codec: quantized_int16
prefetch_window: 16
```

Фабрика (`app/chunk_source_factory.py`) читает конфиг и инстанцирует нужную реализацию
`ChunkSource`; playback-контроллер и UI не знают, какая была выбрана.

## Упаковка (открытый вопрос — решение только по запросу пользователя)

- Кандидаты: **PyInstaller** (проще для проектов с готовыми hook'ами под PySide6) или **Nuitka**
  (быстрее runtime, сложнее конфигурация с CUDA/PyCUDA native-библиотеками).
- Ключевой риск при упаковке — корректный бандлинг `.qsb`-файлов как ассетов (не забыть добавить
  в `datas`/`--include-data-dir`) и нативных `.so`/`.dll` от PyCUDA/CUDA toolkit.
- Дистрибутив для Local-режима требует полного CUDA toolkit на клиентской машине; для
  Selectel/Cluster-режима клиентский пакет теоретически может быть легче (вычисления не локальные),
  но zero-copy interop всё равно требует локального CUDA-контекста для приёма чанков — полный CUDA
  runtime остаётся обязательным во всех трёх сценариях.
- **Агент обязан спросить пользователя** перед выбором конкретного инструмента упаковки и перед
  реализацией шага упаковки в CI — это открытый вопрос, зафиксированный в `AGENTS.md`, раздел
  «Не делать без явного запроса», не принимается по умолчанию.
