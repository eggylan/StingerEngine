# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
from ..include.modconfig import *
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()

EngineClient = clientApi.GetSystem(MOD_NAME, CLIENT_NAME)
class ErrorUI(ScreenNode):
	def __init__(self, namespace, name, param):
		ScreenNode.__init__(self, namespace, name, param)
		self.err_info = param.get("err_info", "未知错误")

	def Create(self):
		"""
		@description UI创建成功时调用
		"""
		err_label = self.GetBaseUIControl("/root_panel/err_info_label").asLabel()
		err_label.SetText(self.err_info)
		exit_button = self.GetBaseUIControl("/root_panel/exit_button").asButton()
		exit_button.AddTouchEventParams({"isSwallow": True})
		exit_button.SetButtonTouchUpCallback(self.OnExit)

	def OnExit(self, args):
		clientApi.PopScreen()
		EngineClient.ForceDisconnect()
		
	def Destroy(self):
		"""
		@description UI销毁时调用
		"""
		pass

	def OnActive(self):
		"""
		@description UI重新回到栈顶时调用
		"""
		pass

	def OnDeactive(self):
		"""
		@description 栈顶UI有其他UI入栈时调用
		"""
		pass
