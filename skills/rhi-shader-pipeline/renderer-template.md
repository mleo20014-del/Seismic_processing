# Почему QQuickRhiItem и шаблон рендер-класса

## Почему `QQuickRhiItem`, а не альтернативы

- `QQuickFramebufferObject` — legacy, жёстко привязан к OpenGL, не портируется на RHI-абстракцию.
- `Qt3D` — ECS-архитектура с накладными расходами, вытесняется Qt Quick 3D; не даёт нужного уровня
  контроля над сырыми буферами для raymarching больших вокселных сеток.
- `VTK`/`PyVista` — дают готовый volume rendering и десятилетия scientific-viz алгоритмов, но: не
  имеют встроенного zero-copy CUDA-interop; интегрируются в Qt только через
  `QVTKRenderWindowInteractor`/`pyvistaqt.QtInteractor` (`QWidget`, отдельный OpenGL-контекст, не
  `QQuickItem`), что рвёт единый QML-пайплайн; задокументированы регрессии производительности VTK9
  vs VTK5 при интерактивном вращении и активные баги связки с PySide6. Полный разбор —
  `VTK_PyVista_RHI_comparison.md`. Роль VTK/PyVista в проекте — только offline QA-визуализация вне
  продакшен-рендера.
- `QQuickRhiItem` — единственный вариант, дающий: (а) единый API поверх OpenGL/Vulkan/Metal/D3D,
  (б) прямой доступ к `QRhiTexture`/`QRhiBuffer` для регистрации в CUDA-interop, (в) чистую
  Python-интеграцию без написания и сборки C++ QML-плагина.

## Закреплённый backend: OpenGL

```python
from PySide6.QtQuick import QQuickWindow
from PySide6.QtGui import QRhi

QQuickWindow.setGraphicsApi(QRhi.OpenGL)  # один раз при старте приложения, до создания окна
```

Причина закрепления — зрелость CUDA↔OpenGL interop через PyCUDA (см.
`skills/gpu-interop/SKILL.md`). Смена backend на Vulkan пересматривается только вместе с
пересмотром слоя interop.

## Структура рендер-класса (шаблон)

```python
from PySide6.QtQuick import QQuickRhiItem, QQuickRhiItemRenderer
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = "GeoViewer"
QML_IMPORT_MAJOR_VERSION = 1

class WavefieldVolumeRenderer(QQuickRhiItemRenderer):
    def initialize(self, cb):
        # создание QRhiTexture под 3D-объём (формат R16F/R32F), QRhiBuffer под uniform
        # (view/proj/transfer function/timestepIndex/stepCount/opacityScale)
        # регистрация текстуры в interop-слое (см. skills/gpu-interop) — один раз
        ...
    def synchronize(self, item):
        # чтение свойств Python-объекта item: currentTimestep, decimationStride,
        # playbackSpeed, opacityScale — копирование в uniform-буфер
        ...
    def render(self, cb):
        # bind pipeline, bind raymarching-шейдер, draw fullscreen triangle / bounding cube
        ...

@QmlElement
class WavefieldVolumeItem(QQuickRhiItem):
    def createRenderer(self):
        return WavefieldVolumeRenderer()
```

`Item`-класс регистрируется в QML через `@QmlElement` (`QML_ELEMENT`) и используется как обычный
QML-компонент внутри `Viewer3D/`.
