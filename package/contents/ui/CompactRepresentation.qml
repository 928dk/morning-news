import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import org.kde.plasma.core as PlasmaCore

Item {
    id: compactRoot
    implicitWidth: PlasmaCore.Units.gridUnit * 6
    implicitHeight: PlasmaCore.Units.gridUnit * 2

    property bool repLoadError: false
    property var repStats: ({})
    property string statusText: "—"
    property bool hasFailure: false

    RowLayout {
        anchors.fill: parent
        anchors.margins: PlasmaCore.Units.smallSpacing
        spacing: PlasmaCore.Units.smallSpacing

        Label {
            text: hasFailure ? "⚠" : "☕"
            font.pointSize: PlasmaCore.Theme.defaultFont.pointSize * 1.2
        }

        Label {
            text: compactRoot.statusText
            font.pointSize: PlasmaCore.Theme.defaultFont.pointSize * 0.75
            font.bold: true
            color: hasFailure ? "#e66100" : PlasmaCore.Theme.textColor
            elide: Text.ElideRight
            Layout.fillWidth: true
        }
    }

    function updateDisplay() {
        hasFailure = repStats.failed_count > 0;
        if (repLoadError) {
            statusText = "—";
        } else {
            statusText = (repStats.ok_count || 0) + "/" + (repStats.total_services || 0)
                + ((repStats.new_file_count || 0) > 0 ? " +" + repStats.new_file_count : "");
        }
    }
}
