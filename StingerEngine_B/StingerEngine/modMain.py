# -*- coding: utf-8 -*-
# 介绍：StingerEngine 是一个基于 我的世界（Minecraft）网易版 的视觉小说开发框架。
# 该引擎提供了丰富的剧情表现功能，包括文本显示、角色立绘、背景切换、音乐音效控制、分支选择、变量标记和条件判断等。

from mod.common.mod import Mod
from StingerEngine.include.modconfig import CLIENT_CLSPATH, CLIENT_NAME, MOD_NAME, SERVER_CLSPATH, SERVER_NAME


@Mod.Binding(name="StingerEngine", version="0.0.1")
class StingerEngine(object):

    def __init__(self):
        pass

    @Mod.InitServer()
    def StingerEngineServerInit(self):
        import mod.server.extraServerApi as serverApi
        serverApi.RegisterSystem(MOD_NAME, SERVER_NAME, SERVER_CLSPATH)

    @Mod.DestroyServer()
    def StingerEngineServerDestroy(self):
        pass

    @Mod.InitClient()
    def StingerEngineClientInit(self):
        import mod.client.extraClientApi as clientApi
        clientApi.RegisterSystem(MOD_NAME, CLIENT_NAME, CLIENT_CLSPATH)

    @Mod.DestroyClient()
    def StingerEngineClientDestroy(self):
        pass
