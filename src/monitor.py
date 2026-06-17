"""
屏幕监控模块 — 定时截取指定区域，检测新消息。
使用mss截屏（比PIL快10倍），适合高频轮询。
"""
import time
import logging
import threading
from typing import Optional, Callable
import mss
import numpy as np

logger = logging.getLogger(__name__)


class ScreenMonitor:
    """定时截取屏幕指定区域，检测新消息后回调处理函数。"""

    def __init__(self, region: dict):
        """
        Args:
            region: {"left": x, "top": y, "width": w, "height": h}
        """
        self.region = region
        self.interval = 2.0  # 默认2秒检测一次
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._previous_text: str = ""
        self._on_new_message: Optional[Callable[[str], None]] = None
        self._sct = mss.mss()

    def set_callback(self, callback: Callable[[str], None]):
        """设置新消息回调函数。参数为新消息文本。"""
        self._on_new_message = callback

    def set_region(self, left, top, width, height):
        """动态更新截图区域"""
        self.region = {"left": left, "top": top, "width": width, "height": height}

    def set_interval(self, seconds: float):
        """设置轮询间隔（秒）"""
        self.interval = max(0.5, seconds)

    def capture(self) -> Optional[np.ndarray]:
        """截取指定区域的屏幕图像，返回numpy数组(BGR格式)"""
        try:
            screenshot = self._sct.grab(self.region)
            # mss返回BGRA，转BGR
            img = np.array(screenshot)
            return img[:, :, :3]  # 去掉alpha通道
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None

    def _run_loop(self, ocr_func, ai_func):
        """监控主循环（在线程中运行）"""
        logger.info("监控循环启动")
        # 首次截图建立基准
        initial = self.capture()
        if initial is not None:
            self._previous_text = ocr_func(initial)

        while self._running:
            try:
                time.sleep(self.interval)
                image = self.capture()
                if image is None:
                    continue

                current_text = ocr_func(image)

                # 检测新消息
                from .ocr_engine import extract_latest_message
                new_msg = extract_latest_message(current_text, self._previous_text)

                if new_msg:
                    logger.info(f"检测到新消息: {new_msg[:50]}...")
                    # 调用AI生成回复
                    reply = ai_func(new_msg)
                    if reply and self._on_new_message:
                        self._on_new_message(reply)

                self._previous_text = current_text

            except Exception as e:
                logger.error(f"监控循环异常: {e}")

        logger.info("监控循环已停止")

    def start(self, ocr_func, ai_func):
        """启动监控线程"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            args=(ocr_func, ai_func),
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        """停止监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
        logger.info("监控已停止")

    @property
    def is_running(self):
        return self._running
