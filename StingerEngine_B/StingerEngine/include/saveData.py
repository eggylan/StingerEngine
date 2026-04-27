# -*- coding: utf-8 -*-
from mod_log import logger
import json

from StingerEngine.include.modconfig import (
    SAVE_KEY_PREFIX,
    SAVE_MANUAL_SLOT_COUNT,
    SAVE_SCHEMA_VERSION,
    SAVE_SLOT_AUTO_ID,
    SAVE_SLOT_QUICK_ID,
)

try:
    integer_types = (int, long)
except NameError:
    integer_types = (int,)


def _BuildManualSlotIds():
    return tuple(["slot_{}".format(index) for index in range(1, SAVE_MANUAL_SLOT_COUNT + 1)])


SAVE_MANUAL_SLOT_IDS = _BuildManualSlotIds()
SAVE_SPECIAL_SLOT_IDS = (SAVE_SLOT_AUTO_ID, SAVE_SLOT_QUICK_ID)
SAVE_ALL_SLOT_IDS = SAVE_MANUAL_SLOT_IDS + SAVE_SPECIAL_SLOT_IDS

SAVE_VALIDATE_OK = "ok"
SAVE_ERROR_NOT_DICT = "snapshot_not_dict"
SAVE_ERROR_BAD_SCHEMA = "bad_schema_version"
SAVE_ERROR_BAD_SLOT = "bad_slot_id"
SAVE_ERROR_BAD_ENTRY = "bad_entry"
SAVE_ERROR_BAD_INDEX = "bad_current_index"
SAVE_ERROR_BAD_PAUSE_MODE = "bad_pause_mode"
SAVE_ERROR_BAD_DIALOG = "bad_dialog"
SAVE_ERROR_BAD_VISUAL = "bad_visual"
SAVE_ERROR_BAD_CHARACTERS = "bad_characters"
SAVE_ERROR_BAD_MENU = "bad_pending_menu"
SAVE_ERROR_BAD_INLINE_QUEUE = "bad_inline_queue"
SAVE_ERROR_BAD_HISTORY = "bad_history"
SAVE_ERROR_EMPTY_SCRIPT = "script_empty"
SAVE_ERROR_INDEX_OUT_OF_RANGE = "current_index_out_of_range"
SAVE_ERROR_LABEL_NOT_FOUND = "label_not_found"
SAVE_ERROR_MENU_LABEL_NOT_FOUND = "menu_label_not_found"

SAVEABLE_PAUSE_MODES = ("tap", "menu", "ended")
RESTORABLE_PAUSE_MODES = SAVEABLE_PAUSE_MODES


def NormalizeSaveSlotId(slot_id):
    if slot_id is None:
        return None
    if not isinstance(slot_id, basestring):
        return None
    slot_id = slot_id.strip()
    if slot_id in SAVE_ALL_SLOT_IDS:
        return slot_id
    return None


def IsValidSaveSlotId(slot_id):
    return NormalizeSaveSlotId(slot_id) is not None


def GetSaveMetaKey():
    return "{}_meta_v{}".format(SAVE_KEY_PREFIX, SAVE_SCHEMA_VERSION)


def GetSaveSlotKey(slot_id):
    slot_id = NormalizeSaveSlotId(slot_id)
    if not slot_id:
        raise ValueError("无效的存档槽位: {}".format(slot_id))
    return "{}_{}_v{}".format(SAVE_KEY_PREFIX, slot_id, SAVE_SCHEMA_VERSION)


def CreateDefaultDialogState():
    return {
        "speaker": "",
        "content": "",
        "dialog_visible": False,
        "speaker_visible": False,
    }


def CreateDefaultVisualState():
    return {
        "background": None,
        "music": None,
        "cg_front": "0",
        "cg": {"0": None, "1": None},
        "fade_visible": False,
    }


def CloneSerializableData(value, default_value):
    try:
        return json.loads(json.dumps(value))
    except Exception:
        return default_value


