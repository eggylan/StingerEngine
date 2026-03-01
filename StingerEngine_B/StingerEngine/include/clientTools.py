# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
CF = clientApi.GetEngineCompFactory()
levelId = clientApi.GetLevelId()

compCustomAudio = CF.CreateCustomAudio(levelId)
compGame = CF.CreateGame(levelId)
compTextNotifyClient= CF.CreateTextNotifyClient(levelId)

def PlayUISound(soundName,volume=1.0,pitch=1.0,loop=False):
    return compCustomAudio.PlayCustomUIMusic(soundName,volume,pitch,loop)

def PlayBGM(soundName,volume=1.0,loop=True):
    return compCustomAudio.PlayGlobalCustomMusic(soundName,volume,loop)

def StopMusic(name,fadeoutTime=0.0):
    return compCustomAudio.StopCustomMusic(name,fadeoutTime)

def NotifyMsg(message):
    return compTextNotifyClient.SetLeftCornerNotify(message)

