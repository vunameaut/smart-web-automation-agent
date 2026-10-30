"""QThread worker to run async tasks in background without blocking Qt GUI."""

import asyncio
from PySide6.QtCore import QThread, Signal


class TaskExecutionWorker(QThread):
    """Worker chạy async task trong một thread độc lập với Qt event loop."""
    
    # Signals
    started_signal = Signal(str)            # task_id
    finished_signal = Signal(dict)          # result dict
    error_signal = Signal(str)              # error message

    def __init__(self, task_manager, task_id: str, dry_run: bool = False):
        super().__init__()
        self.task_manager = task_manager
        self.task_id = task_id
        self.dry_run = dry_run

    def run(self):
        """Khởi tạo một event loop mới trong thread này để chạy coroutine an toàn."""
        self.started_signal.emit(self.task_id)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                self.task_manager.run_now(self.task_id, dry_run=self.dry_run)
            )
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            loop.close()

