"""
虚线框叠加层 — 透明窗口显示鼠标为中心的截图区域。
"""
import tkinter as tk
import threading


class CaptureOverlay:
    """显示一个半透明虚线矩形，标识当前截图区域（鼠标为中心）。"""

    def __init__(self, width: int = 400, height: int = 300):
        self.width = width
        self.height = height
        self._running = False
        self._thread = None
        self._root = None
        self._canvas = None
        self._dash_offset = 0  # 虚线滚动动画

    def start(self):
        """启动叠加层窗口（独立线程）"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """停止叠加层"""
        self._running = False
        if self._root:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                pass

    def set_size(self, width: int, height: int):
        """更新矩形尺寸"""
        self.width = width
        self.height = height

    def _run(self):
        """叠加层主循环"""
        self._root = tk.Tk()
        self._root.title("截图区域")
        self._root.overrideredirect(True)       # 无标题栏
        self._root.attributes('-topmost', True)  # 置顶
        self._root.attributes('-alpha', 0.55)    # 半透明
        self._root.configure(bg='black')

        # 让窗口不对鼠标事件做反应（点击穿透）
        try:
            self._root.attributes('-transparentcolor', 'black')
        except Exception:
            pass  # 某些系统不支持，降级使用alpha

        # 初始位置
        geo = f"{self.width + 4}x{self.height + 4}+0+0"
        self._root.geometry(geo)

        # Canvas画虚线框
        self._canvas = tk.Canvas(
            self._root, width=self.width + 4, height=self.height + 4,
            bg='black', highlightthickness=0, bd=0,
        )
        self._canvas.pack(fill="both", expand=True)

        self._update_loop()

    def _update_loop(self):
        """持续更新虚线框位置（以鼠标为中心）"""
        if not self._running or not self._root:
            return

        try:
            # 获取鼠标位置
            import pyautogui
            mx, my = pyautogui.position()

            # 计算矩形左上角
            left = mx - self.width // 2
            top = my - self.height // 2

            # 更新窗口位置
            self._root.geometry(f"{self.width + 4}x{self.height + 4}+{left - 2}+{top - 2}")

            # 画虚线矩形
            self._canvas.delete("all")
            # 滚动虚线效果
            self._dash_offset = (self._dash_offset + 1) % 12
            self._canvas.create_rectangle(
                2, 2, self.width + 2, self.height + 2,
                outline='#00ff00', width=2,
                dash=(8, 4),
                dashoffset=self._dash_offset,
            )
            # 四角小标记
            size = 10
            for cx, cy in [(2, 2), (self.width + 2, 2),
                           (2, self.height + 2), (self.width + 2, self.height + 2)]:
                self._canvas.create_line(
                    cx, cy + size, cx, cy - size,
                    fill='#00ff00', width=1,
                )
                self._canvas.create_line(
                    cx - size, cy, cx + size, cy,
                    fill='#00ff00', width=1,
                )

            self._root.update()

        except Exception:
            pass

        # 约30fps刷新
        if self._running:
            self._root.after(33, self._update_loop)


def get_mouse_center_region(width: int, height: int) -> dict:
    """
    获取以鼠标为中心的截图区域坐标。

    Returns:
        {"left": x, "top": y, "width": w, "height": h}
    """
    import pyautogui
    mx, my = pyautogui.position()
    return {
        "left": max(0, mx - width // 2),
        "top": max(0, my - height // 2),
        "width": width,
        "height": height,
    }
