"""Background Scheduler Thread - Chạy AsyncIOScheduler độc lập với Qt GUI thread."""

import asyncio
import threading
from PySide6.QtCore import QThread
from app.core.scheduler import TaskScheduler
from app.utils.logging_config import get_logger

logger = get_logger("autoweb.scheduler_thread")


class SchedulerThread(QThread):
    """Thread chạy background event loop cho AsyncIOScheduler để tránh crash 'no running event loop'."""

    def __init__(self, scheduler: TaskScheduler):
        super().__init__()
        self.scheduler = scheduler
        self.loop = None

    def run(self):
        """Khởi tạo event loop độc lập và kích hoạt scheduler bên trong loop."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        async def _run_scheduler():
            self.scheduler.start()
            logger.info("Scheduler đã kích hoạt thành công bên trong background event loop.")
            # Giữ event loop hoạt động
            while True:
                await asyncio.sleep(3600)

        try:
            self.loop.run_until_complete(_run_scheduler())
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Lỗi trong SchedulerThread: {e}")
        finally:
            try:
                self.scheduler.shutdown()
            except Exception:
                pass
            self.loop.close()
            logger.info("SchedulerThread đã dừng an toàn.")

    def stop(self):
        """Dừng scheduler và dừng event loop an toàn."""
        if self.loop and self.loop.is_running():
            def _cancel_and_stop():
                try:
                    for task in asyncio.all_tasks(self.loop):
                        task.cancel()
                except Exception:
                    pass
                self.loop.stop()

            self.loop.call_soon_threadsafe(_cancel_and_stop)
        self.wait(2000)
