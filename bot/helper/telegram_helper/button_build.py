from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import inspect

class ButtonMaker:
    def __init__(self):
        self.__button = []
        self.__header_button = []
        self.__first_body_button = []
        self.__last_body_button = []
        self.__footer_button = []
        
        self._supports_style = "style" in inspect.signature(InlineKeyboardButton.__init__).parameters

    def _create_button(self, text, url=None, callback_data=None, style=None):
        kwargs = {"text": text}
        if url:
            kwargs["url"] = url
        if callback_data:
            kwargs["callback_data"] = callback_data
        
        if style and self._supports_style:
            kwargs["style"] = style
            
        return InlineKeyboardButton(**kwargs)

    def ubutton(self, key, link, position=None, style=None):
        btn = self._create_button(text=key, url=link, style=style)
        if not position:
            self.__button.append(btn)
        elif position == "header":
            self.__header_button.append(btn)
        elif position == "f_body":
            self.__first_body_button.append(btn)
        elif position == "l_body":
            self.__last_body_button.append(btn)
        elif position == "footer":
            self.__footer_button.append(btn)

    def ibutton(self, key, data, position=None, style=None):
        btn = self._create_button(text=key, callback_data=data, style=style)
        if not position:
            self.__button.append(btn)
        elif position == "header":
            self.__header_button.append(btn)
        elif position == "f_body":
            self.__first_body_button.append(btn)
        elif position == "l_body":
            self.__last_body_button.append(btn)
        elif position == "footer":
            self.__footer_button.append(btn)

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
    
