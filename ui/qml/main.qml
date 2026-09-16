// main.qml — минимальное окно приложения (Фаза 0 каркас).
// Тема, стиль, компоненты добавляются в Фазе 1+.
import QtQuick
import QtQuick.Window

Window {
    id: root

    width: 1280
    height: 800
    minimumWidth: 800
    minimumHeight: 600

    title: "Seismic Processing — Фаза 0 (каркас)"
    visible: true

    // Фоновый цвет — временный placeholder до Colors.qml (Фаза 1)
    color: "#1e1e2e"

    Text {
        anchors.centerIn: parent
        text: "Фаза 0: каркас готов\nUI/Rendering слой инициализирован"
        color: "#cdd6f4"
        font.pixelSize: 18
        font.family: "monospace"
        horizontalAlignment: Text.AlignHCenter
        lineHeight: 1.5
    }
}
