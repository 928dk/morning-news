from PyQt5.QtCore import QThread, pyqtSignal

from src.collector import collect
from src.summarizer import summarize
from src.db import save_report
from src.config import REPORT_PATH
import json


class RefreshWorker(QThread):
    started = pyqtSignal()
    finished = pyqtSignal(dict, str)
    error = pyqtSignal(str)

    def run(self):
        self.started.emit()
        try:
            data = collect()
            llm_summary = summarize(data)
            data["summary"] = llm_summary
            save_report(data, llm_summary)
            REPORT_PATH.write_text(json.dumps(data, indent=2, default=str))
            self.finished.emit(data, llm_summary)
        except Exception as e:
            self.error.emit(str(e))
