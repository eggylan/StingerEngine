# -*- coding: utf-8 -*-
import json
import time

from StingerEngine.include.modconfig import SAVE_SCHEMA_VERSION, SAVE_SLOT_AUTO_ID, SAVE_SLOT_QUICK_ID
from StingerEngine.include.saveData import (
    CloneSerializableData,
    GetSaveMetaKey,
    GetSaveSlotKey,
    NormalizeSaveSlotId,
    SAVE_ALL_SLOT_IDS,
    ValidateSaveSnapshot,
)

SAVE_ARCHIVE_OK = "ok"
SAVE_ARCHIVE_BAD_SLOT = "bad_slot_id"
SAVE_ARCHIVE_BAD_SNAPSHOT = "bad_snapshot"
SAVE_ARCHIVE_EMPTY_SLOT = "slot_empty"
SAVE_ARCHIVE_CORRUPT_SLOT = "slot_corrupt"
SAVE_ARCHIVE_INVALID_SLOT = "slot_invalid"
SAVE_ARCHIVE_BAD_META = "meta_invalid"
SAVE_ARCHIVE_WRITE_FAILED = "write_failed"
SAVE_ARCHIVE_DELETE_FAILED = "delete_failed"
SAVE_ARCHIVE_EXCEPTION = "exception"


