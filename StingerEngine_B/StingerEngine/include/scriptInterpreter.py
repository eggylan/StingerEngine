# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
from clientTools import logger, compGame, PlayBGM, PlayUISound, StopMusic
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
        self.chars_per_tick = 3  # 每次显示3个字符
        
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
            "character_enter": self._handle_character_enter,
            "character_show": self._handle_character_show,
            "character_update": self._handle_character_update,
            "character_play_anim": self._handle_character_play_anim,
            "character_hide": self._handle_character_hide,
            "character_clear": self._handle_character_clear,
            "character_move": self._handle_character_move,
            "character_scale": self._handle_character_scale,
        }
        
    def execute(self, command):
        """执行命令,返回是否需要暂停"""
        if not isinstance(command, dict):
            return False
            
        cmd_type = command.get("type")
        handler = self.handlers.get(cmd_type)
        
        if handler:
            return handler(command)
        
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

    # ------------------------------------------------------------------
    #  角色指令处理
    # ------------------------------------------------------------------

    def _handle_character_enter(self, cmd):
        char_id = cmd.get("id")
        if not char_id:
            logger.warn("character_enter 缺少 id 字段")
            return False
        image = cmd.get("image")
        position = cmd.get("position", "center")
        fade_in = self._parse_float(cmd.get("fade_in", 0))
        return self.ui.character_manager.enter(char_id, image, position, fade_in)

    def _handle_character_show(self, cmd):
        char_id = cmd.get("id")
        if not char_id:
            logger.warn("character_show 缺少 id 字段")
            return False
        image = cmd.get("image")
        position = cmd.get("position", "center")
        return self.ui.character_manager.show(char_id, image, position)

    def _handle_character_update(self, cmd):
        char_id = cmd.get("id")
        if not char_id:
            logger.warn("character_update 缺少 id 字段")
            return False
        image = cmd.get("image")
        expression = cmd.get("expression")
        transition = self._parse_float(cmd.get("transition", 0))
        return self.ui.character_manager.update(char_id, image, expression, transition)

    def _handle_character_play_anim(self, cmd):
        char_id = cmd.get("id")
        if not char_id:
            logger.warn("character_play_anim 缺少 id 字段")
            return False
        animdata = cmd.get("animdata")
        loop = bool(cmd.get("loop", False))
        speed = self._parse_float(cmd.get("speed", 1.0)) or 1.0
        return self.ui.character_manager.play_anim(char_id, animdata, loop, speed)

    def _handle_character_hide(self, cmd):
        char_id = cmd.get("id")
        if not char_id:
            logger.warn("character_hide 缺少 id 字段")
            return False
        fade_out = self._parse_float(cmd.get("fade_out", 0))
        return self.ui.character_manager.hide(char_id, fade_out)

    def _handle_character_clear(self, cmd):
        fade_out = self._parse_float(cmd.get("fade_out", 0))
        return self.ui.character_manager.clear(fade_out)

    def _handle_character_move(self, cmd):
        char_id = cmd.get("id")
        pause_during_move = bool(cmd.get("pause", True))
        if not char_id:
            logger.warn("character_move 缺少 id 字段")
            return False
        target = cmd.get("position", "center")
        duration = self._parse_float(cmd.get("duration", 0.5))
        return self.ui.character_manager.move(char_id, target, duration, pause_during_move)

    def _handle_character_scale(self, cmd):
        char_id = cmd.get("id")
        if not char_id:
            logger.warn("character_scale 缺少 id 字段")
            return False
        scale_x = self._parse_float(cmd.get("scale_x", 1.0)) or 1.0
        scale_y = self._parse_float(cmd.get("scale_y", 1.0)) or 1.0
        duration = self._parse_float(cmd.get("duration", 0))
        return self.ui.character_manager.scale(char_id, scale_x, scale_y, duration)

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
    """角色立绘管理器：管理舞台上角色面板的创建、显示、更新、移动、缩放和清除

    每个角色通过 GameUI.character 模板动态创建到 stage_panel 下，
    使用 SetFullPosition 实现基于百分比的定位。
    """

    # 位置预设（基于bottom_middle锚点的X轴偏移，relativeValue 乘以父容器宽度）
    POSITIONS = {
        "left":         -0.25,
        "center_left":  -0.12,
        "center":        0.0,
        "center_right":  0.12,
        "right":         0.25,
    }

    # 默认角色图片尺寸占比（相对父容器）
    DEFAULT_SCALE_X = 0.30    # 30% 宽
    DEFAULT_SCALE_Y = 0.92    # 92% 高

    def __init__(self, ui_instance, stage_panel):
        """
        Args:
            ui_instance: GameUI (ScreenNode) 实例，用于 CreateChildControl / RemoveChildControl
            stage_panel: 舞台面板控件（角色控件的父容器）
        """
        self.ui = ui_instance
        self.stage_panel = stage_panel
        self.characters = {}    # {char_id: dict}
        self._anim_counter = 0

    #  公共方法
    def enter(self, char_id, image, position="center", fade_in=0):
        """角色入场（带可选淡入动画）

        Args:
            char_id:  角色唯一标识
            image:    贴图路径（传给 SetSprite）
            position: 位置名称或 float 偏移量
            fade_in:  淡入时长（秒），0 表示直接显示

        Returns:
            bool: 是否需要暂停脚本执行
        """
        if char_id in self.characters:
            self._remove_character(char_id)

        control, image_base, image_emotion = self._create_character_control(char_id, image, position)
        if not control:
            return False

        if fade_in > 0:
            self.ui.pause_mode = "wait"
            anim_name = self._next_anim_name("char_enter")

            def _on_done():
                if self.ui.pause_mode != "wait":
                    return
                self.ui.pause_mode = None
                self.ui.ExecuteUntilPause()

            self._fade_appear(control, fade_in, anim_name, callback=_on_done)
            return True
        else:
            control.SetVisible(True)
            return False

    def show(self, char_id, image, position="center"):
        """直接显示角色（无入场动画）"""
        if char_id in self.characters:
            self._remove_character(char_id)

        control, image_base, image_emotion = self._create_character_control(char_id, image, position)
        if not control:
            return False

        control.SetVisible(True)
        return False

    def update(self, char_id, image=None, expression=None, transition=0):
        """更新角色外观（图片/表情），可选带过渡动画

        transition > 0时执行 淡出→换图→淡入 动画。
        """
        char_data = self.characters.get(char_id)
        if not char_data:
            logger.warn("角色不存在，无法更新: {}".format(char_id))
            return False

        if transition > 0 and image:
            self.ui.pause_mode = "wait"
            control = char_data["control"]
            half = transition / 2.0
            anim_out = self._next_anim_name("char_upd_out")
            anim_in  = self._next_anim_name("char_upd_in")

            def _on_out():
                if char_id not in self.characters:
                    return
                char_data["image_base"].asImage().SetSprite(image)
                char_data["image"] = image
                if expression:
                    char_data["image_emotion"].asImage().SetSprite(expression)
                    char_data["image_emotion"].SetVisible(True)

                def _on_in():
                    if self.ui.pause_mode != "wait":
                        return
                    self.ui.pause_mode = None
                    self.ui.ExecuteUntilPause()

                self._fade_appear(control, half, anim_in, callback=_on_in)

            self._fade_disappear(control, half, anim_out, callback=_on_out)
            return True
        else:
            if image:
                char_data["image_base"].asImage().SetSprite(image)
                char_data["image"] = image
            if expression:
                char_data["image_emotion"].asImage().SetSprite(expression)
                char_data["image_emotion"].SetVisible(True)
            return False

    def play_anim(self, char_id, animdata, loop=False, speed=1.0):
        """播放角色自定义动画

        animdata 为动画定义字典，格式同 RegisterUIAnimations 中的动画，例如:
            {"anim_type": "offset", "duration": 0.5, "from": [0,0], "to": [10,0]}

        loop=True  时动画循环播放，脚本不暂停。
        loop=False 时脚本暂停直到动画结束。
        """
        char_data = self.characters.get(char_id)
        if not char_data:
            logger.warn("角色不存在，无法播放动画: {}".format(char_id))
            return False

        if not animdata or not isinstance(animdata, dict):
            logger.warn("character_play_anim 的 animdata 无效")
            return False

        control = char_data["image_base"]
        anim_name = self._next_anim_name("char_anim")
        anim_def = dict(animdata)  # 浅拷贝，避免修改原始数据

        if speed > 0 and speed != 1.0 and "duration" in anim_def:
            anim_def["duration"] = anim_def["duration"] / speed

        if loop and "next" not in anim_def:
            anim_def["next"] = "@GameUI.{}".format(anim_name)

        anim_type = anim_def.get("anim_type", "offset")
        reg_data = {"namespace": "GameUI", anim_name: anim_def}
        clientApi.RegisterUIAnimations(reg_data, override=True)

        control.RemoveAnimation(anim_type)
        control.SetAnimation(anim_type, "GameUI", anim_name, True)

        if not loop:
            self.ui.pause_mode = "wait"

            def _on_anim_done():
                control.RemoveAnimation(anim_type)
                if self.ui.pause_mode != "wait":
                    return
                self.ui.pause_mode = None
                self.ui.ExecuteUntilPause()

            control.SetAnimEndCallback(anim_name, _on_anim_done)
            return True

        return False

    def hide(self, char_id, fade_out=0):
        """隐藏并移除单个角色"""
        char_data = self.characters.get(char_id)
        if not char_data:
            return False

        if fade_out > 0:
            self.ui.pause_mode = "wait"
            anim_name = self._next_anim_name("char_hide")
            control = char_data["control"]

            def _on_done():
                self._remove_character(char_id)
                if self.ui.pause_mode != "wait":
                    return
                self.ui.pause_mode = None
                self.ui.ExecuteUntilPause()

            self._fade_disappear(control, fade_out, anim_name, callback=_on_done)
            return True
        else:
            self._remove_character(char_id)
            return False

    def clear(self, fade_out=0):
        """清除舞台上的所有角色"""
        if not self.characters:
            return False

        ids = list(self.characters.keys())

        if fade_out > 0:
            self.ui.pause_mode = "wait"
            pending = [len(ids)]

            def _make_cb(cid):
                def _on_done():
                    pending[0] -= 1
                    if pending[0] <= 0:
                        for c in ids:
                            self._remove_character(c)
                        if self.ui.pause_mode != "wait":
                            return
                        self.ui.pause_mode = None
                        self.ui.ExecuteUntilPause()
                return _on_done

            for cid in ids:
                anim_name = self._next_anim_name("char_clr")
                self._fade_disappear(
                    self.characters[cid]["control"],
                    fade_out,
                    anim_name,
                    callback=_make_cb(cid),
                )
            return True
        else:
            for cid in ids:
                self._remove_character(cid)
            return False

    def move(self, char_id, target_position, duration=0.5,pause_during_move=True):
        """移动角色到目标位置（带 smoothstep 缓动）

        target_position 可以是预设名称（如 "left"）或一个 float 偏移量。
        duration <= 0 时立即移动。
        """
        char_data = self.characters.get(char_id)
        if not char_data:
            logger.warn("角色不存在，无法移动: {}".format(char_id))
            return False

        image_base = char_data["image_base"]
        end_rel = self._get_position_value(target_position)

        if duration <= 0:
            self._set_position_x(image_base, end_rel)
            char_data["position"] = target_position
            return False

        start_rel = self._get_position_value(char_data["position"])
        self.ui.pause_mode = "wait"
        interval = 0.02   # ~50 FPS
        steps_total = max(1, int(duration / interval))
        state = {"step": 0, "timer": None}

        def _tick():
            if char_id not in self.characters:
                if state["timer"]:
                    compGame.CancelTimer(state["timer"])
                return

            state["step"] += 1
            t = min(1.0, float(state["step"]) / steps_total)
            t = t * t * (3.0 - 2.0 * t)  # smoothstep
            current = start_rel + (end_rel - start_rel) * t
            self._set_position_x(image_base, current)

            if state["step"] >= steps_total:
                if state["timer"]:
                    compGame.CancelTimer(state["timer"])
                    state["timer"] = None
                char_data["position"] = target_position
                if self.ui.pause_mode != "wait":
                    return
                self.ui.pause_mode = None
                self.ui.ExecuteUntilPause()

        state["timer"] = compGame.AddRepeatedTimer(interval, _tick)
        char_data["_move_timer"] = state["timer"]
        return pause_during_move

    def scale(self, char_id, scale_x=1.0, scale_y=1.0, duration=0):
        """改变角色大小（带可选过渡动画）

        scale_x / scale_y 为相对于默认尺寸的倍率（1.0 = 原始大小）。
        duration <= 0 时立即缩放。
        """
        char_data = self.characters.get(char_id)
        if not char_data:
            logger.warn("角色不存在，无法缩放: {}".format(char_id))
            return False

        image_base = char_data["image_base"]
        end_rx = self.DEFAULT_SCALE_X * scale_x
        end_ry = self.DEFAULT_SCALE_Y * scale_y

        if duration <= 0:
            self._set_size(image_base, end_rx, end_ry)
            return False

        cur_x = image_base.GetFullSize("x")
        cur_y = image_base.GetFullSize("y")
        start_rx = cur_x.get("relativeValue", self.DEFAULT_SCALE_X)
        start_ry = cur_y.get("relativeValue", self.DEFAULT_SCALE_Y)

        self.ui.pause_mode = "wait"
        interval = 0.02
        steps_total = max(1, int(duration / interval))
        state = {"step": 0, "timer": None}

        def _tick():
            if char_id not in self.characters:
                if state["timer"]:
                    compGame.CancelTimer(state["timer"])
                return

            state["step"] += 1
            t = min(1.0, float(state["step"]) / steps_total)
            t = t * t * (3.0 - 2.0 * t)  # smoothstep
            cx = start_rx + (end_rx - start_rx) * t
            cy = start_ry + (end_ry - start_ry) * t
            self._set_size(image_base, cx, cy)

            if state["step"] >= steps_total:
                if state["timer"]:
                    compGame.CancelTimer(state["timer"])
                    state["timer"] = None
                if self.ui.pause_mode != "wait":
                    return
                self.ui.pause_mode = None
                self.ui.ExecuteUntilPause()

        state["timer"] = compGame.AddRepeatedTimer(interval, _tick)
        char_data["_scale_timer"] = state["timer"]
        return True

    def destroy(self):
        """销毁所有角色控件（UI 销毁时调用）"""
        ids = list(self.characters.keys())
        for cid in ids:
            self._remove_character(cid)

    # 以下是内部方法
    def _create_character_control(self, char_id, image, position):
        """创建角色控件并存储元数据

        Returns:
            tuple: (control, image_base, image_emotion) 或 (None, None, None)
        """
        control = self.ui.CreateChildControl(
            "GameUI.character",
            "char_{}".format(char_id),
            self.stage_panel,
        )
        if not control:
            logger.error("角色控件创建失败: {}".format(char_id))
            return None, None, None

        image_base = control.GetChildByPath("/character_image_base")
        image_emotion = control.GetChildByPath("/character_image_base/character_image_emotion")

        # 设置立绘图片
        if image:
            image_base.asImage().SetSprite(image)

        # 默认隐藏表情覆盖层（此处尚未完成）
        if image_emotion:
            image_emotion.SetVisible(False)

        # 应用位置
        self._apply_position(image_base, position)

        self.characters[char_id] = {
            "control": control,
            "image_base": image_base,
            "image_emotion": image_emotion,
            "position": position,
            "image": image,
        }
        return control, image_base, image_emotion

    def _apply_position(self, image_base, position):
        """将位置预设应用到角色控件 X 轴"""
        rel = self._get_position_value(position)
        self._set_position_x(image_base, rel)

    def _get_position_value(self, position):
        """将位置标识（字符串或数字）转换为 relativeValue"""
        if isinstance(position, (int, float)):
            return float(position)
        return self.POSITIONS.get(position, 0.0)

    @staticmethod
    def _set_position_x(control, relative_value):
        """设置控件x轴位置（基于父容器百分比）"""
        control.SetFullPosition("x", {
            "followType": "parent",
            "relativeValue": relative_value,
            "absoluteValue": 0,
        })

    @staticmethod
    def _set_size(control, rel_x, rel_y):
        """设置控件相对尺寸"""
        control.SetFullSize("x", {"followType": "parent", "relativeValue": rel_x, "absoluteValue": 0})
        control.SetFullSize("y", {"followType": "parent", "relativeValue": rel_y, "absoluteValue": 0})

    def _remove_character(self, char_id):
        """移除角色控件并取消关联定时器"""
        char_data = self.characters.pop(char_id, None)
        if not char_data:
            return
        # 取消可能正在运行的移动/缩放定时器
        for key in ("_move_timer", "_scale_timer"):
            timer = char_data.get(key)
            if timer:
                try:
                    compGame.CancelTimer(timer)
                except Exception:
                    pass
        control = char_data.get("control")
        if control:
            try:
                self.ui.RemoveChildControl(control)
            except Exception:
                pass

    def _next_anim_name(self, prefix="char"):
        """生成唯一动画名称，避免多角色动画冲突"""
        self._anim_counter += 1
        return "{}_{}".format(prefix, self._anim_counter)

    def _fade_appear(self, control, duration, anim_name, callback=None):
        """淡入效果（alpha 0 → 1，控件从透明变为可见）"""
        control.SetVisible(True)

        def _wrapper():
            if callback:
                callback()

        anim_data = {
            "namespace": "GameUI",
            anim_name: {
                "anim_type": "alpha",
                "duration": duration,
                "from": 0,
                "to": 1,
                "next": "",
            },
        }
        clientApi.RegisterUIAnimations(anim_data, override=True)
        control.RemoveAnimation("alpha")
        control.SetAnimation("alpha", "GameUI", anim_name, True)
        control.SetAnimEndCallback(anim_name, _wrapper)

    def _fade_disappear(self, control, duration, anim_name, callback=None):
        """淡出效果（alpha 1 → 0，控件从可见变为透明）"""
        control.SetVisible(True)

        def _wrapper():
            control.SetVisible(False)
            if callback:
                callback()

        anim_data = {
            "namespace": "GameUI",
            anim_name: {
                "anim_type": "alpha",
                "duration": duration,
                "from": 1,
                "to": 0,
                "next": "",
            },
        }
        clientApi.RegisterUIAnimations(anim_data, override=True)
        control.RemoveAnimation("alpha")
        control.SetAnimation("alpha", "GameUI", anim_name, True)
        control.SetAnimEndCallback(anim_name, _wrapper)


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