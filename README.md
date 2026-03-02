# StingerEngine

**StingerEngine** 是一个基于 **我的世界（Minecraft）网易版** 的视觉小说开发框架，以 Add-on 形式运行。该框架提供了丰富的剧情表现功能，让开发者能够在 Minecraft 中轻松制作视觉小说类游戏。

---

## 功能特性

- 📝 **对话文本显示** — 支持角色名与对话内容，内置打字机逐字显示效果
- 🖼️ **背景切换** — 动态切换场景背景图
- 🎵 **音乐与音效控制** — 播放/停止背景音乐（BGM）与音效（SFX），支持淡出
- 🌫️ **淡入 / 淡出过渡** — 场景切换时的屏幕过渡动画
- 🗂️ **分支选择菜单** — 提供玩家可选择的选项分支
- 🔢 **变量系统** — 在剧本中设置和读取任意变量（如好感度等）
- ❓ **条件判断** — 根据变量值执行不同的剧情命令
- 🏷️ **标签 / 跳转** — 通过 `label` 和 `jump` 实现剧情流程跳转
- 🛡️ **错误处理界面** — 脚本运行时异常会显示专用错误 UI
- 📦 **章节脚本系统** — 剧本以 Python 数据结构编写，便于扩展和维护

---

## 项目结构

```
StingerEngine/
├── StingerEngine_B/              # 行为包（Behavior Pack）
│   ├── manifest.json
│   ├── entities/
│   │   └── player.json           # 玩家实体（含断开连接事件）
│   └── StingerEngine/            # Mod 主体代码
│       ├── modMain.py            # 入口，注册客户端与服务端系统
│       ├── EngineServer.py       # 服务端系统（玩家管理、断线处理）
│       ├── EngineClient.py       # 客户端系统（UI 管理、BGM 控制）
│       ├── include/
│       │   ├── modconfig.py      # 配置常量
│       │   ├── clientTools.py    # 客户端工具函数（音频、通知）
│       │   └── serverTools.py    # 服务端工具函数（Player 类）
│       ├── uiScript/
│       │   ├── MainInterfaceUI.py  # 主菜单界面脚本
│       │   ├── GameUI.py           # 游戏界面脚本（剧本执行引擎）
│       │   └── ErrorUI.py          # 错误界面脚本
│       └── chapters/
│           └── demo.py           # 内置演示章节脚本
└── StingerEngine_R/              # 资源包（Resource Pack）
    ├── manifest.json
    ├── ui/                       # UI 布局定义（JSON）
    │   ├── MainInterfaceUI.json
    │   ├── GameUI.json
    │   └── ErrorUI.json
    └── textures/
        └── modTextures/          # Mod 内置贴图资源
```

---

## 快速开始

### 环境要求

- 我的世界（Minecraft）**网易版**，引擎版本 **≥ 1.18.0**
- 章节脚本使用 Python 编写，由 Minecraft 网易版引擎内置的 Python 运行时执行，**无需额外安装 Python 环境**

### 安装

1. 将 `StingerEngine_B` 文件夹放入存档的行为包目录，将 `StingerEngine_R` 放入资源包目录。
2. 确认存档根目录下的 `world_behavior_packs.json` 和 `world_resource_packs.json` 中已引用对应包的 `pack_id`（项目已包含示例配置文件）。
3. 启动存档后，框架会自动初始化，显示主菜单界面。

### 编写章节脚本

在 `StingerEngine_B/StingerEngine/chapters/` 目录下创建新的 Python 文件，参照 `demo.py` 的格式编写剧本数据：

```python
# -*- coding: utf-8 -*-
script_data = [
    {"type": "bg", "image": "textures/modTextures/your_bg"},
    {"type": "fade_in", "duration": 1.5},
    {"type": "music", "file": "your_bgm", "action": "play"},

    {"type": "text", "speaker": "角色A", "content": "你好，世界！"},
    {
        "type": "menu",
        "title": "你想怎么回应？",
        "choices": [
            {"label": "route_a", "text": "热情地打招呼"},
            {"label": "route_b", "text": "沉默不语"}
        ]
    },

    {"type": "label", "name": "route_a"},
    {"type": "set_var", "variable": "favorability", "value": 1},
    {"type": "text", "speaker": "我", "content": "你好！"},
    {"type": "jump", "target": "end"},

    {"type": "label", "name": "route_b"},
    {"type": "text", "speaker": "我", "content": "（保持沉默）"},

    {"type": "label", "name": "end"},
    {"type": "fade_out", "duration": 2.0},
    {"type": "return_to_title"}
]
```

在 `MainInterfaceUI.py` 中将章节名传入 `CreateGameUI`：

```python
EngineClient.CreateGameUI("your_chapter_name")
```

---

## 剧本命令参考

| 命令类型 | 说明 | 示例 |
|---|---|---|
| `text` | 显示对话文本，可选 `typewriter_speed` 控制打字速度（单位：秒/次，默认 0.03） | `{"type": "text", "speaker": "苏瑶", "content": "你好", "typewriter_speed": 0.05}` |
| `bg` | 切换背景图 | `{"type": "bg", "image": "textures/modTextures/bg_cafe"}` |
| `fade_in` | 淡入效果 | `{"type": "fade_in", "duration": 1.0}` |
| `fade_out` | 淡出效果 | `{"type": "fade_out", "duration": 1.0}` |
| `wait` | 等待指定秒数 | `{"type": "wait", "duration": 0.5}` |
| `music` | 控制背景音乐（`play` / `stop` / `change`） | `{"type": "music", "file": "bgm_name", "action": "play"}` |
| `sfx` | 播放音效 | `{"type": "sfx", "file": "sfx_door", "loop": false}` |
| `set_var` | 设置变量 | `{"type": "set_var", "variable": "score", "value": 10}` |
| `label` | 定义跳转锚点 | `{"type": "label", "name": "scene_2"}` |
| `jump` | 跳转到标签 | `{"type": "jump", "target": "scene_2"}` |
| `condition` | 条件判断 | `{"type": "condition", "condition": "score >= 5", "true_commands": [...], "false_commands": [...]}` |
| `menu` | 显示选择菜单 | `{"type": "menu", "title": "请选择", "choices": [{"label": "a", "text": "选项A"}]}` |
| `return_to_title` | 返回主菜单 | `{"type": "return_to_title"}` |

---

## 内置演示

项目内置了一个完整的演示章节 **《雨后的咖啡香》**（`chapters/demo.py`），展示了以下功能：

- 场景背景与音乐切换
- 多角色对话
- 两段分支选择
- 变量记录（好感度）
- 条件判断与多结局
- 淡入 / 淡出过渡

在主菜单点击 **"新游戏"** 即可体验演示剧情。

---

## 版本信息

| 项目 | 版本 |
|---|---|
| StingerEngine | 0.0.1 |
| 最低引擎版本 | Minecraft 网易版 1.18.0 |
