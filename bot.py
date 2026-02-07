# bot_complete.py
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import sqlite3
from datetime import datetime, timedelta
import random
import string

# ====== НАСТРОЙКИ ======
API_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Вставь токен своего бота
ADMIN_ID = 123456789  # Твой Telegram ID (для админ-команд)
ADMIN_USERNAME = "@Ctypesrr"  # Юзер, который будет указан пользователю
CHANNEL_IDS = [-1001234567890, -1009876543210]  # ID 10 каналов, на которые нужно подписаться

# ====== БАЗА ДАННЫХ ======
conn = sqlite3.connect("bot.db")
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    start_time TEXT,
    completed INTEGER DEFAULT 0,
    paid INTEGER DEFAULT 0,
    reward_code TEXT
)
''')
conn.commit()

# ====== БОТ ======
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ====== Утилиты ======
def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def user_completed(user_id):
    c.execute("SELECT completed, paid FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row:
        return row[0] == 1 and row[1] == 0
    return False

# ====== КНОПКИ ======
def get_withdraw_keyboard():
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="Вывести подарок", callback_data="withdraw"))
    return kb.as_markup()

# ====== КОМАНДА /START ======
@dp.message(F.text == "/start")
async def start(message: types.Message):
    user_id = message.from_user.id
    now = datetime.now().isoformat()
    reward_code = generate_code()
    c.execute("INSERT OR IGNORE INTO users (user_id, start_time, reward_code) VALUES (?, ?, ?)",
              (user_id, now, reward_code))
    conn.commit()

    text = (
        f"Привет! 🎉\n\n"
        f"Подпишись на все 10 каналов и останься там 4 дня.\n"
        f"После этого сможешь вывести подарок.\n\n"
        f"Твой уникальный код для вывода: {reward_code}\n\n"
        f"Все вопросы по подаркам: {ADMIN_USERNAME}"
    )
    await message.answer(text, reply_markup=get_withdraw_keyboard())

# ====== CALLBACK ДЛЯ ВЫВОДА ======
@dp.callback_query(F.data == "withdraw")
async def withdraw(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    c.execute("SELECT start_time, completed, paid, reward_code FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        await callback.message.answer("Что-то пошло не так, начни заново с /start")
        return

    start_time = datetime.fromisoformat(row[0])
    completed, paid, code = row[1], row[2], row[3]

    now = datetime.now()
    if paid:
        await callback.message.answer("Подарок уже отправлен ✅")
        return

    if (now - start_time) >= timedelta(days=4):
        # помечаем completed
        c.execute("UPDATE users SET completed=1 WHERE user_id=?", (user_id,))
        conn.commit()
        await callback.message.answer(
            f"Задание выполнено! 🎁\n"
            f"Сделай скрин и отправь администратору {ADMIN_USERNAME}.\n"
            f"Код для проверки: {code}"
        )
    else:
        remaining = timedelta(days=4) - (now - start_time)
        await callback.message.answer(
            f"Еще не прошло 4 дня ⏳\nОсталось: {remaining.days} дн. {remaining.seconds//3600} ч."
        )

# ====== КОМАНДА ДЛЯ АДМИНА: СПИСОК ОЖИДАЮЩИХ ======
@dp.message(F.text == "/pending" and F.from_user.id == ADMIN_ID)
async def pending(message: types.Message):
    c.execute("SELECT user_id, reward_code FROM users WHERE completed=1 AND paid=0")
    rows = c.fetchall()
    if not rows:
        await message.answer("Нет пользователей, ожидающих подарок ✅")
        return
    text = "Пользователи, которым нужно вручную отправить подарок:\n\n"
    for r in rows:
        text += f"User ID: {r[0]} | Код: {r[1]}\n"
    await message.answer(text)

# ====== КОМАНДА ДЛЯ МАРКИРОВКИ ПОЛУЧЕННОГО ПОДАРКА ======
@dp.message(F.text.startswith("/mark_paid") and F.from_user.id == ADMIN_ID)
async def mark_paid(message: types.Message):
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Использование: /mark_paid <user_id>")
        return
    user_id = int(parts[1])
    c.execute("UPDATE users SET paid=1 WHERE user_id=?", (user_id,))
    conn.commit()
    await message.answer(f"Подарок отмечен как отправленный для {user_id} ✅")

# ====== ЗАПУСК БОТА ======
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    dp.run_polling(bot)