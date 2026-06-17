"""
虚线框叠加层 — 透明窗口显示鼠标为中心的截图区域。
使用 tkinter Toplevel 实现，与主窗口共享事件循环。
"""
import tkinter as tk


class CaptureOverlay:
    """一个绿色虚线矩形窗口，始终跟随鼠标，标识当前截图区域。"""

    def __init__(self, parent_root: tk.Tk, width: int = 600, height: int = 400):
        self.width = width
        self.height = height
        self._active = False
        self._parent = parent_root
        self._win: tk.Toplevel = None
        self._canvas: tk.Canvas = None
        self._dash_offset = 0
        self._job_id = None

    def start(self):
        """显示叠加层"""
        if self._active:
            return
        self._active = True
        self._create_window()
        self._update_loop()

    def stop(self):
        """隐藏叠加层"""
        self._active = False
        if self._job_id:
            self._parent.after_cancel(self._job_id)
            self._job_id = None
        if self._win:
            try:
                self._win.destroy()
            except Exception:
                pass
            self._win = None

    def set_size(self, width: int, height: int):
        """更新矩形尺寸（即时生效）"""
        self.width = width
        self.height = height
        if self._active:
            self._parent.after(0, self._refresh_now)

    def _create_window(self):
        """创建透明置顶窗口"""
        if self._win:
            return
        self._win = tk.Toplevel(self._parent)
        self._win.overrideredirect(True)
        self._win.attributes('-topmost', True)
        self._win.attributes('-alpha', 0.6)
        # 设置透明色：背景用纯黑，然后让黑色变为透明
        self._win.configure(bg='#010101')
        self._win.attributes('-transparentcolor', '#010101')

        self._canvas = tk.Canvas(
            self._win, width=self.width + 6, height=self.height + 6,
            bg='#010101', highlightthickness=0,
        )
        self._canvas.pack()

    def _refresh_now(self):
        """立即刷新一次位置和绘制"""
        try:
            self._draw_frame()
        except Exception:
            pass

    def _update_loop(self):
        """持续更新（约30fps）"""
        if not self._active:
            return
        try:
            self._draw_frame()
        except Exception:
            pass
        self._job_id = self._parent.after(33, self._update_loop)

    def _draw_frame(self):
        """绘制虚线框并更新位置"""
        import pyautogui
        mx, my = pyautogui.position()

        left = mx - self.width // 2
        top = my - self.height // 2

        self._win.geometry(f"{self.width + 6}x{self.height + 6}+{left - 3}+{top - 3}")
        self._canvas.config(width=self.width + 6, height=self.height + 6)

        self._canvas.delete("all")
        self._dash_offset = (self._dash_offset + 1) % 12

        # 虚线矩形
        self._canvas.create_rectangle(
            3, 3, self.width + 3, self.height + 3,
            outline='#00ff00', width=2,
            dash=(8, 4), dashoffset=self._dash_offset,
        )
        # 四角标记
        s = 12
        corners = [(3, 3), (self.width + 3, 3),
                   (3, self.height + 3), (self.width + 3, self.height + 3)]
        for cx, cy in corners:
            self._canvas.create_line(cx, cy - s, cx, cy + s, fill='#00ff00', width=1)
            self._canvas.create_line(cx - s, cy, cx + s, cy, fill='#00ff00', width=1)

        self._win.update_idletasks()


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
