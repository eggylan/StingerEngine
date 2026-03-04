# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
from mod_log import logger as logger
from clientTools import compGame, PlayBGM, PlayUISound, StopMusic
from modconfig import *

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


class ExpressionValidator(object):
    """无eval计算条件表达式

    支持的运算符: > < == >= <= != [and] [or] [not] ()
    示例:
        variable >= 1
        (a > b) [and] (c != 6)
        [not] (x == 0)
    """

    def __init__(self, expression, variables):
        self.variables = variables
        self.tokens = self._tokenize(expression)
        self.pos = 0

    @staticmethod
    def _tokenize(expr):
        tokens = []
        i = 0
        while i < len(expr):
            ch = expr[i]
            # 跳过空白
            if ch.isspace():
                i += 1
                continue
            # [and] [or] [not]
            if ch == '[':
                j = expr.find(']', i)
                if j == -1:
                    raise ValueError("未闭合的方括号")
                kw = expr[i + 1:j]
                if kw in ('and', 'or', 'not'):
                    tokens.append(kw.upper())  # 'AND','OR','NOT'
                else:
                    raise ValueError("未知关键字: [{}]".format(kw))
                i = j + 1
                continue
            # 双字符运算符 >= <= == !=
            if i + 1 < len(expr) and expr[i:i + 2] in ('>=', '<=', '==', '!='):
                tokens.append(expr[i:i + 2])
                i += 2
                continue
            # 单字符运算符 > <
            if ch in ('>', '<'):
                tokens.append(ch)
                i += 1
                continue
            # 括号
            if ch == '(':
                tokens.append('(')
                i += 1
                continue
            if ch == ')':
                tokens.append(')')
                i += 1
                continue
            # 数字，含负号，前面无值token时允许
            is_neg = (
                ch == '-'
                and i + 1 < len(expr)
                and (expr[i + 1].isdigit() or expr[i + 1] == '.')
                and (not tokens or tokens[-1] in (
                    '(', '>=', '<=', '==', '!=', '>', '<', 'AND', 'OR', 'NOT'))
            )
            if ch.isdigit() or ch == '.' or is_neg:
                j = (i + 1) if is_neg else i
                has_dot = (ch == '.')
                while j < len(expr) and (expr[j].isdigit() or (expr[j] == '.' and not has_dot)):
                    if expr[j] == '.':
                        has_dot = True
                    j += 1
                tokens.append(('NUM', expr[i:j]))
                i = j
                continue
            # 标识符（变量名）
            if ch.isalpha() or ch == '_':
                j = i
                while j < len(expr) and (expr[j].isalnum() or expr[j] == '_'):
                    j += 1
                tokens.append(('VAR', expr[i:j]))
                i = j
                continue
            raise ValueError("无法识别的字符: '{}'".format(ch))
        return tokens

    def _peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def evaluate(self):
        """解析并计算表达式的值"""
        result = self._expr_or()
        if self.pos < len(self.tokens):
            raise ValueError("表达式解析不完整，剩余: {}".format(self.tokens[self.pos:]))
        return result

    def _expr_or(self):
        left = self._expr_and()
        while self._peek() == 'OR':
            self._advance()
            right = self._expr_and()
            left = left or right
        return left

    def _expr_and(self):
        left = self._expr_not()
        while self._peek() == 'AND':
            self._advance()
            right = self._expr_not()
            left = left and right
        return left

    def _expr_not(self):
        if self._peek() == 'NOT':
            self._advance()
            return not self._expr_not()
        return self._expr_comparison()

    def _expr_comparison(self):
        left = self._atom()
        op = self._peek()
        if op in ('>', '<', '>=', '<=', '==', '!='):
            self._advance()
            right = self._atom()
            if op == '>':  return left > right
            if op == '<':  return left < right
            if op == '>=': return left >= right
            if op == '<=': return left <= right
            if op == '==': return left == right
            if op == '!=': return left != right
        return left

    def _atom(self):
        tok = self._peek()
        if tok is None:
            raise ValueError("表达式意外结束")
        # 括号子表达式
        if tok == '(':
            self._advance()
            result = self._expr_or()
            if self._peek() != ')':
                raise ValueError("缺少右括号 ')'")
            self._advance()
            return result
        # 数字
        if isinstance(tok, tuple) and tok[0] == 'NUM':
            self._advance()
            val = tok[1]
            return float(val) if '.' in val else int(val)
        # 变量或布尔字面量
        if isinstance(tok, tuple) and tok[0] == 'VAR':
            self._advance()
            name = tok[1]
            if name == 'True':  return True
            if name == 'False': return False
            if name == 'None':  return None
            if name in self.variables:
                return self.variables[name]
            raise ValueError("未定义的变量: '{}'".format(name))
        raise ValueError("意外的token: {}".format(tok))


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
            "show_image": self._handle_show_image,
            "hide_image": self._handle_hide_image,
            "var": self._handle_var,
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
        if cmd_type in ("character", "action"):
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
    
    def _handle_show_image(self, cmd):
        image_name = cmd.get("image")
        fade = self._parse_float(cmd.get("fade", 0))
        # 为了实现两CG平滑切换，这里使用cg_image_0和cg_image_1交替显示
        if not image_name or not self.ui.cg_panel:
            return False

        front = self.ui.cg_front # 当前前景槽位
        back = "1" if front == "0" else "0"  # 即将使用的后景槽位
        front_ctrl = self.ui.cg_image_0_base if front == "0" else self.ui.cg_image_1_base  
        back_ctrl  = self.ui.cg_image_1_base if front == "0" else self.ui.cg_image_0_base

        # 将新图片设置到后景控件
        back_ctrl.asImage().SetSprite(image_name)
        self.ui.current_cg[back] = image_name
        self.ui.cg_panel.SetVisible(True)

        has_old = self.ui.current_cg[front] is not None

        if fade > 0 and has_old:
            # 有旧图：先让后景可见，然后淡出前景以实现交叉渐变
            back_ctrl.SetVisible(True)
            self.ui.pause_mode = "wait"
            def _on_crossfade_done():
                front_ctrl.SetVisible(False)
                self.ui.current_cg[front] = None
                self.ui.cg_front = back
                self.ui.pause_mode = None
                self.ui.ExecuteUntilPause()
            self._do_fade(front_ctrl, "in", fade, callback=_on_crossfade_done)
            return True
        elif fade > 0:
            # 首张图片：渐入显示
            back_ctrl.SetVisible(True)
            self.ui.pause_mode = "wait"
            def _on_fadein_done():
                self.ui.cg_front = back
                self.ui.pause_mode = None
                self.ui.ExecuteUntilPause()
            self._do_fade(back_ctrl, "out", fade, callback=_on_fadein_done)
            return True
        else:
            # 无渐变，直接切换
            back_ctrl.SetVisible(True)
            if has_old:
                front_ctrl.SetVisible(False)
                self.ui.current_cg[front] = None
            self.ui.cg_front = back
            return False

    def _handle_hide_image(self, cmd):
        if not self.ui.cg_panel:
            return False
        fade = self._parse_float(cmd.get("fade", 0))
        front = self.ui.cg_front
        front_ctrl = self.ui.cg_image_0_base if front == "0" else self.ui.cg_image_1_base

        if fade > 0 and self.ui.current_cg[front] is not None:
            # 渐隐当前CG
            self.ui.pause_mode = "wait"
            def _on_hide_done():
                self.ui.cg_panel.SetVisible(False)
                self.ui.cg_image_0_base.SetVisible(False)
                self.ui.cg_image_1_base.SetVisible(False)
                self.ui.current_cg = {"0": None, "1": None}
                self.ui.pause_mode = None
                self.ui.ExecuteUntilPause()
            self._do_fade(front_ctrl, "in", fade, callback=_on_hide_done)
            return True

        # 无渐变，直接隐藏
        self.ui.cg_panel.SetVisible(False)
        self.ui.cg_image_0_base.SetVisible(False)
        self.ui.cg_image_1_base.SetVisible(False)
        self.ui.current_cg = {"0": None, "1": None}
        return False
        
    def _handle_fade_in(self, cmd):
        self.ui.pause_mode = "wait"
        def _fade_callback():
            self.ui.pause_mode = None
            self.ui.ExecuteUntilPause()
        duration = self._parse_float(cmd.get("duration", 1.0))
        self._do_fade(self.ui.fade_overlay,"in", duration, callback=_fade_callback)
        return False
    
    def _handle_fade_out(self, cmd):
        self.ui.pause_mode = "wait"
        def _fade_callback():
            self.ui.pause_mode = None
            self.ui.ExecuteUntilPause()
        duration = self._parse_float(cmd.get("duration", 1.0))
        self._do_fade(self.ui.fade_overlay,"out", duration, callback=_fade_callback)
        return False
    
    def _do_fade(self, baseControl, direction, duration, callback=None):
        if not baseControl:
            return
        baseControl.SetVisible(True)
        if direction == "in":
            def callback_wrapper():
                baseControl.SetVisible(False)
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
            baseControl.RemoveAnimation("alpha") # 先移除旧动画，如果不存在这里不会报错
            baseControl.SetAnimation("alpha","GameUI","fade",True)
            baseControl.SetAnimEndCallback("fade", callback_wrapper)
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
            baseControl.RemoveAnimation("alpha")
            baseControl.SetAnimation("alpha","GameUI","fade",True)
            baseControl.SetAnimEndCallback("fade", callback_wrapper)
    
    def _handle_var(self, cmd):
        var_name = cmd.get("variable")
        operation = cmd.get("operation","set")
        # 支持的操作：赋值(set)，加法(add)，减法(sub)，乘法(mul)，除法(div)
        if var_name and operation in ("set", "add", "sub", "mul", "div"):
            current_value = self.ui.variables.get(var_name, 0)
            value = self._parse_var_value(cmd.get("value", 0))
            if operation == "set":
                new_value = value
            elif operation == "add":
                new_value = self._parse_float(current_value) + self._parse_float(value)
            elif operation == "sub":
                new_value = self._parse_float(current_value) - self._parse_float(value)
            elif operation == "mul":
                new_value = self._parse_float(current_value) * self._parse_float(value)
            elif operation == "div":
                value_num = self._parse_float(value)
                new_value = self._parse_float(current_value) / value_num if value_num != 0 else 0
            self.ui.variables[var_name] = new_value
            logger.info("变量更新: {} {} {} => {}".format(var_name, operation, value, new_value))
        else:
            raise ValueError("无效的变量操作: variable='{}', operation='{}'".format(var_name, operation))
        return False
        
    def _handle_jump(self, cmd):
        target = cmd.get("target")
        if target:
            self.ui._jump_to_label(target)
        return False
        
    def _handle_condition(self, cmd):
        condition = cmd.get("condition")
        is_true = self._eval_condition(condition)
        logger.info("条件判断: '{}' => {}".format(condition, is_true))
        
        commands = cmd.get("true_commands" if is_true else "false_commands", [])
        return self._execute_inline(commands)
        
    def _handle_menu(self, cmd):
        self.ui.pending_menu = cmd
        self.ui.menu_manager.show_menu(cmd)
        self.ui.pause_mode = "menu"
        return True
        
    def _handle_music(self, cmd):
        action = cmd.get("action", "play")
        name = cmd.get("file")
        fade = self._parse_float(cmd.get("fade", 0.0))
        
        if action in ("play", "change") and name:
            if action == "change" and self.ui.current_music:
                StopMusic(self.ui.current_music, fade)
            PlayUISound(name, loop=True)
            # 注意，使用PlayBGM的话，如果玩家在原版游戏设置里把音乐音量调到0了，这里是不会有声音的
            # 但是如果用PlayUISound，调整音量就变得不方便，而网易也没有调原版音乐音量的接口，这里暂时先用PlayUISound来播放bgm，后续如果需要更复杂的音乐控制再改回来
            self.ui.current_music = name
            logger.info("正在播放背景音乐: {}".format(name))
        elif action == "stop":
            target = name or self.ui.current_music
            if target:
                StopMusic(target, fade)
            self.ui.current_music = None
            logger.info("停止背景音乐: {}".format(target))
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
        
    def _execute_inline(self, commands):
        """执行内联命令列表"""
        if not isinstance(commands, list):
            return False
            
        for i, command in enumerate(commands):
            if isinstance(command, dict) and self.execute(command):
                # 暂停时，将剩余未执行的内联命令存入队列，恢复后继续执行
                remaining = commands[i + 1:]
                if remaining:
                    self.ui.inline_queue = remaining + self.ui.inline_queue
                return True
        return False
        
    def _eval_condition(self, expression):
        """评估条件表达式"""
        if not expression:
            return False
        try:
            parser = ExpressionValidator(expression, dict(self.ui.variables))
            return bool(parser.evaluate())
        except Exception as e:
            logger.error("条件表达式执行失败: {}, error={}".format(expression, e))
            return False
            
    @staticmethod
    def _parse_var_value(value):
        """解析变量值，保留布尔类型"""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            text = value.strip()
            lowered = text.lower()
            if lowered == "true":
                return True
            if lowered == "false":
                return False
            if lowered in ("none", "null"):
                return None
            try:
                if "." in text:
                    return float(text)
                return int(text)
            except Exception:
                return value
        return value

    @staticmethod
    def _parse_float(value):
        """安全解析浮点数"""
        try:
            return float(value)
        except Exception:
            return 0.0