def ValidateSaveSnapshot(snapshot):
    logger.debug("Validating save snapshot: {}".format(snapshot))
    if not isinstance(snapshot, dict):
        return False, SAVE_ERROR_NOT_DICT

    if snapshot.get("schema_version") != SAVE_SCHEMA_VERSION:
        return False, SAVE_ERROR_BAD_SCHEMA

    slot_id = snapshot.get("slot_id")
    if slot_id is not None and not IsValidSaveSlotId(slot_id):
        return False, SAVE_ERROR_BAD_SLOT

    entry = snapshot.get("entry")
    if not isinstance(entry,basestring) or not entry:
        return False, SAVE_ERROR_BAD_ENTRY

    current_index = snapshot.get("current_index")
    if not isinstance(current_index, integer_types) or current_index < 0:
        return False, SAVE_ERROR_BAD_INDEX

    pause_mode = snapshot.get("pause_mode")
    if pause_mode not in RESTORABLE_PAUSE_MODES:
        return False, SAVE_ERROR_BAD_PAUSE_MODE

    dialog = snapshot.get("dialog")
    if not _is_valid_dialog(dialog):
        return False, SAVE_ERROR_BAD_DIALOG

    visual = snapshot.get("visual")
    if not _is_valid_visual(visual):
        return False, SAVE_ERROR_BAD_VISUAL

    characters = snapshot.get("characters")
    if not _is_valid_characters(characters):
        return False, SAVE_ERROR_BAD_CHARACTERS

    pending_menu = snapshot.get("pending_menu")
    if pause_mode == "menu" and not _is_valid_pending_menu(pending_menu):
        return False, SAVE_ERROR_BAD_MENU

    inline_queue = snapshot.get("inline_queue")
    if inline_queue is not None and not isinstance(inline_queue, list):
        return False, SAVE_ERROR_BAD_INLINE_QUEUE

    history = snapshot.get("history")
    if history is not None and not isinstance(history, list):
        return False, SAVE_ERROR_BAD_HISTORY

    return True, SAVE_VALIDATE_OK


def ValidateSnapshotAgainstScript(snapshot, script_data, label_index):
    if not isinstance(script_data, list) or not script_data:
        return False, SAVE_ERROR_EMPTY_SCRIPT

    current_index = snapshot.get("current_index")
    if not isinstance(current_index, integer_types) or current_index < 0 or current_index > len(script_data):
        return False, SAVE_ERROR_INDEX_OUT_OF_RANGE

    current_label = snapshot.get("current_label")
    if current_label and current_label not in label_index:
        return False, SAVE_ERROR_LABEL_NOT_FOUND

    pending_menu = snapshot.get("pending_menu")
    if isinstance(pending_menu, dict):
        for choice in pending_menu.get("choices", []):
            if not isinstance(choice, dict):
                continue
            target = choice.get("label")
            if target and target not in label_index:
                return False, SAVE_ERROR_MENU_LABEL_NOT_FOUND

    return True, SAVE_VALIDATE_OK


def _is_valid_dialog(dialog):
    if not isinstance(dialog, dict):
        return False
    return (
        isinstance(dialog.get("speaker", ""), basestring)
        and isinstance(dialog.get("content", ""), basestring)
        and isinstance(dialog.get("dialog_visible", False), bool)
        and isinstance(dialog.get("speaker_visible", False), bool)
    )


def _is_valid_visual(visual):
    if not isinstance(visual, dict):
        return False
    cg = visual.get("cg")
    if not isinstance(cg, dict):
        return False
    if visual.get("cg_front", "0") not in ("0", "1"):
        return False
    return True


def _is_valid_characters(characters):
    if not isinstance(characters, list):
        return False
    for item in characters:
        if not isinstance(item, dict):
            return False
        char_id = item.get("id")
        if not isinstance(char_id, basestring) or not char_id:
            return False
    return True


def _is_valid_pending_menu(pending_menu):
    if not isinstance(pending_menu, dict):
        return False
    choices = pending_menu.get("choices")
    if not isinstance(choices, list) or not choices:
        return False
    return True