class SaveArchiveService(object):
    def list_slots(self, player):
        meta, meta_error = self._load_meta(player)
        slots = {}
        for slot_id in SAVE_ALL_SLOT_IDS:
            slot_meta = self._get_slot_meta(meta, slot_id)
            if slot_meta:
                slot_meta = CloneSerializableData(slot_meta, {})
                slot_meta.setdefault("slot_id", slot_id)
                slot_meta.setdefault("exists", True)
                load_result = self._read_slot_snapshot(player, slot_id)
                if not load_result.get("ok"):
                    slot_meta["status"] = load_result.get("code", SAVE_ARCHIVE_INVALID_SLOT)
                else:
                    slot_meta["status"] = SAVE_ARCHIVE_OK
            else:
                slot_meta = self._empty_slot_meta(slot_id)
            slots[slot_id] = slot_meta

        response = self._response(True, meta_error or SAVE_ARCHIVE_OK, "槽位列表已读取")
        response["meta"] = meta
        response["latest_slot"] = meta.get("latest_slot")
        response["slots"] = slots
        return response

    def write_slot(self, player, slot_id, snapshot, title=None):
        slot_id = NormalizeSaveSlotId(slot_id)
        if not slot_id:
            return self._response(False, SAVE_ARCHIVE_BAD_SLOT, "无效的存档槽位")

        snapshot = CloneSerializableData(snapshot, None)
        if not isinstance(snapshot, dict):
            return self._response(False, SAVE_ARCHIVE_BAD_SNAPSHOT, "存档正文不是字典")

        snapshot["slot_id"] = slot_id
        valid, validate_code = ValidateSaveSnapshot(snapshot)
        if not valid:
            response = self._response(False, validate_code, "存档正文校验失败")
            response["slot_id"] = slot_id
            return response

        meta, meta_error = self._load_meta(player)
        slot_meta = self._build_slot_meta(slot_id, snapshot, title)
        meta.setdefault("slots", {})[slot_id] = slot_meta
        meta["latest_slot"] = slot_id
        meta["schema_version"] = SAVE_SCHEMA_VERSION

        snapshot_text = self._encode_json(snapshot)
        meta_text = self._encode_json(meta)
        try:
            slot_saved = player.SetExtraData(GetSaveSlotKey(slot_id), snapshot_text, False)
            meta_saved = player.SetExtraData(GetSaveMetaKey(), meta_text, False)
            flushed = player.SaveExtraData()
        except Exception as exc:
            return self._exception_response(SAVE_ARCHIVE_EXCEPTION, "写入存档失败", exc)

        if slot_saved is False or meta_saved is False or flushed is False:
            response = self._response(False, SAVE_ARCHIVE_WRITE_FAILED, "写入存档失败")
            response["slot_id"] = slot_id
            return response

        response = self._response(True, meta_error or SAVE_ARCHIVE_OK, "存档写入成功")
        response["slot_id"] = slot_id
        response["slot"] = slot_meta
        response["meta"] = meta
        response["latest_slot"] = meta.get("latest_slot")
        return response

    def load_slot(self, player, slot_id):
        slot_id = NormalizeSaveSlotId(slot_id)
        if not slot_id:
            return self._response(False, SAVE_ARCHIVE_BAD_SLOT, "无效的存档槽位")

        read_result = self._read_slot_snapshot(player, slot_id)
        if not read_result.get("ok"):
            return read_result

        meta, meta_error = self._load_meta(player)
        response = self._response(True, meta_error or SAVE_ARCHIVE_OK, "存档读取成功")
        response["slot_id"] = slot_id
        response["slot"] = self._get_slot_meta(meta, slot_id) or self._build_slot_meta(slot_id, read_result["snapshot"])
        response["snapshot"] = read_result["snapshot"]
        return response

    def delete_slot(self, player, slot_id):
        slot_id = NormalizeSaveSlotId(slot_id)
        if not slot_id:
            return self._response(False, SAVE_ARCHIVE_BAD_SLOT, "无效的存档槽位")

        meta, meta_error = self._load_meta(player)
        if slot_id in meta.get("slots", {}):
            del meta["slots"][slot_id]
        if meta.get("latest_slot") == slot_id:
            meta["latest_slot"] = self._select_latest_slot(meta)

        try:
            slot_saved = player.SetExtraData(GetSaveSlotKey(slot_id), "", False)
            meta_saved = player.SetExtraData(GetSaveMetaKey(), self._encode_json(meta), False)
            flushed = player.SaveExtraData()
        except Exception as exc:
            return self._exception_response(SAVE_ARCHIVE_EXCEPTION, "删除存档失败", exc)

        if slot_saved is False or meta_saved is False or flushed is False:
            response = self._response(False, SAVE_ARCHIVE_DELETE_FAILED, "删除存档失败")
            response["slot_id"] = slot_id
            return response

        response = self._response(True, meta_error or SAVE_ARCHIVE_OK, "存档删除成功")
        response["slot_id"] = slot_id
        response["meta"] = meta
        response["latest_slot"] = meta.get("latest_slot")
        response["slots"] = self.list_slots(player).get("slots", {})
        return response

    def query_continue(self, player):
        meta, meta_error = self._load_meta(player)
        latest_slot = NormalizeSaveSlotId(meta.get("latest_slot"))
        if not latest_slot:
            latest_slot = self._select_latest_slot(meta)

        has_save = False
        slot_meta = None
        status = SAVE_ARCHIVE_EMPTY_SLOT
        if latest_slot:
            read_result = self._read_slot_snapshot(player, latest_slot)
            status = read_result.get("code", SAVE_ARCHIVE_OK)
            if read_result.get("ok"):
                has_save = True
                slot_meta = self._get_slot_meta(meta, latest_slot) or self._build_slot_meta(latest_slot, read_result["snapshot"])

        response = self._response(True, meta_error or SAVE_ARCHIVE_OK, "继续游戏入口查询完成")
        response["has_save"] = has_save
        response["latest_slot"] = latest_slot if has_save else None
        response["slot"] = slot_meta
        response["status"] = status
        return response

    def _read_slot_snapshot(self, player, slot_id):
        try:
            raw_value = player.GetExtraData(GetSaveSlotKey(slot_id))
        except Exception as exc:
            return self._exception_response(SAVE_ARCHIVE_EXCEPTION, "读取存档失败", exc)

        if raw_value is None or raw_value == "":
            response = self._response(False, SAVE_ARCHIVE_EMPTY_SLOT, "槽位为空")
            response["slot_id"] = slot_id
            return response

        snapshot, decode_error = self._decode_json(raw_value)
        if decode_error:
            response = self._response(False, SAVE_ARCHIVE_CORRUPT_SLOT, "槽位正文损坏")
            response["slot_id"] = slot_id
            response["detail"] = decode_error
            return response

        if isinstance(snapshot, dict):
            snapshot["slot_id"] = slot_id
        valid, validate_code = ValidateSaveSnapshot(snapshot)
        if not valid:
            response = self._response(False, validate_code or SAVE_ARCHIVE_INVALID_SLOT, "槽位正文不可用")
            response["slot_id"] = slot_id
            return response

        response = self._response(True, SAVE_ARCHIVE_OK, "槽位正文已读取")
        response["slot_id"] = slot_id
        response["snapshot"] = snapshot
        return response

    def _load_meta(self, player):
        try:
            raw_value = player.GetExtraData(GetSaveMetaKey())
        except Exception:
            return self._default_meta(), SAVE_ARCHIVE_BAD_META

        if raw_value is None or raw_value == "":
            return self._default_meta(), None

        meta, decode_error = self._decode_json(raw_value)
        if decode_error or not isinstance(meta, dict):
            return self._default_meta(), SAVE_ARCHIVE_BAD_META
        if meta.get("schema_version") != SAVE_SCHEMA_VERSION:
            return self._default_meta(), SAVE_ARCHIVE_BAD_META

        slots = meta.get("slots")
        if not isinstance(slots, dict):
            meta["slots"] = {}
        clean_slots = {}
        for slot_id, slot_meta in meta.get("slots", {}).items():
            normalized_slot_id = NormalizeSaveSlotId(slot_id)
            if normalized_slot_id and isinstance(slot_meta, dict):
                clean_slot_meta = CloneSerializableData(slot_meta, {})
                clean_slot_meta["slot_id"] = normalized_slot_id
                clean_slot_meta["exists"] = bool(clean_slot_meta.get("exists", True))
                clean_slots[normalized_slot_id] = clean_slot_meta
        meta["slots"] = clean_slots

        latest_slot = NormalizeSaveSlotId(meta.get("latest_slot"))
        meta["latest_slot"] = latest_slot if latest_slot in clean_slots else self._select_latest_slot(meta)
        return meta, None

    def _default_meta(self):
        return {
            "schema_version": SAVE_SCHEMA_VERSION,
            "latest_slot": None,
            "slots": {},
        }

    def _empty_slot_meta(self, slot_id):
        return {
            "slot_id": slot_id,
            "exists": False,
            "is_auto": slot_id == SAVE_SLOT_AUTO_ID,
            "is_quick": slot_id == SAVE_SLOT_QUICK_ID,
            "status": SAVE_ARCHIVE_EMPTY_SLOT,
        }

    def _get_slot_meta(self, meta, slot_id):
        slots = meta.get("slots", {})
        slot_meta = slots.get(slot_id)
        if isinstance(slot_meta, dict) and slot_meta.get("exists", True):
            return slot_meta
        return None

    def _build_slot_meta(self, slot_id, snapshot, title=None):
        dialog = snapshot.get("dialog", {}) if isinstance(snapshot, dict) else {}
        content = dialog.get("content") if isinstance(dialog, dict) else None
        title = title or snapshot.get("current_label") or self._short_text(content) or snapshot.get("entry", "")
        return {
            "slot_id": slot_id,
            "exists": True,
            "entry": snapshot.get("entry"),
            "title": title,
            "current_label": snapshot.get("current_label"),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "chapter_progress": "{}:{}".format(snapshot.get("entry"), snapshot.get("current_index")),
            "is_auto": slot_id == SAVE_SLOT_AUTO_ID,
            "is_quick": slot_id == SAVE_SLOT_QUICK_ID,
            "has_pending_menu": bool(snapshot.get("pending_menu")),
        }

    def _select_latest_slot(self, meta):
        candidates = []
        for slot_id, slot_meta in meta.get("slots", {}).items():
            if NormalizeSaveSlotId(slot_id) and isinstance(slot_meta, dict) and slot_meta.get("exists", True):
                candidates.append((slot_meta.get("updated_at", ""), slot_id))
        if not candidates:
            return None
        candidates.sort(reverse=True)
        return candidates[0][1]

    def _encode_json(self, value):
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))

    def _decode_json(self, value):
        if isinstance(value, dict):
            return CloneSerializableData(value, {}), None
        if not isinstance(value, basestring):
            return None, "not_string"
        try:
            value = value.strip()
            if not value:
                return None, "empty"
            return json.loads(value), None
        except Exception as exc:
            return None, "{}".format(exc)

    def _short_text(self, text):
        if not text:
            return None
        if isinstance(text, basestring):
            text = text.strip()
        else:
            text = "{}".format(text).strip()
        if len(text) <= 16:
            return text
        return text[:16] + "..."

    def _response(self, ok, code, message):
        return {
            "ok": bool(ok),
            "code": code,
            "message": message,
            "schema_version": SAVE_SCHEMA_VERSION,
        }

    def _exception_response(self, code, message, exc):
        response = self._response(False, code, message)
        response["detail"] = "{}".format(exc)
        return response

