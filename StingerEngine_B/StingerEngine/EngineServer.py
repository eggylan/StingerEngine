# -*- coding: utf-8 -*-
from .include.QuModLibs.Server import *
from .include.QuModLibs.Server import InjectRPCPlayerId
from .include.saveArchiveService import SaveArchiveService
from .include.serverTools import Player

ServerSystem = serverApi.GetServerSystemCls()


# ====== 模块级单例引用 ======
_engine_server = None


def get_engine_server():
    """获取 EngineServer 单例"""
    return _engine_server


# ====== 服务端 RPC API（通过 Call/@AllowCall 暴露给客户端调用） ======

@AllowCall
@InjectRPCPlayerId
def SaveList(playerId, source=None):
    """客户端请求槽位列表"""
    server = get_engine_server()
    if server is None:
        return
    return server._handle_save_api(playerId, "list", source=source)


@AllowCall
@InjectRPCPlayerId
def SaveWrite(playerId, slot_id=None, snapshot=None, title=None, source=None):
    """客户端请求写入存档"""
    server = get_engine_server()
    if server is None:
        return
    return server._handle_save_api(playerId, "write", slot_id=slot_id, snapshot=snapshot, title=title, source=source)


@AllowCall
@InjectRPCPlayerId
def SaveLoad(playerId, slot_id=None, source=None):
    """客户端请求读取存档"""
    server = get_engine_server()
    if server is None:
        return
    return server._handle_save_api(playerId, "load", slot_id=slot_id, source=source)


@AllowCall
@InjectRPCPlayerId
def SaveDelete(playerId, slot_id=None, source=None):
    """客户端请求删除存档"""
    server = get_engine_server()
    if server is None:
        return
    return server._handle_save_api(playerId, "delete", slot_id=slot_id, source=source)


@AllowCall
@InjectRPCPlayerId
def SaveContinue(playerId, source=None):
    """客户端请求查询继续游戏"""
    server = get_engine_server()
    if server is None:
        return
    return server._handle_save_api(playerId, "continue", source=source)


@AllowCall
@InjectRPCPlayerId
def ForceDisconnect(playerId):
    """客户端请求强制断开连接"""
    server = get_engine_server()
    if server is None:
        return
    if playerId in server._current_players:
        server._current_players[playerId].Disconnect()


# ====== EngineServer 系统类 ======

class EngineServer(ServerSystem):
    def __init__(self, namespace, systemName):
        global _engine_server
        ServerSystem.__init__(self, namespace, systemName)
        _engine_server = self

        self._current_players = {}  # 存储当前在线玩家的信息，键为玩家实体ID，值为Player对象
        self._save_archive_service = SaveArchiveService()

        # ====== 引擎事件监听（使用 QuModLibs ListenForEvent） ======
        ListenForEvent("PlayerJoinMessageEvent", self, self.OnPlayerJoin)
        ListenForEvent("PlayerIntendLeaveServerEvent", self, self.OnPlayerLeft)

    # ====== 玩家管理 ======

    def OnPlayerJoin(self, eventData):
        playerid = eventData.get("id", -1)
        if playerid != -1:
            self._current_players[playerid] = Player(playerid)
        if len(self._current_players) > 1:
            self._force_disconnect_player(playerid)

    def OnPlayerLeft(self, eventData):
        playerid = eventData.get("playerId", -1)
        if playerid in self._current_players:
            del self._current_players[playerid]

    def _force_disconnect_player(self, playerid):
        if playerid in self._current_players:
            self._current_players[playerid].Disconnect()

    # ====== 存档 API 处理 ======

    def _get_or_create_player(self, playerId):
        """获取或创建 Player 对象"""
        if playerId is None:
            return None
        player = self._current_players.get(playerId)
        if player is None:
            player = Player(playerId)
            self._current_players[playerId] = player
        return player

    def _handle_save_api(self, playerId, action, **kwargs):
        """统一处理存档 API 请求，通过 Call 异步回传响应"""
        player = self._get_or_create_player(playerId)
        if player is None:
            response = {"ok": False, "code": "player_not_found", "message": "无法定位请求玩家"}
            if kwargs.get("source"):
                response["source"] = kwargs["source"]
            Call(playerId, "OnSaveResponse", action, response)
            return

        try:
            if action == "list":
                response = self._save_archive_service.list_slots(player)
            elif action == "write":
                response = self._save_archive_service.write_slot(player, kwargs.get("slot_id"), kwargs.get("snapshot"), kwargs.get("title"))
            elif action == "load":
                response = self._save_archive_service.load_slot(player, kwargs.get("slot_id"))
            elif action == "delete":
                response = self._save_archive_service.delete_slot(player, kwargs.get("slot_id"))
            elif action == "continue":
                response = self._save_archive_service.query_continue(player)
            else:
                response = {"ok": False, "code": "unknown_action", "message": "未知的存档操作: {}".format(action)}
        except Exception as exc:
            import traceback
            response = {"ok": False, "code": "exception", "message": "服务端存档处理异常: {}".format(str(exc))}
            errorPrint("[EngineServer] 存档处理异常: {}".format(traceback.format_exc()))

        source = kwargs.get("source")
        if source and isinstance(response, dict):
            response["source"] = source

        # 通过 QuModLibs Call 机制回传响应到客户端
        Call(playerId, "OnSaveResponse", action, response)

    def Destroy(self):
        global _engine_server
        errorPrint("[EngineServer] EngineServer Destroyed")
        _engine_server = None
