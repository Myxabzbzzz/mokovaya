from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎤 Хочу собеседовать", callback_data="join_interviewer")],
            [InlineKeyboardButton(text="💻 Хочу пройти собеседование", callback_data="join_candidate")],
            [InlineKeyboardButton(text="✏️ Изменить имя/юзернейм", callback_data="edit_profile")],
            [InlineKeyboardButton(text="🎲 Случайная задача", callback_data="random_task")],
        ]
    )


async def send_main_menu(message: Message) -> None:
    await message.answer(
        "Выбери, что хочешь сделать:",
        reply_markup=main_menu_keyboard(),
    )
