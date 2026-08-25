# -*- coding: utf-8 -*-
"""Alt+滚轮调节当前窗口透明度；按屏幕在最大化时透视桌面壁纸。"""

from __future__ import annotations

import ctypes
import json
import logging
import os
import sys
import time
from ctypes import POINTER, Structure, byref, sizeof, wintypes
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Win32 types / constants
# ---------------------------------------------------------------------------

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)

LRESULT = ctypes.c_int64 if sizeof(ctypes.c_void_p) == 8 else ctypes.c_long
LONG_PTR = ctypes.c_int64 if sizeof(ctypes.c_void_p) == 8 else ctypes.c_long

HWND = wintypes.HWND
HMENU = wintypes.HMENU
HICON = wintypes.HICON
HINSTANCE = wintypes.HINSTANCE
HHOOK = wintypes.HHOOK
UINT = wintypes.UINT
DWORD = wintypes.DWORD
WPARAM = wintypes.WPARAM
LPARAM = wintypes.LPARAM
BOOL = wintypes.BOOL
WCHAR = wintypes.WCHAR

WH_MOUSE_LL = 14
WM_MOUSEWHEEL = 0x020A
WM_COMMAND = 0x0111
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_QUERYENDSESSION = 0x0011
WM_ENDSESSION = 0x0016
WM_TIMER = 0x0113
WM_PAINT = 0x000F
WM_DISPLAYCHANGE = 0x007E
WM_RBUTTONUP = 0x0205
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_MOUSEMOVE = 0x0200
WM_NCHITTEST = 0x0084
WM_APP = 0x8000
WM_TRAY = WM_APP + 1
WM_NULL = 0x0000
WM_QUIT = 0x0012

VK_MENU = 0x12
GWL_EXSTYLE = -20
GWL_STYLE = -16
WS_CHILD = 0x40000000
WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000
WS_CAPTION = 0x00C00000
WS_EX_LAYERED = 0x00080000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOPMOST = 0x00000008
WS_EX_NOACTIVATE = 0x08000000
WS_EX_NOREDIRECTIONBITMAP = 0x00200000
LWA_ALPHA = 0x00000002
LWA_COLORKEY = 0x00000001

WCA_ACCENT_POLICY = 19
ACCENT_DISABLED = 0
ACCENT_ENABLE_TRANSPARENTGRADIENT = 2
ACCENT_FLAG_ENABLE_BLURBEHIND = 2

SW_HIDE = 0
SW_SHOWNORMAL = 1
SW_SHOWMINIMIZED = 2
SW_SHOWMAXIMIZED = 3
SW_SHOWNOACTIVATE = 4
SW_MINIMIZE = 6
SW_SHOWMINNOACTIVE = 7
SW_RESTORE = 9
SW_FORCEMINIMIZE = 11

WM_SYSCOMMAND = 0x0112
SC_MINIMIZE = 0xF020
SC_MAXIMIZE = 0xF030
SC_RESTORE = 0xF120

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
TASKMGR_CLASSES = {"TaskManagerWindow", "TaskManagerMain"}
TASKMGR_PROCESSES = {"taskmgr.exe"}
# 这些窗口用 UpdateLayeredWindow / DirectComposition 自绘，不能再 SetLayeredWindowAttributes
COMPOSITION_CLASSES = {
    "TXGuiFoundation",
    "WeChatMainWndForPC",
}
COMPOSITION_PROCESSES = {
    "wemeetapp.exe",
    "wemeetapp_new.exe",
    "wechat.exe",
    "weixin.exe",
    "wechatappex.exe",
    "qq.exe",
    "qqapp.exe",
}

GA_ROOT = 2
MONITOR_DEFAULTTONEAREST = 2
DWMWA_CLOAKED = 14

NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004

MF_STRING = 0x00000000
MF_SEPARATOR = 0x00000800
MF_CHECKED = 0x00000008
MF_GRAYED = 0x00000001
TPM_RIGHTBUTTON = 0x0002

IDI_APPLICATION = 32512
IMAGE_ICON = 1
LR_DEFAULTSIZE = 0x00000040
LR_SHARED = 0x00008000
LR_LOADFROMFILE = 0x00000010
SM_CXSMICON = 49
HTCLIENT = 1
MK_LBUTTON = 0x0001
SMTO_ABORTIFHUNG = 0x0002
GW_CHILD = 5
GW_HWNDNEXT = 2

CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001
COLOR_WINDOW = 5
CW_USEDEFAULT = 0x80000000
HWND_MESSAGE = HWND(-3)

ERROR_ALREADY_EXISTS = 183
ERROR_ACCESS_DENIED = 5

ID_TOGGLE_PEEK = 1001
ID_RESTART_ADMIN = 1003
ID_TOGGLE_WALLPAPER_CLICK = 1004
ID_EXIT = 1002
TIMER_SCAN = 1
TIMER_OSD = 2

SKIP_CLASSES = {
    "Shell_TrayWnd",
    "Shell_SecondaryTrayWnd",
    "Progman",
    "WorkerW",
    "NotifyIconOverflowWindow",
    "Windows.UI.Core.CoreWindow",
    "ForegroundStaging",
    "ApplicationManager_ImmersiveShellWindow",
    "ImmersiveLauncher",
    "SearchHost",
    "Shell_CharmWindow",
    "DummyDWMListenerWindow",
    "TaskListThumbnailWnd",
    "TaskListOverlayWnd",
    "SysShadow",
    "IME",
    "MSCTFIME UI",
    "XamlExplorerHostIslandWindow",
    "Windows.Internal.Shell.TabProxyWindow",
    "TopLevelWindowForOverflowXamlIsland",
    "Xaml_WindowedPopupClass",
    "Windows.UI.Input.InputSite.WindowClass",
    "NativeHWNDHost",
    "#32769",
    "Auto-Suggest Dropdown",
}


