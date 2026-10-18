#!/usr/bin/env python3
"""Video Tools menu (-vt). The user picks tools before the task starts."""
from asyncio import sleep
from html import escape
from time import time

from pyrogram.filters import create, regex
from pyrogram.handlers import CallbackQueryHandler, MessageHandler

from bot import bot
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.video_tools import custom_tools
from bot.helper.telegram_helper.button_build import ButtonMaker, page_style

try:
    from pyrogram.enums import ButtonStyle

    PLAIN = ButtonStyle.DEFAULT
except ImportError:
    PLAIN = None
from bot.helper.telegram_helper.message_utils import (
    deleteMessage,
    editMessage,
    sendMessage,
)

VT_TIMEOUT = 180
VT_STATE = {}

EXTRACT = {"audio": "Audio", "subs": "Subtitles", "video": "Video Only"}
REMOVE = {"subs": "Subtitles", "audio": "Extra Audio", "attach": "Attachments"}
CONVERT = {"mkv": "MKV", "mp4": "MP4", "mp3": "MP3 (Audio)", "m4a": "M4A (Audio)"}
SHOTS = [3, 5, 10]
LABELS = {
    "rename": "Rename",
    "merge_video": "Video + Video",
    "merge_audio": "Video + Audio",
    "merge_subs": "Video + Subtitle",
    "extract": "Extract",
    "remove": "Remove Stream",
    "trim": "Trim",
    "ss": "Screenshots",
    "convert": "Convert To",
}


def _selected_text(sel):
    parts = []
    for key, val in sel.items():
        if not val:
            continue
        label = LABELS.get(key, key)
        if key == "rename":
            parts.append(f"{label} → <code>{escape(val)}</code>")
        elif key in ("extract", "remove"):
            names = EXTRACT if key == "extract" else REMOVE
            parts.append(f"{label} → {', '.join(names[k] for k in val)}")
        elif key == "trim":
            parts.append(f"{label} → {val[0]}{' - ' + val[1] if val[1] else ''}")
        elif key == "ss":
            parts.append(f"{label} → {val}")
        elif key == "convert":
            parts.append(f"{label} → {CONVERT[val]}")
        elif key == "custom":
            parts.extend(val)
        else:
            parts.append(label)
    return parts


def _btn(buttons, uid, key, label, sel_on, position=None, arg=""):
    data = f"vtool {uid} {key} {arg}".strip()
    # selected = green, the rest plain (no auto red for words like "remove")
    buttons.ibutton(
        f"{'✓ ' if sel_on else ''}{label}", data, position, style=page_style(sel_on) or PLAIN
    )


def _menu(state):
    uid, sel, page = state["user"], state["sel"], state["page"]
    left = max(0, int(VT_TIMEOUT - (time() - state["time"])))
    buttons = ButtonMaker()
    if state["wait"] == "rename":
        text = "㊂ <b><u>Video Tools : Rename</u></b>\n\n<blockquote>Send the new name.\nWithout extension the original one is kept.</blockquote>"
        if sel.get(state["wait"]):
            buttons.ibutton("Remove", f"vtool {uid} unset {state['wait']}")
        buttons.ibutton("◀️ Back", f"vtool {uid} back")
        return text, buttons.build_menu(2)
    if state["wait"] == "trim":
        text = (
            "㊂ <b><u>Video Tools : Trim</u></b>\n\n<blockquote>Send start and end:\n"
            "<code>00:01:30-00:05:00</code> or <code>90-300</code> (seconds)\n"
            "Only start: <code>00:10:00</code></blockquote>\n<i>Cut without re-encoding, starts at the nearest keyframe.</i>"
        )
        if sel.get(state["wait"]):
            buttons.ibutton("Remove", f"vtool {uid} unset {state['wait']}")
        buttons.ibutton("◀️ Back", f"vtool {uid} back")
        return text, buttons.build_menu(2)
    if page == "extract":
        for k, v in EXTRACT.items():
            _btn(buttons, uid, "extract", v, k in sel.get("extract", []), arg=k)
    elif page == "remove":
        for k, v in REMOVE.items():
            _btn(buttons, uid, "remove", v, k in sel.get("remove", []), arg=k)
    elif page == "convert":
        for k, v in CONVERT.items():
            _btn(buttons, uid, "convert", v, sel.get("convert") == k, arg=k)
    elif page == "ss":
        for n in SHOTS:
            _btn(buttons, uid, "ss", f"{n} Shots", sel.get("ss") == n, arg=str(n))
    if page != "main":
        buttons.ibutton("◀️ Back", f"vtool {uid} back", "footer")
        title = {"extract": "Extract", "remove": "Remove Stream", "convert": "Convert To", "ss": "Screenshots"}[page]
        text = f"㊂ <b><u>Video Tools : {title}</u></b>\n\n<i>Choose one, it takes you back to the menu.</i>"
        return text, buttons.build_menu(2)

    _btn(buttons, uid, "rename", "Rename", bool(sel.get("rename")), "header")
    _btn(buttons, uid, "merge_video", "Video + Video", bool(sel.get("merge_video")))
    _btn(buttons, uid, "merge_audio", "Video + Audio", bool(sel.get("merge_audio")))
    _btn(buttons, uid, "merge_subs", "Video + Subtitle", bool(sel.get("merge_subs")))
    _btn(buttons, uid, "page", "Extract", bool(sel.get("extract")), arg="extract")
    _btn(buttons, uid, "page", "Remove Stream", bool(sel.get("remove")), arg="remove")
    _btn(buttons, uid, "trim", "Trim", bool(sel.get("trim")))
    _btn(buttons, uid, "page", "Screenshots", bool(sel.get("ss")), arg="ss")
    _btn(buttons, uid, "page", "Convert To", bool(sel.get("convert")), arg="convert")
    for no, name in enumerate(custom_tools()):
        _btn(buttons, uid, "custom", name, name in sel.get("custom", []), arg=str(no))
    chosen = _selected_text(sel)
    if chosen:
        buttons.ibutton("Reset", f"vtool {uid} reset", "l_body")
        buttons.ibutton("Close", f"vtool {uid} close", "footer")
        buttons.ibutton("Continue ▶", f"vtool {uid} done", "footer")
    else:
        buttons.ibutton("Close", f"vtool {uid} close", "footer")
    if chosen:
        lines = "╭ <b>Selected:</b>\n" + "\n".join(f"┊ {c}" for c in chosen)
    else:
        lines = "╭ <b>Selected:</b> None"
    text = (
        f"㊂ <b><u>Video Tools</u></b>\n\n<blockquote>{lines}\n"
        f"╰ <b>Closes in:</b> {left}s</blockquote>\n\n"
        f"<i>Pick a tool. Nothing is re-encoded, so it's fast.</i>"
    )
    return text, buttons.build_menu(2, lb_cols=1, f_cols=2)


