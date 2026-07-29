# -*- coding: utf-8 -*-
from .include.QuModLibs.Client import *
from .include.clientTools import compCustomAudio, compGame as _compGame_tools

ClientSystem = clientApi.GetClientSystemCls()
from .include.modconfig import UI_PUSH_DELAY


# ====== 模块级单例 ======
_engine_client = None


def get_engine_client():
    """获取 EngineClient 单例"""
    return _engine_client


# ====== 服务端 -> 客户端 RPC 回调（@AllowCall 注册，由服务端 Call 触发） ======

@AllowCall
def OnSaveResponse(action, response):
    """接收服务端存档操作响应（list/write/load/delete/continue）"""
    client = get_engine_client()
    if client is None:
        return
    client._dispatch_save_response(action, response)


@AllowCall
def OnPlayBGM(bgm, volume=1.0, loop=True):
    """服务端请求播放 BGM"""
    from .include.clientTools import PlayBGM
    PlayBGM(bgm, volume, loop)


@AllowCall
def OnStopBGM(name, fadeoutTime=0.0):
    """服务端请求停止 BGM"""
    from .include.clientTools import StopMusic
    StopMusic(name, fadeoutTime)


# ====== EngineClient 系统类 ======

class EngineClient(ClientSystem):
    def __init__(self, namespace, systemName):
        global _engine_client
        ClientSystem.__init__(self, namespace, systemName)
        _engine_client = self

        self._ui_push_timer = None
        self._save_response_listeners = []
        self._key_event_listeners = []
        self._game_ui_runtime = None

        # ====== 引擎事件监听（使用 QuModLibs ListenForEvent） ======
        ListenForEvent("UiInitFinished", self, self.OnUiInitFinished)
        ListenForEvent("OnKeyPressInGame", self, self.OnKeyPressInGame)

    def OnUiInitFinished(self, eventData):
        compCustomAudio.DisableOriginMusic(True)  # 禁止原版音乐
        self.CreateMainInterfaceUI()

    def _cancel_pending_push(self):
        if self._ui_push_timer:
            try:
                _compGame_tools.CancelTimer(self._ui_push_timer)
            except Exception:
                pass
            self._ui_push_timer = None

    def _schedule_push(self, ui_cls, param=None):
        """延迟推送 UI（ui_cls 为 ScreenNodeWrapper 子类，注册由 @autoRegister 完成）"""
        def _push_ui():
            self._ui_push_timer = None
            ui_cls.pushScreen(createParams=param)

        self._cancel_pending_push()
        self._ui_push_timer = _compGame_tools.AddTimer(UI_PUSH_DELAY, _push_ui)

    def CreateMainInterfaceUI(self):
        self._schedule_push(_MainInterfaceUI_import.MainInterfaceUI)

    def CreateGameUI(self, entry=None, startMode="new", resumeSlotId=None, resumeSnapshot=None):
        if resumeSnapshot and not entry:
            entry = resumeSnapshot.get("entry")
        param = {"startMode": startMode}
        if entry:
            param["entry"] = entry
        if resumeSlotId:
            param["resumeSlotId"] = resumeSlotId
        if resumeSnapshot:
            param["resumeSnapshot"] = resumeSnapshot
        self._schedule_push(_GameUI_import.GameUI, param)

    def CreateSystemMenuUI(self, initialTab="save", context=None):
        param = {"initialTab": initialTab or "save"}
        if context:
            param["context"] = context
        self._schedule_push(_SystemMenuUI_import.SystemMenuUI, param)

    def CreateErrorUI(self, errinfo):
        self._schedule_push(_ErrorUI_import.ErrorUI, {"err_info": errinfo})

    def ForceDisconnect(self):
        """触发强制断开连接"""
        Call("ForceDisconnect")

    # ====== Game UI Runtime 管理 ======

    def RegisterGameUIRuntime(self, runtime):
        self._game_ui_runtime = runtime

    def UnregisterGameUIRuntime(self, runtime):
        if self._game_ui_runtime == runtime:
            self._game_ui_runtime = None

    def GetGameUIRuntime(self):
        return self._game_ui_runtime

    # ====== 存档响应监听器管理 ======

    def RegisterSaveResponseListener(self, listener):
        if listener and listener not in self._save_response_listeners:
            self._save_response_listeners.append(listener)

    def UnregisterSaveResponseListener(self, listener):
        if listener in self._save_response_listeners:
            self._save_response_listeners.remove(listener)

    # ====== 按键事件监听器管理 ======

    def RegisterKeyEventListener(self, listener):
        if listener and listener not in self._key_event_listeners:
            self._key_event_listeners.append(listener)

    def UnregisterKeyEventListener(self, listener):
        if listener in self._key_event_listeners:
            self._key_event_listeners.remove(listener)

    # ====== 存档请求（使用 QuModLibs Call 通信） ======

    @staticmethod
    def RequestSaveList(source=None):
        Call("SaveList", source=source)

    @staticmethod
    def RequestSaveContinue(source=None):
        Call("SaveContinue", source=source)

    @staticmethod
    def RequestSaveWrite(slot_id, snapshot, title=None, source=None):
        Call("SaveWrite", slot_id=slot_id, snapshot=snapshot, title=title, source=source)

    @staticmethod
    def RequestSaveLoad(slot_id, source=None):
        Call("SaveLoad", slot_id=slot_id, source=source)

    @staticmethod
    def RequestSaveDelete(slot_id, source=None):
        Call("SaveDelete", slot_id=slot_id, source=source)

    # ====== 存档响应分发 ======

    def _dispatch_save_response(self, action, response):
        """将服务端存档响应分发给所有已注册监听器"""
        # 兼容旧有的事件名常量，构造 event_name 映射
        event_name_map = {
            "list": "SAVE_LIST_RESPONSE",
            "write": "SAVE_WRITE_RESPONSE",
            "load": "SAVE_LOAD_RESPONSE",
            "delete": "SAVE_DELETE_RESPONSE",
            "continue": "SAVE_CONTINUE_RESPONSE",
        }
        event_name = event_name_map.get(action, action)
        for listener in list(self._save_response_listeners):
            try:
                callback = getattr(listener, "OnSaveResponse", None)
                if callback:
                    callback(event_name, response)
            except Exception:
                import traceback
                errorPrint("[EngineClient] 存档响应分发异常: {}".format(traceback.format_exc()))

    # ====== 按键事件分发 ======

    def OnKeyPressInGame(self, eventData):
        if not isinstance(eventData, dict):
            eventData = {}
        for listener in list(self._key_event_listeners):
            try:
                callback = getattr(listener, "OnKeyPressInGame", None)
                if callback:
                    callback(eventData)
            except Exception:
                import traceback
                errorPrint("[EngineClient] 按键事件分发异常: {}".format(traceback.format_exc()))

    def Destroy(self):
        global _engine_client
        self._cancel_pending_push()
        compCustomAudio.DisableOriginMusic(False)  # 恢复原版音乐
        errorPrint("[EngineClient] EngineClient Destroyed")
        _engine_client = None


# ====== 预导入 UI 模块以触发 @autoRegister（必须在 UiInitFinished 之前） ======
import StingerEngine.uiScript.ErrorUI as _ErrorUI_import
import StingerEngine.uiScript.MainInterfaceUI as _MainInterfaceUI_import
import StingerEngine.uiScript.GameUI as _GameUI_import
import StingerEngine.uiScript.SystemMenuUI as _SystemMenuUI_import
# 消除 lint 未使用警告
_ErrorUI_import = _ErrorUI_import
_MainInterfaceUI_import = _MainInterfaceUI_import
_GameUI_import = _GameUI_import
_SystemMenuUI_import = _SystemMenuUI_import
