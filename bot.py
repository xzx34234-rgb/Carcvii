import telebot
from telebot import types

TOKEN = "7918361952:AAEFKZ05dpjO0OO3yyzzZGaBwRE3Us5W5D0"
bot = telebot.TeleBot(TOKEN)

# ---------------- ДАННЫЕ ----------------

users = {}
pending_trades = {}

def get_user(uid):
    if uid not in users:
        users[uid] = {
            "money": 10000,
            "cars": []
        }
    return users[uid]

# ---------------- КНОПКИ ВНИЗУ ----------------

def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚗 Гараж", "🎁 Получить авто")
    kb.add("🔄 Обмен")
    return kb

# ---------------- /start ----------------

@bot.message_handler(commands=["start"])
def start(msg):
    get_user(msg.from_user.id)
    bot.send_message(
        msg.chat.id,
        "🚘 Добро пожаловать в Car Case Bot!",
        reply_markup=main_keyboard()
    )

# ---------------- ПОЛУЧИТЬ АВТО ----------------

@bot.message_handler(func=lambda m: m.text == "🎁 Получить авто")
def get_car(msg):
    user = get_user(msg.from_user.id)

    car = {
        "name": "BMW M4",
        "hp": 510,
        "speed": 290,
        "image": "https://i.postimg.cc/1t9Pfr8F/IMG-20251224-140330.jpg"
    }

    user["cars"].append(car)

    text = (
        f"🎉 Ты получил авто!\n\n"
        f"🚗 {car['name']}\n"
        f"⚡ {car['hp']} HP\n"
        f"🏁 {car['speed']} км/ч"
    )

    bot.send_photo(msg.chat.id, car["image"], caption=text)

# ---------------- ГАРАЖ ----------------

@bot.message_handler(func=lambda m: m.text == "🚗 Гараж")
def garage(msg):
    user = get_user(msg.from_user.id)

    if not user["cars"]:
        bot.send_message(msg.chat.id, "🚫 Гараж пуст")
        return

    text = "🚗 Твои авто:\n\n"
    for i, car in enumerate(user["cars"], 1):
        text += f"{i}. {car['name']} | {car['hp']} HP\n"

    bot.send_message(msg.chat.id, text)

# ---------------- ОБМЕН ----------------

@bot.message_handler(func=lambda m: m.text == "🔄 Обмен")
def trade_start(msg):
    bot.send_message(msg.chat.id, "✏️ Введи @username игрока:")
    bot.register_next_step_handler(msg, trade_get_user)

def trade_get_user(msg):
    if not msg.text.startswith("@"):
        bot.send_message(msg.chat.id, "❌ Неверный username")
        return

    pending_trades[msg.from_user.id] = {
        "to": msg.text,
        "price": 0,
        "car": None
    }

    bot.send_message(msg.chat.id, "💰 Введи цену (€), 0 = обмен:")
    bot.register_next_step_handler(msg, trade_get_price)

def trade_get_price(msg):
    if not msg.text.isdigit():
        bot.send_message(msg.chat.id, "❌ Введи число")
        return

    pending_trades[msg.from_user.id]["price"] = int(msg.text)
    bot.send_message(msg.chat.id, "🚗 Введи номер авто из гаража:")
    bot.register_next_step_handler(msg, trade_get_car)

def trade_get_car(msg):
    user = get_user(msg.from_user.id)

    if not msg.text.isdigit():
        return

    idx = int(msg.text) - 1
    if idx < 0 or idx >= len(user["cars"]):
        bot.send_message(msg.chat.id, "❌ Неверный номер")
        return

    trade = pending_trades[msg.from_user.id]
    trade["car"] = idx

    car = user["cars"][idx]

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Принять", callback_data=f"trade_yes_{msg.from_user.id}"),
        types.InlineKeyboardButton("❌ Отказ", callback_data="trade_no")
    )

    text = (
        f"🔄 Запрос на покупку\n\n"
        f"🚗 {car['name']}\n"
        f"💰 Цена: {trade['price']}€"
    )

    bot.send_message(trade["to"], text, reply_markup=kb)
    bot.send_message(msg.chat.id, "📨 Запрос отправлен")

# ---------------- CALLBACK ----------------

@bot.callback_query_handler(func=lambda c: c.data.startswith("trade"))
def trade_callback(call):
    bot.answer_callback_query(call.id)

    if call.data == "trade_no":
        bot.send_message(call.message.chat.id, "❌ Обмен отменён")
        return

    seller_id = int(call.data.split("_")[2])
    buyer_id = call.from_user.id

    trade = pending_trades.get(seller_id)
    if not trade:
        return

    seller = get_user(seller_id)
    buyer = get_user(buyer_id)

    price = trade["price"]
    idx = trade["car"]

    if buyer["money"] < price:
        bot.send_message(buyer_id, "❌ Недостаточно денег")
        return

    car = seller["cars"].pop(idx)
    buyer["cars"].append(car)

    buyer["money"] -= price
    seller["money"] += price

    bot.send_message(buyer_id, f"✅ Ты получил {car['name']}")
    bot.send_message(seller_id, f"💰 Авто продано за {price}€")

    del pending_trades[seller_id]

# ---------------- ЗАПУСК ----------------

bot.infinity_polling()