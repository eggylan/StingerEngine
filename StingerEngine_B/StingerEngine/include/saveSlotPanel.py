# -*- coding: utf-8 -*-
from StingerEngine.include.saveData import (
    SAVE_ALL_SLOT_IDS,
    SAVE_MANUAL_SLOT_IDS,
    SAVE_SLOT_AUTO_ID,
    SAVE_SLOT_QUICK_ID,
)

SAVE_SLOT_DISPLAY_NAMES = {}
for _index, _slot_id in enumerate(SAVE_MANUAL_SLOT_IDS):
    SAVE_SLOT_DISPLAY_NAMES[_slot_id] = "存档 {}".format(_index + 1)
SAVE_SLOT_DISPLAY_NAMES[SAVE_SLOT_AUTO_ID] = "自动存档"
SAVE_SLOT_DISPLAY_NAMES[SAVE_SLOT_QUICK_ID] = "快速存档"


class SaveSlotPanel(object):
    def __init__(self, ui, stack_control, item_def_name, on_select=None, on_delete=None):
        self.ui = ui
        self.stack_control = stack_control
        self.item_def_name = item_def_name
        self.on_select = on_select
        self.on_delete = on_delete
        self.mode = "load"
        self.slots = {}
        self.item_controls = []

    def set_mode(self, mode):
        self.mode = mode if mode in ("save", "load") else "load"

    def render(self, slots):
        self.clear()
        self.slots = slots if isinstance(slots, dict) else {}
        total_height = 0
        for slot_id in SAVE_ALL_SLOT_IDS:
            slot_meta = self.slots.get(slot_id) or {"slot_id": slot_id, "exists": False}
            item = self._create_slot_item(slot_id, slot_meta)
            if item:
                self.item_controls.append(item)
                total_height += self._get_control_height(item)
        self._resize_stack(total_height)

    def clear(self):
        for control in self.item_controls:
            try:
                self.ui.RemoveChildControl(control)
            except Exception:
                pass
        self.item_controls = []

    def destroy(self):
        self.clear()

    def get_slot_meta(self, slot_id):
        return self.slots.get(slot_id) or {"slot_id": slot_id, "exists": False}

    def _create_slot_item(self, slot_id, slot_meta):
        item = self.ui.CreateChildControl(
            self.item_def_name,
            "save_slot_item_{}".format(slot_id),
            self.stack_control,
            True,
        )
        if not item:
            return None

        self._set_label(item, "/slot_title", self._build_title(slot_id, slot_meta))
        self._set_label(item, "/slot_detail", self._build_detail(slot_meta))

        select_button = self._get_button(item, "/select_button")
        if select_button:
            select_button.AddTouchEventParams({"isSwallow": True})
            select_label = self._get_label(item, "/select_button/button_label")
            if select_label:
                select_label.SetText(self._get_select_text(slot_meta))

            def on_select(args, current_slot_id=slot_id):
                if self.on_select:
                    self.on_select(current_slot_id, self.get_slot_meta(current_slot_id))

            select_button.SetButtonTouchUpCallback(on_select)

        delete_button = self._get_button(item, "/delete_button")
        if delete_button:
            delete_button.AddTouchEventParams({"isSwallow": True})
            delete_label = self._get_label(item, "/delete_button/button_label")
            if delete_label:
                delete_label.SetText("删除")

            def on_delete(args, current_slot_id=slot_id):
                if self.on_delete:
                    self.on_delete(current_slot_id, self.get_slot_meta(current_slot_id))

            delete_button.SetButtonTouchUpCallback(on_delete)
            delete_button.SetVisible(bool(slot_meta.get("exists")))

        return item

    def _build_title(self, slot_id, slot_meta):
        name = SAVE_SLOT_DISPLAY_NAMES.get(slot_id, str(slot_id))
        if not slot_meta.get("exists"):
            return name + " · 空槽位"
        title = str(slot_meta.get("title") or slot_meta.get("current_label") or slot_meta.get("entry") or "未命名")
        return name + " · " + title

    def _build_detail(self, slot_meta):
        if not slot_meta.get("exists"):
            return "尚未保存进度"
        status = str(slot_meta.get("status") or "ok")
        if status != "ok":
            return "状态：" + status
        progress = str(slot_meta.get("chapter_progress") or slot_meta.get("entry") or "未知进度")
        updated_at = str(slot_meta.get("updated_at") or "未知时间")
        return progress + "  " + updated_at

    def _get_select_text(self, slot_meta):
        if self.mode == "save":
            return "覆盖" if slot_meta.get("exists") else "存档"
        return "读取" if slot_meta.get("exists") else "空"

    def _resize_stack(self, total_height):
        try:
            current_size = self.stack_control.GetSize()
            if current_size and len(current_size) >= 2:
                self.stack_control.SetSize((current_size[0], total_height or current_size[1]))
        except Exception:
            pass

    def _get_button(self, item, path):
        try:
            return item.GetChildByPath(path).asButton()
        except Exception:
            return None

    def _get_label(self, item, path):
        try:
            return item.GetChildByPath(path).asLabel()
        except Exception:
            return None

    def _set_label(self, item, path, text):
        label = self._get_label(item, path)
        if label:
            label.SetText(text)

    @staticmethod
    def _get_control_height(control):
        try:
            size = control.GetSize()
            if size and len(size) >= 2:
                return int(round(float(size[1])))
        except Exception:
            pass
        return 0



