# 窗口透明度 / 最大化透视桌面

Windows 后台小工具，用来「透过最大化窗口看壁纸」，并和 Wallpaper Engine 互动。

包含两部分：

1. **窗口透明度**（`window_opacity.py`）：Alt+滚轮调节当前窗口不透明度；某窗口最大化时，按屏幕把同屏其它窗口最小化，并把最大化窗口调成半透明。
2. **壁纸点击转发**（`wallpaper_click_passthrough.ahk`）：窗口最大化时，客户区里的左键点击仍作用于当前窗口，同时复制一份给 Wallpaper Engine，不抢焦点、不点桌面图标。

## 功能

### Alt+滚轮调节透明度

- 先点一下要操作的窗口，按住 **Alt** 滚动滚轮。
- 向上更不透明，向下更透明（默认最低约 15%，避免窗口完全消失）。
- 调节时窗口上方会短暂显示「不透明度 xx%」。

### 最大化透视（按屏幕）

- 某个窗口**最大化**时：同一块屏幕上的其它窗口会被最小化，最大化窗口设为约 85% 不透明，壁纸能透出来。
- **还原**该窗口后：其它窗口按原来的位置和状态恢复。
- 多显示器独立处理：左边最大化不会动右边屏幕上的窗口。
- 同一屏幕上改最大化另一个窗口时，会切换透视目标，而不会把新窗口「顶回」普通大小。
- 启动时如果已经有窗口处于最大化，不会立刻动手；之后再执行一次最大化（或在托盘里重新勾选「最大化透视桌面」）才会生效。

### 壁纸点击转发（Wallpaper Engine）

- 仅当**鼠标下的窗口已最大化**，并且点在**内容区**（不是标题栏、关闭按钮、边框）时才会转发。
- 当前窗口照常收到点击；脚本只向 Wallpaper Engine 的壁纸窗口 `PostMessage`，不会激活桌面。
- 请在 Wallpaper Engine 中打开该壁纸的鼠标交互。
- 托盘图标「壁纸点击转发」可取消勾选「启用转发」临时关闭。

## 用法

双击 `启动.vbs`（会同时启动透明度和点击转发），或分别运行：

```powershell
python window_opacity.py
```

```text
C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe wallpaper_click_passthrough.ahk
```

任务栏右下角会出现两个托盘图标：

| 图标提示 | 右键菜单 |
| --- | --- |
| 窗口透明度：Alt+滚轮调节 | 最大化透视桌面、以管理员身份运行、退出 |
| 壁纸点击转发 | 启用转发、退出 |

调试透明度工具（保留控制台、写更详细日志）：

```powershell
python window_opacity.py --debug
```

日志默认写到 `%TEMP%\window-opacity.log`。

## 依赖

- **Python 3.8+**，只用标准库，不必 `pip install`。
- **AutoHotkey v2**（点击转发需要）。已安装到默认路径时，`启动.vbs` 会自动拉起脚本。

## 配置

编辑同目录下的 `config.json`（改完后请退出再重新启动透明度工具）：

| 项 | 含义 | 默认 |
| --- | --- | --- |
| `wheel_step` | Alt+滚轮每格改变的不透明度（0–255） | `10` |
| `min_opacity_percent` | 滚轮能调到的最低不透明度 | `15` |
| `maximize_peek_opacity_percent` | 最大化时的不透明度 | `85` |
| `maximize_peek_enabled` | 是否启用最大化透视 | `true` |
| `scan_interval_ms` | 扫描窗口状态的间隔 | `200` |
| `debug` | 写更详细日志 | `false` |
| `exclude_class_names` | 忽略的窗口类名 | `[]` |
| `exclude_title_keywords` | 标题包含这些字则忽略 | `[]` |

## 开始菜单与开机启动

```powershell
powershell -ExecutionPolicy Bypass -File .\安装开始菜单.ps1
powershell -ExecutionPolicy Bypass -File .\卸载开始菜单.ps1
powershell -ExecutionPolicy Bypass -File .\安装开机启动.ps1
powershell -ExecutionPolicy Bypass -File .\卸载开机启动.ps1
```

开始菜单和开机启动都指向 `启动.vbs`，因此会一并启动透明度工具和壁纸点击转发。

## 限制与已知问题

- **任务管理器等更高权限窗口**：普通权限下无法改透明度（UIPI）。请右键托盘选「以管理员身份运行」，通过 UAC 后再调。最小化任务管理器在普通权限下仍可工作。
- **微信（新版 weixin.exe / Qt）**：窗口本身已是分层透明度，用系统分层接口调节。
- **腾讯会议等 TXGuiFoundation 自绘窗口**：不能再用 `SetLayeredWindowAttributes`（会整窗变白），改为走 DWM 合成器；观感可能和普通窗口不完全一样。
- 部分全屏游戏、受保护窗口、个别 GPU 合成窗口可能不支持分层透明度。
- 壁纸点击转发只发给 Wallpaper Engine 的壁纸窗口，不会点到桌面图标；Wallpaper Engine 未运行或壁纸未开交互时，转发没有可见效果。
