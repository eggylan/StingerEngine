# Stinger Engine

Stinger Engine 是一个基于《我的世界》中国版 AddOn 与 ModAPI 的视觉小说开发框架，目标是在 Minecraft 场景内提供接近 AVG / VN 的剧情表现能力。

当前仓库已经包含一套可运行的基础框架：

- 客户端主界面、游戏界面、错误界面
- 剧情脚本解释器
- 打字机文本效果
- 背景切换、CG 显示、淡入淡出
- 角色立绘进场、切换、移动、隐藏
- BGM / SFX 播放控制
- 菜单分支、变量系统、条件判断、标签跳转
- 一个完整的 demo 剧本《雨后的咖啡香》

## ⚠️⚠️ Alpha 阶段警告

**本项目仍处于 Alpha 阶段，适合继续开发、验证设计和做原型，但暂不适合作为稳定发行版直接投入生产。**

当前的限制包括：

- API、脚本命令格式等仍可能变动
- 无存档读档、历史记录、自动推进等功能
- 错误处理尚未完善
- 当前服务端逻辑为单人体验，多人进入时会被主动断开
- demo 资源和脚本主要用于验证功能，不代表最终项目结构已经冻结

如果你准备基于本项目继续扩展，建议先在分支中验证自己的章节结构、资源规范和 UI 需求，再逐步固化接口。

## 项目定位

本项目是一个“Minecraft 中国版视觉小说运行壳”。

行为包负责：

- 注册客户端 / 服务端系统
- 载入章节脚本
- 解释剧情命令并驱动 UI
- 处理玩家进入、退出和单人限制

资源包负责：

- UI 定义文件
- 音频定义
- 图片、立绘、背景、CG 等资源

## 当前能力

脚本解释器已经支持以下剧情命令类型：

- label
- text
- bg
- fade_in
- fade_out
- wait
- show_image
- hide_image
- var
- jump
- condition
- menu
- music
- sfx
- return_to_title
- character_enter
- character_show
- character_update
- character_play_anim
- character_hide
- character_clear
- character_move
- character_scale

这意味着你已经可以组织出带有分支、条件解锁和基础演出效果的完整短篇剧情。
详见：[脚本指令集.md](/docs/脚本指令集.md)

## 目录说明

目录如下：

- StingerEngine_B/
	行为包。包含 Python 脚本、章节、系统注册与运行逻辑。
- StingerEngine_R/
	资源包。包含 UI、声音定义、贴图与演示资源。
- docs/
	项目文档。

行为包内部重点结构：

- StingerEngine/modMain.py
	AddOn 注册入口。
- StingerEngine/EngineClient.py
	客户端系统，负责 UI 初始化与界面切换。
- StingerEngine/EngineServer.py
	服务端系统，负责玩家管理和单人限制。
- StingerEngine/include/
	公共配置、客户端工具、服务端工具、剧情解释器。
- StingerEngine/chapters/
	剧情章节脚本。
- StingerEngine/uiScript/
	界面脚本。

## 已有内容

仓库当前包含一个可直接运行的示例章节：

- 章节入口：StingerEngine_B/StingerEngine/chapters/main.py
- 示例剧本：StingerEngine_B/StingerEngine/chapters/demo.py

示例剧本《雨后的咖啡香》演示了这些能力：

- 对话推进
- 角色登场与表情切换
- BGM 和音效播放
- 分支选择
- 好感度变量
- 条件分支解锁隐藏结局
- 结局跳转与返回标题

## 快速开始

### 1. 打开工程

使用 MC Studio 打开当前 AddOn 工程目录。

工程名称：Stinger Engine

命名空间：stinger

最低引擎版本：1.18.0

### 2. 运行默认流程

当前默认入口为：

- 加载主界面
- 点击开始
- 进入章节 main
- main 再导入 demo.script_data

如果你没有修改入口逻辑，直接运行后就会进入演示流程。

### 3. 新增自己的章节

在 StingerEngine_B/StingerEngine/chapters/ 下新增一个 Python 文件，例如：

```python
# -*- coding: utf-8 -*-

script_data = [
		{"type": "bg", "image": "textures/modTextures/default/bg_room"},
		{"type": "fade_in", "duration": 1.0},
		{"type": "text", "speaker": "旁白", "content": "新的故事开始了。"},
		{"type": "return_to_title"}
]
```

然后在主界面或其他入口中调用对应章节名，例如：

```python
EngineClient.CreateGameUI("your_chapter_name")
```