class POINT(Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class RECT(Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


class MSG(Structure):
    _fields_ = [
        ("hwnd", HWND),
        ("message", UINT),
        ("wParam", WPARAM),
        ("lParam", LPARAM),
        ("time", DWORD),
        ("pt", POINT),
    ]


class MSLLHOOKSTRUCT(Structure):
    _fields_ = [
        ("pt", POINT),
        ("mouseData", DWORD),
        ("flags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class WINDOWPLACEMENT(Structure):
    _fields_ = [
        ("length", UINT),
        ("flags", UINT),
        ("showCmd", UINT),
        ("ptMinPosition", POINT),
        ("ptMaxPosition", POINT),
        ("rcNormalPosition", RECT),
    ]


class WNDCLASSEXW(Structure):
    _fields_ = [
        ("cbSize", UINT),
        ("style", UINT),
        ("lpfnWndProc", ctypes.c_void_p),  # assigned from WNDPROC
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", HINSTANCE),
        ("hIcon", HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HANDLE),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", HICON),
    ]


class PAINTSTRUCT(Structure):
    _fields_ = [
        ("hdc", wintypes.HDC),
        ("fErase", BOOL),
        ("rcPaint", RECT),
        ("fRestore", BOOL),
        ("fIncUpdate", BOOL),
        ("rgbReserved", ctypes.c_byte * 32),
    ]


class GUID(Structure):
    _fields_ = [
        ("Data1", DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_byte * 8),
    ]


class NOTIFYICONDATAW(Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("hWnd", HWND),
        ("uID", UINT),
        ("uFlags", UINT),
        ("uCallbackMessage", UINT),
        ("hIcon", HICON),
        ("szTip", WCHAR * 128),
        ("dwState", DWORD),
        ("dwStateMask", DWORD),
        ("szInfo", WCHAR * 256),
        ("uVersion", UINT),
        ("szInfoTitle", WCHAR * 64),
        ("dwInfoFlags", DWORD),
        ("guidItem", GUID),
        ("hBalloonIcon", HICON),
    ]


class ACCENT_POLICY(Structure):
    _fields_ = [
        ("AccentState", DWORD),
        ("AccentFlags", DWORD),
        ("GradientColor", DWORD),
        ("AnimationId", DWORD),
    ]


class WINDOWCOMPOSITIONATTRIBDATA(Structure):
    _fields_ = [
        ("Attrib", DWORD),
        ("pvData", ctypes.c_void_p),
        ("cbData", ctypes.c_size_t),
    ]


WNDPROC = ctypes.WINFUNCTYPE(LRESULT, HWND, UINT, WPARAM, LPARAM)
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, WPARAM, LPARAM)
WNDENUMPROC = ctypes.WINFUNCTYPE(BOOL, HWND, LPARAM)
WINEVENTPROC = ctypes.WINFUNCTYPE(
    None, wintypes.HANDLE, DWORD, HWND, ctypes.c_long, ctypes.c_long, DWORD, DWORD
)

if sizeof(ctypes.c_void_p) == 8:
    _GetWindowLongPtr = user32.GetWindowLongPtrW
    _SetWindowLongPtr = user32.SetWindowLongPtrW
else:
    _GetWindowLongPtr = user32.GetWindowLongW
    _SetWindowLongPtr = user32.SetWindowLongW

_GetWindowLongPtr.restype = LONG_PTR
_GetWindowLongPtr.argtypes = [HWND, ctypes.c_int]
_SetWindowLongPtr.restype = LONG_PTR
_SetWindowLongPtr.argtypes = [HWND, ctypes.c_int, LONG_PTR]

user32.SetLayeredWindowAttributes.argtypes = [HWND, DWORD, ctypes.c_ubyte, DWORD]
user32.SetLayeredWindowAttributes.restype = BOOL
user32.GetLayeredWindowAttributes.argtypes = [
    HWND,
    POINTER(DWORD),
    POINTER(ctypes.c_ubyte),
    POINTER(DWORD),
]
user32.GetLayeredWindowAttributes.restype = BOOL
user32.CallNextHookEx.restype = LRESULT
user32.CallNextHookEx.argtypes = [HHOOK, ctypes.c_int, WPARAM, LPARAM]
user32.SetWindowsHookExW.restype = HHOOK
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, HINSTANCE, DWORD]
user32.UnhookWindowsHookEx.argtypes = [HHOOK]
user32.DefWindowProcW.restype = LRESULT
user32.DefWindowProcW.argtypes = [HWND, UINT, WPARAM, LPARAM]
user32.CreateWindowExW.restype = HWND
user32.MonitorFromWindow.restype = HWND
user32.MonitorFromWindow.argtypes = [HWND, DWORD]
user32.GetForegroundWindow.restype = HWND
user32.GetAncestor.restype = HWND
user32.GetAncestor.argtypes = [HWND, UINT]
user32.IsZoomed.restype = BOOL
user32.IsZoomed.argtypes = [HWND]
user32.IsIconic.restype = BOOL
user32.IsIconic.argtypes = [HWND]
user32.IsWindow.restype = BOOL
user32.IsWindowVisible.restype = BOOL
user32.LoadIconW.restype = HICON
user32.LoadIconW.argtypes = [HINSTANCE, wintypes.LPCWSTR]
user32.LoadImageW.restype = HICON
user32.LoadImageW.argtypes = [HINSTANCE, wintypes.LPCWSTR, UINT, ctypes.c_int, ctypes.c_int, UINT]
user32.DestroyIcon.argtypes = [HICON]
user32.DestroyIcon.restype = BOOL
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype = ctypes.c_int
user32.WindowFromPoint.restype = HWND
user32.WindowFromPoint.argtypes = [POINT]
user32.FindWindowW.restype = HWND
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.GetWindow.restype = HWND
user32.GetWindow.argtypes = [HWND, UINT]
user32.ScreenToClient.restype = BOOL
user32.ScreenToClient.argtypes = [HWND, POINTER(POINT)]
user32.SendMessageTimeoutW.restype = ctypes.c_size_t
user32.SendMessageTimeoutW.argtypes = [
    HWND,
    UINT,
    WPARAM,
    LPARAM,
    UINT,
    UINT,
    POINTER(ctypes.c_size_t),
]
user32.LoadCursorW.restype = wintypes.HANDLE
user32.LoadCursorW.argtypes = [HINSTANCE, wintypes.LPCWSTR]
user32.SetWinEventHook.restype = wintypes.HANDLE
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.PostMessageW.restype = BOOL
user32.PostMessageW.argtypes = [HWND, UINT, WPARAM, LPARAM]
user32.GetWindowThreadProcessId.restype = DWORD
user32.GetWindowThreadProcessId.argtypes = [HWND, POINTER(DWORD)]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.CreateMutexW.restype = wintypes.HANDLE
kernel32.QueryFullProcessImageNameW.restype = BOOL
user32.FillRect.argtypes = [wintypes.HDC, POINTER(RECT), wintypes.HANDLE]
gdi32.SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]
gdi32.SetTextColor.argtypes = [wintypes.HDC, DWORD]
gdi32.SetTextColor.restype = DWORD

try:
    _SetWindowCompositionAttribute = user32.SetWindowCompositionAttribute
    _SetWindowCompositionAttribute.argtypes = [HWND, POINTER(WINDOWCOMPOSITIONATTRIBDATA)]
    _SetWindowCompositionAttribute.restype = BOOL
except AttributeError:
    _SetWindowCompositionAttribute = None


def MAKEINTRESOURCE(value: int):
    return ctypes.cast(value, wintypes.LPCWSTR)

EVENT_OBJECT_LOCATIONCHANGE = 0x800B
EVENT_OBJECT_DESTROY = 0x8001
EVENT_SYSTEM_FOREGROUND = 0x0003
EVENT_OBJECT_STATECHANGE = 0x800A
WINEVENT_OUTOFCONTEXT = 0x0000
WINEVENT_SKIPOWNPROCESS = 0x0002
OBJID_WINDOW = 0


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
LOG_PATH = os.path.join(os.environ.get("TEMP", SCRIPT_DIR), "window-opacity.log")
ICON_PATH = os.path.join(SCRIPT_DIR, "icons", "window-opacity.ico")


def _load_config() -> dict:
    defaults = {
        "wheel_step": 10,
        "min_opacity_percent": 15,
        "maximize_peek_opacity_percent": 85,
        "maximize_peek_enabled": True,
        "wallpaper_click_enabled": True,
        "scan_interval_ms": 200,
        "debug": False,
        "exclude_class_names": [],
        "exclude_title_keywords": [],
    }
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        defaults.update(data or {})
    except FileNotFoundError:
        pass
    except Exception:
        logging.exception("读取 config.json 失败，使用默认值")
    return defaults


CFG = _load_config()


def load_app_icon() -> Tuple[int, bool]:
    if os.path.isfile(ICON_PATH):
        size = int(user32.GetSystemMetrics(SM_CXSMICON) or 16)
        icon = user32.LoadImageW(None, ICON_PATH, IMAGE_ICON, size, size, LR_LOADFROMFILE)
        if icon:
            return int(icon), True
        icon = user32.LoadImageW(
            None, ICON_PATH, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE
        )
        if icon:
            return int(icon), True
    fallback = user32.LoadIconW(None, MAKEINTRESOURCE(IDI_APPLICATION))
    return int(fallback or 0), False


def close_legacy_ahk_script() -> None:
    """关掉旧版单独托盘的 AutoHotkey 点击转发，避免出现第二个图标。"""
    needle = "wallpaper_click_passthrough.ahk"
    found: List[int] = []

    def _enum(hwnd, _lparam):
        title = _title(int(hwnd)).lower()
        cls = _class_name(int(hwnd)).lower()
        if needle in title and "autohotkey" in cls:
            found.append(int(hwnd))
        return True

    user32.EnumWindows(WNDENUMPROC(_enum), 0)
    for hwnd in found:
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    if found:
        logging.info("已关闭旧版壁纸点击转发脚本 %s 个", len(found))


def setup_logging() -> None:
    level = logging.DEBUG if CFG.get("debug") or "--debug" in sys.argv else logging.INFO
    logging.basicConfig(
        filename=LOG_PATH,
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        encoding="utf-8",
    )
    if "--debug" in sys.argv:
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(console)


# ---------------------------------------------------------------------------
# Window helpers
# ---------------------------------------------------------------------------

def _class_name(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def _title(hwnd: int) -> str:
    n = user32.GetWindowTextLengthW(hwnd)
    if n <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def _is_cloaked(hwnd: int) -> bool:
    value = DWORD(0)
    hr = dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, byref(value), sizeof(value))
    return hr == 0 and value.value != 0


def _process_basename(hwnd: int) -> str:
    pid = DWORD(0)
    user32.GetWindowThreadProcessId(hwnd, byref(pid))
    if not pid.value:
        return ""
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        return ""
    try:
        size = DWORD(32768)
        buf = ctypes.create_unicode_buffer(32768)
        if not kernel32.QueryFullProcessImageNameW(handle, 0, buf, byref(size)):
            return ""
        return os.path.basename(buf.value).lower()
    finally:
        kernel32.CloseHandle(handle)


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def is_task_manager(hwnd: int) -> bool:
    cls = _class_name(hwnd)
    if cls in TASKMGR_CLASSES:
        return True
    title = _title(hwnd)
    if title in ("任务管理器", "Task Manager"):
        return True
    return _process_basename(hwnd) in TASKMGR_PROCESSES


def is_manageable_window(hwnd: int, extra_skip: Optional[set] = None) -> bool:
    if not hwnd or not user32.IsWindow(hwnd):
        return False
    if not user32.IsWindowVisible(hwnd):
        return False
    if user32.GetAncestor(hwnd, GA_ROOT) != hwnd:
        return False

    style = int(_GetWindowLongPtr(hwnd, GWL_STYLE))
    ex = int(_GetWindowLongPtr(hwnd, GWL_EXSTYLE))
    if style & WS_CHILD:
        return False
    if _is_cloaked(hwnd):
        return False

    # 任务管理器常以更高完整性运行；最小化时 GetWindowRect 会变成约 26px 高，不能用尺寸判断
    if is_task_manager(hwnd):
        return not bool(user32.IsIconic(hwnd))

    if (ex & WS_EX_TOOLWINDOW) and not (ex & WS_EX_APPWINDOW):
        return False

    cls = _class_name(hwnd)
    if cls in SKIP_CLASSES:
        return False
    skip = extra_skip or set(CFG.get("exclude_class_names") or [])
    if cls in skip:
        return False

    title = _title(hwnd)
    if cls == "ApplicationFrameWindow" and not title:
        return False
    if not title and not (ex & WS_EX_APPWINDOW):
        return False
    for kw in CFG.get("exclude_title_keywords") or []:
        if kw and kw in title:
            return False

    rc = RECT()
    user32.GetWindowRect(hwnd, byref(rc))
    if rc.width < 80 or rc.height < 80:
        return False
    return True


def list_app_windows() -> List[int]:
    found: List[int] = []

    def _enum(hwnd, _lparam):
        if is_manageable_window(int(hwnd)):
            found.append(int(hwnd))
        return True

    cb = WNDENUMPROC(_enum)
    user32.EnumWindows(cb, 0)
    return found


_composition_alpha: Dict[int, int] = {}
_accent_applied: set = set()


def get_opacity(hwnd: int) -> int:
    if _needs_composition_opacity(hwnd):
        return int(_composition_alpha.get(hwnd, 255))
    _composition_alpha.pop(hwnd, None)
    color = DWORD(0)
    alpha = ctypes.c_ubyte(0)
    flags = DWORD(0)
    if not user32.GetLayeredWindowAttributes(hwnd, byref(color), byref(alpha), byref(flags)):
        return 255
    if flags.value & LWA_ALPHA:
        return int(alpha.value)
    return 255


def _needs_composition_opacity(hwnd: int) -> bool:
    """只有会因切换绘制路径而白屏的窗口才走合成器。

    新版微信 (weixin.exe / Qt) 已经带 WS_EX_LAYERED + LWA_ALPHA，继续用
    SetLayeredWindowAttributes 即可。合成器路径对这类窗口几乎看不出变化。
    经典 TXGuiFoundation / UpdateLayeredWindow 窗口才需要避开 LWA。
    """
    ex = int(_GetWindowLongPtr(hwnd, GWL_EXSTYLE))
    if ex & WS_EX_LAYERED:
        color = DWORD(0)
        alpha = ctypes.c_ubyte(0)
        flags = DWORD(0)
        if user32.GetLayeredWindowAttributes(hwnd, byref(color), byref(alpha), byref(flags)):
            if flags.value & (LWA_ALPHA | LWA_COLORKEY):
                return False
            return True
        return True
    if _class_name(hwnd) in COMPOSITION_CLASSES:
        return True
    proc = _process_basename(hwnd)
    if proc in COMPOSITION_PROCESSES or proc.startswith("wemeet"):
        return True
    return False


def _set_composition_opacity(hwnd: int, alpha: int) -> bool:
    if _SetWindowCompositionAttribute is None:
        return False
    accent = ACCENT_POLICY()
    if alpha >= 255:
        accent.AccentState = ACCENT_DISABLED
        accent.AccentFlags = 0
        accent.GradientColor = 0
        _composition_alpha.pop(hwnd, None)
        _accent_applied.discard(hwnd)
    else:
        accent.AccentState = ACCENT_ENABLE_TRANSPARENTGRADIENT
        accent.AccentFlags = ACCENT_FLAG_ENABLE_BLURBEHIND
        accent.GradientColor = (int(alpha) << 24)
        _composition_alpha[hwnd] = int(alpha)
        _accent_applied.add(hwnd)
    data = WINDOWCOMPOSITIONATTRIBDATA()
    data.Attrib = WCA_ACCENT_POLICY
    data.pvData = ctypes.cast(byref(accent), ctypes.c_void_p)
    data.cbData = sizeof(accent)
    ok = bool(_SetWindowCompositionAttribute(hwnd, byref(data)))
    if not ok:
        logging.debug("SetWindowCompositionAttribute 失败 hwnd=%s err=%s", hwnd, ctypes.get_last_error())
        _composition_alpha.pop(hwnd, None)
        _accent_applied.discard(hwnd)
    return ok


def _clear_composition_accent(hwnd: int) -> None:
    if hwnd not in _accent_applied or _SetWindowCompositionAttribute is None:
        return
    accent = ACCENT_POLICY()
    accent.AccentState = ACCENT_DISABLED
    data = WINDOWCOMPOSITIONATTRIBDATA()
    data.Attrib = WCA_ACCENT_POLICY
    data.pvData = ctypes.cast(byref(accent), ctypes.c_void_p)
    data.cbData = sizeof(accent)
    _SetWindowCompositionAttribute(hwnd, byref(data))
    _accent_applied.discard(hwnd)
    _composition_alpha.pop(hwnd, None)


def _set_layered_opacity(hwnd: int, alpha: int) -> bool:
    _clear_composition_accent(hwnd)
    ex = int(_GetWindowLongPtr(hwnd, GWL_EXSTYLE))
    if not (ex & WS_EX_LAYERED):
        kernel32.SetLastError(0)
        _SetWindowLongPtr(hwnd, GWL_EXSTYLE, ex | WS_EX_LAYERED)
        if ctypes.get_last_error() == ERROR_ACCESS_DENIED:
            logging.debug("无权限设置 WS_EX_LAYERED hwnd=%s", hwnd)
            return False
    kernel32.SetLastError(0)
    ok = bool(user32.SetLayeredWindowAttributes(hwnd, 0, alpha, LWA_ALPHA))
    if not ok:
        logging.debug("SetLayeredWindowAttributes 失败 hwnd=%s err=%s", hwnd, ctypes.get_last_error())
    return ok


def set_opacity(hwnd: int, alpha: int) -> bool:
    alpha = max(0, min(255, int(alpha)))
    if _needs_composition_opacity(hwnd):
        ok = _set_composition_opacity(hwnd, alpha)
        if ok:
            return True
        logging.info("合成透明度失败，跳过分层属性以免白屏 hwnd=%s class=%s", hwnd, _class_name(hwnd))
        return False
    return _set_layered_opacity(hwnd, alpha)


def clone_placement(pl: WINDOWPLACEMENT) -> WINDOWPLACEMENT:
    copied = WINDOWPLACEMENT()
    ctypes.memmove(ctypes.addressof(copied), ctypes.addressof(pl), sizeof(WINDOWPLACEMENT))
    return copied


def get_placement(hwnd: int) -> Optional[WINDOWPLACEMENT]:
    pl = WINDOWPLACEMENT()
    pl.length = sizeof(WINDOWPLACEMENT)
    if not user32.GetWindowPlacement(hwnd, byref(pl)):
        return None
    return clone_placement(pl)


def minimize_window(hwnd: int) -> bool:
    """普通窗口用 ShowWindow；任务管理器等受 UIPI 保护的窗口必须发 SC_MINIMIZE。"""
    if not hwnd or not user32.IsWindow(hwnd):
        return False
    if user32.IsIconic(hwnd):
        return True
    user32.ShowWindow(hwnd, SW_SHOWMINNOACTIVE)
    if user32.IsIconic(hwnd):
        return True
    user32.ShowWindow(hwnd, SW_FORCEMINIMIZE)
    if user32.IsIconic(hwnd):
        return True
    user32.PostMessageW(hwnd, WM_SYSCOMMAND, SC_MINIMIZE, 0)
    return True


def restore_window(hwnd: int, placement: WINDOWPLACEMENT) -> None:
    if not hwnd or not user32.IsWindow(hwnd):
        return
    tmp = clone_placement(placement)
    desired = int(placement.showCmd)
    tmp.showCmd = SW_SHOWNOACTIVATE
    if user32.SetWindowPlacement(hwnd, byref(tmp)):
        return
    if desired == SW_SHOWMAXIMIZED:
        user32.PostMessageW(hwnd, WM_SYSCOMMAND, SC_MAXIMIZE, 0)
    else:
        user32.PostMessageW(hwnd, WM_SYSCOMMAND, SC_RESTORE, 0)


def percent_to_alpha(percent: int) -> int:
    return int(round(max(0, min(100, percent)) * 255 / 100.0))


def alpha_to_percent(alpha: int) -> int:
    return int(round(max(0, min(255, alpha)) * 100 / 255.0))


# ---------------------------------------------------------------------------
# Peek (per-monitor maximize)
# ---------------------------------------------------------------------------

@dataclass
class PeekState:
    maximized_hwnd: int
    previous_alpha: int
    others: List[Tuple[int, WINDOWPLACEMENT]] = field(default_factory=list)


class PeekManager:
    def __init__(self) -> None:
        self.states: Dict[int, PeekState] = {}
        self._prev_max: Optional[Dict[int, int]] = None

    def enabled(self) -> bool:
        return bool(CFG.get("maximize_peek_enabled", True))

    def start(self, monitor: int, hwnd: int) -> None:
        if monitor in self.states:
            return
        others = self._collect_and_minimize_others(monitor, hwnd)
        prev = get_opacity(hwnd)
        peek_alpha = percent_to_alpha(int(CFG.get("maximize_peek_opacity_percent", 85)))
        set_opacity(hwnd, peek_alpha)
        self.states[monitor] = PeekState(hwnd, prev, others)
        logging.info("开始透视 monitor=%s hwnd=%s title=%s", monitor, hwnd, _title(hwnd))

    def switch(self, monitor: int, new_hwnd: int) -> None:
        """同一屏幕上最大化窗口切换：不要把新窗口还原回旧尺寸，也不要把旧窗口拉回前台。"""
        state = self.states.get(monitor)
        if state is None:
            self.start(monitor, new_hwnd)
            return
        old = state.maximized_hwnd
        if old == new_hwnd:
            return

        if user32.IsWindow(old):
            set_opacity(old, state.previous_alpha)

        others: List[Tuple[int, WINDOWPLACEMENT]] = []
        for hwnd, pl in state.others:
            if hwnd == new_hwnd or not user32.IsWindow(hwnd):
                continue
            others.append((hwnd, pl))

        if user32.IsWindow(old):
            old_pl = get_placement(old)
            if old_pl is not None:
                others.append((old, old_pl))
            minimize_window(old)

        already = {new_hwnd} | {h for h, _ in others}
        for hwnd, pl in self._collect_and_minimize_others(monitor, new_hwnd):
            if hwnd not in already:
                others.append((hwnd, pl))
                already.add(hwnd)

        prev = get_opacity(new_hwnd)
        peek_alpha = percent_to_alpha(int(CFG.get("maximize_peek_opacity_percent", 85)))
        set_opacity(new_hwnd, peek_alpha)
        self.states[monitor] = PeekState(new_hwnd, prev, others)
        logging.info("切换透视 %s -> %s", _title(old), _title(new_hwnd))

    def end(self, monitor: int, preserve_hwnd: int = 0) -> None:
        state = self.states.pop(monitor, None)
        if state is None:
            return
        if user32.IsWindow(state.maximized_hwnd) and state.maximized_hwnd != preserve_hwnd:
            set_opacity(state.maximized_hwnd, state.previous_alpha)
        for other, pl in reversed(state.others):
            if other == preserve_hwnd or not user32.IsWindow(other):
                continue
            restore_window(other, pl)
        logging.info("结束透视 monitor=%s hwnd=%s", monitor, state.maximized_hwnd)

    def end_all(self) -> None:
        for monitor in list(self.states.keys()):
            self.end(monitor)

    def _collect_and_minimize_others(
        self, monitor: int, keep_hwnd: int
    ) -> List[Tuple[int, WINDOWPLACEMENT]]:
        others: List[Tuple[int, WINDOWPLACEMENT]] = []
        for other in list_app_windows():
            if other == keep_hwnd:
                continue
            if int(user32.MonitorFromWindow(other, MONITOR_DEFAULTTONEAREST) or 0) != monitor:
                continue
            if user32.IsIconic(other):
                continue
            pl = get_placement(other)
            if pl is None:
                continue
            others.append((other, pl))
            minimize_window(other)
        return others

    def _foreground_root(self) -> int:
        fg = int(user32.GetForegroundWindow() or 0)
        if not fg:
            return 0
        return int(user32.GetAncestor(fg, GA_ROOT) or fg)

    def _should_keep_others_minimized(self, monitor: int, keep_hwnd: int) -> bool:
        """最上层窗口仍是这块屏幕上的最大化窗口时，才继续把其它窗口收起来。

        从任务栏打开普通窗口 B 时，B 会抢到焦点，此时先不动 B；
        再点回最大化的 A 后，B 应被重新最小化。
        """
        if not user32.IsWindow(keep_hwnd) or user32.IsIconic(keep_hwnd) or not user32.IsZoomed(keep_hwnd):
            return False
        fg_root = self._foreground_root()
        if not fg_root:
            return True
        if fg_root == keep_hwnd:
            return True
        fg_monitor = int(user32.MonitorFromWindow(fg_root, MONITOR_DEFAULTTONEAREST) or 0)
        if fg_monitor != monitor:
            return True
        if not is_manageable_window(fg_root):
            return True
        return False

    def _merge_minimized(self, state: PeekState, newly: List[Tuple[int, WINDOWPLACEMENT]]) -> None:
        if not newly:
            return
        index = {hwnd: i for i, (hwnd, _) in enumerate(state.others)}
        for hwnd, pl in newly:
            if hwnd in index:
                state.others[index[hwnd]] = (hwnd, pl)
            else:
                index[hwnd] = len(state.others)
                state.others.append((hwnd, pl))
        logging.info(
            "透视中重新最小化 %s",
            ", ".join(_title(hwnd) or str(hwnd) for hwnd, _ in newly),
        )

    def _enforce_others_minimized(self, monitor: int, keep_hwnd: int) -> None:
        state = self.states.get(monitor)
        if state is None:
            return
        if not self._should_keep_others_minimized(monitor, keep_hwnd):
            return
        newly = self._collect_and_minimize_others(monitor, keep_hwnd)
        self._merge_minimized(state, newly)

    def _pick_maximized(self) -> Dict[int, int]:
        by_monitor: Dict[int, List[int]] = {}
        fg = int(user32.GetForegroundWindow() or 0)
        fg_root = int(user32.GetAncestor(fg, GA_ROOT) or 0) if fg else 0

        for hwnd in list_app_windows():
            if user32.IsIconic(hwnd) or not user32.IsZoomed(hwnd):
                continue
            monitor = int(user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST) or 0)
            if not monitor:
                continue
            by_monitor.setdefault(monitor, []).append(hwnd)

        picked: Dict[int, int] = {}
        for monitor, hwnds in by_monitor.items():
            prev = None if self._prev_max is None else self._prev_max.get(monitor)
            current = self.states[monitor].maximized_hwnd if monitor in self.states else None
            if fg_root in hwnds:
                picked[monitor] = fg_root
                continue
            newcomers = [h for h in hwnds if h != prev and h != current]
            if newcomers:
                picked[monitor] = newcomers[0]
                continue
            if current in hwnds:
                picked[monitor] = current
                continue
            picked[monitor] = hwnds[0]
        return picked

    def scan(self) -> None:
        if not self.enabled():
            if self.states:
                self.end_all()
            return

        maximized = self._pick_maximized()

        for monitor in list(self.states.keys()):
            current = self.states[monitor].maximized_hwnd
            target = maximized.get(monitor)
            if target == current:
                self._enforce_others_minimized(monitor, current)
                continue
            if target:
                self.switch(monitor, target)
            else:
                self.end(monitor)

        # 启动时已经最大化的窗口不立刻动手，只在之后「新发生的最大化」时透视
        if self._prev_max is None:
            self._prev_max = maximized
            return

        for monitor, hwnd in maximized.items():
            if monitor not in self.states and self._prev_max.get(monitor) != hwnd:
                self.start(monitor, hwnd)

        self._prev_max = maximized