class CharacterManager(object):
    def __init__(self, stage_panel):
        self.stage_panel = stage_panel


class MenuManager(object):
    """管理可点击的分支选择按钮"""

    BUTTON_HEIGHT = 23   # choice_button_panel模板高度
    DIVIDER_HEIGHT = 4   # choice_divider模板高度（按钮间分隔）

    def __init__(self, ui_instance):
        self.ui = ui_instance
        self.menu_panel = ui_instance.menu_panel
        self.choice_controls = []  # 已创建的子控件列表，用于清理

    def show_menu(self, cmd):
        """显示菜单选项按钮"""
        choices = cmd.get("choices", [])
        title = cmd.get("title", "")

        if not choices:
            logger.warn("菜单无可用选项，自动继续")
            self.ui.pending_menu = None
            self.ui.pause_mode = None
            self.ui.ExecuteUntilPause()
            return

        # 显示标题到对话框（如有）
        if title:
            self.ui.speaker_panel.SetVisible(False)
            self.ui.dialog_panel.SetVisible(True)
            self.ui.dialog_label.SetText(title)

        # 隐藏全屏触摸按钮，让选项按钮可以接收点击事件
        self.ui.touch_button.SetVisible(False)

        # 清理旧按钮
        self._clear_choices()

        # 计算面板高度并调整大小，使 stack_panel 居中显示
        n = len(choices)
        total_height = n * self.BUTTON_HEIGHT + max(0, n - 1) * self.DIVIDER_HEIGHT
        current_size = self.menu_panel.GetSize()
        self.menu_panel.SetSize((current_size[0], total_height))

        # 逐项创建按钮，按钮之间插入分隔
        for i, choice in enumerate(choices):
            if i > 0:
                divider = self.ui.CreateChildControl(
                    "GameUI.choice_divider",
                    "divider_{}".format(i),
                    self.menu_panel
                )
                self.choice_controls.append(divider)

            choice_text = choice.get("text", "选项{}".format(i + 1))
            button_panel = self._create_choice_button(i, choice_text)
            self.choice_controls.append(button_panel)

        # 显示菜单面板
        self.menu_panel.SetVisible(True)

    def hide_menu(self):
        """隐藏菜单并清理所有动态控件"""
        self._clear_choices()
        self.menu_panel.SetVisible(False)
        # 恢复全屏触摸按钮
        self.ui.touch_button.SetVisible(True)


    def _create_choice_button(self, choice_index, choice_text):
        """创建单个选项按钮并绑定点击回调"""
        button_panel = self.ui.CreateChildControl(
            "GameUI.choice_button_panel",
            "choice_{}".format(choice_index),
            self.menu_panel
        )
        button = button_panel.GetChildByPath("/choice_button").asButton()
        button_label = button_panel.GetChildByPath("/choice_button/button_label").asLabel()

        # 设置按钮文字
        button_label.SetText(choice_text)

        # 启用触摸事件并绑定回调
        button.AddTouchEventParams({"isSwallow": True})

        def on_choice_click(args, idx=choice_index):
            self._on_choice_selected(idx)

        button.SetButtonTouchUpCallback(on_choice_click)
        return button_panel

    def _on_choice_selected(self, choice_index):
        """选项被点击后的处理：隐藏菜单 -> 设置变量 -> 跳转标签 -> 继续剧本"""
        cmd = self.ui.pending_menu
        if not cmd:
            return

        choices = cmd.get("choices", [])
        if choice_index < 0 or choice_index >= len(choices):
            logger.error("无效的选项索引: {}".format(choice_index))
            return

        choice = choices[choice_index]
        target = choice.get("label")

        logger.info("玩家选择了: [{}] {}".format(choice_index, choice.get("text", "")))

        # 隐藏菜单并恢复触摸按钮
        self.hide_menu()

        # 清除待处理菜单
        self.ui.pending_menu = None
        self.ui.pause_mode = None

        # 处理选项关联的变量设置（可选字段 set_var）
        set_var = choice.get("set_var")
        if set_var and isinstance(set_var, dict):
            self.ui.variables.update(set_var)

        # 跳转到指定标签
        if target:
            self.ui._jump_to_label(target)

        # 继续执行剧本
        self.ui.ExecuteUntilPause()

    def _clear_choices(self):
        """移除所有动态创建的选项按钮和分隔符"""
        for control in self.choice_controls:
            try:
                self.ui.RemoveChildControl(control)
            except Exception:
                pass
        self.choice_controls = []