async def _refresh(state):
    text, buttons = _menu(state)
    await editMessage(state["msg"], text, buttons)


async def video_tools_menu(message, user_id):
    """Returns the selected tools, {} when closed without any, None when cancelled."""
    state = {
        "user": user_id,
        "sel": {},
        "page": "main",
        "wait": None,
        "time": time(),
        "result": None,
        "msg": None,
    }
    text, buttons = _menu(state)
    state["msg"] = await sendMessage(message, text, buttons)
    if isinstance(state["msg"], str):
        return {}
    VT_STATE[state["msg"].id] = state

    async def _text_filter(_, __, event):
        user = event.from_user or event.sender_chat
        return bool(
            state["wait"]
            and event.text
            and user
            and user.id == user_id
            and event.chat.id == message.chat.id
        )

    handler = bot.add_handler(
        MessageHandler(_on_text(state), filters=create(_text_filter)), group=-1
    )
    try:
        while state["result"] is None and time() - state["time"] < VT_TIMEOUT:
            await sleep(0.5)
    finally:
        bot.remove_handler(*handler)
        VT_STATE.pop(state["msg"].id, None)
    await deleteMessage(state["msg"])
    if state["result"] is None:  # timeout: go on with what was picked
        return state["sel"]
    return state["result"] if state["result"] != "cancel" else None


def _on_text(state):
    async def handler(_, message):
        value = message.text.strip()
        if state["wait"] == "rename":
            state["sel"]["rename"] = value.replace("/", "_")
        elif state["wait"] == "trim":
            start, _, end = value.partition("-")
            state["sel"]["trim"] = (start.strip(), end.strip())
        state["wait"] = None
        await deleteMessage(message)
        await _refresh(state)

    return handler


@new_task
async def vtool_callback(_, query):
    data = query.data.split()
    state = VT_STATE.get(query.message.id)
    if state is None:
        await query.answer("This menu is closed!", show_alert=True)
        return await deleteMessage(query.message)
    if query.from_user.id != state["user"]:
        return await query.answer("This is not for you!", show_alert=True)
    await query.answer()
    action, arg = data[2], (data[3] if len(data) > 3 else "")
    sel = state["sel"]
    if action == "close":
        state["result"] = "cancel"
        return
    if action == "done":
        state["result"] = dict(sel)
        return
    if action == "reset":
        sel.clear()
    elif action == "back":
        state["wait"], state["page"] = None, "main"
    elif action == "page":
        state["page"] = arg
    elif action in ("rename", "trim"):
        state["wait"] = action
    elif action == "unset":
        sel.pop(arg, None)
        state["wait"] = None
    elif action in ("merge_video", "merge_audio", "merge_subs"):
        sel[action] = not sel.get(action)
    elif action in ("extract", "remove"):
        items = sel.setdefault(action, [])
        items.remove(arg) if arg in items else items.append(arg)
        state["page"] = "main"
    elif action == "convert":
        sel["convert"] = None if sel.get("convert") == arg else arg
        state["page"] = "main"
    elif action == "ss":
        sel["ss"] = None if sel.get("ss") == int(arg) else int(arg)
        state["page"] = "main"
    elif action == "custom":
        names = list(custom_tools())
        if arg.isdigit() and int(arg) < len(names):
            items = sel.setdefault("custom", [])
            name = names[int(arg)]
            items.remove(name) if name in items else items.append(name)
    await _refresh(state)


bot.add_handler(CallbackQueryHandler(vtool_callback, filters=regex(r"^vtool")))
