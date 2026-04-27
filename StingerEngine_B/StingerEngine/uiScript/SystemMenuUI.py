# -*- coding: utf-8 -*-
import traceback
import mod.client.extraClientApi as clientApi

from StingerEngine.include.clientTools import GetLocalConfigData, NotifyMsg, SetLocalConfigData, compGame, logger
from StingerEngine.include.modconfig import (
    CLIENT_NAME,
    MOD_NAME,
    SAVE_CLIENT_CONFIG_NAME,
    SAVE_LIST_RESPONSE,
    SAVE_LOAD_RESPONSE,
    SAVE_WRITE_RESPONSE,
)
from StingerEngine.include.saveData import SAVE_MANUAL_SLOT_IDS
from StingerEngine.include.saveSlotPanel import SaveSlotGridPanel

ScreenNode = clientApi.GetScreenNodeCls()

EngineClient = clientApi.GetSystem(MOD_NAME, CLIENT_NAME)
SYSTEM_MENU_SOURCE = "system_menu"


class SystemMenuUI(ScreenNode):
    def __init__(self, namespace, name, param):
        ScreenNode.__init__(self, namespace, name, param)
        self.param = param or {}
        self.runtime = None
        self.context = self.param.get("context", "game")
        self.is_title_context = False
        self.active_tab = self.param.get("initialTab", "save")
        self.current_page = 0
        self.slots = {}
        self.slot_grid = None
        self.history_controls = []
        self.setting_controls = []
        self._title_settings = {}
        self._pending_confirm_callback = None
        self._anim_counter = 0
        self._timers = []

        self.root_panel = None
        self.shell_panel = None
        self.nav_panel = None
        self.content_panel = None
        self.content_title = None
        self.slot_grid_panel = None
        self.history_stack_panel = None
        self.settings_stack_panel = None
        self.empty_label = None
        self.page_panel = None
        self.page_label = None
        self.confirm_panel = None
        self.confirm_message = None

    def Create(self):
        try:
            self.runtime = EngineClient.GetGameUIRuntime()
            self.is_title_context = self.context == "title" or self.runtime is None
            if self.is_title_context:
                self.active_tab = "settings"
                self._load_title_settings()
            self._init_controls()
            self._bind_buttons()
            self._apply_context_controls()
            self.slot_grid = SaveSlotGridPanel(
                self,
                self.slot_grid_panel,
                "SystemMenuUI.slot_card_panel",
                self.OnSlotSelected,
                SAVE_MANUAL_SLOT_IDS,
                6,
            )
            if not self.is_title_context:
                EngineClient.RegisterSaveResponseListener(self)
            self.SetActiveTab(self.active_tab)
            self._play_open_animation()
        except Exception:
            logger.error("SystemMenuUI Create出错:\n{}".format(traceback.format_exc()))
            NotifyMsg("系统菜单打开失败")
            self.SetRemove()

    def _init_controls(self):
        self.root_panel = self.GetBaseUIControl("/root_panel")
        self.shell_panel = self.GetBaseUIControl("/root_panel/shell_panel")
        self.nav_panel = self.GetBaseUIControl("/root_panel/shell_panel/nav_panel")
        self.content_panel = self.GetBaseUIControl("/root_panel/shell_panel/content_panel")
        self.content_title = self.GetBaseUIControl("/root_panel/shell_panel/content_panel/content_title").asLabel()
        self.slot_grid_panel = self.GetBaseUIControl("/root_panel/shell_panel/content_panel/slot_grid_panel")
        self.history_stack_panel = self.GetBaseUIControl("/root_panel/shell_panel/content_panel/history_stack_panel")
        self.settings_stack_panel = self.GetBaseUIControl("/root_panel/shell_panel/content_panel/settings_stack_panel")
        self.empty_label = self.GetBaseUIControl("/root_panel/shell_panel/content_panel/empty_label").asLabel()
        self.page_panel = self.GetBaseUIControl("/root_panel/shell_panel/content_panel/page_panel")
        self.page_label = self.GetBaseUIControl("/root_panel/shell_panel/content_panel/page_panel/page_label").asLabel()
        self.confirm_panel = self.GetBaseUIControl("/root_panel/confirm_panel")
        self.confirm_message = self.GetBaseUIControl("/root_panel/confirm_panel/confirm_message").asLabel()
        self.confirm_panel.SetVisible(False)

    def _bind_buttons(self):
        self._bind_button("/root_panel/modal_blocker", self.OnModalBlocker)
        self._bind_button("/root_panel/shell_panel/nav_panel/nav_tab_stack/nav_history_button", self.OnHistoryTab)
        self._bind_button("/root_panel/shell_panel/nav_panel/nav_tab_stack/nav_load_button", self.OnLoadTab)
        self._bind_button("/root_panel/shell_panel/nav_panel/nav_tab_stack/nav_save_button", self.OnSaveTab)
        self._bind_button("/root_panel/shell_panel/nav_panel/nav_tab_stack/nav_settings_button", self.OnSettingsTab)
        self._bind_button("/root_panel/shell_panel/nav_panel/nav_action_stack/new_game_button", self.OnNewGame)
        self._bind_button("/root_panel/shell_panel/nav_panel/nav_action_stack/title_button", self.OnReturnTitle)
        self._bind_button("/root_panel/shell_panel/nav_panel/nav_action_stack/return_game_button", self.OnReturnGame)
        self._bind_button("/root_panel/shell_panel/content_panel/page_panel/prev_page_button", self.OnPrevPage)
        self._bind_button("/root_panel/shell_panel/content_panel/page_panel/next_page_button", self.OnNextPage)
        self._bind_button("/root_panel/confirm_panel/confirm_ok_button", self.OnConfirmOk)
        self._bind_button("/root_panel/confirm_panel/confirm_cancel_button", self.OnConfirmCancel)

    def _bind_button(self, path, callback):
        button = self.GetBaseUIControl(path).asButton()
        button.AddTouchEventParams({"isSwallow": True})
        button.SetButtonTouchUpCallback(callback)
        return button

    def _apply_context_controls(self):
        if not self.is_title_context:
            return
        hidden_paths = (
            "/root_panel/shell_panel/nav_panel/nav_tab_stack/nav_history_button",
            "/root_panel/shell_panel/nav_panel/nav_tab_stack/nav_load_button",
            "/root_panel/shell_panel/nav_panel/nav_tab_stack/nav_save_button",
            "/root_panel/shell_panel/nav_panel/nav_action_stack/new_game_button",
            "/root_panel/shell_panel/nav_panel/nav_action_stack/title_button",
        )
        for path in hidden_paths:
            self._set_control_visible(path, False)
        self._set_button_label(
            "/root_panel/shell_panel/nav_panel/nav_action_stack/return_game_button",
            "关闭设置",
        )

    def OnHistoryTab(self, args):
        self.SetActiveTab("history")

    def OnLoadTab(self, args):
        self.SetActiveTab("load")

    def OnSaveTab(self, args):
        self.SetActiveTab("save")

    def OnSettingsTab(self, args):
        self.SetActiveTab("settings")

    def OnModalBlocker(self, args):
        return

    def SetActiveTab(self, tab):
        if self.is_title_context and tab != "settings":
            tab = "settings"
        if tab not in ("history", "load", "save", "settings"):
            tab = "save"
        self._cancel_all_timers()
        self.active_tab = tab
        self._clear_history_items()
        self._clear_setting_items()
        self._hide_content_sections()

        if tab == "history":
            if not self.runtime:
                self.SetActiveTab("settings")
                return
            self.content_title.SetText("历史")
            self.history_stack_panel.SetVisible(True)
            self.RenderHistory()
        elif tab == "settings":
            self.content_title.SetText("设置")
            self.settings_stack_panel.SetVisible(True)
            self.RenderSettings()
        elif tab == "load":
            if not self.runtime:
                self.SetActiveTab("settings")
                return
            self.content_title.SetText("读取游戏")
            self.slot_grid_panel.SetVisible(True)
            self.page_panel.SetVisible(True)
            self.slot_grid.set_mode("load")
            EngineClient.RequestSaveList(SYSTEM_MENU_SOURCE)
        else:
            if not self.runtime:
                self.SetActiveTab("settings")
                return
            self.content_title.SetText("保存游戏")
            self.slot_grid_panel.SetVisible(True)
            self.page_panel.SetVisible(True)
            self.slot_grid.set_mode("save")
            EngineClient.RequestSaveList(SYSTEM_MENU_SOURCE)

        self._play_alpha(self.content_panel, 0.0, 1.0, 0.12)

    def _hide_content_sections(self):
        self.slot_grid_panel.SetVisible(False)
        self.history_stack_panel.SetVisible(False)
        self.settings_stack_panel.SetVisible(False)
        self.page_panel.SetVisible(False)
        self.empty_label.SetVisible(False)
        if self.slot_grid:
            self.slot_grid.clear()

    def OnPrevPage(self, args):
        if not self.slot_grid:
            return
        self._cancel_all_timers()
        self.current_page -= 1
        self.slot_grid.set_page(self.current_page)
        self.current_page = self.slot_grid.page_index
        self.slot_grid.render(self.slots, self.current_page, True)
        self._update_page_label()

    def OnNextPage(self, args):
        if not self.slot_grid:
            return
        self._cancel_all_timers()
        self.current_page += 1
        self.slot_grid.set_page(self.current_page)
        self.current_page = self.slot_grid.page_index
        self.slot_grid.render(self.slots, self.current_page, True)
        self._update_page_label()

    def OnSlotSelected(self, slot_id, slot_meta):
        if self.active_tab == "save":
            if not self.runtime:
                NotifyMsg("当前没有可保存的游戏")
                return
            if not self.runtime.CanSaveNow():
                NotifyMsg("当前演出中，稍后可存档")
                return
            if slot_meta.get("exists"):
                self._show_confirm("覆盖这个槽位？", lambda: self._write_slot(slot_id))
            else:
                self._write_slot(slot_id)
            return

        if not slot_meta.get("exists"):
            NotifyMsg("该槽位暂无存档")
            return
        EngineClient.RequestSaveLoad(slot_id, SYSTEM_MENU_SOURCE)

    def _write_slot(self, slot_id):
        try:
            snapshot = self.runtime.BuildSaveSnapshot(slot_id)
        except Exception as exc:
            NotifyMsg("无法存档: " + str(exc))
            return
        EngineClient.RequestSaveWrite(slot_id, snapshot, None, SYSTEM_MENU_SOURCE)

    def OnSaveResponse(self, event_name, data):
        if data.get("source") != SYSTEM_MENU_SOURCE:
            return
        if event_name == SAVE_LIST_RESPONSE:
            self._handle_list_response(data)
        elif event_name == SAVE_WRITE_RESPONSE:
            self._handle_write_response(data)
        elif event_name == SAVE_LOAD_RESPONSE:
            self._handle_load_response(data)

    def _handle_list_response(self, data):
        if not data.get("ok", False):
            NotifyMsg(data.get("message", "读取槽位列表失败"))
            return
        self.slots = data.get("slots", {}) if isinstance(data.get("slots"), dict) else {}
        if self.slot_grid:
            self.slot_grid.set_page(self.current_page)
            self.current_page = self.slot_grid.page_index
            self.slot_grid.render(self.slots, self.current_page, True)
        self._update_page_label()

    def _handle_write_response(self, data):
        if not data.get("ok", False):
            NotifyMsg(data.get("message", "存档失败"))
            return
        NotifyMsg("存档成功")
        EngineClient.RequestSaveList(SYSTEM_MENU_SOURCE)

    def _handle_load_response(self, data):
        if not data.get("ok", False):
            NotifyMsg(data.get("message", "读取存档失败"))
            return
        snapshot = data.get("snapshot")
        if not snapshot:
            NotifyMsg("存档正文为空")
            return
        if not self.runtime:
            NotifyMsg("当前没有可恢复的游戏")
            return
        try:
            self.runtime.ApplySaveSnapshot(snapshot)
            remember = getattr(self.runtime, "_remember_recent_slot", None)
            if remember:
                remember(data.get("slot_id"))
            NotifyMsg("读档完成")
            self.SetRemove()
        except Exception as exc:
            logger.error("系统菜单读档失败:\n{}".format(traceback.format_exc()))
            NotifyMsg("读档失败: " + str(exc))

    def _update_page_label(self):
        if not self.slot_grid:
            return
        page_count = self.slot_grid.page_count()
        self.page_label.SetText("第{}页，共{}页".format(self.current_page + 1, page_count))

    def RenderHistory(self):
        items = []
        if self.runtime:
            items = self.runtime.GetHistoryItems()
        if not items:
            self.empty_label.SetText("暂无历史")
            self.empty_label.SetVisible(True)
            return

        visible_count = self._get_visible_history_count()
        recent_items = items[-visible_count:]
        for index, item in enumerate(recent_items):
            control = self.CreateChildControl(
                "SystemMenuUI.history_item_panel",
                "history_item_{}".format(index),
                self.history_stack_panel,
                True,
            )
            if not control:
                continue
            speaker = str(item.get("speaker"))
            content = str(item.get("content"))
            if not speaker:
                speaker = "旁白"
            self._set_child_label(control, "/history_speaker", speaker)
            self._set_child_label(control, "/history_content", content)
            self.history_controls.append(control)
            self.AnimateListItem(control, index)

    def RenderSettings(self):
        definitions = self._get_setting_definitions()
        if not definitions:
            self.empty_label.SetText("暂无可设置项目")
            self.empty_label.SetVisible(True)
            return
        for index, definition in enumerate(definitions):
            control = self.CreateChildControl(
                "SystemMenuUI.settings_option_panel",
                "settings_option_{}".format(index),
                self.settings_stack_panel,
                True,
            )
            if not control:
                continue
            key = definition.get("key")
            self._set_child_label(control, "/option_label", str(definition.get("label")))
            self._set_child_label(control, "/option_value", self._get_setting_display_text(definition))
            button = control.GetChildByPath("/option_button").asButton()
            button.AddTouchEventParams({"isSwallow": True})

            def on_click(args, current_definition=definition):
                self._advance_setting(current_definition)

            button.SetButtonTouchUpCallback(on_click)
            self.setting_controls.append(control)
            self.AnimateListItem(control, index)

    def _get_setting_definitions(self):
        if self.runtime:
            return self.runtime.GetSettingDefinitions()
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

    def _get_setting_display_text(self, definition):
        key = definition.get("key")
        value = self._get_setting_value(key)
        if definition.get("type") == "toggle":
            return "开启" if value else "关闭"
        choices = definition.get("choices", [])
        for choice in choices:
            if self._is_same_value(choice.get("value"), value):
                return str(choice.get("label"))
        return str(value)

    def _advance_setting(self, definition):
        key = definition.get("key")
        if definition.get("type") == "toggle":
            self._set_setting_value(key, not bool(self._get_setting_value(key)))
        else:
            choices = definition.get("choices", [])
            if not choices:
                return
            value = self._get_setting_value(key)
            current_index = 0
            for index, choice in enumerate(choices):
                if self._is_same_value(choice.get("value"), value):
                    current_index = index
                    break
            next_choice = choices[(current_index + 1) % len(choices)]
            self._set_setting_value(key, next_choice.get("value"))
        self.RenderSettingsRefresh()

    def _load_title_settings(self):
        self._title_settings = GetLocalConfigData(SAVE_CLIENT_CONFIG_NAME, {})
        if not isinstance(self._title_settings, dict):
            self._title_settings = {}
        self._title_settings.setdefault("typewriter_speed", 0.03)
        self._title_settings.setdefault("auto_save_enabled", True)

    def _save_title_settings(self):
        SetLocalConfigData(SAVE_CLIENT_CONFIG_NAME, self._title_settings)

    def _get_setting_value(self, key):
        if self.runtime:
            return self.runtime.GetSettingValue(key)
        return self._title_settings.get(key)

    def _set_setting_value(self, key, value):
        if self.runtime:
            self.runtime.SetSettingValue(key, value)
            return
        if key == "typewriter_speed":
            try:
                value = float(value)
            except Exception:
                value = 0.03
        elif key == "auto_save_enabled":
            value = bool(value)
        self._title_settings[key] = value
        self._save_title_settings()

    def RenderSettingsRefresh(self):
        self._cancel_all_timers()
        self._clear_setting_items()
        self.RenderSettings()

    def OnNewGame(self, args):
        self._show_confirm("开启新游戏？当前进度可先保存。", self._start_new_game)

    def _start_new_game(self):
        runtime = self.runtime
        self.SetRemove()
        if runtime:
            runtime.SetRemove()
        EngineClient.CreateGameUI("main")

    def OnReturnTitle(self, args):
        if self.is_title_context:
            self.SetRemove()
            return
        self._show_confirm("返回主菜单？", self._return_title)

    def _return_title(self):
        runtime = self.runtime
        self.SetRemove()
        if runtime:
            runtime.SetRemove()
        EngineClient.CreateMainInterfaceUI()

    def OnReturnGame(self, args):
        self.SetRemove()

    def _show_confirm(self, message, callback):
        self._pending_confirm_callback = callback
        self.confirm_message.SetText(message)
        self.confirm_panel.SetVisible(True)
        self._play_alpha(self.confirm_panel, 0.0, 1.0, 0.10)

    def _hide_confirm(self):
        self._pending_confirm_callback = None
        self.confirm_panel.SetVisible(False)

    def OnConfirmOk(self, args):
        callback = self._pending_confirm_callback
        self._hide_confirm()
        if callback:
            callback()

    def OnConfirmCancel(self, args):
        self._hide_confirm()

    def AnimateGridItem(self, control, order, x_value, y_value):
        delay = order * 0.035

        def _start():
            control.SetVisible(True)
            self._play_alpha(control, 0.0, 1.0, 0.16)
            self._animate_position(control, max(0.0, x_value - 12.0), y_value, x_value, y_value, 0.18)

        control.SetVisible(False)
        self._add_delay(delay, _start)

    def AnimateListItem(self, control, order):
        delay = order * 0.025

        def _start():
            control.SetVisible(True)
            self._play_alpha(control, 0.0, 1.0, 0.14)

        control.SetVisible(False)
        self._add_delay(delay, _start)

    def _play_open_animation(self):
        if self.shell_panel:
            self._play_alpha(self.shell_panel, 0.0, 1.0, 0.16)

    def _get_visible_history_count(self):
        height = 200.0
        try:
            size = self.history_stack_panel.GetSize()
            if size and len(size) >= 2:
                height = float(size[1])
        except Exception:
            pass
        count = int(height / 48.0)
        if count < 1:
            count = 1
        if count > 9:
            count = 9
        return count

    def _play_alpha(self, control, from_alpha, to_alpha, duration):
        if not control:
            return
        self._anim_counter += 1
        anim_name = "menu_alpha_{}".format(self._anim_counter)
        anim_data = {
            "namespace": "SystemMenuUI",
            anim_name: {
                "anim_type": "alpha",
                "duration": duration,
                "from": from_alpha,
                "to": to_alpha,
                "next": "",
            },
        }
        clientApi.RegisterUIAnimations(anim_data, override=True)
        try:
            control.RemoveAnimation("alpha")
        except Exception:
            pass
        control.SetAnimation("alpha", "SystemMenuUI", anim_name, True)

    def _animate_position(self, control, start_x, start_y, end_x, end_y, duration):
        if not control:
            return
        interval = 0.02
        steps_total = max(1, int(duration / interval))
        state = {"step": 0, "timer": None}

        def _tick():
            state["step"] += 1
            t = min(1.0, float(state["step"]) / steps_total)
            t = t * t * (3.0 - 2.0 * t)
            x_value = start_x + (end_x - start_x) * t
            y_value = start_y + (end_y - start_y) * t
            self._set_local_position(control, x_value, y_value)
            if state["step"] >= steps_total:
                self._cancel_timer(state["timer"])
                state["timer"] = None

        self._set_local_position(control, start_x, start_y)
        state["timer"] = compGame.AddRepeatedTimer(interval, _tick)
        self._timers.append(state["timer"])

    def _add_delay(self, delay, callback):
        if delay <= 0:
            callback()
            return
        state = {"timer": None}

        def _run():
            timer = state.get("timer")
            if timer in self._timers:
                self._timers.remove(timer)
            callback()

        timer = compGame.AddTimer(delay, _run)
        state["timer"] = timer
        self._timers.append(timer)

    def _cancel_timer(self, timer):
        if not timer:
            return
        try:
            compGame.CancelTimer(timer)
        except Exception:
            pass
        if timer in self._timers:
            self._timers.remove(timer)

    def _cancel_all_timers(self):
        for timer in list(self._timers):
            self._cancel_timer(timer)

    def _clear_history_items(self):
        for control in self.history_controls:
            try:
                self.RemoveChildControl(control)
            except Exception:
                pass
        self.history_controls = []

    def _clear_setting_items(self):
        for control in self.setting_controls:
            try:
                self.RemoveChildControl(control)
            except Exception:
                pass
        self.setting_controls = []

    def _set_child_label(self, control, path, text):
        try:
            label = control.GetChildByPath(path).asLabel()
            if label:
                label.SetText(text)
        except Exception:
            pass

    def _set_control_visible(self, path, visible):
        try:
            self.GetBaseUIControl(path).SetVisible(bool(visible))
        except Exception:
            pass

    def _set_button_label(self, path, text):
        try:
            label = self.GetBaseUIControl(path + "/button_label").asLabel()
            if label:
                label.SetText(text)
        except Exception:
            pass

    @staticmethod
    def _set_local_position(control, x_value, y_value):
        try:
            control.SetPosition((x_value, y_value))
        except Exception:
            pass

    @staticmethod
    def _is_same_value(left, right):
        try:
            return abs(float(left) - float(right)) < 0.0001
        except Exception:
            return left == right

    def Destroy(self):
        try:
            EngineClient.UnregisterSaveResponseListener(self)
            if self.slot_grid:
                self.slot_grid.destroy()
            self._clear_history_items()
            self._clear_setting_items()
            for timer in list(self._timers):
                self._cancel_timer(timer)
        except Exception:
            pass

    def OnActive(self):
        pass

    def OnDeactive(self):
        pass