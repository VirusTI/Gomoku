from types import FunctionType

from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from _token import TOKEN
from src.data_types import Board


class RequestProcessor():

    def __init__(self):
        self.__processor_unit = TeleBot(TOKEN)
        self.gui_output = GUIOutput(self.__processor_unit)

    def start_polling(self):
        self.__processor_unit.polling(none_stop=True)

    def request_handler(self, request_type: str) -> FunctionType:
        """
        :param request_type: [text_message, button_pushing, user_registration]
        :return:
        """

        if request_type == 'start_game':

            def wrapper(handler):
                return self.__processor_unit.message_handler(
                    regexp="Play")(
                    lambda message: handler(
                        message.chat.id))

            return wrapper

        if request_type == 'get_statistics':

            def wrapper(handler):
                return self.__processor_unit.message_handler(
                    regexp="Get statistics")(
                    lambda message: handler(
                        message.chat.id))

            return wrapper

        elif request_type == 'button_pushing':

            def wrapper(handler):
                return self.__processor_unit.callback_query_handler(func=lambda message: True)(
                    lambda call: handler(call.message.chat.id, *(map(int, call.data.split(' ')))))

            return wrapper

        elif request_type == 'user_registration':

            def wrapper(handler):
                return self.__processor_unit.message_handler(commands=['start'])(
                    lambda message: handler(message.chat.id, message.chat.username))

            return wrapper


class GUIOutput():
    def __init__(self, output_device):
        self.__output_device = output_device

    def print_text(self, user_id: int, text: str):
        self.__output_device.send_message(user_id, text)

    def print_welcome(self, user_id: int, text: str):
        buttons = ReplyKeyboardMarkup(resize_keyboard=False)
        play_btn = KeyboardButton('Play')
        statistics_btn = KeyboardButton('Get statistics')
        buttons.add(play_btn, statistics_btn)
        self.__output_device.send_message(user_id, text, reply_markup=buttons)

    @staticmethod
    def __make_markup(board: Board) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup(row_width=board.sizeX)
        for i in range(board.sizeY):
            markup.add(
                *(InlineKeyboardButton(board[i, j].str(), callback_data=f'{i} {j}') for j in range(board.sizeX)))
        return markup

    def draw_board(
            self,
            user_id: int,
            board: Board,
            turn_username: str) -> int:
        return self.__output_device.send_message(
            user_id,
            f'{turn_username}`s turn',
            reply_markup=self.__make_markup(board)).message_id

    def update_board(
            self,
            user_id: int,
            game_display_id: int,
            board: Board,
            turn_username: str):
        return self.__output_device.edit_message_text(
            chat_id=user_id,
            message_id=game_display_id,
            text=f'{turn_username}`s turn',
            reply_markup=self.__make_markup(board)).message_id

    def close_board(self, user_id: int, game_display_id: int):
        self.__output_device.edit_message_text(
            chat_id=user_id,
            message_id=game_display_id,
            text='Game finished!',
            reply_markup=None)
