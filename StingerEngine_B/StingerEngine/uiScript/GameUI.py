# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
import traceback
from mod_log import logger as logger
from ..include.modconfig import *
from ..include.clientTools import compGame, PlayBGM, PlayUISound, StopMusic

ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()

EngineClient = clientApi.GetSystem(MOD_NAME, CLIENT_NAME)

class TypewriterEffect(object):
    """打字机效果管理器"""
    def __init__(self, label_control, default_speed=0.03):
        self.label = label_control
        self.default_speed = default_speed
        self.timer = None
        self.full_text = ""
        self.current_index = 0
        self.is_active = False
        self.chars_per_tick = 3  # 每次显示3个字符,提升性能
        
    def start(self, text, speed=None):
        """开始打字机效果"""
        self.stop()
        
        if not self.label or not text:
            return
            
        speed = self._parse_speed(speed)
        
        # 速度为0或文本太短时直接显示
        if speed <= 0 or len(text) <= self.chars_per_tick:
            self.label.SetText(text)
            return
            
        self.full_text = text
        self.current_index = 0
        self.is_active = True
        self.label.SetText("")
        self.timer = compGame.AddRepeatedTimer(speed, self._tick)
        
    def stop(self):
        """停止打字机效果"""
        if self.timer:
            compGame.CancelTimer(self.timer)
            self.timer = None
        self.is_active = False
        
    def finish(self):
        """立即完成打字机效果"""
        if self.is_active and self.label:
            self.label.SetText(self.full_text)
        self.stop()
        
    def _tick(self):
        """定时器回调"""
        if not self.is_active or not self.label:
            self.stop()
            return
            
        self.current_index += self.chars_per_tick
        
        if self.current_index >= len(self.full_text):
            self.label.SetText(self.full_text)
            self.stop()
        else:
            self.label.SetText(self.full_text[:self.current_index])
            
    def _parse_speed(self, speed):
        """解析速度参数"""
        if speed is None:
            return self.default_speed
        try:
            return float(speed)
        except Exception:
            return self.default_speed


class CommandExecutor(object):
    """命令执行器"""
    def __init__(self, ui_instance):
        self.ui = ui_instance
        self.handlers = {
            "label": self._handle_label,
            "text": self._handle_text,
            "bg": self._handle_bg,
            "fade_in":self._handle_fade_in,
            "fade_out":self._handle_fade_out,
            "wait": self._handle_wait,
            "set_var": self._handle_set_var,
            "jump": self._handle_jump,
            "condition": self._handle_condition,
            "menu": self._handle_menu,
            "music": self._handle_music,
            "sfx": self._handle_sfx,
            "return_to_title": self._handle_return,
        }
        
    def execute(self, command):
        """执行命令,返回是否需要暂停"""
        if not isinstance(command, dict):
            return False
            
        cmd_type = command.get("type")
        handler = self.handlers.get(cmd_type)
        
        if handler:
            return handler(command)
        
        # todo: 支持更多命令类型
        if cmd_type in ("character", "show_image", "action"):
            return False
            
        logger.warn("未识别的剧情命令: {}".format(cmd_type))
        return False
        
    def _handle_label(self, cmd):
        return False
        
    def _handle_text(self, cmd):
        speaker = cmd.get("speaker", "")
        content = cmd.get("content", "")
        speed = cmd.get("typewriter_speed")
        if speaker == "":
            self.ui.speaker_panel.SetVisible(False)
        else:
            self.ui.speaker_panel.SetVisible(True)
            self.ui.speaker_label.SetText(speaker)
        if not content == "":
            self.ui.dialog_panel.SetVisible(True)
        text = "{}".format(content) 
        self.ui.typewriter.start(text, speed)
        self.ui.pause_mode = "tap"
        return True

    def _handle_bg(self, cmd):
        image_name = cmd.get("image")
        if image_name and self.ui.bg_image:
            self.ui.bg_image.SetSprite(image_name)
        return False
        
    def _handle_wait(self, cmd):
        duration = self._parse_float(cmd.get("duration", 0))
        if duration <= 0:
            return False
            
        self.ui.pause_mode = "wait"
        compGame.AddTimer(duration, self.ui._on_wait_finished)
        return True
        
    def _handle_fade_in(self, cmd):
        self.ui.pause_mode = "wait"
        def _fade_callback():
            self.ui.pause_mode = None
            self.ui.ExecuteUntilPause()
        duration = self._parse_float(cmd.get("duration", 1.0))
        self._do_fade("in", duration, callback=_fade_callback)
        return False
    
    def _handle_fade_out(self, cmd):
        self.ui.pause_mode = "wait"
        def _fade_callback():
            self.ui.pause_mode = None
            self.ui.ExecuteUntilPause()
        duration = self._parse_float(cmd.get("duration", 1.0))
        self._do_fade("out", duration, callback=_fade_callback)
        return False
    
    def _do_fade(self,direction, duration, callback=None):
        if not self.ui.fade_overlay:
            return
        self.ui.fade_overlay.SetVisible(True)
        if direction == "in":
            def callback_wrapper():
                self.ui.fade_overlay.SetVisible(False)
                if callback:
                    callback()
            anim_data = {
                "namespace": "GameUI",
                "fade": {
                    "anim_type": "alpha",
                    "duration": duration,
                    "from": 1,
                    "next": "",
                    "to": 0
                },
            }
            clientApi.RegisterUIAnimations(anim_data,override=True)
            self.ui.fade_overlay.RemoveAnimation("alpha") # 先移除旧动画，如果不存在这里不会报错
            self.ui.fade_overlay.SetAnimation("alpha","GameUI","fade",True)
            self.ui.fade_overlay.SetAnimEndCallback("fade", callback_wrapper)
        elif direction == "out":
            def callback_wrapper():
                if callback:
                    callback()
            anim_data = {
                "namespace": "GameUI",
                "fade": {
                    "anim_type": "alpha",
                    "duration": duration,
                    "from": 0,
                    "next": "",
                    "to": 1
                },
            }
            clientApi.RegisterUIAnimations(anim_data,override=True)
            self.ui.fade_overlay.RemoveAnimation("alpha")
            self.ui.fade_overlay.SetAnimation("alpha","GameUI","fade",True)
            self.ui.fade_overlay.SetAnimEndCallback("fade", callback_wrapper)
    
    def _handle_set_var(self, cmd):
        var_name = cmd.get("variable")
        if var_name:
            self.ui.variables[var_name] = cmd.get("value")
        return False
        
    def _handle_jump(self, cmd):
        target = cmd.get("target")
        if target:
            self.ui._jump_to_label(target)
        return False
        
    def _handle_condition(self, cmd):
        condition = cmd.get("condition")
        is_true = self._eval_condition(condition)
        
        commands = cmd.get("true_commands" if is_true else "false_commands", [])
        return self._execute_inline(commands)
        
    def _handle_menu(self, cmd):
        self.ui.pending_menu = cmd
        self._show_menu(cmd)
        self.ui.pause_mode = "menu"
        return True
        
    def _handle_music(self, cmd):
        action = cmd.get("action", "play")
        name = cmd.get("file")
        fade = self._parse_float(cmd.get("fade", 0.0))
        
        if action in ("play", "change") and name:
            if action == "change" and self.ui.current_music:
                StopMusic(self.ui.current_music, fade)
            PlayBGM(name)
            self.ui.current_music = name
        elif action == "stop":
            target = name or self.ui.current_music
            if target:
                StopMusic(target, fade)
            self.ui.current_music = None
        return False
        
    def _handle_sfx(self, cmd):
        sound_name = cmd.get("file")
        if sound_name:
            PlayUISound(sound_name, loop=bool(cmd.get("loop", False)))
        return False
        
    def _handle_return(self, cmd):
        self.ui.pause_mode = "ended"
        clientApi.PopScreen()
        EngineClient.CreateMainInterfaceUI()
        return True
        
    def _show_menu(self, cmd):
        title = cmd.get("title", "请选择")
        choices = cmd.get("choices", [])
        
        if not choices:
            text = "{}\\n(无可用选项，自动继续)".format(title)
            self.ui.typewriter.start(text)
            self.ui.pause_mode = "tap"
            return
            
        lines = [title]
        for i, choice in enumerate(choices):
            choice_text = choice.get("text", "选项{}".format(i + 1))
            lines.append("{}. {}".format(i + 1, choice_text))
        lines.append("\\n点击屏幕确认默认选项：1")
        
        self.ui.typewriter.start("\\n".join(lines))
        
    def _execute_inline(self, commands):
        """执行内联命令列表"""
        if not isinstance(commands, list):
            return False
            
        for command in commands:
            if isinstance(command, dict) and self.execute(command):
                return True
        return False
        
    def _eval_condition(self, expression):
        """评估条件表达式"""
        if not expression:
            return False
        try:
            return bool(eval(expression, {"__builtins__": {}}, dict(self.ui.variables)))
        except Exception as e:
            logger.error("条件表达式执行失败: {}, error={}".format(expression, e))
            return False
            
    @staticmethod
    def _parse_float(value):
        """安全解析浮点数"""
        try:
            return float(value)
        except Exception:
            return 0.0


