# -*- coding: utf-8 -*-
import mod.server.extraServerApi as serverApi
from modconfig import *
from math import pow
from mod_log import logger as logger

CF = serverApi.GetEngineCompFactory()
levelId = serverApi.GetLevelId()
compCmd = CF.CreateCommand(levelId)
compGame = CF.CreateGame(levelId)

def ExecuteCommand(commandStr,entityId=None,showOutput=False):
    compCmd.SetCommand(commandStr,entityId,showOutput)


class Player:
    def __init__(self, playerEntityId):
        self.entityId = playerEntityId
        self.state = None
        self.compPlayer = CF.CreatePlayer(self.entityId)
        self.compName = CF.CreateName(self.entityId)
        self.compMsg = CF.CreateMsg(self.entityId)
        self.compGame = CF.CreateGame(self.entityId)
        self.compRot = CF.CreateRot(self.entityId)
        self.compPos = CF.CreatePos(self.entityId)
        self.compDimension = CF.CreateDimension(self.entityId)
        self.compExtraData = CF.CreateExtraData(self.entityId)
        self.compEntityEvent = CF.CreateEntityEvent(self.entityId)

    def Disconnect(self):
        self.compEntityEvent.TriggerCustomEvent(self.entityId,"stinger:disconnect")

    def GetName(self):
        return self.compName.GetName()

    def clear_title(self):
        ExecuteCommand("title @s clear",self.entityId)
    
    def send_action_bar(self, action_bar):
        # type: (str) -> None
        ExecuteCommand("title @s actionbar {}".format(action_bar), self.entityId)

    def set_title_times(self, fadein=20, duration=20, fadeout=5):
        """
        设置Title的显示时间
        :param fadein: 淡入时间
        :type fadein: int
        :param duration: 保持时间
        :type duration: int
        :param fadeout: 淡出时间
        :type fadeout: int
        :return:
        """
        if fadein is None:
            fadein = 20
        if duration is None:
            duration = 20
        if fadeout is None:
            fadeout = 5
        ExecuteCommand("title @s times {} {} {}".format(fadein, duration, fadeout), self.entityId)

    def send_title(self, title, sub_title=None, fadein=None, duration=None, fadeout=None):
        """
        发送Title
        :param title: 文本内容
        :type title: str
        :param sub_title: 富文本
        :type sub_title: str | None
        :param fadein: 淡入时间
        :type fadein: int | None
        :param duration: 保持时间
        :type duration: int | None
        :param fadeout: 淡出时间
        :type fadeout: int | None
        """
        if fadein is not None or duration is not None or fadeout is not None:
            self.set_title_times(fadein, duration, fadeout)
        else:
            ExecuteCommand("title @s reset", self.entityId)
        if sub_title is not None:
            ExecuteCommand("title @s subtitle {}".format(sub_title), self.entityId)
        ExecuteCommand("title @s title {}".format(title), self.entityId)
   
    def send_message(self, message, color='\xc2\xa7f'):
        """
        发送消息
        :param message: 消息
        :type message: str
        :param color: 颜色（可选）
        :type color: str
        """
        self.compMsg.NotifyOneMessage(self.entityId, message, color)

    def send_tip(self, tip):
        """
        发送Tip提示
        :param tip: 提示
        :type tip: str
        """
        self.compGame.SetOneTipMessage(self.entityId, tip)

    def send_popup(self, popup, sub=""):
        """
        发送Popup提示
        :param popup: 主提示
        :type popup: str
        :param sub: 副提示
        :type sub: str
        """
        self.compGame.SetOnePopupNotice(self.entityId, popup, sub)

    def play_bgm(self, bgm, volume=1, loop=True):
        """
        播放背景音乐
        :param bgm: 背景音乐ID
        :type bgm: str
        :param volume: 音量
        :type volume: float
        :param loop: 是否循环播放
        :type loop: bool
        """
        EGGameServerSystem = serverApi.GetSystem(MOD_NAME, SERVER_NAME)
        params = {
            "bgm": bgm,
            "volume": volume,
            "loop": loop
        }
        EGGameServerSystem.NotifyToClient(self.entityId, "PlayBGM", params)
    def stop_bgm(self,name,fadeoutTime=0.0):
        """
        停止背景音乐
        """
        EGGameServerSystem = serverApi.GetSystem(MOD_NAME, SERVER_NAME)
        EGGameServerSystem.NotifyToClient(self.entityId, "StopBGM", {
            "name": name,
            "fadeoutTime": fadeoutTime
        })

    def play_sound(self, sound, pos, volume=1, pitch=1):
        """
        通过服务端指令播放声音，可同时播放多个同sound
        :param sound: 声音ID
        :type sound: str
        :param pos: 播放位置
        :type pos: tuple[float, float, float]
        :param volume: 音量
        :type volume: float
        :param pitch: 音调
        :type pitch: float
        """
        ExecuteCommand('playsound {sound} "{player}" {pos} {volume} {pitch}'.format(
            sound = sound,
            player = self.GetName(),
            pos = "{} {} {}".format(pos[0], pos[1], pos[2]),
            volume = volume,
            pitch = pitch
        ))

    @staticmethod
    def get_note_sound_pitch(key):
        return pow(2, (float(key) - 12) / 12)
    
    def play_note_pling_sound(self, pos, key):
        self.play_sound("note.pling", pos, 1, Player.get_note_sound_pitch(key))

    def teleport(self, pos, yaw=None, pitch=None, dimension=None):
        if yaw is None:
            yaw = self.compRot.GetRot()[1]
        if pitch is None:
            pitch = self.compRot.GetRot()[0]
        if dimension is None or self.compDimension.GetEntityDimensionId() == dimension:
            self.compPos.SetPos(pos)
            self.compRot.SetRot((pitch, yaw))
        else:
            pos = (pos[0], pos[1] + 1.62, pos[2])  # 这边需要加上眼睛高度（不知道为什么同世界传送就又不用加）
            self.compDimension.ChangePlayerDimension(dimension, pos)
            self.compRot.SetRot((pitch, yaw))

    def set_game_type(self, mode):
        self.compPlayer.SetPlayerGameType(mode)

    def clear_inventory(self):
        ExecuteCommand("clear @s", self.entityId)


    def GetExtraData(self, key):
        return self.compExtraData.GetExtraData(key)
    def SetExtraData(self, key, value,autoSave=True):
        return self.compExtraData.SetExtraData(key, value,autoSave)
    def SaveExtraData(self):
        return self.compExtraData.SaveExtraData()
