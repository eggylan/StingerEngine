# -*- coding: utf-8 -*-
import traceback
from ..include.QuModLibs.Client import *
from ..include.QuModLibs.UI import ScreenNodeWrapper
from ..include.clientTools import NotifyMsg, compGame as _compGame, logger
from ..include.modconfig import (
    SAVE_LIST_RESPONSE,
    SAVE_LOAD_RESPONSE,
)
from ..include.saveData import SAVE_MANUAL_SLOT_IDS
from ..include.saveSlotPanel import SaveSlotGridPanel
from ..EngineClient import get_engine_client

MAIN_INTERFACE_SOURCE = "main_interface"


@ScreenNodeWrapper.autoRegister("MainInterfaceUI.MainInterfaceUI")
class MainInterfaceUI(ScreenNodeWrapper):
    def __init__(self, namespace, name, param):
        ScreenNodeWrapper.__init__(self, namespace, name, param)
        self.param = param or {}
        self.slots = {}
        self.current_page = 0
        self.slot_grid = None
        self._anim_counter = 0
        self._timers = []

        self.root_panel = None
        self.hero_panel = None
        self.menu_panel = None
        self.footer_panel = None
        self.sky_glow = None
        self.vignette = None
        self.load_modal_layer = None
        self.load_panel = None
        self.load_grid_panel = None
        self.load_page_panel = None
        self.load_page_label = None
        self.load_status_label = None

    def Create(self):
        ScreenNodeWrapper.Create(self)
        try:
            self._init_controls()
            self._bind_buttons()
            self.slot_grid = SaveSlotGridPanel(
                self,
                self.load_grid_panel,
                "MainInterfaceUI.slot_card_panel",
                self.OnLoadSlotSelected,
                SAVE_MANUAL_SLOT_IDS,
                6,
            )
            self.slot_grid.set_mode("load")
            engine_client = get_engine_client()
            if engine_client:
                engine_client.RegisterSaveResponseListener(self)
            self._hide_load_modal()
            self._register_loop_animations()
            self._play_intro_animation()
        except Exception:
            errinfo = traceback.format_exc()
            errorPrint("[MainInterfaceUI] Create error:\n{}".format(errinfo))
            try:
                self.SetRemove()
            except Exception:
                pass
            engine_client = get_engine_client()
            if engine_client:
                engine_client.CreateErrorUI(errinfo)

    def _init_controls(self):
        self.root_panel = self.GetBaseUIControl("/root_panel")
        self.hero_panel = self.GetBaseUIControl("/root_panel/hero_panel")
        self.menu_panel = self.GetBaseUIControl("/root_panel/menu_panel")
        self.footer_panel = self.GetBaseUIControl("/root_panel/footer_panel")
        self.sky_glow = self.GetBaseUIControl("/root_panel/sky_glow")
        self.vignette = self.GetBaseUIControl("/root_panel/vignette_overlay")
        self.load_modal_layer = self.GetBaseUIControl("/root_panel/load_modal_layer")
        self.load_panel = self.GetBaseUIControl("/root_panel/load_modal_layer/load_panel")
        self.load_grid_panel = self.GetBaseUIControl("/root_panel/load_modal_layer/load_panel/slot_grid_panel")
        self.load_page_panel = self.GetBaseUIControl("/root_panel/load_modal_layer/load_panel/page_panel")
        self.load_page_label = self.GetBaseUIControl("/root_panel/load_modal_layer/load_panel/page_panel/page_label").asLabel()
        self.load_status_label = self.GetBaseUIControl("/root_panel/load_modal_layer/load_panel/load_status_label").asLabel()

    def _bind_buttons(self):
        self._bind_button("/root_panel/menu_panel/button_stack/start_new_game", self.OnStartNewGame)
        self._bind_button("/root_panel/menu_panel/button_stack/load_game", self.OnOpenLoadPanel)
        self._bind_button("/root_panel/menu_panel/button_stack/settings_button", self.OnSettings)
        self._bind_button("/root_panel/menu_panel/button_stack/exit_game", self.OnExit)
        self._bind_button("/root_panel/load_modal_layer/modal_blocker", self.OnCloseLoadPanel)
        self._bind_button("/root_panel/load_modal_layer/load_panel/close_load_button", self.OnCloseLoadPanel)
        self._bind_button("/root_panel/load_modal_layer/load_panel/page_panel/prev_page_button", self.OnPrevPage)
        self._bind_button("/root_panel/load_modal_layer/load_panel/page_panel/next_page_button", self.OnNextPage)

    def _bind_button(self, path, callback):
        button = self.GetBaseUIControl(path).asButton()
        button.AddTouchEventParams({"isSwallow": True})
        button.SetButtonTouchUpCallback(callback)
        return button

    def _engine_client(self):
        return get_engine_client()

    def OnStartNewGame(self, args):
        self.SetRemove()
        ec = self._engine_client()
        if ec:
            ec.CreateGameUI("main")

    def OnOpenLoadPanel(self, args):
        self.current_page = 0
        self.load_modal_layer.SetVisible(True)
        self.load_grid_panel.SetVisible(False)
        self.load_page_panel.SetVisible(False)
        self.load_status_label.SetText("正在读取存档槽位...")
        self._play_alpha(self.load_modal_layer, 0.0, 1.0, 0.12)
        ec = self._engine_client()
        if ec:
            ec.RequestSaveList(MAIN_INTERFACE_SOURCE)

    def OnCloseLoadPanel(self, args):
        self._hide_load_modal()

    def OnSettings(self, args):
        ec = self._engine_client()
        if ec:
            ec.CreateSystemMenuUI("settings", "title")

    def OnExit(self, args):
        self.SetRemove()
        ec = self._engine_client()
        if ec:
            ec.ForceDisconnect()

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

    def OnLoadSlotSelected(self, slot_id, slot_meta):
        if not slot_meta.get("exists"):
            NotifyMsg("该槽位暂无存档")
            return
        self.load_status_label.SetText("正在读取 {}...".format(str(slot_meta.get("title") or slot_id)))
        ec = self._engine_client()
        if ec:
            ec.RequestSaveLoad(slot_id, MAIN_INTERFACE_SOURCE)

    def OnSaveResponse(self, event_name, data):
        if data.get("source") != MAIN_INTERFACE_SOURCE:
            return
        if event_name == SAVE_LIST_RESPONSE:
            self._handle_list_response(data)
        elif event_name == SAVE_LOAD_RESPONSE:
            self._handle_load_response(data)

    def _handle_list_response(self, data):
        if not data.get("ok", False):
            message = str(data.get("message") or "读取槽位列表失败")
            self.load_status_label.SetText(message)
            NotifyMsg(message)
            return
        self.slots = data.get("slots", {}) if isinstance(data.get("slots"), dict) else {}
        self.load_grid_panel.SetVisible(True)
        self.load_page_panel.SetVisible(True)
        self.load_status_label.SetText("选择要读取的存档。")
        if self.slot_grid:
            self.slot_grid.set_page(self.current_page)
            self.current_page = self.slot_grid.page_index
            self.slot_grid.render(self.slots, self.current_page, True)
        self._update_page_label()

    def _handle_load_response(self, data):
        if not data.get("ok", False):
            message = str(data.get("message") or "读取存档失败")
            self.load_status_label.SetText(message)
            NotifyMsg(message)
            return
        snapshot = data.get("snapshot")
        if not snapshot:
            NotifyMsg("存档正文为空")
            self.load_status_label.SetText("存档正文为空。")
            return
        slot_id = data.get("slot_id")
        self.SetRemove()
        ec = self._engine_client()
        if ec:
            ec.CreateGameUI(snapshot.get("entry"), "resume", slot_id, snapshot)

    def _hide_load_modal(self):
        self._cancel_all_timers()
        if self.slot_grid:
            self.slot_grid.clear()
        if self.load_modal_layer:
            self.load_modal_layer.SetVisible(False)

    def _update_page_label(self):
        if not self.slot_grid or not self.load_page_label:
            return
        page_count = self.slot_grid.page_count()
        self.load_page_label.SetText("第{}页 / 共{}页".format(self.current_page + 1, page_count))

    def AnimateGridItem(self, control, order, x_value, y_value):
        delay = order * 0.03

        def _start():
            control.SetVisible(True)
            self._play_alpha(control, 0.0, 1.0, 0.14)

        control.SetVisible(False)
        self._add_delay(delay, _start)

    def _play_intro_animation(self):
        self._play_alpha(self.hero_panel, 0.0, 1.0, 0.36)
        self._play_alpha(self.menu_panel, 0.0, 1.0, 0.28)
        self._play_alpha(self.footer_panel, 0.0, 1.0, 0.32)
        button_paths = (
            "/root_panel/menu_panel/button_stack/start_new_game",
            "/root_panel/menu_panel/button_stack/load_game",
            "/root_panel/menu_panel/button_stack/settings_button",
            "/root_panel/menu_panel/button_stack/exit_game",
        )
        for index, path in enumerate(button_paths):
            try:
                control = self.GetBaseUIControl(path)
            except Exception:
                continue

            def _start_button(current_control=control):
                current_control.SetVisible(True)
                self._play_alpha(current_control, 0.0, 1.0, 0.16)

            control.SetVisible(False)
            self._add_delay(0.10 + index * 0.05, _start_button)

    def _register_loop_animations(self):
        anim_data = {
            "namespace": "MainInterfaceUI",
            "sky_glow_pulse": {
                "anim_type": "alpha",
                "duration": 3.2,
                "from": 0.18,
                "to": 0.42,
                "next": "@MainInterfaceUI.sky_glow_pulse_back",
            },
            "sky_glow_pulse_back": {
                "anim_type": "alpha",
                "duration": 3.2,
                "from": 0.42,
                "to": 0.18,
                "next": "@MainInterfaceUI.sky_glow_pulse",
            },
            "vignette_breathe": {
                "anim_type": "alpha",
                "duration": 4.0,
                "from": 0.34,
                "to": 0.48,
                "next": "@MainInterfaceUI.vignette_breathe_back",
            },
            "vignette_breathe_back": {
                "anim_type": "alpha",
                "duration": 4.0,
                "from": 0.48,
                "to": 0.34,
                "next": "@MainInterfaceUI.vignette_breathe",
            },
        }
        clientApi.RegisterUIAnimations(anim_data, override=True)
        self._set_loop_animation(self.sky_glow, "sky_glow_pulse")
        self._set_loop_animation(self.vignette, "vignette_breathe")

    def _set_loop_animation(self, control, anim_name):
        if not control:
            return
        try:
            control.RemoveAnimation("alpha")
        except Exception:
            pass
        control.SetAnimation("alpha", "MainInterfaceUI", anim_name, True)

    def _play_alpha(self, control, from_alpha, to_alpha, duration):
        if not control:
            return
        self._anim_counter += 1
        anim_name = "title_alpha_{}".format(self._anim_counter)
        anim_data = {
            "namespace": "MainInterfaceUI",
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
        control.SetAnimation("alpha", "MainInterfaceUI", anim_name, True)

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

        timer = _compGame.AddTimer(delay, _run)
        state["timer"] = timer
        self._timers.append(timer)

    def _cancel_timer(self, timer):
        if not timer:
            return
        try:
            _compGame.CancelTimer(timer)
        except Exception:
            pass
        if timer in self._timers:
            self._timers.remove(timer)

    def _cancel_all_timers(self):
        for timer in list(self._timers):
            self._cancel_timer(timer)

    def Destroy(self):
        try:
            ec = get_engine_client()
            if ec:
                ec.UnregisterSaveResponseListener(self)
            if self.slot_grid:
                self.slot_grid.destroy()
            self._cancel_all_timers()
        except Exception:
            pass
        ScreenNodeWrapper.Destroy(self) if hasattr(ScreenNodeWrapper, 'Destroy') else None

    def OnActive(self):
        pass

    def OnDeactive(self):
        pass
