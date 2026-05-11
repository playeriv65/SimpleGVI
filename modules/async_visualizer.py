import logging
import threading
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class AsyncVisualizer:
    """Bounded async visualization writer with backpressure."""

    def __init__(self, max_threads: int = 2, max_pending: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_threads)
        self._pending: set[Future] = set()
        self._lock = threading.Lock()
        self._completed_count = 0
        self._failed_count = 0
        self._max_pending = max(1, max_pending)

    def submit_visualization(
        self,
        func: Callable,
        image_source,
        segmentation,
        gvi: float,
        output_path: str,
        callback: Optional[Callable] = None,
    ) -> Future:
        self._drain_until_capacity()

        def _task():
            try:
                func(image_source, segmentation, gvi, output_path)
                with self._lock:
                    self._completed_count += 1
                if callback:
                    callback(output_path, None)
                return output_path
            except Exception as e:
                with self._lock:
                    self._failed_count += 1
                logger.error(f"可视化任务失败: {output_path} - {e}")
                if callback:
                    callback(output_path, e)
                raise

        future = self._executor.submit(_task)
        with self._lock:
            self._pending.add(future)
        return future

    def _drain_until_capacity(self):
        while True:
            with self._lock:
                self._pending = {future for future in self._pending if not future.done()}
                if len(self._pending) < self._max_pending:
                    return
                pending = set(self._pending)

            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                self._consume_future(future)

    def _consume_future(self, future: Future):
        try:
            future.result()
        except Exception:
            pass
        with self._lock:
            self._pending.discard(future)

    def wait_all(self, timeout: Optional[float] = None):
        with self._lock:
            pending = set(self._pending)

        for future in pending:
            try:
                future.result(timeout=timeout)
            except Exception:
                pass

        with self._lock:
            self._pending.clear()

    def get_stats(self) -> dict:
        with self._lock:
            pending_count = len([future for future in self._pending if not future.done()])
            return {
                "completed": self._completed_count,
                "failed": self._failed_count,
                "pending": pending_count,
            }

    def shutdown(self, wait_for_tasks: bool = True):
        self._executor.shutdown(wait=wait_for_tasks)


_visualizer: Optional[AsyncVisualizer] = None
_init_lock = threading.Lock()


def get_async_visualizer(max_threads: int = 2, max_pending: int = 4) -> AsyncVisualizer:
    global _visualizer

    if _visualizer is None:
        with _init_lock:
            if _visualizer is None:
                _visualizer = AsyncVisualizer(
                    max_threads=max_threads,
                    max_pending=max_pending,
                )

    return _visualizer


def shutdown_async_visualizer():
    global _visualizer

    if _visualizer is not None:
        with _init_lock:
            if _visualizer is not None:
                _visualizer.shutdown(wait_for_tasks=True)
                _visualizer = None
