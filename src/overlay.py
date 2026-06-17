"""
虚线框叠加层 — 使用 Win32 API 创建透明窗口，鼠标为中心显示绿色虚线框。
纯 Windows API 实现，不依赖 tkinter 透明色，稳定可靠。
"""
import ctypes
import ctypes.wintypes
import threading
import time

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

# Win32 常量
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_POPUP = 0x80000000
ULW_ALPHA = 0x00000002


class CaptureOverlay:
    """一个跟随鼠标的绿色虚线矩形窗口，始终置顶且点击穿透。"""

    def __init__(self, parent_root=None, width: int = 600, height: int = 400):
        self.width = width
        self.height = height
        self._active = False
        self._thread = None
        self._hwnd = None

    def start(self):
        if self._active:
            return
        self._active = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._active = False
        if self._hwnd:
            user32.PostMessageW(self._hwnd, 0x0010, 0, 0)  # WM_CLOSE

    def set_size(self, width: int, height: int):
        self.width = width
        self.height = height

    def _run(self):
        """主循环 — 在独立线程中运行消息泵"""
        # 注册窗口类
        wnd_class = ctypes.wintypes.WNDCLASSW()
        wnd_class.lpfnWndProc = _WNDPROC
        wnd_class.hInstance = kernel32.GetModuleHandleW(None)
        wnd_class.lpszClassName = "CaptureOverlayClass"
        wnd_class.hbrBackground = gdi32.GetStockObject(5)  # NULL_BRUSH
        atom = user32.RegisterClassW(ctypes.byref(wnd_class))
        if not atom:
            return  # 注册失败

        # 创建窗口
        self._hwnd = user32.CreateWindowExW(
            WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_TOOLWINDOW,
            ctypes.c_void_p(atom),
            "CaptureOverlay",
            WS_POPUP,
            0, 0, self.width, self.height,
            None, None,
            wnd_class.hInstance,
            None,
        )
        if not self._hwnd:
            return

        # 设置分层窗口（允许逐像素alpha）
        user32.SetLayeredWindowAttributes(self._hwnd, 0, 200, ULW_ALPHA)

        # 显示窗口
        user32.ShowWindow(self._hwnd, 1)

        # 设置定时器用于刷新（33ms ≈ 30fps）
        user32.SetTimer(self._hwnd, 1, 33, None)

        # 消息循环
        msg = ctypes.wintypes.MSG()
        while self._active:
            # 处理所有待处理消息
            while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):  # PM_REMOVE
                if msg.message == 0x0002:  # WM_DESTROY
                    break
                if msg.message == 0x0010:  # WM_CLOSE
                    user32.DestroyWindow(self._hwnd)
                    self._hwnd = None
                    break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

            if not self._hwnd:
                break

            # 更新位置和绘制
            self._update_frame()

            time.sleep(0.016)  # ~60fps实际上30fps就够了

        if self._hwnd:
            user32.DestroyWindow(self._hwnd)
            self._hwnd = None

    def _update_frame(self):
        """更新窗口位置（鼠标为中心）并重绘"""
        import pyautogui
        try:
            mx, my = pyautogui.position()
        except Exception:
            return

        left = mx - self.width // 2
        top = my - self.height // 2

        # 移动窗口
        user32.MoveWindow(self._hwnd, left, top, self.width, self.height, True)

        # 强制重绘
        user32.InvalidateRect(self._hwnd, None, True)
        user32.UpdateWindow(self._hwnd)


# 窗口过程（全局函数，由 Windows 调用）
@ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_uint, ctypes.c_ulong, ctypes.c_long)
def _WNDPROC(hwnd, msg, wparam, lparam):
    if msg == 0x000F:  # WM_PAINT
        _paint_overlay(hwnd)
        return 0
    if msg == 0x0113:  # WM_TIMER
        return 0
    if msg == 0x0002:  # WM_DESTROY
        user32.PostQuitMessage(0)
        return 0
    return user32.DefWindowProcW(ctypes.c_void_p(hwnd), msg, wparam, lparam)


def _paint_overlay(hwnd):
    """绘制绿色虚线框"""
    ps = ctypes.create_string_buffer(64)  # PAINTSTRUCT
    hdc = user32.BeginPaint(hwnd, ps)
    if not hdc:
        return

    # 获取窗口尺寸
    rect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top

    # 创建绿色画笔
    green_pen = gdi32.CreatePen(0, 2, 0x0000FF00)  # PS_SOLID, width=2, BGR green
    gdi32.SelectObject(hdc, green_pen)
    gdi32.SelectObject(hdc, gdi32.GetStockObject(5))  # NULL_BRUSH（空心矩形）

    # 绘制虚线效果的主矩形（用偏移的小矩形模拟）
    for offset in range(0, 12, 4):
        gdi32.Rectangle(hdc, 2 + offset, 2, 2 + offset + 2, h - 2)
        gdi32.Rectangle(hdc, w - 2 - offset, 2, w - 2 - offset - 2, h - 2)
        gdi32.Rectangle(hdc, 2, 2 + offset, w - 2, 2 + offset + 2)
        gdi32.Rectangle(hdc, 2, h - 2 - offset, w - 2, h - 2 - offset - 2)

    # 四角标记
    s = 10
    white_pen = gdi32.CreatePen(0, 1, 0x0000FF00)
    gdi32.SelectObject(hdc, white_pen)
    corners = [(2, 2), (w - 2, 2), (2, h - 2), (w - 2, h - 2)]
    for cx, cy in corners:
        gdi32.MoveToEx(hdc, cx, cy - s, None)
        gdi32.LineTo(hdc, cx, cy + s)
        gdi32.MoveToEx(hdc, cx - s, cy, None)
        gdi32.LineTo(hdc, cx + s, cy)

    gdi32.DeleteObject(green_pen)
    gdi32.DeleteObject(white_pen)
    user32.EndPaint(hwnd, ps)


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