### 4. 修改默认章节入口

当前主入口文件为 StingerEngine_B/StingerEngine/chapters/main.py，它默认执行：

```python
from demo import script_data as script_data
```

你可以将它改成自己的章节模块，或者保留 main.py 作为统一转发入口。

## 脚本格式概览

剧情以 Python 列表形式组织，每个元素是一个命令字典。示例：

```python
script_data = [
		{"type": "var", "variable": "favorability", "operation": "set", "value": 0},
		{"type": "bg", "image": "textures/modTextures/demo/bg_cafe_rain"},
		{"type": "text", "speaker": "我", "content": "这是一句对白。"},
		{
				"type": "menu",
				"title": "如何回应？",
				"choices": [
						{"label": "route_a", "text": "选项 A"},
						{"label": "route_b", "text": "选项 B"}
				]
		},
		{"type": "label", "name": "route_a"},
		{"type": "text", "speaker": "系统", "content": "进入 A 路线。"}
]
```

### 条件表达式

当前条件判断不依赖 eval，而是使用内置表达式解析器。已支持：

- 比较运算：>、<、>=、<=、==、!=
- 逻辑关键字：[and]、[or]、[not]
- 括号
- 数字、布尔值、变量名

示例：

```python
{
		"type": "condition",
		"condition": "favorability >= 1 [and] found_notebook == True",
		"true_commands": [
				{"type": "jump", "target": "good_end"}
		],
		"false_commands": [
				{"type": "jump", "target": "normal_end"}
		]
}
```

## 资源约定

资源命名约定大致如下：

- 背景 / 立绘 / CG 通过图片路径引用
- BGM / SFX 通过 sound_definitions.json 中定义的音频 ID 引用
- demo 音频前缀采用 demo.bgm.* 和 demo.sfx.*

例如：

- 背景图：textures/modTextures/demo/bg_cafe_rain
- 立绘：textures/modTextures/demo/char_yao_normal
- BGM：demo.bgm.relax
- 音效：demo.sfx.door_open

建议你在正式项目中统一规划：

- 章节前缀
- 角色 ID
- 图片命名
- 音频命名
- UI 资源目录

否则后续剧本规模扩大后会很难维护。

## 当前已知限制

- 仅单人游戏，多人会自动断开新加入玩家
- 错误处理不完善
- 章节资源、UI 样式和脚本还在演进中

## FAQ

### 1. 这个项目是游戏成品吗？

不是。它更接近一个视觉小说开发框架和演示工程，而不是完整成品游戏。

### 2. 为什么多人进入时会被踢出？

因为当前服务端实现按单人体验设计。第二名玩家进入时会触发主动断开逻辑，避免多人状态与剧情 UI 流程互相干扰。

### 3. 如何切换到自己的剧本？

最简单的做法是：

- 在 chapters 目录新增章节文件
- 保持导出变量名为 script_data
- 在 main.py 中导入你的 script_data
- 或在入口 UI 中直接调用 CreateGameUI("你的章节名")

### 4. 报“未找到章节脚本”怎么办？

优先检查：

- 文件是否位于 StingerEngine_B/StingerEngine/chapters/
- 文件名是否与传入的 entry 一致
- 模块内是否导出了 script_data
- Python 文件编码和语法是否正确

### 5. 可以直接扩展成多章节项目吗？

可以。当前结构已经适合把每个章节拆到独立 Python 文件中，再由统一入口或章节选择界面进行跳转。

### 6. 可以做多人联机剧情吗？

理论上可以，但当前实现没有为多人状态同步、分支一致性、UI 生命周期冲突和音频表现做设计。如果要支持多人，需要重构服务端状态管理和客户端会话模型。

### 7. 为什么这里用 Python 写剧情？

因为当前工程直接运行在网易版 AddOn / ModAPI 的 Python 脚本体系中，使用 Python 列表和字典描述剧情命令，调试成本较低，适合快速迭代原型。

## 版权与许可证

本项目的代码部分，采用 Apache License 2.0 进行许可。

你可以：

- 使用、修改和分发代码
- 在保留许可证与声明的前提下进行二次开发
- 在商业或非商业项目中使用

你需要注意：

- 需要保留原始版权声明与许可证文本
- 修改后应明确说明变更
- 本项目按“现状”提供，不附带任何明示或暗示担保



本项目内附的demo中的剧本、美术、音频等，皆为CC0协议或AI生成，旨在验证可行性，不受 Apache License 2.0 影响。
