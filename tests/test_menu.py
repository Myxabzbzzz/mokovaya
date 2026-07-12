from unittest.mock import AsyncMock

from bot.handlers.menu import main_menu_keyboard, send_main_menu


def test_main_menu_keyboard_has_both_role_buttons():
    keyboard = main_menu_keyboard()

    callback_data = {
        button.callback_data
        for row in keyboard.inline_keyboard
        for button in row
    }
    assert callback_data == {
        "join_interviewer",
        "join_candidate",
        "edit_profile",
        "random_task",
    }

    texts = {
        button.text
        for row in keyboard.inline_keyboard
        for button in row
    }
    assert "🎤 Хочу собеседовать" in texts
    assert "💻 Хочу пройти собеседование" in texts
    assert "✏️ Изменить имя/юзернейм" in texts
    assert "🎲 Случайная задача" in texts


async def test_send_main_menu_calls_message_answer():
    message = AsyncMock()

    await send_main_menu(message)

    message.answer.assert_awaited_once()
    _, kwargs = message.answer.call_args
    assert "reply_markup" in kwargs
