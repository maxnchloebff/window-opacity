#Requires AutoHotkey v2.0
#SingleInstance Force
Persistent
#UseHook
CoordMode "Mouse", "Screen"
A_MaxHotkeysPerInterval := 200

; 最大化窗口里的点击原样留给当前窗口（~ 前缀不拦截），
; 同时把一份鼠标消息 Post 给 Wallpaper Engine，不激活桌面、不抢焦点。

WM_MOUSEMOVE := 0x0200
WM_LBUTTONDOWN := 0x0201
WM_LBUTTONUP := 0x0202
WM_NCHITTEST := 0x0084
HTCLIENT := 1
MK_LBUTTON := 0x0001
SMTO_ABORTIFHUNG := 0x0002
GW_CHILD := 5
GW_HWNDNEXT := 2

g_enabled := true
g_pressHwnd := 0

A_IconTip := "壁纸点击转发（仅最大化窗口的客户区）"
A_TrayMenu.Delete()
A_TrayMenu.Add("启用转发", ToggleEnabled)
A_TrayMenu.Check("启用转发")
A_TrayMenu.Add()
A_TrayMenu.Add("退出", (*) => ExitApp())

ToggleEnabled(*) {
    global g_enabled
    g_enabled := !g_enabled
    if g_enabled
        A_TrayMenu.Check("启用转发")
    else
        A_TrayMenu.Uncheck("启用转发")
}

~LButton:: {
    global g_enabled, g_pressHwnd
    g_pressHwnd := 0
    if !g_enabled
        return
    if !GetClickContext(&winHwnd, &sx, &sy)
        return
    target := FindWallpaperTarget(sx, sy)
    if !target
        return
    PostMouse(target, WM_MOUSEMOVE, MK_LBUTTON, sx, sy)
    PostMouse(target, WM_LBUTTONDOWN, MK_LBUTTON, sx, sy)
    g_pressHwnd := target
}

~LButton Up:: {
    global g_pressHwnd
    if !g_pressHwnd || !WinExist("ahk_id " g_pressHwnd)
        return
    MouseGetPos &sx, &sy
    PostMouse(g_pressHwnd, WM_LBUTTONUP, 0, sx, sy)
    g_pressHwnd := 0
}

GetClickContext(&winHwnd, &sx, &sy) {
    MouseGetPos &sx, &sy, &winHwnd
    if !winHwnd
        return false
    cls := WinGetClass("ahk_id " winHwnd)
    if cls ~= "i)^(Progman|WorkerW|Shell_TrayWnd|Shell_SecondaryTrayWnd|NotifyIconOverflowWindow)$"
        return false
    if cls ~= "i)^WPE"
        return false
    try minMax := WinGetMinMax("ahk_id " winHwnd)
    catch
        return false
    if minMax != 1
        return false
    lParam := (sy & 0xFFFF) << 16 | (sx & 0xFFFF)
    hit := 0
    ok := DllCall("user32\SendMessageTimeoutW"
        , "ptr", winHwnd
        , "uint", WM_NCHITTEST
        , "ptr", 0
        , "ptr", lParam
        , "uint", SMTO_ABORTIFHUNG
        , "uint", 50
        , "uptr*", &hit)
    if !ok || hit != HTCLIENT
        return false
    return true
}

FindWallpaperTarget(x, y) {
    progman := DllCall("user32\FindWindowW", "wstr", "Progman", "ptr", 0, "ptr")
    if !progman
        return 0
    layer := 0
    child := DllCall("user32\GetWindow", "ptr", progman, "uint", GW_CHILD, "ptr")
    while child {
        if WinGetClass("ahk_id " child) = "WorkerW" {
            wpe := FindWpeChildAt(child, x, y)
            if wpe
                return PickClickHwnd(wpe, x, y)
        }
        child := DllCall("user32\GetWindow", "ptr", child, "uint", GW_HWNDNEXT, "ptr")
    }
    return 0
}

FindWpeChildAt(parent, x, y) {
    child := DllCall("user32\GetWindow", "ptr", parent, "uint", GW_CHILD, "ptr")
    while child {
        cls := WinGetClass("ahk_id " child)
        if (cls = "WPEDesktopCEFWindow" || cls = "WPECloneView") && PointInWindow(child, x, y)
            return child
        child := DllCall("user32\GetWindow", "ptr", child, "uint", GW_HWNDNEXT, "ptr")
    }
    return 0
}

PickClickHwnd(root, x, y) {
    for cls in ["Chrome_RenderWidgetHostHWND", "Chrome_WidgetWin_1"] {
        found := FindDescendantClassAt(root, cls, x, y)
        if found
            return found
    }
    return root
}

FindDescendantClassAt(hwnd, wantClass, x, y) {
    if WinGetClass("ahk_id " hwnd) = wantClass && PointInWindow(hwnd, x, y)
        return hwnd
    child := DllCall("user32\GetWindow", "ptr", hwnd, "uint", GW_CHILD, "ptr")
    while child {
        found := FindDescendantClassAt(child, wantClass, x, y)
        if found
            return found
        child := DllCall("user32\GetWindow", "ptr", child, "uint", GW_HWNDNEXT, "ptr")
    }
    return 0
}

PointInWindow(hwnd, x, y) {
    rect := Buffer(16)
    if !DllCall("user32\GetWindowRect", "ptr", hwnd, "ptr", rect)
        return false
    l := NumGet(rect, 0, "int")
    t := NumGet(rect, 4, "int")
    r := NumGet(rect, 8, "int")
    b := NumGet(rect, 12, "int")
    return x >= l && x < r && y >= t && y < b
}

PostMouse(hwnd, msg, wParam, screenX, screenY) {
    pt := Buffer(8)
    NumPut("int", screenX, pt, 0)
    NumPut("int", screenY, pt, 4)
    DllCall("user32\ScreenToClient", "ptr", hwnd, "ptr", pt)
    cx := NumGet(pt, 0, "int")
    cy := NumGet(pt, 4, "int")
    lParam := (cy & 0xFFFF) << 16 | (cx & 0xFFFF)
    DllCall("user32\PostMessageW", "ptr", hwnd, "uint", msg, "uptr", wParam, "uptr", lParam)
}