# ---------------------------------------------------------------------------
# Wallpaper Engine click passthrough
# ---------------------------------------------------------------------------

WALLPAPER_SKIP_CLASSES = {
    "Progman",
    "WorkerW",
    "Shell_TrayWnd",
    "Shell_SecondaryTrayWnd",
    "NotifyIconOverflowWindow",
}
WALLPAPER_LAYER_CLASSES = {"WPEDesktopCEFWindow", "WPECloneView"}
WALLPAPER_CLICK_CLASSES = ("Chrome_RenderWidgetHostHWND", "Chrome_WidgetWin_1")


class WallpaperClickForwarder:
    """最大化窗口客户区里的左键，复制一份给 Wallpaper Engine，不抢焦点。"""

    def __init__(self) -> None:
        self.press_hwnd = 0

    def enabled(self) -> bool:
        return bool(CFG.get("wallpaper_click_enabled", True))

    def on_button_down(self, x: int, y: int) -> None:
        self.press_hwnd = 0
        if not self.enabled():
            return
        if not self._is_maximized_client_click(x, y):
            return
        target = self._find_wallpaper_target(x, y)
        if not target:
            return
        self._post_mouse(target, WM_MOUSEMOVE, MK_LBUTTON, x, y)
        self._post_mouse(target, WM_LBUTTONDOWN, MK_LBUTTON, x, y)
        self.press_hwnd = target

    def on_button_up(self, x: int, y: int) -> None:
        hwnd = self.press_hwnd
        self.press_hwnd = 0
        if not hwnd or not user32.IsWindow(hwnd):
            return
        self._post_mouse(hwnd, WM_LBUTTONUP, 0, x, y)

    def _is_maximized_client_click(self, x: int, y: int) -> bool:
        hwnd = int(user32.WindowFromPoint(POINT(x, y)) or 0)
        if not hwnd:
            return False
        root = int(user32.GetAncestor(hwnd, GA_ROOT) or hwnd)
        cls = _class_name(root)
        if cls in WALLPAPER_SKIP_CLASSES or cls.startswith("WPE"):
            return False
        if user32.IsIconic(root) or not user32.IsZoomed(root):
            return False
        lparam = (y & 0xFFFF) << 16 | (x & 0xFFFF)
        hit = ctypes.c_size_t(0)
        ok = user32.SendMessageTimeoutW(
            root, WM_NCHITTEST, 0, lparam, SMTO_ABORTIFHUNG, 50, byref(hit)
        )
        return bool(ok) and int(hit.value) == HTCLIENT

    def _find_wallpaper_target(self, x: int, y: int) -> int:
        progman = int(user32.FindWindowW("Progman", None) or 0)
        if not progman:
            return 0
        child = int(user32.GetWindow(progman, GW_CHILD) or 0)
        while child:
            if _class_name(child) == "WorkerW":
                wpe = self._find_wpe_child_at(child, x, y)
                if wpe:
                    return self._pick_click_hwnd(wpe, x, y)
            child = int(user32.GetWindow(child, GW_HWNDNEXT) or 0)
        return 0

    def _find_wpe_child_at(self, parent: int, x: int, y: int) -> int:
        child = int(user32.GetWindow(parent, GW_CHILD) or 0)
        while child:
            if _class_name(child) in WALLPAPER_LAYER_CLASSES and self._point_in_window(child, x, y):
                return child
            child = int(user32.GetWindow(child, GW_HWNDNEXT) or 0)
        return 0

    def _pick_click_hwnd(self, root: int, x: int, y: int) -> int:
        for cls in WALLPAPER_CLICK_CLASSES:
            found = self._find_descendant_class_at(root, cls, x, y)
            if found:
                return found
        return root

    def _find_descendant_class_at(self, hwnd: int, want_class: str, x: int, y: int) -> int:
        if _class_name(hwnd) == want_class and self._point_in_window(hwnd, x, y):
            return hwnd
        child = int(user32.GetWindow(hwnd, GW_CHILD) or 0)
        while child:
            found = self._find_descendant_class_at(child, want_class, x, y)
            if found:
                return found
            child = int(user32.GetWindow(child, GW_HWNDNEXT) or 0)
        return 0

    def _point_in_window(self, hwnd: int, x: int, y: int) -> bool:
        rc = RECT()
        if not user32.GetWindowRect(hwnd, byref(rc)):
            return False
        return rc.left <= x < rc.right and rc.top <= y < rc.bottom

    def _post_mouse(self, hwnd: int, msg: int, wparam: int, screen_x: int, screen_y: int) -> None:
        pt = POINT(screen_x, screen_y)
        user32.ScreenToClient(hwnd, byref(pt))
        lparam = (pt.y & 0xFFFF) << 16 | (pt.x & 0xFFFF)
        user32.PostMessageW(hwnd, msg, wparam, lparam)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