class SaveSlotGridPanel(object):
    CARD_MAX_SIZE = (150.0, 86.0)
    CARD_MIN_SIZE = (86.0, 58.0)
    GRID_PADDING = (14.0, 10.0)
    GRID_GAP = (18.0, 18.0)
    GRID_COLUMN_COUNT = 3

    def __init__(self, ui, grid_control, item_def_name, on_select=None, slot_ids=None, page_size=6):
        self.ui = ui
        self.grid_control = grid_control
        self.item_def_name = item_def_name
        self.on_select = on_select
        self.slot_ids = list(slot_ids or SAVE_MANUAL_SLOT_IDS)
        self.page_size = page_size or 6
        self.page_index = 0
        self.mode = "load"
        self.slots = {}
        self.item_controls = []

    def set_mode(self, mode):
        self.mode = mode if mode in ("save", "load") else "load"

    def page_count(self):
        if not self.slot_ids:
            return 1
        return int((len(self.slot_ids) + self.page_size - 1) / self.page_size)

    def set_page(self, page_index):
        count = self.page_count()
        if page_index < 0:
            page_index = 0
        if page_index >= count:
            page_index = count - 1
        self.page_index = page_index

    def render(self, slots=None, page_index=None, animate=False):
        if slots is not None:
            self.slots = slots if isinstance(slots, dict) else {}
        if page_index is not None:
            self.set_page(page_index)
        self.clear()

        start = self.page_index * self.page_size
        page_slots = self.slot_ids[start:start + self.page_size]
        for index, slot_id in enumerate(page_slots):
            slot_meta = self.slots.get(slot_id) or {"slot_id": slot_id, "exists": False}
            item = self._create_slot_card(index, slot_id, slot_meta, animate)
            if item:
                self.item_controls.append(item)

    def clear(self):
        for control in self.item_controls:
            try:
                self.ui.RemoveChildControl(control)
            except Exception:
                pass
        self.item_controls = []

    def destroy(self):
        self.clear()

    def get_slot_meta(self, slot_id):
        return self.slots.get(slot_id) or {"slot_id": slot_id, "exists": False}

    def _create_slot_card(self, index, slot_id, slot_meta, animate):
        item = self.ui.CreateChildControl(
            self.item_def_name,
            "save_grid_slot_{}_{}".format(self.page_index, slot_id),
            self.grid_control,
            True,
        )
        if not item:
            return None

        column_count, row_count = self._get_grid_shape()
        col = index % column_count
        row = int(index / column_count)
        x_value, y_value, card_width, card_height = self._get_card_layout(col, row, column_count, row_count)
        try:
            item.SetSize((card_width, card_height), True)
        except Exception:
            pass
        self._set_local_position(item, x_value, y_value)

        self._set_label(item, "/slot_index", self._build_index_text(slot_id))
        self._set_label(item, "/slot_title", self._build_title(slot_id, slot_meta))
        self._set_label(item, "/slot_detail", self._build_detail(slot_meta))
        self._set_label(item, "/slot_action", self._get_action_text(slot_meta))

        card_button = self._get_button(item, "/card_button")
        if card_button:
            card_button.AddTouchEventParams({"isSwallow": True})

            def on_click(args, current_slot_id=slot_id):
                if self.on_select:
                    self.on_select(current_slot_id, self.get_slot_meta(current_slot_id))

            card_button.SetButtonTouchUpCallback(on_click)

        animator = getattr(self.ui, "AnimateGridItem", None)
        if animate and animator:
            animator(item, index, x_value, y_value)
        return item

    def _build_index_text(self, slot_id):
        name = SAVE_SLOT_DISPLAY_NAMES.get(slot_id, str(slot_id))
        return name

    def _build_title(self, slot_id, slot_meta):
        if not slot_meta.get("exists"):
            return "空槽位"
        return str(slot_meta.get("title") or slot_meta.get("current_label") or slot_meta.get("entry") or "未命名")

    def _build_detail(self, slot_meta):
        if not slot_meta.get("exists"):
            return "点击保存当前进度" if self.mode == "save" else "暂无可读取的进度"
        status = str(slot_meta.get("status") or "ok")
        if status != "ok":
            return "状态：" + status
        progress = str(slot_meta.get("chapter_progress") or slot_meta.get("entry") or "未知进度")
        updated_at = str(slot_meta.get("updated_at") or "未知时间")
        return progress + "\n" + updated_at

    def _get_action_text(self, slot_meta):
        if self.mode == "save":
            return "覆盖" if slot_meta.get("exists") else "保存"
        return "读取" if slot_meta.get("exists") else "空"

    def _get_grid_size(self):
        grid_width = 650.0
        grid_height = 300.0
        try:
            size = self.grid_control.GetSize()
            if size and len(size) >= 2:
                grid_width = float(size[0])
                grid_height = float(size[1])
        except Exception:
            pass
        return grid_width, grid_height

    def _get_grid_shape(self):
        column_count = self.GRID_COLUMN_COUNT
        row_count = int((self.page_size + column_count - 1) / column_count)
        if row_count < 1:
            row_count = 1
        return column_count, row_count

    def _get_card_layout(self, col, row, column_count, row_count):
        grid_width, grid_height = self._get_grid_size()

        gap_x = self.GRID_GAP[0]
        gap_y = self.GRID_GAP[1]
        total_gap_x = gap_x * max(0, column_count - 1)
        total_gap_y = gap_y * max(0, row_count - 1)
        inner_width = max(1.0, grid_width - self.GRID_PADDING[0] * 2.0 - total_gap_x)
        inner_height = max(1.0, grid_height - self.GRID_PADDING[1] * 2.0 - total_gap_y)
        cell_width = max(1.0, inner_width / column_count)
        cell_height = max(1.0, inner_height / row_count)
        card_width = min(self.CARD_MAX_SIZE[0], max(self.CARD_MIN_SIZE[0], cell_width))
        card_height = min(self.CARD_MAX_SIZE[1], max(self.CARD_MIN_SIZE[1], cell_height))
        if card_width > cell_width:
            card_width = cell_width
        if card_height > cell_height:
            card_height = cell_height
        x_value = self.GRID_PADDING[0] + col * (cell_width + gap_x) + (cell_width - card_width) * 0.5
        y_value = self.GRID_PADDING[1] + row * (cell_height + gap_y) + (cell_height - card_height) * 0.5
        return x_value, y_value, card_width, card_height

    def _get_button(self, item, path):
        try:
            return item.GetChildByPath(path).asButton()
        except Exception:
            return None

    def _get_label(self, item, path):
        try:
            return item.GetChildByPath(path).asLabel()
        except Exception:
            return None

    def _set_label(self, item, path, text):
        label = self._get_label(item, path)
        if label:
            label.SetText(text)

    @staticmethod
    def _set_local_position(control, x_value, y_value):
        try:
            control.SetPosition((x_value, y_value))
        except Exception:
            pass
