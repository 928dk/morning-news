// fetcher.js — load report.json and expose morning news data
// Only imported by main.qml — data flows to children via property bindings

var reportPath = "file://$HOME/.cache/morning-news/report.json";
var data = null;
var loaded = false;
var loadError = false;

function fetchReport() {
    var doc = new XMLHttpRequest();
    try {
        doc.open('GET', reportPath, false);
        doc.send();
        var status = doc.status;
        if (status === 0 || status === 200) {
            var text = doc.responseText;
            if (text && text.length > 0) {
                data = JSON.parse(text);
                loaded = true;
                loadError = false;
                return true;
            }
        }
    } catch (e) {
        // File not available
    }
    loadError = true;
    return false;
}

function getServices() {
    if (!data || !data.services) return [];
    return data.services;
}

function getFailures() {
    if (!data || !data.failures) return [];
    return data.failures;
}

function getNewFiles() {
    if (!data || !data.new_files) return [];
    return data.new_files;
}

function getSummary() {
    if (!data || !data.summary) return "";
    return data.summary;
}

function getGeneratedAt() {
    if (!data || !data.generated_at) return "";
    return data.generated_at;
}

function getStats() {
    if (!data || !data.summary_stats) return {
        total_services: 0, failed_count: 0, ok_count: 0,
        new_file_count: 0, unknown_count: 0
    };
    return data.summary_stats;
}

function getServiceIcon(status) {
    if (status === "failed") return "❌";
    if (status === "completed") return "✅";
    return "⏳";
}