class GameUI(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        self.param = param
        
        # 加载章节脚本
        entry = param.get("entry", "demo")
        self.script_data = self._load_script(entry)
        
        # 状态变量
        self.current_index = 0
        self.pause_mode = None  # None | tap | menu | wait | ended
        self.variables = {}
        self.label_index = {}
        self.pending_menu = None
        self.current_music = None
        
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
            script_module = clientApi.ImportModule("StingerEngine.chapters.demo")
            logger.info("已加载默认章节脚本")
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
        self.touch_button = self.GetBaseUIControl("/root_panel/touch_button").asButton()
        self.touch_button.AddTouchEventParams({"isSwallow": True})
        self.touch_button.SetButtonTouchUpCallback(self.OnTouchButton)
        self.bg_image = self.GetBaseUIControl("/root_panel/background_image").asImage()
        self.fade_overlay = self.GetBaseUIControl("/root_panel/fade_overlay").asImage()

        # 初始化组件
        typewriter_speed = self.param.get("typewriter_speed", 0.03)
        self.typewriter = TypewriterEffect(self.dialog_label, typewriter_speed)
        self.executor = CommandExecutor(self)
        
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
            
        # menu模式,确认选择
        if self.pause_mode == "menu":
            self._confirm_menu_choice()
            if self.pause_mode != "ended":
                self.ExecuteUntilPause()
            return
            
    def ExecuteUntilPause(self):
        """执行剧本直到遇到暂停"""
        max_steps = 500
        steps = 0
        
        while self.pause_mode is None and self.current_index < len(self.script_data):
            if steps >= max_steps:
                logger.error("剧情执行超过安全步数，疑似存在循环跳转")
                self.pause_mode = "ended"
                self.typewriter.start("剧情执行异常：疑似循环跳转")
                return
                
            command = self.script_data[self.current_index]
            self.current_index += 1
            steps += 1
            
            if self.executor.execute(command):
                return
                
        # 剧本执行完毕
        if self.current_index >= len(self.script_data) and self.pause_mode is None:
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
        self.pause_mode = "ended"
        
    def OnActive(self):
        """UI重新回到栈顶时调用"""
        pass
        
    def OnDeactive(self):
        """栈顶UI有其他UI入栈时调用"""
        pass