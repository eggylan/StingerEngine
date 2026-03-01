# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
from ..include.modconfig import *
from ..include.clientTools import compCustomAudio
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()

EngineClient = clientApi.GetSystem(MOD_NAME, CLIENT_NAME)
class MainInterfaceUI(ScreenNode):
	def __init__(self, namespace, name, param):
		ScreenNode.__init__(self, namespace, name, param)

	def Create(self):
		"""
		@description UI创建成功时调用
		"""
		start_button = self.GetBaseUIControl("/root_panel/start_new_game").asButton()
		start_button.AddTouchEventParams({"isSwallow": True})
		start_button.SetButtonTouchUpCallback(self.OnStartNewGame)
		
		exit_button = self.GetBaseUIControl("/root_panel/exit_game").asButton()
		exit_button.AddTouchEventParams({"isSwallow": True})
		exit_button.SetButtonTouchUpCallback(self.OnExit)

		raiseError_button = self.GetBaseUIControl("/root_panel/raiseError").asButton()
		raiseError_button.AddTouchEventParams({"isSwallow": True})
		raiseError_button.SetButtonTouchUpCallback(self.OnRaiseError)

	def OnStartNewGame(self, args):
		clientApi.PopScreen()
		EngineClient.CreateGameUI("demo")
	
	def OnExit(self, args):
		EngineClient.ForceDisconnect()

	def OnRaiseError(self, args):
		# 测试用
		import traceback
		try:
			raise Exception("这是一个测试错误")
		except Exception as e:
			errinfo = traceback.format_exc()
		EngineClient.CreateErrorUI(errinfo)

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
