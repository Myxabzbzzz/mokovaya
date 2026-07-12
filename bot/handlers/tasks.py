from aiogram import F, Router
from aiogram.types import CallbackQuery

from services.tasks import pick_random_task

router = Router()

DIFFICULTY_LABELS = {"easy": "Easy", "medium": "Medium"}


@router.callback_query(F.data == "random_task")
async def send_random_task(callback: CallbackQuery) -> None:
    task = pick_random_task()
    await callback.answer()
    await callback.message.answer(
        f"🎲 {DIFFICULTY_LABELS[task.difficulty]} · {task.source}\n"
        f"{task.title}\n{task.url}"
    )
