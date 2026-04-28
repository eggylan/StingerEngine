# -*- coding: utf-8 -*-
import traceback
from ..include.QuModLibs.Client import *
from ..include.QuModLibs.UI import ScreenNodeWrapper
from ..include.clientTools import (
    GetLocalConfigData,
    NotifyMsg,
    PlayUISound,
    SetLocalConfigData,
    StopMusic,
    logger,
)
from ..include.modconfig import (
    SAVE_CLIENT_CONFIG_NAME,
    SAVE_DEFAULT_QUICK_LOAD_KEY,
    SAVE_DEFAULT_QUICK_SAVE_KEY,
    SAVE_LOAD_RESPONSE,
    SAVE_SLOT_AUTO_ID,
    SAVE_SLOT_QUICK_ID,
    SAVE_WRITE_RESPONSE,
    SCRIPT_EXECUTION_STEP_LIMIT,
)
from ..include.saveData import (
    CloneSerializableData,
    CreateDefaultDialogState,
    CreateDefaultVisualState,
    IsValidSaveSlotId,
    SAVE_SCHEMA_VERSION,
    SAVEABLE_PAUSE_MODES,
    ValidateSaveSnapshot,
    ValidateSnapshotAgainstScript,
)
from ..include.scriptInterpreter import TypewriterEffect, CommandExecutor, CharacterManager, MenuManager
from ..EngineClient import get_engine_client

GAME_QUICK_SAVE_SOURCE = "game_quick"
GAME_AUTO_SAVE_SOURCE = "game_auto"


