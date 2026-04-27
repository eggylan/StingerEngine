# -*- coding: utf-8 -*-

import traceback
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
    SAVE_CONTINUE_QUERY,
    SAVE_CONTINUE_RESPONSE,
    SAVE_DELETE_REQUEST,
    SAVE_DELETE_RESPONSE,
    SAVE_LIST_REQUEST,
    SAVE_LIST_RESPONSE,
    SAVE_LOAD_REQUEST,
    SAVE_LOAD_RESPONSE,
    SAVE_WRITE_REQUEST,
    SAVE_WRITE_RESPONSE,
    SERVER_NAME,
    SYSTEM_MENU_UI_CLSPATH,
    SYSTEM_MENU_UI_DEF,
    SYSTEM_MENU_UI_NAME,
    UI_PUSH_DELAY,
)
ClientSystem = clientApi.GetClientSystemCls()


class EngineClient(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self._registered_ui = {}
        self._ui_push_timer = None
        self._save_response_listeners = []
        self._key_event_listeners = []
        self._game_ui_runtime = None
        
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
        self.ListenForEngineEvent("OnKeyPressInGame", self.OnKeyPressInGame)
        self.ListenForServerEvent(SAVE_LIST_RESPONSE, self.OnSaveListResponse)
        self.ListenForServerEvent(SAVE_WRITE_RESPONSE, self.OnSaveWriteResponse)
        self.ListenForServerEvent(SAVE_LOAD_RESPONSE, self.OnSaveLoadResponse)
        self.ListenForServerEvent(SAVE_DELETE_RESPONSE, self.OnSaveDeleteResponse)
        self.ListenForServerEvent(SAVE_CONTINUE_RESPONSE, self.OnSaveContinueResponse)

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

    def CreateGameUI(self, entry=None, startMode="new", resumeSlotId=None, resumeSnapshot=None):
        self._register_ui(GAME_UI_NAME, GAME_UI_CLSPATH, GAME_UI_DEF)
        if resumeSnapshot and not entry:
            entry = resumeSnapshot.get("entry")
        param = {"startMode": startMode}
        if entry:
            param["entry"] = entry
        if resumeSlotId:
            param["resumeSlotId"] = resumeSlotId
        if resumeSnapshot:
            param["resumeSnapshot"] = resumeSnapshot
        self._schedule_push(GAME_UI_NAME, param)

    def CreateSystemMenuUI(self, initialTab="save", context=None):
        self._register_ui(SYSTEM_MENU_UI_NAME, SYSTEM_MENU_UI_CLSPATH, SYSTEM_MENU_UI_DEF)
        param = {"initialTab": initialTab or "save"}
        if context:
            param["context"] = context
        self._schedule_push(SYSTEM_MENU_UI_NAME, param)

    def RegisterGameUIRuntime(self, runtime):
        self._game_ui_runtime = runtime

    def UnregisterGameUIRuntime(self, runtime):
        if self._game_ui_runtime == runtime:
            self._game_ui_runtime = None

    def GetGameUIRuntime(self):
        return self._game_ui_runtime

    def RegisterSaveResponseListener(self, listener):
        if listener and listener not in self._save_response_listeners:
            self._save_response_listeners.append(listener)

    def UnregisterSaveResponseListener(self, listener):
        if listener in self._save_response_listeners:
            self._save_response_listeners.remove(listener)

    def RegisterKeyEventListener(self, listener):
        if listener and listener not in self._key_event_listeners:
            self._key_event_listeners.append(listener)

    def UnregisterKeyEventListener(self, listener):
        if listener in self._key_event_listeners:
            self._key_event_listeners.remove(listener)

    def RequestSaveList(self, source=None):
        data = {}
        if source:
            data["source"] = source
        self.NotifyToServer(SAVE_LIST_REQUEST, data)

    def RequestSaveContinue(self, source=None):
        data = {}
        if source:
            data["source"] = source
        self.NotifyToServer(SAVE_CONTINUE_QUERY, data)

    def RequestSaveWrite(self, slot_id, snapshot, title=None, source=None):
        data = {"slot_id": slot_id, "snapshot": snapshot}
        if title:
            data["title"] = title
        if source:
            data["source"] = source
        self.NotifyToServer(SAVE_WRITE_REQUEST, data)

    def RequestSaveLoad(self, slot_id, source=None):
        data = {"slot_id": slot_id}
        if source:
            data["source"] = source
        self.NotifyToServer(SAVE_LOAD_REQUEST, data)

    def RequestSaveDelete(self, slot_id, source=None):
        data = {"slot_id": slot_id}
        if source:
            data["source"] = source
        self.NotifyToServer(SAVE_DELETE_REQUEST, data)

    def OnSaveListResponse(self, eventData):
        self._dispatch_save_response(SAVE_LIST_RESPONSE, eventData)

    def OnSaveWriteResponse(self, eventData):
        self._dispatch_save_response(SAVE_WRITE_RESPONSE, eventData)

    def OnSaveLoadResponse(self, eventData):
        self._dispatch_save_response(SAVE_LOAD_RESPONSE, eventData)

    def OnSaveDeleteResponse(self, eventData):
        self._dispatch_save_response(SAVE_DELETE_RESPONSE, eventData)

    def OnSaveContinueResponse(self, eventData):
        self._dispatch_save_response(SAVE_CONTINUE_RESPONSE, eventData)

    def OnKeyPressInGame(self, eventData):
        if not isinstance(eventData, dict):
            eventData = {}
        for listener in list(self._key_event_listeners):
            try:
                callback = getattr(listener, "OnKeyPressInGame", None)
                if callback:
                    callback(eventData)
            except Exception:
                logger.error("按键事件分发失败:\n{}".format(traceback.format_exc()))

    def _dispatch_save_response(self, event_name, eventData):
        if not isinstance(eventData, dict):
            eventData = {}
        for listener in list(self._save_response_listeners):
            try:
                callback = getattr(listener, "OnSaveResponse", None)
                if callback:
                    callback(event_name, eventData)
            except Exception:
                logger.error("存档响应分发失败:\n{}".format(traceback.format_exc()))

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
