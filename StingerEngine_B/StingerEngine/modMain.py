# -*- coding: utf-8 -*-
# 介绍：StingerEngine 是一个基于 我的世界（Minecraft）网易版 的视觉小说开发框架。
# 该引擎提供了丰富的剧情表现功能，包括文本显示、角色立绘、背景切换、音乐音效控制、分支选择、变量标记和条件判断等。
# 本 Mod 基于 QuModLibs 框架构建，遵循其开发规范。

from .include.QuModLibs.QuMod import *

# ====== 创建 EasyMod 实例并注册系统 ======
myMod = EasyMod()

# 注册原生 Python 客户端/服务端系统（由 QuModLibs 统一管理生命周期）
myMod.regNativePyServer("StingerEngine", "StingerEngineServer", "EngineServer.EngineServer")
myMod.regNativePyClient("StingerEngine", "StingerEngineClient", "EngineClient.EngineClient")