class WindowOpacityApp:
    def __init__(self) -> None:
        self.peek = PeekManager()
        self.wallpaper = WallpaperClickForwarder()
        self.hwnd = HWND()
        self.osd_hwnd = HWND()
        self.osd_text = "不透明度 100%"
        self.hook = HHOOK()
        self.event_hooks: List[wintypes.HANDLE] = []
        self.nid = NOTIFYICONDATAW()
        self.app_icon = HICON()
        self._icon_owned = False
        self._mouse_proc = HOOKPROC(self._on_mouse)
        self._wnd_proc = WNDPROC(self._wndproc)
        self._osd_proc = WNDPROC(self._osd_wndproc)
        self._event_proc = WINEVENTPROC(self._on_win_event)
        self._class = "WindowOpacityHiddenHost"
        self._osd_class = "WindowOpacityOSD"
        self._mutex = wintypes.HANDLE()

    def run(self) -> int:
        close_legacy_ahk_script()
        if not self._ensure_single_instance():
            return 0
        self._maybe_hide_console()
        self._register_classes()
        self._create_hidden_window()
        self._create_osd()
        self._add_tray()
        self._install_hooks()
        interval = max(80, int(CFG.get("scan_interval_ms", 200)))
        user32.SetTimer(self.hwnd, TIMER_SCAN, interval, None)
        self.peek.scan()
        logging.info("WindowOpacity 已启动")
        return self._message_loop()

    def _ensure_single_instance(self) -> bool:
        retries = 25 if "--elevated" in sys.argv else 1
        for attempt in range(retries):
            kernel32.SetLastError(0)
            handle = kernel32.CreateMutexW(None, False, "Local\\WindowOpacityManager")
            if ctypes.get_last_error() != ERROR_ALREADY_EXISTS:
                self._mutex = handle
                return True
            if handle:
                kernel32.CloseHandle(handle)
            if attempt + 1 < retries:
                time.sleep(0.2)
        logging.info("已有实例在运行，退出")
        return False

    def _restart_elevated(self) -> None:
        if is_admin():
            return
        script = os.path.abspath(__file__)
        params = '"' + script + '" --elevated'
        if "--debug" in sys.argv:
            params += " --debug"
        show = 1 if "--debug" in sys.argv else 0
        shell32.ShellExecuteW.restype = ctypes.c_void_p
        ret = int(shell32.ShellExecuteW(None, "runas", sys.executable, params, SCRIPT_DIR, show) or 0)
        if ret > 32:
            logging.info("已请求以管理员身份重启")
            user32.DestroyWindow(self.hwnd)
        else:
            logging.info("管理员提权被取消或失败 ret=%s", ret)

    def _maybe_hide_console(self) -> None:
        if "--debug" in sys.argv:
            return
        console = kernel32.GetConsoleWindow()
        if console:
            user32.ShowWindow(console, SW_HIDE)

    def _register_classes(self) -> None:
        self.app_icon, self._icon_owned = load_app_icon()
        hinst = kernel32.GetModuleHandleW(None)
        wc = WNDCLASSEXW()
        wc.cbSize = sizeof(WNDCLASSEXW)
        wc.style = CS_HREDRAW | CS_VREDRAW
        wc.lpfnWndProc = ctypes.cast(self._wnd_proc, ctypes.c_void_p)
        wc.hInstance = hinst
        wc.hIcon = self.app_icon
        wc.hIconSm = self.app_icon
        wc.hCursor = user32.LoadCursorW(None, MAKEINTRESOURCE(32512))
        wc.hbrBackground = ctypes.c_void_p(COLOR_WINDOW + 1)
        wc.lpszClassName = self._class
        if not user32.RegisterClassExW(byref(wc)):
            err = ctypes.get_last_error()
            if err != 1410:  # already registered
                raise ctypes.WinError(err)

        oc = WNDCLASSEXW()
        oc.cbSize = sizeof(WNDCLASSEXW)
        oc.style = CS_HREDRAW | CS_VREDRAW
        oc.lpfnWndProc = ctypes.cast(self._osd_proc, ctypes.c_void_p)
        oc.hInstance = hinst
        oc.hbrBackground = ctypes.c_void_p(COLOR_WINDOW + 1)
        oc.lpszClassName = self._osd_class
        user32.RegisterClassExW(byref(oc))

    def _create_hidden_window(self) -> None:
        hinst = kernel32.GetModuleHandleW(None)
        self.hwnd = user32.CreateWindowExW(
            WS_EX_TOOLWINDOW,
            self._class,
            "WindowOpacity",
            0,
            0,
            0,
            0,
            0,
            None,
            None,
            hinst,
            None,
        )
        if not self.hwnd:
            raise ctypes.WinError(ctypes.get_last_error())
        user32.ShowWindow(self.hwnd, SW_HIDE)

    def _create_osd(self) -> None:
        hinst = kernel32.GetModuleHandleW(None)
        self.osd_hwnd = user32.CreateWindowExW(
            WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_LAYERED | WS_EX_NOACTIVATE,
            self._osd_class,
            "",
            WS_POPUP,
            0,
            0,
            196,
            44,
            None,
            None,
            hinst,
            None,
        )
        user32.SetLayeredWindowAttributes(self.osd_hwnd, 0, 230, LWA_ALPHA)

    def _add_tray(self) -> None:
        icon = self.app_icon or user32.LoadIconW(None, MAKEINTRESOURCE(IDI_APPLICATION))
        self.nid.cbSize = sizeof(NOTIFYICONDATAW)
        self.nid.hWnd = self.hwnd
        self.nid.uID = 1
        self.nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        self.nid.uCallbackMessage = WM_TRAY
        self.nid.hIcon = icon
        self.nid.szTip = "窗口透明度：Alt+滚轮 / 透视桌面 / 壁纸点击"
        if not shell32.Shell_NotifyIconW(NIM_ADD, byref(self.nid)):
            logging.warning("托盘图标添加失败")

    def _install_hooks(self) -> None:
        self.hook = user32.SetWindowsHookExW(WH_MOUSE_LL, self._mouse_proc, None, 0)
        if not self.hook:
            py_dll = "python%d%d.dll" % (sys.version_info.major, sys.version_info.minor)
            hmod = kernel32.GetModuleHandleW(py_dll) or kernel32.GetModuleHandleW(None)
            self.hook = user32.SetWindowsHookExW(WH_MOUSE_LL, self._mouse_proc, hmod, 0)
        if not self.hook:
            logging.error("鼠标钩子安装失败 err=%s", ctypes.get_last_error())
        else:
            logging.info("Alt+滚轮钩子已安装")
        for ev in (
            EVENT_OBJECT_DESTROY,
            EVENT_SYSTEM_FOREGROUND,
            EVENT_OBJECT_STATECHANGE,
        ):
            hh = user32.SetWinEventHook(
                ev, ev, None, self._event_proc, 0, 0,
                WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS,
            )
            if hh:
                self.event_hooks.append(hh)

    def _on_mouse(self, nCode: int, wParam: int, lParam: int) -> int:
        try:
            if nCode >= 0:
                if wParam == WM_MOUSEWHEEL:
                    if user32.GetAsyncKeyState(VK_MENU) & 0x8000:
                        info = ctypes.cast(lParam, POINTER(MSLLHOOKSTRUCT)).contents
                        delta = ctypes.c_short((info.mouseData >> 16) & 0xFFFF).value
                        self._adjust_foreground(1 if delta > 0 else -1)
                        return 1
                elif wParam == WM_LBUTTONDOWN:
                    info = ctypes.cast(lParam, POINTER(MSLLHOOKSTRUCT)).contents
                    self.wallpaper.on_button_down(int(info.pt.x), int(info.pt.y))
                elif wParam == WM_LBUTTONUP:
                    info = ctypes.cast(lParam, POINTER(MSLLHOOKSTRUCT)).contents
                    self.wallpaper.on_button_up(int(info.pt.x), int(info.pt.y))
        except Exception:
            logging.exception("鼠标钩子异常")
        return user32.CallNextHookEx(self.hook, nCode, wParam, lParam)

    def _on_win_event(self, _hook, event, hwnd, id_object, _id_child, _thread, _time) -> None:
        if id_object != OBJID_WINDOW:
            return
        if event in (
            EVENT_OBJECT_DESTROY,
            EVENT_SYSTEM_FOREGROUND,
            EVENT_OBJECT_STATECHANGE,
        ):
            try:
                self.peek.scan()
            except Exception:
                logging.exception("窗口事件扫描失败")

    def _adjust_foreground(self, direction: int) -> None:
        hwnd = int(user32.GetForegroundWindow() or 0)
        if not hwnd:
            return
        hwnd = int(user32.GetAncestor(hwnd, GA_ROOT) or hwnd)
        if not is_manageable_window(hwnd):
            return
        step = int(CFG.get("wheel_step", 10))
        mn = percent_to_alpha(int(CFG.get("min_opacity_percent", 15)))
        current = get_opacity(hwnd)
        new = max(mn, min(255, current + direction * step))
        if set_opacity(hwnd, new):
            # 最大化透视中用滚轮改透明度时，取消最大化后不要倒回旧值
            for state in self.peek.states.values():
                if state.maximized_hwnd == hwnd:
                    state.previous_alpha = new
            self._show_osd(hwnd, new)
            return
        if is_task_manager(hwnd) or ctypes.get_last_error() == ERROR_ACCESS_DENIED:
            if not is_admin():
                self._show_osd(hwnd, text="需要管理员权限")

    def _show_osd(self, target: int, alpha: Optional[int] = None, text: Optional[str] = None) -> None:
        self.osd_text = text if text else ("不透明度 %d%%" % alpha_to_percent(alpha or 255))
        rc = RECT()
        user32.GetWindowRect(target, byref(rc))
        w, h = (240, 44) if text else (196, 44)
        x = rc.left + max(0, (rc.width - w) // 2)
        y = rc.top + 48
        if y < 8:
            y = 8
        user32.SetWindowPos(self.osd_hwnd, HWND(-1), x, y, w, h, 0x0010 | 0x0040)
        user32.InvalidateRect(self.osd_hwnd, None, True)
        user32.ShowWindow(self.osd_hwnd, SW_SHOWNOACTIVATE)
        user32.SetTimer(self.hwnd, TIMER_OSD, 1600 if text else 900, None)

    def _wndproc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        try:
            if msg == WM_TIMER:
                if wparam == TIMER_SCAN:
                    self.peek.scan()
                elif wparam == TIMER_OSD:
                    user32.KillTimer(hwnd, TIMER_OSD)
                    user32.ShowWindow(self.osd_hwnd, SW_HIDE)
                return 0
            if msg == WM_TRAY:
                mouse = lparam & 0xFFFF
                if mouse in (WM_RBUTTONUP, WM_LBUTTONUP):
                    self._popup_menu()
                return 0
            if msg == WM_COMMAND:
                cmd = wparam & 0xFFFF
                if cmd == ID_TOGGLE_PEEK:
                    CFG["maximize_peek_enabled"] = not bool(CFG.get("maximize_peek_enabled", True))
                    self._save_config()
                    if not CFG["maximize_peek_enabled"]:
                        self.peek.end_all()
                    else:
                        self.peek._prev_max = {}
                        self.peek.scan()
                elif cmd == ID_TOGGLE_WALLPAPER_CLICK:
                    CFG["wallpaper_click_enabled"] = not bool(
                        CFG.get("wallpaper_click_enabled", True)
                    )
                    self._save_config()
                elif cmd == ID_RESTART_ADMIN:
                    self._restart_elevated()
                elif cmd == ID_EXIT:
                    user32.DestroyWindow(hwnd)
                return 0
            if msg == WM_DISPLAYCHANGE:
                self.peek.end_all()
                return 0
            if msg == WM_CLOSE:
                user32.DestroyWindow(hwnd)
                return 0
            if msg in (WM_QUERYENDSESSION, WM_ENDSESSION):
                self.peek.end_all()
                return 1
            if msg == WM_DESTROY:
                self._cleanup()
                user32.PostQuitMessage(0)
                return 0
        except Exception:
            logging.exception("窗口过程异常")
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _osd_wndproc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        if msg == WM_PAINT:
            ps = PAINTSTRUCT()
            hdc = user32.BeginPaint(hwnd, byref(ps))
            rc = RECT()
            user32.GetClientRect(hwnd, byref(rc))
            brush = gdi32.CreateSolidBrush(0x00222222)
            user32.FillRect(hdc, byref(rc), brush)
            gdi32.DeleteObject(brush)
            gdi32.SetBkMode(hdc, 1)
            gdi32.SetTextColor(hdc, 0x00FFFFFF)
            user32.DrawTextW(hdc, self.osd_text, -1, byref(rc), 0x0001 | 0x0004 | 0x0020)
            user32.EndPaint(hwnd, byref(ps))
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _popup_menu(self) -> None:
        menu = user32.CreatePopupMenu()
        peek_on = bool(CFG.get("maximize_peek_enabled", True))
        flags = MF_STRING | (MF_CHECKED if peek_on else 0)
        user32.AppendMenuW(menu, flags, ID_TOGGLE_PEEK, "最大化透视桌面")
        click_on = bool(CFG.get("wallpaper_click_enabled", True))
        click_flags = MF_STRING | (MF_CHECKED if click_on else 0)
        user32.AppendMenuW(menu, click_flags, ID_TOGGLE_WALLPAPER_CLICK, "壁纸点击转发")
        admin_flags = MF_STRING | (MF_GRAYED if is_admin() else 0)
        user32.AppendMenuW(menu, admin_flags, ID_RESTART_ADMIN, "以管理员身份运行")
        user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(menu, MF_STRING, ID_EXIT, "退出")
        pt = POINT()
        user32.GetCursorPos(byref(pt))
        user32.SetForegroundWindow(self.hwnd)
        user32.TrackPopupMenu(menu, TPM_RIGHTBUTTON, pt.x, pt.y, 0, self.hwnd, None)
        user32.PostMessageW(self.hwnd, WM_NULL, 0, 0)
        user32.DestroyMenu(menu)

    def _save_config(self) -> None:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            data = {}
        data["maximize_peek_enabled"] = bool(CFG.get("maximize_peek_enabled", True))
        data["wallpaper_click_enabled"] = bool(CFG.get("wallpaper_click_enabled", True))
        with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

    def _cleanup(self) -> None:
        try:
            user32.KillTimer(self.hwnd, TIMER_SCAN)
            user32.KillTimer(self.hwnd, TIMER_OSD)
            self.peek.end_all()
            if self.hook:
                user32.UnhookWindowsHookEx(self.hook)
                self.hook = HHOOK()
            for hh in self.event_hooks:
                user32.UnhookWinEvent(hh)
            self.event_hooks.clear()
            shell32.Shell_NotifyIconW(NIM_DELETE, byref(self.nid))
            if self._icon_owned and self.app_icon:
                user32.DestroyIcon(self.app_icon)
                self.app_icon = HICON()
                self._icon_owned = False
            if self.osd_hwnd:
                user32.DestroyWindow(self.osd_hwnd)
                self.osd_hwnd = HWND()
        except Exception:
            logging.exception("清理失败")

    def _message_loop(self) -> int:
        msg = MSG()
        while True:
            ret = user32.GetMessageW(byref(msg), None, 0, 0)
            if ret == 0 or ret == -1:
                break
            user32.TranslateMessage(byref(msg))
            user32.DispatchMessageW(byref(msg))
        return int(msg.wParam)


def main() -> int:
    setup_logging()
    try:
        return WindowOpacityApp().run()
    except Exception:
        logging.exception("启动失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