@ScreenNodeWrapper.autoRegister("GameUI.GameUI")
class GameUI(ScreenNodeWrapper):
    def __init__(self, namespace, name, param):
        ScreenNodeWrapper.__init__(self, namespace, name, param)
        self.param = param
        self.entry = param.get("entry", "main")
        self.script_data = []

        # 状态变量
        self.current_index = 0
        self.pause_mode = None  # None | tap | menu | wait | ended
        self.variables = {}
        self.label_index = {}
        self.current_label = None
        self.current_dialog = CreateDefaultDialogState()
        self.last_saveable_state = None
        self.pending_menu = None
        self.current_bg = None
        self.current_music = None
        self.current_cg = {"0": None, "1": None}
        self.cg_front = "0"  # 当前前景CG槽位，"0" 或 "1"
        self.fade_visible = False
        self.inline_queue = []  # 内联命令队列（condition 等暂停恢复用）
        self.world_context = {}
        self.dialog_history = []
        self.max_history_items = 120

        # 组件
        self.typewriter = None
        self.executor = None
        self.character_manager = None
        self.menu_manager = None
        self.dialog_panel = None
        self.dialog_label = None 
        self.speaker_panel = None
        self.speaker_label = None
        self.stage_panel = None
        self.menu_panel = None
        self.touch_button = None
        self.bg_image = None
        self.cg_panel = None
        self.cg_image_0_base = None
        self.cg_image_1_base = None
        self.fade_overlay = None
        self.system_menu_button = None
        self._save_preferences = {}
        self._auto_save_pending_reason = None
        self._last_auto_save_label = None
        self._last_auto_save_index = -1
        self._is_auto_saving = False

    def _show_error_ui(self, errinfo):
        try:
            self.pause_mode = "ended"
            self.SetRemove()
        except Exception:
            pass
        ec = get_engine_client()
        if ec:
            ec.CreateErrorUI(errinfo)

    @staticmethod
    def _to_text(value):
        if value is None:
            return ""
        if isinstance(value, basestring):
            return value

    def _set_dialog_state(self, speaker, content, dialog_visible=True, speaker_visible=True):
        speaker = self._to_text(speaker)
        content = self._to_text(content)
        dialog_visible = bool(dialog_visible)
        speaker_visible = bool(speaker_visible and speaker)

        self.current_dialog = {
            "speaker": speaker,
            "content": content,
            "dialog_visible": dialog_visible,
            "speaker_visible": speaker_visible,
        }

        if self.dialog_panel:
            self.dialog_panel.SetVisible(dialog_visible)
        if self.dialog_label:
            self.dialog_label.SetText(content)
        if self.speaker_panel:
            self.speaker_panel.SetVisible(speaker_visible)
        if self.speaker_label:
            self.speaker_label.SetText(speaker)

    def _update_last_saveable_state(self):
        if self.pause_mode not in SAVEABLE_PAUSE_MODES:
            return
        self.last_saveable_state = {
            "entry": self.entry,
            "current_index": self.current_index,
            "pause_mode": self.pause_mode,
            "current_label": self.current_label,
        }

    def CanSaveNow(self):
        if self.pause_mode not in SAVEABLE_PAUSE_MODES:
            return False
        if self.character_manager and self.character_manager.has_active_transition():
            return False
        return True

    def RecordHistory(self, record_type, speaker, content):
        content = self._to_text(content)
        if not content:
            return
        item = {
            "type": record_type or "text",
            "speaker": self._to_text(speaker),
            "content": content,
            "entry": self.entry,
            "index": int(self.current_index),
            "label": self.current_label or "",
        }
        self.dialog_history.append(item)
        if len(self.dialog_history) > self.max_history_items:
            self.dialog_history = self.dialog_history[-self.max_history_items:]

    def GetHistoryItems(self):
        return CloneSerializableData(self.dialog_history, [])

    def GetSettingDefinitions(self):
        return [
            {
                "key": "typewriter_speed",
                "label": "文字速度",
                "type": "choice",
                "choices": [
                    {"label": "慢", "value": 0.06},
                    {"label": "标准", "value": 0.03},
                    {"label": "快", "value": 0.015},
                    {"label": "瞬间", "value": 0.0},
                ],
            },
            {
                "key": "auto_save_enabled",
                "label": "自动存档",
                "type": "toggle",
            },
        ]

    def GetSettingValue(self, key):
        return self._save_preferences.get(key)

    def SetSettingValue(self, key, value):
        if key == "typewriter_speed":
            try:
                value = float(value)
            except Exception:
                value = 0.03
            self._save_preferences[key] = value
            if self.typewriter:
                self.typewriter.default_speed = value
        elif key == "auto_save_enabled":
            self._save_preferences[key] = bool(value)
        else:
            self._save_preferences[key] = value
        self._save_save_preferences()

    def GetTypewriterSpeed(self):
        try:
            return float(self._save_preferences.get("typewriter_speed", 0.03))
        except Exception:
            return 0.03

    def IsAutoSaveEnabled(self):
        return bool(self._save_preferences.get("auto_save_enabled", True))

    def BuildSaveSnapshot(self, slotId=None, finishTypewriter=True):
        if slotId is not None and not IsValidSaveSlotId(slotId):
            raise ValueError("无效的存档槽位: {}".format(slotId))
        if not self.CanSaveNow():
            raise ValueError("当前状态不可存档: {}".format(self.pause_mode))

        if finishTypewriter and self.typewriter and self.typewriter.is_active:
            self.typewriter.finish()

        dialog = CloneSerializableData(self.current_dialog, CreateDefaultDialogState())
        pending_menu = CloneSerializableData(self.pending_menu, None)
        inline_queue = CloneSerializableData(self.inline_queue, [])
        variables = CloneSerializableData(self.variables, {})
        world_context = CloneSerializableData(self.world_context, {})
        characters = []
        if self.character_manager:
            characters = self.character_manager.export_state()

        snapshot = {
            "schema_version": SAVE_SCHEMA_VERSION,
            "slot_id": slotId,
            "entry": self.entry,
            "current_index": int(self.current_index),
            "pause_mode": self.pause_mode,
            "current_label": self.current_label,
            "variables": variables,
            "dialog": dialog,
            "pending_menu": pending_menu,
            "inline_queue": inline_queue,
            "visual": {
                "background": self.current_bg,
                "music": self.current_music,
                "cg_front": self.cg_front,
                "cg": CloneSerializableData(self.current_cg, {"0": None, "1": None}),
                "fade_visible": bool(self.fade_visible),
            },
            "characters": characters,
            "world_context": world_context,
            "history": CloneSerializableData(self.dialog_history, []),
        }

        valid, error_code = ValidateSaveSnapshot(snapshot)
        if not valid:
            raise ValueError("存档快照校验失败: {}".format(error_code))

        self._update_last_saveable_state()
        return snapshot

    def ApplySaveSnapshot(self, snapshot):
        snapshot = CloneSerializableData(snapshot, None)
        valid, error_code = ValidateSaveSnapshot(snapshot)
        if not valid:
            raise ValueError("存档快照校验失败: {}".format(error_code))

        entry = snapshot.get("entry", "main")
        script_data = self._load_script(entry)
        label_index = self._build_label_index_for(script_data)
        valid, error_code = ValidateSnapshotAgainstScript(snapshot, script_data, label_index)
        if not valid:
            raise ValueError("存档与当前脚本不兼容: {}".format(error_code))

        self.ResetRuntimeState()
        self.entry = entry
        self.script_data = script_data
        self.label_index = label_index

        visual = snapshot.get("visual") or CreateDefaultVisualState()
        self._apply_visual_state(visual)

        if self.character_manager:
            self.character_manager.restore_state(snapshot.get("characters", []))

        self.variables = CloneSerializableData(snapshot.get("variables", {}), {})
        self.world_context = CloneSerializableData(snapshot.get("world_context", {}), {})
        self.dialog_history = CloneSerializableData(snapshot.get("history", []), [])

        dialog = snapshot.get("dialog") or CreateDefaultDialogState()
        self._set_dialog_state(
            dialog.get("speaker", ""),
            dialog.get("content", ""),
            dialog.get("dialog_visible", False),
            dialog.get("speaker_visible", False),
        )

        self.pending_menu = CloneSerializableData(snapshot.get("pending_menu"), None)
        self.pause_mode = snapshot.get("pause_mode")
        if self.pause_mode == "menu" and self.pending_menu and self.menu_manager:
            self.menu_manager.show_menu(self.pending_menu)
            self._set_dialog_state(
                dialog.get("speaker", ""),
                dialog.get("content", ""),
                dialog.get("dialog_visible", False),
                dialog.get("speaker_visible", False),
            )
        elif self.pause_mode == "tap" and self.touch_button:
            self.touch_button.SetVisible(True)
        elif self.touch_button:
            self.touch_button.SetVisible(False)

        self.current_index = int(snapshot.get("current_index", 0))
        self.inline_queue = CloneSerializableData(snapshot.get("inline_queue", []), [])
        self.current_label = snapshot.get("current_label")
        self._update_last_saveable_state()
        self._last_auto_save_label = self.current_label
        self._last_auto_save_index = self.current_index

    def ResetRuntimeState(self):
        if self.typewriter:
            self.typewriter.stop()
        if self.menu_manager:
            self.menu_manager.hide_menu()
        if self.character_manager:
            self.character_manager.destroy()
        if self.current_music:
            try:
                StopMusic(self.current_music, 0.0)
            except Exception:
                pass

        self.current_index = 0
        self.pause_mode = None
        self.variables = {}
        self.current_label = None
        self.current_dialog = CreateDefaultDialogState()
        self.last_saveable_state = None
        self.pending_menu = None
        self.current_bg = None
        self.current_music = None
        self.current_cg = {"0": None, "1": None}
        self.cg_front = "0"
        self.fade_visible = False
        self.inline_queue = []
        self.world_context = {}
        self.dialog_history = []

        if self.dialog_panel:
            self.dialog_panel.SetVisible(False)
        if self.dialog_label:
            self.dialog_label.SetText("")
        if self.speaker_panel:
            self.speaker_panel.SetVisible(False)
        if self.speaker_label:
            self.speaker_label.SetText("")
        if self.touch_button:
            self.touch_button.SetVisible(True)
        if self.bg_image:
            self.bg_image.SetSprite("textures/modTextures/default/black")
        if self.cg_panel:
            self.cg_panel.SetVisible(False)
        if self.cg_image_0_base:
            self.cg_image_0_base.SetVisible(False)
        if self.cg_image_1_base:
            self.cg_image_1_base.SetVisible(False)
        if self.fade_overlay:
            self.fade_overlay.SetVisible(False)

    def _apply_visual_state(self, visual):
        background = visual.get("background")
        if background and self.bg_image:
            self.bg_image.SetSprite(background)
        self.current_bg = background

        self._apply_cg_state(visual.get("cg") or {"0": None, "1": None}, visual.get("cg_front", "0"))

        music = visual.get("music")
        if music:
            PlayUISound(music, loop=True)
        self.current_music = music

        self.fade_visible = bool(visual.get("fade_visible", False))
        if self.fade_overlay:
            self.fade_overlay.SetVisible(self.fade_visible)

    def _apply_cg_state(self, cg_state, cg_front):
        self.current_cg = {
            "0": cg_state.get("0"),
            "1": cg_state.get("1"),
        }
        self.cg_front = cg_front if cg_front in ("0", "1") else "0"

        has_cg = False
        for slot, control in (("0", self.cg_image_0_base), ("1", self.cg_image_1_base)):
            image = self.current_cg.get(slot)
            if image and control:
                control.asImage().SetSprite(image)
                control.SetVisible(True)
                has_cg = True
            elif control:
                control.SetVisible(False)
        if self.cg_panel:
            self.cg_panel.SetVisible(has_cg)
        
    def _load_script(self, entry):
        """加载章节脚本"""
        module_path = "StingerEngine.chapters.{}".format(entry)
        script_module = clientApi.ImportModule(module_path)
        
        if not script_module:
            logger.error("未找到章节脚本 {}".format(module_path))
            raise ValueError("章节脚本不存在: {}".format(entry))
        else:
            logger.info("已加载章节脚本 {}".format(entry))
            
        script_data = getattr(script_module, "script_data", None)
        if not isinstance(script_data, list) or not script_data:
            raise ValueError("章节脚本为空或格式错误: {}".format(entry))
        return script_data
        
    def Create(self):
        """UI创建成功时调用"""
        ScreenNodeWrapper.Create(self)
        try:
            # 加载脚本
            self.script_data = self._load_script(self.entry)

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
            self._init_system_menu_controls()
            self._load_save_preferences()
            ec = get_engine_client()
            if ec:
                ec.RegisterGameUIRuntime(self)

            # 初始化组件
            typewriter_speed = self.param.get("typewriter_speed", self.GetTypewriterSpeed())
            self.typewriter = TypewriterEffect(self.dialog_label, typewriter_speed)
            self.executor = CommandExecutor(self)
            self.character_manager = CharacterManager(self, self.stage_panel)
            self.menu_manager = MenuManager(self)
            # 构建标签索引
            self._build_label_index()
            if self.param.get("startMode") == "resume" and self.param.get("resumeSnapshot"):
                self.ApplySaveSnapshot(self.param.get("resumeSnapshot"))
            else:
                self.pause_mode = None
                self.ExecuteUntilPause()
        except Exception:
            errinfo = traceback.format_exc()
            logger.error("GameUI Create出错:\n{}".format(errinfo))
            self._show_error_ui(errinfo)
        
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

    def _init_system_menu_controls(self):
        self.system_menu_button = self.GetBaseUIControl("/root_panel/system_menu_button").asButton()
        self.system_menu_button.AddTouchEventParams({"isSwallow": True})
        self.system_menu_button.SetButtonTouchUpCallback(self.OnSystemMenuButton)
        ec = get_engine_client()
        if ec:
            ec.RegisterSaveResponseListener(self)
            ec.RegisterKeyEventListener(self)

    def _load_save_preferences(self):
        self._save_preferences = GetLocalConfigData(SAVE_CLIENT_CONFIG_NAME, {})
        if not isinstance(self._save_preferences, dict):
            self._save_preferences = {}
        self._save_preferences.setdefault("recent_slot", None)
        self._save_preferences.setdefault("save_tutorial_seen", False)
        self._save_preferences.setdefault("quick_save_key", SAVE_DEFAULT_QUICK_SAVE_KEY)
        self._save_preferences.setdefault("quick_load_key", SAVE_DEFAULT_QUICK_LOAD_KEY)
        self._save_preferences.setdefault("typewriter_speed", 0.03)
        self._save_preferences.setdefault("auto_save_enabled", True)

    def _save_save_preferences(self):
        SetLocalConfigData(SAVE_CLIENT_CONFIG_NAME, self._save_preferences)

    def _remember_recent_slot(self, slot_id):
        if not IsValidSaveSlotId(slot_id):
            return
        self._save_preferences["recent_slot"] = slot_id
        self._save_save_preferences()

    def MarkAutoSavePending(self, reason):
        self._auto_save_pending_reason = reason or "auto"

    def TryAutoSave(self, reason="auto"):
        if not self.IsAutoSaveEnabled():
            self._auto_save_pending_reason = None
            return False
        if self._is_auto_saving or not self._auto_save_pending_reason:
            return False
        if not self.CanSaveNow():
            return False

        marker_label = self.current_label
        marker_index = self.current_index
        if marker_label == self._last_auto_save_label and marker_index == self._last_auto_save_index:
            self._auto_save_pending_reason = None
            return False

        try:
            self._is_auto_saving = True
            snapshot = self.BuildSaveSnapshot(SAVE_SLOT_AUTO_ID, False)
            ec = get_engine_client()
            if ec:
                ec.RequestSaveWrite(SAVE_SLOT_AUTO_ID, snapshot, "自动存档", GAME_AUTO_SAVE_SOURCE)
            self._last_auto_save_label = marker_label
            self._last_auto_save_index = marker_index
            self._auto_save_pending_reason = None
            return True
        except Exception:
            logger.error("自动存档失败({}):\n{}".format(reason, traceback.format_exc()))
            return False
        finally:
            self._is_auto_saving = False

    def QuickSave(self):
        if not self.CanSaveNow():
            NotifyMsg("当前演出中，稍后可快速存档")
            return
        try:
            snapshot = self.BuildSaveSnapshot(SAVE_SLOT_QUICK_ID)
        except Exception as exc:
            NotifyMsg("快速存档失败: " + self._to_text(exc))
            return
        ec = get_engine_client()
        if ec:
            ec.RequestSaveWrite(SAVE_SLOT_QUICK_ID, snapshot, "快速存档", GAME_QUICK_SAVE_SOURCE)

    def QuickLoad(self):
        ec = get_engine_client()
        if ec:
            ec.RequestSaveLoad(SAVE_SLOT_QUICK_ID, GAME_QUICK_SAVE_SOURCE)

    def OnKeyPressInGame(self, eventData):
        if not self._is_key_down(eventData.get("isDown")):
            return
        key = self._to_text(eventData.get("key", "")).upper()
        quick_save_key = self._to_text(self._save_preferences.get("quick_save_key", SAVE_DEFAULT_QUICK_SAVE_KEY)).upper()
        quick_load_key = self._to_text(self._save_preferences.get("quick_load_key", SAVE_DEFAULT_QUICK_LOAD_KEY)).upper()
        if key == quick_save_key:
            self.QuickSave()
        elif key == quick_load_key:
            self.QuickLoad()

    @staticmethod
    def _is_key_down(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, basestring):
            return value.lower() in ("true", "1", "down")
        return False

    def OnSystemMenuButton(self, args):
        ec = get_engine_client()
        if ec:
            ec.CreateSystemMenuUI("save")

    def OnSaveResponse(self, event_name, data):
        source = data.get("source")
        if source not in (GAME_QUICK_SAVE_SOURCE, GAME_AUTO_SAVE_SOURCE):
            return
        if event_name == SAVE_WRITE_RESPONSE:
            self._handle_save_write_response(data)
        elif event_name == SAVE_LOAD_RESPONSE:
            self._handle_save_load_response(data)

    def _handle_save_write_response(self, data):
        if data.get("ok", False):
            slot_id = data.get("slot_id")
            self._remember_recent_slot(slot_id)
            if slot_id == SAVE_SLOT_AUTO_ID:
                logger.info("自动存档完成")
            elif slot_id == SAVE_SLOT_QUICK_ID:
                NotifyMsg("快速存档成功")
            else:
                NotifyMsg("存档成功")
        else:
            NotifyMsg(data.get("message", "存档失败"))

    def _handle_save_load_response(self, data):
        if not data.get("ok", False):
            NotifyMsg(data.get("message", "读取存档失败"))
            return
        snapshot = data.get("snapshot")
        if not snapshot:
            NotifyMsg("存档正文为空")
            return
        try:
            self.ApplySaveSnapshot(snapshot)
            self._remember_recent_slot(data.get("slot_id"))
            NotifyMsg("读档完成")
        except Exception as exc:
            errinfo = traceback.format_exc()
            logger.error("读档恢复失败:\n{}".format(errinfo))
            NotifyMsg("读档失败: " + self._to_text(exc))

    def ExecuteUntilPause(self):
        """执行剧本直到遇到暂停"""
        try:
            steps = 0
            max_steps = SCRIPT_EXECUTION_STEP_LIMIT
            
            while self.pause_mode is None:
                if steps >= max_steps:
                    raise RuntimeError(
                        "剧情执行超过最大连续步数 {}，可能存在无暂停死循环。entry={}, current_index={}".format(
                            max_steps,
                            self.entry,
                            self.current_index,
                        )
                    )

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
        except Exception:
            errinfo = traceback.format_exc()
            logger.error("剧情执行出错:\n{}".format(errinfo))
            self._show_error_ui(errinfo)
            
    def _build_label_index(self):
        """构建标签索引"""
        self.label_index = self._build_label_index_for(self.script_data)

    @staticmethod
    def _build_label_index_for(script_data):
        label_index = {}
        for index, command in enumerate(script_data):
            if isinstance(command, dict) and command.get("type") == "label":
                name = command.get("name")
                if name:
                    label_index[name] = index
        return label_index
                    
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
        try:
            ec = get_engine_client()
            if ec:
                ec.UnregisterSaveResponseListener(self)
                ec.UnregisterKeyEventListener(self)
                ec.UnregisterGameUIRuntime(self)
            if self.typewriter:
                self.typewriter.stop()
            if self.menu_manager:
                self.menu_manager._clear_choices()
            if self.character_manager:
                self.character_manager.destroy()
            self.pause_mode = "ended"
        except Exception:
            pass
        
    def OnActive(self):
        """UI重新回到栈顶时调用"""
        pass
        
    def OnDeactive(self):
        """栈顶UI有其他UI入栈时调用"""
        pass