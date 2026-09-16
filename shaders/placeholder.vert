// shaders/placeholder.vert — заглушка для тестирования build_shaders.py
// Реальные шейдеры добавляются в Фазе 5 (rhi-shader-pipeline).
// QQuickRhiItem требует GLSL 330+ для корректной работы с Qt RHI.

#version 330 core

layout(location = 0) in vec4 position;

void main() {
    gl_Position = position;
}
