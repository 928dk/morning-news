import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQml.Models
import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore

Item {
    id: fullRoot

    implicitWidth: PlasmaCore.Units.gridUnit * 30
    implicitHeight: PlasmaCore.Units.gridUnit * 22

    property var repServices: []
    property var repNewFiles: []
    property string repSummary: ""
    property string repGeneratedAt: ""
    property var repStats: ({})
    property bool repLoadError: false
    property string footerText: ""

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: PlasmaCore.Units.gridUnit
        spacing: PlasmaCore.Units.smallSpacing

        RowLayout {
            Layout.fillWidth: true
            spacing: PlasmaCore.Units.gridUnit

            Kirigami.Heading {
                level: 2
                text: "☕ Morning News"
                Layout.fillWidth: true
            }

            Button {
                text: "↻"
                onClicked: root.refresh()
            }
        }

        Kirigami.Separator {
            Layout.fillWidth: true
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                width: parent.width
                spacing: PlasmaCore.Units.smallSpacing

                Label {
                    text: "Sync Services"
                    font.bold: true
                    font.pointSize: PlasmaCore.Theme.defaultFont.pointSize * 0.9
                    color: PlasmaCore.Theme.highlightColor
                }

                Repeater {
                    id: serviceRepeater
                    model: ListModel {}

                    Rectangle {
                        width: parent.width
                        height: PlasmaCore.Theme.defaultFont.pixelSize + PlasmaCore.Units.smallSpacing * 2
                        color: index % 2 === 0 ? "transparent" : PlasmaCore.Theme.backgroundColor
                        radius: PlasmaCore.Units.smallSpacing / 2

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: PlasmaCore.Units.smallSpacing
                            spacing: PlasmaCore.Units.smallSpacing

                            Label {
                                text: model.icon || "⏳"
                                font.pointSize: PlasmaCore.Theme.defaultFont.pointSize * 0.8
                            }
                            Label {
                                text: model.name || ""
                                Layout.preferredWidth: parent.width * 0.25
                                elide: Text.ElideRight
                                font.pointSize: PlasmaCore.Theme.defaultFont.pointSize * 0.8
                            }
                            Label {
                                text: model.last_run || "—"
                                Layout.preferredWidth: parent.width * 0.35
                                elide: Text.ElideRight
                                font.pointSize: PlasmaCore.Theme.defaultFont.pointSize * 0.7
                                opacity: 0.7
                            }
                            Label {
                                text: model.status || ""
                                Layout.preferredWidth: parent.width * 0.3
                                elide: Text.ElideRight
                                font.pointSize: PlasmaCore.Theme.defaultFont.pointSize * 0.7
                                horizontalAlignment: Text.AlignRight
                                color: model.status === "failed" ? "#e66100"
                                    : model.status === "completed" ? "#26a269" : PlasmaCore.Theme.textColor
                            }
                        }
                    }
                }

                Kirigami.Separator {
                    Layout.fillWidth: true
                    Layout.topMargin: PlasmaCore.Units.smallSpacing
                }

                Label {
                    text: "New Files"
                    font.bold: true
                    font.pointSize: PlasmaCore.Theme.defaultFont.pointSize * 0.9
                    color: PlasmaCore.Theme.highlightColor
                }

                Repeater {
                    id: filesRepeater
                    model: ListModel {}

                    RowLayout {
                        spacing: PlasmaCore.Units.smallSpacing
                        Label {
                            text: "📁 " + model.directory
                            font.pointSize: PlasmaCore.Theme.defaultFont.pointSize * 0.8
                        }
                        Label {
                            text: model.count + " files"
                            font.pointSize: PlasmaCore.Theme.defaultFont.pointSize * 0.8
                            opacity: 0.7
                        }
                        Label {
                            text: model.total_size || ""
                            font.pointSize: PlasmaCore.Theme.defaultFont.pointSize * 0.7
                            opacity: 0.5
                        }
                    }
                }

                Kirigami.Separator {
                    Layout.fillWidth: true
                    Layout.topMargin: PlasmaCore.Units.smallSpacing
                }

                Label {
                    text: "AI Brief"
                    font.bold: true
                    font.pointSize: PlasmaCore.Theme.defaultFont.pointSize * 0.9
                    color: PlasmaCore.Theme.highlightColor
                }

                Label {
                    id: summaryLabel
                    text: ""
                    font.pointSize: PlasmaCore.Theme.defaultFont.pointSize * 0.8
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                    opacity: 0.8
                }
            }
        }

        Label {
            id: footerLabel
            Layout.fillWidth: true
            text: fullRoot.footerText
            font.pointSize: PlasmaCore.Theme.defaultFont.pointSize * 0.65
            opacity: 0.5
            horizontalAlignment: Text.AlignRight
        }
    }

    function updateDisplay() {
        if (repLoadError) {
            summaryLabel.text = "No report yet. Run: python3 src/cli.py --update";
            footerText = "Run collector first";
            serviceRepeater.model.clear();
            filesRepeater.model.clear();
            return;
        }

        serviceRepeater.model.clear();
        for (var i = 0; i < repServices.length; i++) {
            var svc = repServices[i];
            var icon = svc.status === "failed" ? "❌"
                : svc.status === "completed" ? "✅" : "⏳";
            serviceRepeater.model.append({
                name: svc.name,
                status: svc.status || "unknown",
                last_run: svc.last_run || "—",
                icon: icon
            });
        }

        filesRepeater.model.clear();
        for (var j = 0; j < repNewFiles.length; j++) {
            filesRepeater.model.append(repNewFiles[j]);
        }

        summaryLabel.text = repSummary || "All clear — no issues.";
        footerText = "Generated: " + repGeneratedAt
            + "  |  " + (repStats.ok_count || 0) + "/" + (repStats.total_services || 0) + " OK"
            + ((repStats.failed_count || 0) > 0 ? "  ⚠ " + repStats.failed_count + " failed" : "");
    }
}
