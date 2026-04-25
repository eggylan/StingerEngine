# -*- coding: utf-8 -*-

import mod.client.extraClientApi as clientApi
from StingerEngine.include.clientTools import compCustomAudio, compGame, logger
from StingerEngine.include.modconfig import (
    CLIENT_NAME,
    ERROR_UI_CLSPATH,
    ERROR_UI_DEF,
    ERROR_UI_NAME,
    GAME_UI_CLSPATH,
    GAME_UI_DEF,
    GAME_UI_NAME,
    MAIN_INTERFACE_UI_CLSPATH,
    MAIN_INTERFACE_UI_DEF,
    MAIN_INTERFACE_UI_NAME,
    MOD_NAME,
    SERVER_NAME,
    UI_PUSH_DELAY,
)
ClientSystem = clientApi.GetClientSystemCls()


class EngineClient(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self._registered_ui = {}
        self._ui_push_timer = None
        
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

    def _register_ui(self, ui_name, ui_classpath, ui_def):
        if self._registered_ui.get(ui_name):
            return
        clientApi.RegisterUI(MOD_NAME, ui_name, ui_classpath, ui_def)
        self._registered_ui[ui_name] = True

    def _cancel_pending_push(self):
        if self._ui_push_timer:
            try:
                compGame.CancelTimer(self._ui_push_timer)
            except Exception:
                pass
            self._ui_push_timer = None

    def _schedule_push(self, ui_name, param=None):
        def _push_ui():
            self._ui_push_timer = None
            if param is None:
                clientApi.PushScreen(MOD_NAME, ui_name)
            else:
                clientApi.PushScreen(MOD_NAME, ui_name, param)

        self._cancel_pending_push()
        self._ui_push_timer = compGame.AddTimer(UI_PUSH_DELAY, _push_ui)

    
    def CreateMainInterfaceUI(self):
        self._register_ui(MAIN_INTERFACE_UI_NAME, MAIN_INTERFACE_UI_CLSPATH, MAIN_INTERFACE_UI_DEF)
        self._schedule_push(MAIN_INTERFACE_UI_NAME)

    def CreateGameUI(self,entry=None):
        self._register_ui(GAME_UI_NAME, GAME_UI_CLSPATH, GAME_UI_DEF)
        param = {"entry": entry} if entry else {}
        self._schedule_push(GAME_UI_NAME, param)

    def CreateErrorUI(self, err_info=""):
        self._register_ui(ERROR_UI_NAME, ERROR_UI_CLSPATH, ERROR_UI_DEF)
        err_info_msg = '错误信息：\n{}\n请截图并联系开发者解决该问题。'.format(err_info)
        param = {"err_info": err_info_msg}
        self._schedule_push(ERROR_UI_NAME, param)

    def ForceDisconnect(self):
        # 强制退出游戏
        self._cancel_pending_push()
        self.NotifyToServer("ForceDisconnect", {})

    def Destroy(self):
        self._cancel_pending_push()
        compCustomAudio.DisableOriginMusic(False) # 恢复原版音乐
        logger.info("EngineClient Destroyed")
