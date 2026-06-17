"""
虚线框叠加层 — 半透明绿色矩形窗口，跟随鼠标标识截图区域。
"""
import tkinter as tk


class CaptureOverlay:
    """半透明绿色虚线框，始终置顶跟随鼠标。"""

    def __init__(self, width=600, height=400):
        self.width = width
        self.height = height
        self._running = False
        self._root = None
        self._canvas = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._root = tk.Tk()
        self._root.title("截图区域指示器")
        self._root.overrideredirect(True)
        self._root.attributes('-topmost', True)
        self._root.attributes('-alpha', 0.45)
        self._root.configure(bg='black')
        self._root.geometry(f"{self.width}x{self.height}+0+0")

        self._canvas = tk.Canvas(
            self._root, width=self.width, height=self.height,
            bg='black', highlightthickness=0,
        )
        self._canvas.pack()

        self._update_loop()
        self._root.mainloop()

    def stop(self):
        self._running = False
        if self._root:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                pass
            self._root = None

    def set_size(self, width, height):
        self.width = width
        self.height = height

    def _draw(self):
        """绘制绿色虚线框"""
        self._canvas.delete("all")
        w, h = self.width, self.height

        # 虚线效果：分段绘制边框
        dash_len, gap_len = 8, 5
        # 上边
        x = 1
        while x < w:
            self._canvas.create_line(x, 1, min(x + dash_len, w), 1, fill='#00ff00', width=2)
            x += dash_len + gap_len
        # 下边
        x = 1
        while x < w:
            self._canvas.create_line(x, h - 1, min(x + dash_len, w), h - 1, fill='#00ff00', width=2)
            x += dash_len + gap_len
        # 左边
        y = 1
        while y < h:
            self._canvas.create_line(1, y, 1, min(y + dash_len, h), fill='#00ff00', width=2)
            y += dash_len + gap_len
        # 右边
        y = 1
        while y < h:
            self._canvas.create_line(w - 1, y, w - 1, min(y + dash_len, h), fill='#00ff00', width=2)
            y += dash_len + gap_len

        # 四角标记
        s = 12
        for cx, cy in [(1, 1), (w - 1, 1), (1, h - 1), (w - 1, h - 1)]:
            self._canvas.create_line(cx, cy - s, cx, cy + s, fill='#00ff00', width=1)
            self._canvas.create_line(cx - s, cy, cx + s, cy, fill='#00ff00', width=1)

    def _update_loop(self):
        """持续更新位置"""
        if not self._running or not self._root:
            return
        try:
            import pyautogui
            mx, my = pyautogui.position()
            left = mx - self.width // 2
            top = my - self.height // 2
            self._root.geometry(f"{self.width}x{self.height}+{left}+{top}")
            self._draw()
            self._root.update()
        except Exception:
            pass
        if self._running:
            self._root.after(40, self._update_loop)


def get_mouse_center_region(width: int, height: int) -> dict:
    """获取以鼠标为中心的截图区域坐标。"""
    import pyautogui
    mx, my = pyautogui.position()
    return {
        "left": max(0, mx - width // 2),
        "top": max(0, my - height // 2),
        "width": width,
        "height": height,
    }
