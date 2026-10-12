from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

try:
    from pyrogram.enums import ButtonStyle
except ImportError:
    ButtonStyle = None

DANGER_KEYS = (
    "❌",
    "✘",
    "close",
    "cʟᴏsᴇ",
    "cancel",
    "no!",
    "delete",
    "remove",
    "reset",
    "shutdown",
    "unsubscribe",
    "unsub ",
    "permanent clean",
    "move to bin",
    "stop gdrive",
)
SUCCESS_KEYS = (
    "✓",
    "✅",
    "yes!",
    "done",
    "activate",
    "resume",
    "start rss",
)
PRIMARY_KEYS = ("◀️", "⌫", "back", "♻️", "view in")


def auto_style(key, is_url=False):
    if ButtonStyle is None:
        return None
    text = str(key).lower()
    if any(k in text for k in DANGER_KEYS):
        return ButtonStyle.DANGER
    if any(k in text for k in SUCCESS_KEYS):
        return ButtonStyle.SUCCESS
    if is_url or any(k in text for k in PRIMARY_KEYS):
        return ButtonStyle.PRIMARY
    return ButtonStyle.DEFAULT


def make_button(key, style=None, is_url=False, **kwargs):
    if ButtonStyle is not None:
        kwargs["style"] = style or auto_style(key, is_url)
    return InlineKeyboardButton(text=key, **kwargs)


class ButtonMaker:
    def __init__(self):
        self.__button = []
        self.__header_button = []
        self.__first_body_button = []
        self.__last_body_button = []
        self.__footer_button = []

    def __add(self, button, position):
        if not position:
            self.__button.append(button)
        elif position == "header":
            self.__header_button.append(button)
        elif position == "f_body":
            self.__first_body_button.append(button)
        elif position == "l_body":
            self.__last_body_button.append(button)
        elif position == "footer":
            self.__footer_button.append(button)

    def ubutton(self, key, link, position=None, style=None):
        self.__add(make_button(key, style, True, url=link), position)

    def ibutton(self, key, data, position=None, style=None):
        self.__add(make_button(key, style, callback_data=data), position)

    def build_menu(self, b_cols=1, h_cols=8, fb_cols=2, lb_cols=2, f_cols=8):
        menu = [
            self.__button[i : i + b_cols] for i in range(0, len(self.__button), b_cols)
        ]
        if self.__header_button:
            if len(self.__header_button) > h_cols:
                header_buttons = [
                    self.__header_button[i : i + h_cols]
                    for i in range(0, len(self.__header_button), h_cols)
                ]
                menu = header_buttons + menu
            else:
                menu.insert(0, self.__header_button)
        if self.__first_body_button:
            if len(self.__first_body_button) > fb_cols:
                [
                    menu.append(self.__first_body_button[i : i + fb_cols])
                    for i in range(0, len(self.__first_body_button), fb_cols)
                ]
            else:
                menu.append(self.__first_body_button)
        if self.__last_body_button:
            if len(self.__last_body_button) > lb_cols:
                [
                    menu.append(self.__last_body_button[i : i + lb_cols])
                    for i in range(0, len(self.__last_body_button), lb_cols)
                ]
            else:
                menu.append(self.__last_body_button)
        if self.__footer_button:
            if len(self.__footer_button) > f_cols:
                [
                    menu.append(self.__footer_button[i : i + f_cols])
                    for i in range(0, len(self.__footer_button), f_cols)
                ]
            else:
                menu.append(self.__footer_button)
        return InlineKeyboardMarkup(menu)
