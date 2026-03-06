# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
import traceback
from ..include.modconfig import *
from ..include.clientTools import logger, compGame, PlayBGM, PlayUISound, StopMusic
from ..include.scriptInterpreter import TypewriterEffect, CommandExecutor, CharacterManager, MenuManager
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()

EngineClient = clientApi.GetSystem(MOD_NAME, CLIENT_NAME)
class GameUI(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        self.param = param
        
        # 加载章节脚本
        entry = param.get("entry", "main")
        self.script_data = self._load_script(entry)
        
        # 状态变量
        self.current_index = 0
        self.pause_mode = None  # None | tap | menu | wait | ended
        self.variables = {}
        self.label_index = {}
        self.pending_menu = None
        self.current_music = None
        self.current_cg = {"0": None, "1": None}
        self.cg_front = "0"  # 当前前景CG槽位，"0" 或 "1"
        self.inline_queue = []  # 内联命令队列（condition 等暂停恢复用）

        # 组件
        self.typewriter = None
        self.executor = None
        self.dialog_label = None 
        self.touch_button = None
        
    def _load_script(self, entry):
        """加载章节脚本"""
        module_path = "StingerEngine.chapters.{}".format(entry)
        script_module = clientApi.ImportModule(module_path)
        
        if not script_module:
            logger.error("未找到章节脚本 {}".format(module_path))
        else:
            logger.info("已加载章节脚本 {}".format(entry))
            
        return script_module.script_data if script_module else []
        
    def Create(self):
        """UI创建成功时调用"""
        # 初始化UI控件
        self.dialog_panel = self.GetBaseUIControl("/root_panel/dialog_panel")
        self.dialog_label = self.GetBaseUIControl("/root_panel/dialog_panel/dialog_label").asLabel()
        self.speaker_panel = self.GetBaseUIControl("/root_panel/dialog_panel/speaker_panel")
        self.speaker_label = self.GetBaseUIControl("/root_panel/dialog_panel/speaker_panel/speaker_label").asLabel()
        self.stage_panel = self.GetBaseUIControl("/root_panel/stage_panel")
        self.menu_panel = self.GetBaseUIControl("/root_panel/menu_stack_panel")
        self.touch_button = self.GetBaseUIControl("/root_panel/touch_button").asButton()
        self.touch_button.AddTouchEventParams({"isSwallow": True})
        self.touch_button.SetButtonTouchUpCallback(self.OnTouchButton)
        self.bg_image = self.GetBaseUIControl("/root_panel/background_image").asImage()
        self.cg_panel = self.GetBaseUIControl("/root_panel/cg_panel")
        self.cg_image_0_base = self.GetBaseUIControl("/root_panel/cg_panel/cg_image_0")
        self.cg_image_1_base = self.GetBaseUIControl("/root_panel/cg_panel/cg_image_1")
        self.fade_overlay = self.GetBaseUIControl("/root_panel/fade_overlay").asImage()

        # 初始化组件
        typewriter_speed = self.param.get("typewriter_speed", 0.03)
        self.typewriter = TypewriterEffect(self.dialog_label, typewriter_speed)
        self.executor = CommandExecutor(self)
        self.character_manager = CharacterManager(self, self.stage_panel)
        self.menu_manager = MenuManager(self)
        # 构建标签索引
        self._build_label_index()
        # 开始执行剧本
        self.pause_mode = None
        self.ExecuteUntilPause()
        
    def OnTouchButton(self, args):
        """触摸按钮回调"""
        # 打字机效果进行中,立即完成
        if self.typewriter.is_active:
            self.typewriter.finish()
            return
            
        # tap模式,继续执行
        if self.pause_mode == "tap":
            self.pause_mode = None
            self.ExecuteUntilPause()
            return

    def ExecuteUntilPause(self):
        """执行剧本直到遇到暂停"""
        steps = 0
        
        while self.pause_mode is None:
            # 优先执行内联命令队列（condition 内暂停后的剩余命令）
            if self.inline_queue:
                command = self.inline_queue.pop(0)
                steps += 1
                if isinstance(command, dict) and self.executor.execute(command):
                    return
                continue
            
            # 主脚本
            if self.current_index >= len(self.script_data):
                break
                
            command = self.script_data[self.current_index]
            self.current_index += 1
            steps += 1
            
            if self.executor.execute(command):
                return
                
        # 剧本执行完毕
        if self.current_index >= len(self.script_data) and self.pause_mode is None and not self.inline_queue:
            self.pause_mode = "ended"
            self.typewriter.start("【剧情结束】")
            
    def _build_label_index(self):
        """构建标签索引"""
        self.label_index = {}
        for index, command in enumerate(self.script_data):
            if isinstance(command, dict) and command.get("type") == "label":
                name = command.get("name")
                if name:
                    self.label_index[name] = index
                    
    def _jump_to_label(self, label_name):
        """跳转到指定标签"""
        if label_name not in self.label_index:
            logger.error("未找到跳转标签: {}".format(label_name))
            return
        self.current_index = self.label_index[label_name]
        self.inline_queue = []  # 跳转时清空内联命令队列
        
    def _confirm_menu_choice(self):
        """确认菜单选择(默认选择第一项)"""
        if not self.pending_menu:
            self.pause_mode = None
            return
            
        choices = self.pending_menu.get("choices", [])
        if not choices:
            self.pending_menu = None
            self.pause_mode = None
            return
            
        choice = choices[0]
        target = choice.get("label")
        self.pending_menu = None
        self.pause_mode = None
        
        if target:
            self._jump_to_label(target)
            
    def _on_wait_finished(self):
        """等待完成回调"""
        if self.pause_mode == "wait":
            self.pause_mode = None
            self.ExecuteUntilPause()
            
    def Destroy(self):
        """UI销毁时调用"""
        if self.typewriter:
            self.typewriter.stop()
        if self.menu_manager:
            self.menu_manager._clear_choices()
        if self.character_manager:
            self.character_manager.destroy()
        self.pause_mode = "ended"
        
    def OnActive(self):
        """UI重新回到栈顶时调用"""
        pass
        
    def OnDeactive(self):
        """栈顶UI有其他UI入栈时调用"""
        pass