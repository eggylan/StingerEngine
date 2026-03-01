# -*- coding: utf-8 -*-

import mod.client.extraClientApi as clientApi
from mod_log import logger as logger
from include.modconfig import *
from include.clientTools import compCustomAudio
ClientSystem = clientApi.GetClientSystemCls()


class EngineClient(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        
        # ====== 事件监听 ======
        self.EngineNameSpace = clientApi.GetEngineNamespace()
        self.EngineSystemName = clientApi.GetEngineSystemName()
        self.ListenForEngineEvent = lambda eventName, callback: self.ListenForEvent(
            self.EngineNameSpace, self.EngineSystemName, eventName, self, callback)
        self.ListenForLocalEvent = lambda eventName, callback: self.ListenForEvent(
            MOD_NAME, CLIENT_NAME, eventName, self, callback)
        self.ListenForServerEvent = lambda eventName, callback: self.ListenForEvent(
            MOD_NAME, SERVER_NAME, eventName, self, callback)
        self.UnListenForServerEvent = lambda eventName,callback: self.UnListenForEvent(
            MOD_NAME, SERVER_NAME, eventName, self,callback)
        
        # ========= UI初始化完成事件 =========
        self.ListenForEngineEvent("UiInitFinished", self.OnUiInitFinished)

    def OnUiInitFinished(self, eventData):
        # 注册并创建主界面UI
        compCustomAudio.DisableOriginMusic(True) # 禁止原版音乐
        self.CreateMainInterfaceUI()

    
    def CreateMainInterfaceUI(self):
        clientApi.PopScreen()
        clientApi.RegisterUI(MOD_NAME, MAIN_INTERFACE_UI_NAME, MAIN_INTERFACE_UI_CLSPATH, MAIN_INTERFACE_UI_DEF)
        clientApi.PushScreen(MOD_NAME, MAIN_INTERFACE_UI_NAME)

    def CreateGameUI(self,entry=None):
        clientApi.PopScreen()
        clientApi.RegisterUI(MOD_NAME, GAME_UI_NAME, GAME_UI_CLSPATH, GAME_UI_DEF)
        param = {"entry": entry} if entry else {}
        clientApi.PushScreen(MOD_NAME, GAME_UI_NAME, param)

    def CreateErrorUI(self, err_info=""):
        clientApi.PopScreen()
        clientApi.RegisterUI(MOD_NAME, ERROR_UI_NAME, ERROR_UI_CLSPATH, ERROR_UI_DEF)
        err_info_msg = '错误信息：\n{}\n请截图并联系开发者解决该问题。'.format(err_info)
        param = {"err_info": err_info_msg}
        clientApi.PushScreen(MOD_NAME, ERROR_UI_NAME, param)

    def ForceDisconnect(self):
        # 强制退出游戏
        clientApi.PopScreen()
        self.NotifyToServer("ForceDisconnect", {})

    def Destroy(self):
        compCustomAudio.DisableOriginMusic(False) # 恢复原版音乐
        clientApi.PopScreen()
        logger.info("EngineClient Destroyed")
