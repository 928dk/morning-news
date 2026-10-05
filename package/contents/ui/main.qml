import QtQuick
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import "../code/fetcher.js" as Fetcher

PlasmoidItem {
    id: root

    property var services: []
    property var newFiles: []
    property var failures: []
    property string summary: ""
    property string generatedAt: ""
    property var stats: ({total_services: 0, failed_count: 0, ok_count: 0, new_file_count: 0})
    property bool loadError: false
    property string tipSummary: "No data"
    property int failedCount: 0

    toolTipMainText: "Morning News"
    toolTipSubText: tipSummary

    Timer {
        interval: 60000
        repeat: true
        running: true
        onTriggered: fetchReport()
    }

    function fetchReport() {
        if (Fetcher.fetchReport()) {
            root.services = Fetcher.getServices();
            root.newFiles = Fetcher.getNewFiles();
            root.failures = Fetcher.getFailures();
            root.summary = Fetcher.getSummary();
            root.generatedAt = Fetcher.getGeneratedAt();
            root.stats = Fetcher.getStats();
            root.loadError = false;
        } else {
            root.loadError = true;
        }
        updateDisplay();
    }

    function updateDisplay() {
        failedCount = root.failures.length;
        var ok = root.stats.ok_count || 0;
        var total = root.stats.total_services || 0;
        var files = root.stats.new_file_count || 0;

        if (root.loadError) {
            tipSummary = "No report yet — run --update";
        } else if (failedCount > 0) {
            tipSummary = failedCount + " failed / " + ok + " ok" + (files > 0 ? " +" + files + " files" : "");
        } else {
            tipSummary = ok + " services OK" + (files > 0 ? " +" + files + " files" : "");
        }

        compactItem.updateDisplay();
        fullItem.updateDisplay();
    }

    function refresh() {
        fetchReport();
    }

    Component.onCompleted: fetchReport()

    compactRepresentation: CompactRepresentation {
        id: compactItem
        repLoadError: root.loadError
        repStats: root.stats
    }

    fullRepresentation: FullRepresentation {
        id: fullItem
        repServices: root.services
        repNewFiles: root.newFiles
        repSummary: root.summary
        repGeneratedAt: root.generatedAt
        repStats: root.stats
        repLoadError: root.loadError
    }
}
