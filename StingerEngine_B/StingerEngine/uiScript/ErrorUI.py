# -*- coding: utf-8 -*-
from ..include.QuModLibs.Client import *
from ..include.QuModLibs.UI import ScreenNodeWrapper
from ..EngineClient import get_engine_client


@ScreenNodeWrapper.autoRegister("ErrorUI.ErrorUI")
class ErrorUI(ScreenNodeWrapper):
    def __init__(self, namespace, name, param):
        ScreenNodeWrapper.__init__(self, namespace, name, param)
        self.err_info = param.get("err_info", "未知错误")

    def Create(self):
        ScreenNodeWrapper.Create(self)
        err_label = self.GetBaseUIControl("/root_panel/err_info_label").asLabel()
        err_label.SetText(self.err_info)
        exit_button = self.GetBaseUIControl("/root_panel/exit_button").asButton()
        exit_button.AddTouchEventParams({"isSwallow": True})
        exit_button.SetButtonTouchUpCallback(self.OnExit)

    def OnExit(self, args):
        self.SetRemove()
        engine_client = get_engine_client()
        if engine_client:
            engine_client.ForceDisconnect()

    def Destroy(self):
        pass

    def OnActive(self):
        pass

    def OnDeactive(self):
        pass
