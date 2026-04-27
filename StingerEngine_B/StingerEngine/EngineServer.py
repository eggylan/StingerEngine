# -*- coding: utf-8 -*-

import mod.server.extraServerApi as serverApi
from StingerEngine.include.modconfig import (
    CLIENT_NAME,
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
)
from StingerEngine.include.saveArchiveService import SaveArchiveService
from StingerEngine.include.serverTools import Player, logger
ServerSystem = serverApi.GetServerSystemCls()


class EngineServer(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        # 初始化变量
        self._current_players = {}  # 存储当前在线玩家的信息，键为玩家实体ID，值为Player对象
        self._save_archive_service = SaveArchiveService()

        # ====== 事件监听 ======
        self.EngineNameSpace = serverApi.GetEngineNamespace()
        self.EngineSystemName = serverApi.GetEngineSystemName()
        self.ListenForEngineEvent = lambda eventName, callback: self.ListenForEvent(
            self.EngineNameSpace, self.EngineSystemName, eventName, self, callback)
        self.ListenForLocalEvent = lambda eventName, callback: self.ListenForEvent(
            MOD_NAME, SERVER_NAME, eventName, self, callback)
        self.ListenForClientEvent = lambda eventName, callback: self.ListenForEvent(
            MOD_NAME, CLIENT_NAME, eventName, self, callback)
        
        
        # ======== 玩家加入离开事件 ========
        self.ListenForEngineEvent("PlayerJoinMessageEvent",self.OnPlayerJoin)
        self.ListenForEngineEvent("PlayerIntendLeaveServerEvent",self.OnPlayerLeft)

        # ========= 客户端事件监听 =========
        self.ListenForClientEvent("ForceDisconnect", self.OnClientForceDisconnect)
        self.ListenForClientEvent(SAVE_LIST_REQUEST, self.OnSaveListRequest)
        self.ListenForClientEvent(SAVE_WRITE_REQUEST, self.OnSaveWriteRequest)
        self.ListenForClientEvent(SAVE_LOAD_REQUEST, self.OnSaveLoadRequest)
        self.ListenForClientEvent(SAVE_DELETE_REQUEST, self.OnSaveDeleteRequest)
        self.ListenForClientEvent(SAVE_CONTINUE_QUERY, self.OnSaveContinueQuery)

    def OnPlayerJoin(self, eventData):
        playerid = eventData.get("id",-1)
        if playerid != -1:
            self._current_players[playerid] = Player(playerid)
        if len(self._current_players) > 1:
            self._force_disconnect_player(playerid)
    
    def OnPlayerLeft(self, eventData):
        playerid = eventData.get("playerId",-1)
        if playerid in self._current_players:
            del self._current_players[playerid]
    
    def OnClientForceDisconnect(self, eventData):
        playerid = eventData.get("__id__",None)
        if playerid is not None:
            self._force_disconnect_player(playerid)

    def _force_disconnect_player(self, playerid):
        if playerid in self._current_players:
            self._current_players[playerid].Disconnect()

    def OnSaveListRequest(self, eventData):
        playerid, player = self._get_request_player(eventData)
        if player is None:
            self._notify_save_response(playerid, SAVE_LIST_RESPONSE, self._player_error_response())
            return
        response = self._with_request_context(self._save_archive_service.list_slots(player), eventData)
        self._notify_save_response(playerid, SAVE_LIST_RESPONSE, response)

    def OnSaveWriteRequest(self, eventData):
        playerid, player = self._get_request_player(eventData)
        if player is None:
            self._notify_save_response(playerid, SAVE_WRITE_RESPONSE, self._player_error_response())
            return
        slot_id = eventData.get("slot_id") or eventData.get("slotId")
        snapshot = eventData.get("snapshot")
        title = eventData.get("title")
        response = self._with_request_context(self._save_archive_service.write_slot(player, slot_id, snapshot, title), eventData)
        self._notify_save_response(playerid, SAVE_WRITE_RESPONSE, response)

    def OnSaveLoadRequest(self, eventData):
        playerid, player = self._get_request_player(eventData)
        if player is None:
            self._notify_save_response(playerid, SAVE_LOAD_RESPONSE, self._player_error_response())
            return
        slot_id = eventData.get("slot_id") or eventData.get("slotId")
        response = self._with_request_context(self._save_archive_service.load_slot(player, slot_id), eventData)
        self._notify_save_response(playerid, SAVE_LOAD_RESPONSE, response)

    def OnSaveDeleteRequest(self, eventData):
        playerid, player = self._get_request_player(eventData)
        if player is None:
            self._notify_save_response(playerid, SAVE_DELETE_RESPONSE, self._player_error_response())
            return
        slot_id = eventData.get("slot_id") or eventData.get("slotId")
        response = self._with_request_context(self._save_archive_service.delete_slot(player, slot_id), eventData)
        self._notify_save_response(playerid, SAVE_DELETE_RESPONSE, response)

    def OnSaveContinueQuery(self, eventData):
        playerid, player = self._get_request_player(eventData)
        if player is None:
            self._notify_save_response(playerid, SAVE_CONTINUE_RESPONSE, self._player_error_response())
            return
        response = self._with_request_context(self._save_archive_service.query_continue(player), eventData)
        self._notify_save_response(playerid, SAVE_CONTINUE_RESPONSE, response)

    def _with_request_context(self, response, eventData):
        if not isinstance(response, dict):
            return response
        source = eventData.get("source")
        if source:
            response["source"] = source
        return response

    def _get_request_player(self, eventData):
        playerid = eventData.get("__id__", None)
        if playerid is None:
            return None, None
        player = self._current_players.get(playerid)
        if player is None:
            player = Player(playerid)
            self._current_players[playerid] = player
        return playerid, player

    def _notify_save_response(self, playerid, event_name, response):
        if playerid is None:
            logger.warn("Stinger save response dropped: missing player id")
            return
        self.NotifyToClient(playerid, event_name, response)

    def _player_error_response(self):
        return {
            "ok": False,
            "code": "player_not_found",
            "message": "无法定位请求玩家",
        }

    def Destroy(self):
        logger.info("EngineServer Destroyed")
