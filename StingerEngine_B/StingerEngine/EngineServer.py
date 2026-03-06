# -*- coding: utf-8 -*-

import mod.server.extraServerApi as serverApi
from include.modconfig import *
from include.serverTools import Player, ExecuteCommand, logger
ServerSystem = serverApi.GetServerSystemCls()


class EngineServer(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        # 初始化变量
        self._current_players = {}  # 存储当前在线玩家的信息，键为玩家实体ID，值为Player对象

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
        self.ListenForEngineEvent("PlayerLeftMessageServerEvent",self.OnPlayerLeft)

        # ========= 客户端事件监听 =========
        self.ListenForClientEvent("ForceDisconnect", self.OnClientForceDisconnect)

    def OnPlayerJoin(self, eventData):
        playerid = eventData.get("id",-1)
        if playerid != -1:
            self._current_players[playerid] = Player(playerid)
        if len(self._current_players) > 1:
            self._force_disconnect_player(playerid)
    
    def OnPlayerLeft(self, eventData):
        playerid = eventData.get("id",-1)
        if playerid in self._current_players:
            del self._current_players[playerid]
    
    def OnClientForceDisconnect(self, eventData):
        playerid = eventData.get("__id__",None)
        if playerid is not None:
            self._force_disconnect_player(playerid)

    def _force_disconnect_player(self, playerid):
        if playerid in self._current_players:
            self._current_players[playerid].Disconnect()
        

        

    def Destroy(self):
        logger.info("EngineServer Destroyed")
