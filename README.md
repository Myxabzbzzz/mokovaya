# Моковая

Telegram-бот для парных алгоритмических мок-собеседований: один участник заходит как интервьюер, другой — как кандидат, бот мэтчит их и передаёт контакты. Само собеседование проходит вне бота.

## Запуск

1. Установи зависимости:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Скопируй `.env.example` в `.env` и заполни `BOT_TOKEN` (получить у @BotFather) и `DATABASE_URL` (локальный Postgres).
3. Создай базу и накати миграции:
   ```bash
   createdb mokovaya
   python -m alembic upgrade head
   ```
4. Запусти бота:
   ```bash
   python -m bot.main
   ```

## Тесты

Тесты используют in-memory SQLite и не требуют запущенного Postgres:

```bash
python -m pytest -v
```
# mokovaya
