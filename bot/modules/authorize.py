#!/usr/bin/env python3
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram.filters import command, regex

from html import escape

from bot import user_data, DATABASE_URL, bot, OWNER_ID
from bot.helper.telegram_helper.message_utils import (
    deleteMessage,
    editMessage,
    sendMessage,
    user_info,
)
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.bot_utils import new_task, update_user_ldata


async def authorize(client, message):
    msg = message.text.split()
    tid_ = ""
    if len(msg) > 1:
        nid_ = msg[1].split(":")
        id_ = int(nid_[0])
        if len(nid_) > 1:
            tid_ = int(nid_[1])
    elif (reply_to := message.reply_to_message) and (
        reply_to.text is None and reply_to.caption is None
    ):
        id_ = message.chat.id
        tid_ = message.reply_to_message_id
    elif reply_to:
        id_ = reply_to.from_user.id
    else:
        id_ = message.chat.id
    if id_ in user_data and user_data[id_].get("is_auth"):
        msg = "Already Authorized!"
        if tid_:
            if tid_ not in (tids_ := user_data[id_].get("topic_ids", [])):
                tids_.append(tid_)
                update_user_ldata(id_, "topic_ids", tids_)
                if DATABASE_URL:
                    await DbManger().update_user_data(id_)
                msg = "Topic Authorized!"
            else:
                msg = "Topic Already Authorized!"
    else:
        update_user_ldata(id_, "is_auth", True)
        if tid_:
            update_user_ldata(id_, "topic_ids", [tid_])
            msg = "Topic Authorized!"
        else:
            msg = "Authorized"
        if DATABASE_URL:
            await DbManger().update_user_data(id_)
    await sendMessage(message, msg)


async def unauthorize(client, message):
    msg = message.text.split()
    tid_ = ""
    if len(msg) > 1:
        nid_ = msg[1].split(":")
        id_ = int(nid_[0])
        if len(nid_) > 1:
            tid_ = int(nid_[1])
    elif (reply_to := message.reply_to_message) and (
        reply_to.text is None and reply_to.caption is None
    ):
        id_ = message.chat.id
        tid_ = message.reply_to_message_id
    elif reply_to := message.reply_to_message:
        id_ = reply_to.from_user.id
    else:
        id_ = message.chat.id
    tids_ = []
    if (
        tid_
        and id_ in user_data
        and tid_ in (tids_ := user_data[id_].get("topic_ids", []))
    ):
        tids_.remove(tid_)
        update_user_ldata(id_, "topic_ids", tids_)
    if id_ not in user_data or user_data[id_].get("is_auth"):
        if not tids_:
            update_user_ldata(id_, "is_auth", False)
        if DATABASE_URL:
            await DbManger().update_user_data(id_)
        msg = "Unauthorized"
    else:
        msg = "Already Unauthorized!"
    await sendMessage(message, msg)


async def addSudo(client, message):
    id_ = ""
    msg = message.text.split()
    if len(msg) > 1:
        id_ = int(msg[1].strip())
    elif reply_to := message.reply_to_message:
        id_ = reply_to.from_user.id
    if id_:
        if id_ in user_data and user_data[id_].get("is_sudo"):
            msg = "Already Sudo!"
        else:
            update_user_ldata(id_, "is_sudo", True)
            if DATABASE_URL:
                await DbManger().update_user_data(id_)
            msg = "Promoted as Sudo"
    else:
        msg = "<i>Give User's ID or Reply to User's message of whom you want to Promote as Sudo</i>"
    await sendMessage(message, msg)


async def removeSudo(client, message):
    id_ = ""
    msg = message.text.split()
    if len(msg) > 1:
        id_ = int(msg[1].strip())
    elif reply_to := message.reply_to_message:
        id_ = reply_to.from_user.id
    if id_:
        if id_ in user_data and not user_data[id_].get("is_sudo"):
            msg = "Not a Sudo User, Already Demoted"
        else:
            update_user_ldata(id_, "is_sudo", False)
            if DATABASE_URL:
                await DbManger().update_user_data(id_)
            msg = "Demoted"
    else:
        msg = "<i>Give User's ID or Reply to User's message of whom you want to Demote</i>"
    await sendMessage(message, msg)


async def addBlackList(_, message):
    id_ = ""
    msg = message.text.split()
    if len(msg) > 1:
        id_ = int(msg[1].strip())
    elif reply_to := message.reply_to_message:
        id_ = reply_to.from_user.id
    if id_:
        if id_ in user_data and user_data[id_].get("is_blacklist"):
            msg = "User Already BlackListed!"
        else:
            update_user_ldata(id_, "is_blacklist", True)
            if DATABASE_URL:
                await DbManger().update_user_data(id_)
            msg = "User BlackListed"
    else:
        msg = "Give ID or Reply To message of whom you want to blacklist."
    await sendMessage(message, msg)


async def rmBlackList(_, message):
    id_ = ""
    msg = message.text.split()
    if len(msg) > 1:
        id_ = int(msg[1].strip())
    elif reply_to := message.reply_to_message:
        id_ = reply_to.from_user.id
    if id_:
        if id_ in user_data and not user_data[id_].get("is_blacklist"):
            msg = "<i>User Already Freed</i>"
        else:
            update_user_ldata(id_, "is_blacklist", False)
            if DATABASE_URL:
                await DbManger().update_user_data(id_)
            msg = "<i>User Set Free as Bird!</i>"
    else:
        msg = "Give ID or Reply To message of whom you want to remove from blacklisted"
    await sendMessage(message, msg)


