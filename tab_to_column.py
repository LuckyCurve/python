"""监听剪贴板变化，自动将制表符分隔数据转换为每行一个数值"""

import re
import sys
import ctypes
import win32clipboard
import win32con
import win32gui
from ctypes import wintypes

WM_CLIPBOARDUPDATE = 0x031D
HWND_MESSAGE = -3

wintypes.LRESULT = wintypes.LPARAM

user32 = ctypes.windll.user32
user32.AddClipboardFormatListener.restype = wintypes.BOOL
user32.AddClipboardFormatListener.argtypes = [wintypes.HWND]
user32.RemoveClipboardFormatListener.restype = wintypes.BOOL
user32.RemoveClipboardFormatListener.argtypes = [wintypes.HWND]
user32.GetMessageW.restype = wintypes.BOOL
user32.GetMessageW.argtypes = [
    ctypes.POINTER(wintypes.MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
]
user32.TranslateMessage.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.DispatchMessageW.restype = wintypes.LRESULT
user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.PostQuitMessage.restype = None
user32.PostQuitMessage.argtypes = [wintypes.INT]

kernel32 = ctypes.windll.kernel32
CTRL_C_EVENT = 0
CTRL_BREAK_EVENT = 1


class ClipboardListener:
    def __init__(self):
        self.hwnd = None
        self.last_content = ""
        self.listener_active = False
        self.running = False
        self.main_thread_id = None

    def has_numeric(self, value: str) -> bool:
        """判断字符串中是否包含数字"""
        value = value.strip()
        if not value:
            return False

        numeric_pattern = r"\d+([.,]\d+)?"
        return bool(re.search(numeric_pattern, value))

    def convert_to_column(self, data: str) -> str:
        """将制表符/换行符分隔的数据转换为每行一个数值，只保留包含数字的内容"""
        values = []
        for value in re.split(r"[\t\n]", data):
            cleaned = value.replace(",", "").strip()
            if self.has_numeric(cleaned):
                values.append(cleaned)
        return "\n".join(values)

    def wnd_proc(self, hwnd, msg, wParam, lParam):
        """窗口过程函数，处理系统消息"""
        if msg == WM_CLIPBOARDUPDATE:
            self.handle_clipboard_update()
        elif msg == win32con.WM_DESTROY:
            self.cleanup()
            win32gui.PostQuitMessage(0)
        return win32gui.DefWindowProc(hwnd, msg, wParam, lParam)

    def handle_clipboard_update(self):
        """处理剪贴板更新事件"""
        if not self.running:
            return

        try:
            win32clipboard.OpenClipboard()
            try:
                if not win32clipboard.IsClipboardFormatAvailable(
                    win32con.CF_UNICODETEXT
                ):
                    return

                current = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)

                if current and current != self.last_content:
                    converted = self.convert_to_column(current)

                    if converted and converted != current:
                        win32clipboard.EmptyClipboard()
                        win32clipboard.SetClipboardData(
                            win32con.CF_UNICODETEXT, converted
                        )
                        self.last_content = converted
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            pass

    def create_window(self):
        """创建隐藏的消息窗口"""
        wc = win32gui.WNDCLASS()
        wc.hInstance = win32gui.GetModuleHandle(None)
        wc.lpszClassName = "ClipboardListenerWindow"
        wc.lpfnWndProc = self.wnd_proc

        class_atom = win32gui.RegisterClass(wc)

        self.hwnd = win32gui.CreateWindow(
            class_atom, "", 0, 0, 0, 0, 0, HWND_MESSAGE, 0, wc.hInstance, None
        )

        if not self.hwnd:
            raise RuntimeError("Failed to create message window")

    def cleanup(self):
        """清理资源"""
        if self.hwnd and self.listener_active:
            user32.RemoveClipboardFormatListener(self.hwnd)
            self.listener_active = False

    def run(self):
        """运行剪贴板监听器"""

        def console_ctrl_handler(ctrl_type):
            if ctrl_type == CTRL_C_EVENT or ctrl_type == CTRL_BREAK_EVENT:
                print("\n退出...")
                self.running = False
                self.cleanup()
                user32.PostThreadMessageW(self.main_thread_id, 0x0012, 0, 0)
                user32.DestroyWindow(self.hwnd)
                return True
            return False

        # 设置控制台事件处理器
        handler = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)(
            console_ctrl_handler
        )
        kernel32.SetConsoleCtrlHandler(handler, True)
        self.main_thread_id = kernel32.GetCurrentThreadId()

        try:
            self.create_window()

            if not user32.AddClipboardFormatListener(self.hwnd):
                raise RuntimeError("Failed to register clipboard format listener")

            self.listener_active = True
            self.running = True
            print("剪贴板监听器已启动，按 Ctrl+C 退出...")

            msg = wintypes.MSG()
            while self.running and user32.GetMessageW(ctypes.byref(msg), None, 0, 0):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

        except Exception:
            self.cleanup()


def main():
    listener = ClipboardListener()
    listener.run()


if __name__ == "__main__":
    main()
