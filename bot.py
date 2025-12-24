from telebot import TeleBot, types
import random

TOKEN = "7918361952:AAEFKZ05dpjO0OO3yyzzZGaBwRE3Us5W5D0"
bot = TeleBot(TOKEN)

# ---- ИГРОВЫЕ ДАННЫЕ (временно в памяти) ----
users = {}

cars = {
    "bmw 320i": {"name": "BMW 320i", "price": 25000},
    "audi_rs7": {"name": "Audi RS7", "price": 150000},
    "gtr_r35": {"name": "Nissan GTR R35", "price": 200000}
}

cases = {
    "common": {"name": "Обычный кейс", "price": 0},
    "bronze": {"name": "Бронзовый кейс", "price": 5000},
    "silver": {"name": "Серебряный кейс", "price": 50000},
    "gold": {"name": "Золотой кейс", "price": 100000}
}

# ---- ВСПОМОГАТЕЛЬНОЕ ----
def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "money": 10000,
            "inventory": []
        }
    return users[user_id]

# ---- START ----
@bot.message_handler(commands=["start"])
def start(message):
    user = get_user(message.from_user.id)

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🚗 Автосалон", callback_data="shop"),
        types.InlineKeyboardButton("🎁 Кейсы", callback_data="cases"),
        types.InlineKeyboardButton("📦 Инвентарь", callback_data="inventory"),
        types.InlineKeyboardButton("👤 Профиль", callback_data="profile")
    )

    bot.send_message(
        message.chat.id,
        "🚘 *CAR CASE*\nВыбери действие:",
        parse_mode="Markdown",
        reply_markup=kb
    )

# ---- ОБРАБОТКА КНОПОК ----
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user = get_user(call.from_user.id)

    # ПРОФИЛЬ
    if call.data == "profile":
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            f"👤 Профиль\n💰 Деньги: {user['money']}$\n🚗 Авто: {len(user['inventory'])}"
        )

    # ИНВЕНТАРЬ
    elif call.data == "inventory":
        bot.answer_callback_query(call.id)
        if not user["inventory"]:
            bot.send_message(call.message.chat.id, "📦 Инвентарь пуст")
        else:
            text = "📦 Твои авто:\n"
            for car in user["inventory"]:
                text += f"• {car}\n"
            bot.send_message(call.message.chat.id, text)

    # АВТОСАЛОН
    elif call.data == "shop":
        bot.answer_callback_query(call.id)
        kb = types.InlineKeyboardMarkup()
        for car_id, car in cars.items():
            kb.add(
                types.InlineKeyboardButton(
                    f"{car['name']} — {car['price']}$",
                    callback_data=f"buy_{car_id}"
                )
            )
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back"))
        bot.send_message(call.message.chat.id, "🏪 Автосалон:", reply_markup=kb)

    # ПОКУПКА АВТО
    elif call.data.startswith("buy_"):
        car_id = call.data.replace("buy_", "")
        car = cars[car_id]

        if user["money"] >= car["price"]:
            user["money"] -= car["price"]
            user["inventory"].append(car["name"])
            bot.answer_callback_query(call.id, "Покупка успешна!")
            bot.send_message(call.message.chat.id, f"🚗 Ты купил {car['name']}!")
        else:
            bot.answer_callback_query(call.id, "Недостаточно денег")

    # КЕЙСЫ
    elif call.data == "cases":
        bot.answer_callback_query(call.id)
        kb = types.InlineKeyboardMarkup()
        for case_id, case in cases.items():
            kb.add(
                types.InlineKeyboardButton(
                    f"{case['name']} ({case['price']}$)",
                    callback_data=f"open_{case_id}"
                )
            )
        kb.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back"))
        bot.send_message(call.message.chat.id, "🎁 Кейсы:", reply_markup=kb)

    # ОТКРЫТИЕ КЕЙСА
    elif call.data.startswith("open_"):
        case_id = call.data.replace("open_", "")
        case = cases[case_id]

        if user["money"] >= case["price"]:
            user["money"] -= case["price"]
            car = random.choice(list(cars.values()))
            user["inventory"].append(car["name"])
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                f"🎉 Ты открыл {case['name']}!\n🚗 Выпало: {car['name']}"
            )
        else:
            bot.answer_callback_query(call.id, "Недостаточно денег")

    # НАЗАД
    elif call.data == "back":
        bot.answer_callback_query(call.id)
        start(call.message)

# ---- ЗАПУСК ----
bot.infinity_polling()