async def black_listed(_, message):
    await sendMessage(message, "<i>BlackListed Detected, Restricted from Bot</i>")


bot.add_handler(
    MessageHandler(
        authorize, filters=command(BotCommands.AuthorizeCommand) & CustomFilters.sudo
    )
)
bot.add_handler(
    MessageHandler(
        unauthorize,
        filters=command(BotCommands.UnAuthorizeCommand) & CustomFilters.sudo,
    )
)
async def _users_text(flag, title):
    ids = [uid for uid, data in user_data.items() if data.get(flag)]
    users = [uid for uid in ids if uid > 0]
    chats = [uid for uid in ids if uid < 0]
    lines = []
    if flag == "is_sudo":
        users = [OWNER_ID] + [u for u in users if u != OWNER_ID]
    for no, uid in enumerate(users, start=1):
        info = await user_info(uid)
        name = escape(getattr(info, "first_name", "") or "Unknown")
        tag = f" @{info.username}" if getattr(info, "username", None) else ""
        owner = " 👑" if uid == OWNER_ID else ""
        lines.append(f"\u200e{no}. <b>{name}</b>{tag}{owner} | <code>{uid}</code>")
    text = f"㊂ <b><u>{title} :</u></b>\n\n"
    text += (
        "<blockquote expandable>" + "\n".join(lines) + "</blockquote>"
        if lines
        else "<i>None</i>"
    )
    if chats:
        text += "\n\n<b>Chats:</b>\n<blockquote>" + "\n".join(
            f"\u200e<code>{c}</code>" for c in chats
        ) + "</blockquote>"
    return text


USER_VIEWS = {
    "sudo": ("is_sudo", "Sudo Users"),
    "auth": ("is_auth", "Authorized Users"),
    "black": ("is_blacklist", "Blacklisted Users"),
}


def users_home(uid):
    """/users overview with a button per list."""
    count = lambda flag, sign=0: sum(  # noqa: E731
        1
        for k, d in user_data.items()
        if d.get(flag) and (sign == 0 or (k > 0) == (sign > 0))
    )
    text = f"""㊂ <b><u>Users Overview :</u></b>

<blockquote>╭ <b>Owner:</b> <code>{OWNER_ID}</code>
┊ <b>Sudo:</b> {count("is_sudo")}
┊ <b>Authorized:</b> {count("is_auth", 1)} users | {count("is_auth", -1)} chats
┊ <b>Blacklisted:</b> {count("is_blacklist")}
╰ <b>Saved Data:</b> {len(user_data)}</blockquote>"""
    buttons = ButtonMaker()
    buttons.ibutton("Sudo", f"ulist {uid} sudo")
    buttons.ibutton("Authorized", f"ulist {uid} auth")
    buttons.ibutton("Blacklisted", f"ulist {uid} black")
    buttons.ibutton("All Data", f"ulist {uid} data")
    buttons.ibutton("Cʟᴏsᴇ", f"ulist {uid} close", "footer")
    return text, buttons.build_menu(2)


@new_task
async def users_callback(_, query):
    data = query.data.split()
    if int(data[1]) != query.from_user.id:
        return await query.answer("This is not for you!", show_alert=True)
    await query.answer()
    action = data[2]
    if action == "close":
        return await deleteMessage(query.message)
    if action == "home":
        text, button = users_home(query.from_user.id)
        return await editMessage(query.message, text, button)
    if action == "data":
        from bot.modules.users_settings import users_dump

        return await users_dump(query.message, query.from_user.id)
    if action in USER_VIEWS:
        flag, title = USER_VIEWS[action]
        buttons = ButtonMaker()
        buttons.ibutton("◀️ Back", f"ulist {query.from_user.id} home")
        buttons.ibutton("Cʟᴏsᴇ", f"ulist {query.from_user.id} close")
        await editMessage(
            query.message, await _users_text(flag, title), buttons.build_menu(2)
        )


async def _list_users(message, flag, title):
    buttons = ButtonMaker()
    buttons.ibutton("Cʟᴏsᴇ", f"wzmlx {message.from_user.id} close")
    await sendMessage(message, await _users_text(flag, title), buttons.build_menu(1))


async def auth_list(_, message):
    await _list_users(message, "is_auth", "Authorized Users")


async def sudo_list(_, message):
    await _list_users(message, "is_sudo", "Sudo Users")


bot.add_handler(
    MessageHandler(
        auth_list, filters=command(BotCommands.AuthListCommand) & CustomFilters.sudo
    )
)
bot.add_handler(
    MessageHandler(
        sudo_list, filters=command(BotCommands.SudoListCommand) & CustomFilters.sudo
    )
)
bot.add_handler(
    MessageHandler(
        addSudo, filters=command(BotCommands.AddSudoCommand) & CustomFilters.sudo
    )
)
bot.add_handler(
    MessageHandler(
        removeSudo, filters=command(BotCommands.RmSudoCommand) & CustomFilters.sudo
    )
)
bot.add_handler(
    MessageHandler(
        addBlackList,
        filters=command(BotCommands.AddBlackListCommand) & CustomFilters.sudo,
    )
)
bot.add_handler(
    MessageHandler(
        rmBlackList,
        filters=command(BotCommands.RmBlackListCommand) & CustomFilters.sudo,
    )
)
bot.add_handler(
    MessageHandler(
        black_listed,
        filters=regex(r"^/") & CustomFilters.authorized & CustomFilters.blacklisted,
    )
)
bot.add_handler(CallbackQueryHandler(users_callback, filters=regex(r"^ulist")))
