// main.qml — минимальное окно приложения (Фаза 0 каркас).
// Тема, стиль, компоненты добавляются в Фазе 1+.
// i18n: все пользовательские строки через qsTr() (D004/D011 — с Фазы 0).
import QtQuick
import QtQuick.Window

Window {
    id: root

    width: 1280
    height: 800
    minimumWidth: 800
    minimumHeight: 600

    //: Заголовок главного окна приложения
    title: qsTr("Seismic Processing")
    visible: true

    // Фоновый цвет — временный placeholder до Colors.qml (Фаза 1)
    color: "#1e1e2e"

    Text {
        anchors.centerIn: parent
        //: Текст-заглушка на стартовом экране, Фаза 0
        text: qsTr("Phase 0: scaffold ready\nUI/Rendering layer initialized")
        color: "#cdd6f4"
        font.pixelSize: 18
        font.family: "monospace"
        horizontalAlignment: Text.AlignHCenter
        lineHeight: 1.5
    }
}
