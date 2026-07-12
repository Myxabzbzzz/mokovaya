from unittest.mock import AsyncMock, patch

from bot.handlers.tasks import send_random_task
from services.tasks import Task


def _make_callback():
    callback = AsyncMock()
    callback.message = AsyncMock()
    return callback


async def test_send_random_task_answers_callback_and_sends_task():
    callback = _make_callback()
    fake_task = Task(
        title="Two Sum",
        difficulty="easy",
        source="LeetCode",
        url="https://leetcode.com/problems/two-sum/",
    )

    with patch("bot.handlers.tasks.pick_random_task", return_value=fake_task):
        await send_random_task(callback)

    callback.answer.assert_awaited_once_with()
    callback.message.answer.assert_awaited_once()
    text = callback.message.answer.call_args.args[0]
    assert "Two Sum" in text
    assert "https://leetcode.com/problems/two-sum/" in text
    assert "Easy" in text
    assert "LeetCode" in text


async def test_send_random_task_labels_medium_difficulty():
    callback = _make_callback()
    fake_task = Task(
        title="3Sum",
        difficulty="medium",
        source="LeetCode",
        url="https://leetcode.com/problems/3sum/",
    )

    with patch("bot.handlers.tasks.pick_random_task", return_value=fake_task):
        await send_random_task(callback)

    text = callback.message.answer.call_args.args[0]
    assert "Medium" in text
