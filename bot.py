from telebot import TeleBot, types
import random

# ====== ВСТАВЬ СВОЙ ТОКЕН ОТ BOTFATHER ======
TOKEN = "7918361952:AAEFKZ05dpjO0OO3yyzzZGaBwRE3Us5W5D0"
bot = TeleBot(TOKEN)

# ====== ИГРОВАЯ ИНФОРМАЦИЯ ======
users = {}

# ====== МАШИНЫ ======
# Чтобы добавить новую машину, копируй один блок и меняй name, price, power, speed, acceleration, image
cars = {
    "bmw_m2": {
        "name": "BMW M2",
        "price": 100000,
        "power": 460,
        "speed": 280,
        "acceleration": 4.1,
        "stage": 0,
        "image": "https://i.postimg.cc/1t9Pfr8F/IMG-20251224-140330.jpg"
    },
    "audi_rs7": {
        "name": "Audi RS7",
        "price": 150000,
        "power": 600,
        "speed": 305,
        "acceleration": 3.6,
        "stage": 0,
        "image": "https://i.postimg.cc/1t9Pfr8F/IMG-20251224-140330.jpg"
    }
}

# ====== КЕЙСЫ ======
cases = {
    "common": {"name": "Обычный кейс", "price": 0},
    "bronze": {"name": "Бронзовый кейс", "price": 5000},
    "silver": {"name": "Серебряный кейс", "price": 50000},
    "gold": {"name": "Золотой кейс", "price": 100000}
}

# ====== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======
def get_user(user_id):
    if user_id not in users:
        users[user_id] = {"money": 10000, "inventory": []}
    return users[user_id]

def send_car_card(chat_id, car):
    text = (
        f"🚗 *{car['name']}*\n\n"
        f"⚡ Мощность: {car['power']} л.с.\n"
        f"🏁 Макс. скорость: {car['speed']} км/ч\n"
        f"⏱ Разгон 0–100: {car['acceleration']} сек\n"
        f"🔧 Stage: {car['stage']}\n\n"
        f"💰 Цена: {car['price']}$"
    )
    bot.send_photo(chat_id, car["image"], caption=text, parse_mode="Markdown")

# ====== START ======
@bot.message_handler(commands=["start"])
def start(message):
    user = get_user(message.from_user.id)

    # ReplyKeyboard внизу экрана
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🚗 Автосалон", "🎁 Кейсы")
    kb.row("📦 Инвентарь", "👤 Профиль")

    bot.send_message(message.chat.id, "Добро пожаловать в CAR CASE 🚘", reply_markup=kb)

# ====== ОБРАБОТКА КНОПОК ======
@bot.message_handler(func=lambda message: True)
def menu(message):
    user = get_user(message.from_user.id)

    if message.text == "👤 Профиль":
        bot.send_message(
            message.chat.id,
            f"👤 Профиль\n💰 Деньги: {user['money']}$\n🚗 Авто: {len(user['inventory'])}"
        )

    elif message.text == "📦 Инвентарь":
        if not user["inventory"]:
            bot.send_message(message.chat.id, "📦 Инвентарь пуст")
        else:
            for car_name in user["inventory"]:
                car_obj = next((c for c in cars.values() if c["name"] == car_name), None)
                if car_obj:
                    send_car_card(message.chat.id, car_obj)

    elif message.text == "🚗 Автосалон":
        for car in cars.values():
            send_car_card(message.chat.id, car)
            # Inline кнопка для покупки
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(
                f"Купить {car['name']} — {car['price']}$",
                callback_data=f"buy_{car['name']}"
            ))
            bot.send_message(message.chat.id, "Нажми кнопку чтобы купить:", reply_markup=kb)

    elif message.text == "🎁 Кейсы":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row("📦 Обычный (бесплатно)", "🥉 Бронзовый (5k)")
        kb.row("🥈 Серебряный (50k)", "🥇 Золотой (100k)")
        kb.row("⬅️ Назад")
        bot.send_message(message.chat.id, "Выбери кейс:", reply_markup=kb)

    elif message.text.startswith("📦") or message.text.startswith("🥉") or message.text.startswith("🥈") or message.text.startswith("🥇"):
        case_map = {
            "📦 Обычный (бесплатно)": "common",
            "🥉 Бронзовый (5k)": "bronze",
            "🥈 Серебряный (50k)": "silver",
            "🥇 Золотой (100k)": "gold"
        }
        case_id = case_map.get(message.text)
        case = cases[case_id]

        if user["money"] >= case["price"]:
            user["money"] -= case["price"]
            car = random.choice(list(cars.values()))
            user["inventory"].append(car["name"])
            send_car_card(message.chat.id, car)
            bot.send_message(message.chat.id, f"🎉 Ты открыл {case['name']}!")
        else:
            bot.send_message(message.chat.id, "Недостаточно денег")

    elif message.text == "⬅️ Назад":
        start(message)

# ====== ОБРАБОТКА INLINE КНОПОК ======
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    bot.answer_callback_query(call.id)  # обязательно сразу отвечаем

    user = get_user(call.from_user.id)

    if call.data.startswith("buy_"):
        car_name = call.data[4:]
        car_obj = next((c for c in cars.values() if c["name"] == car_name), None)
        if car_obj:
            if user["money"] >= car_obj["price"]:
                user["money"] -= car_obj["price"]
                user["inventory"].append(car_obj["name"])
                send_car_card(call.message.chat.id, car_obj)
                bot.send_message(call.message.chat.id, f"🎉 Ты купил {car_obj['name']}!")
            else:
                bot.send_message(call.message.chat.id, "Недостаточно денег")

# ====== ЗАПУСК ======
bot.infinity_polling()