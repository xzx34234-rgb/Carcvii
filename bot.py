import telebot
from telebot import types
import json
import random
import os

TOKEN = "ТВОЙ_ТОКЕН_ИЗ_BOTFATHER"
bot = telebot.TeleBot(TOKEN)

def load(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

users = load("users.json")
cars = load("cars.json")
cases = load("cases.json")

def get_user(uid):
    uid = str(uid)
    if uid not in users:
        users[uid] = {"money": 20000, "inventory": [], "stages": {}}
        save("users.json", users)
    return users[uid]

# ---------- Главное меню с кнопками ----------
def main_menu(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👤 Профиль", callback_data="profile"))
    markup.add(types.InlineKeyboardButton("🎁 Кейсы", callback_data="cases"))
    markup.add(types.InlineKeyboardButton("🚗 Автосалон", callback_data="shop"))
    markup.add(types.InlineKeyboardButton("📦 Инвентарь", callback_data="inventory"))
    bot.send_message(chat_id, "Выбери действие:", reply_markup=markup)

@bot.message_handler(commands=["start"])
def start(msg):
    get_user(msg.from_user.id)
    main_menu(msg.chat.id)

# ---------- Обработка нажатий ----------
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    u = get_user(call.from_user.id)

    if call.data == "profile":
        bot.send_message(call.message.chat.id,
                         f"💰 Баланс: {u['money']} $\n🚗 Машин: {len(u['inventory'])}")
    elif call.data == "inventory":
        if not u["inventory"]:
            bot.send_message(call.message.chat.id, "❌ Инвентарь пуст")
            return
        text = "🚗 Твои авто:\n"
        for i in u["inventory"]:
            text += f"- {cars[i]['name']}\n"
        bot.send_message(call.message.chat.id, text)
    elif call.data == "cases":
        markup = types.InlineKeyboardMarkup()
        for c in cases:
            markup.add(types.InlineKeyboardButton(f"{c} ({cases[c]['price']}$)", callback_data=f"case_{c}"))
        bot.send_message(call.message.chat.id, "Выбери кейс:", reply_markup=markup)
    elif call.data.startswith("case_"):
        case = call.data.split("_")[1]
        price = cases[case]["price"]
        if u["money"] < price:
            bot.send_message(call.message.chat.id, "❌ Недостаточно денег")
            return
        u["money"] -= price
        car_id = random.choice(cases[case]["drops"])
        u["inventory"].append(car_id)
        save("users.json", users)
        bot.send_message(call.message.chat.id, f"🎉 Ты получил {cars[car_id]['name']}")
    elif call.data == "shop":
        markup = types.InlineKeyboardMarkup()
        for cid in cars:
            markup.add(types.InlineKeyboardButton(f"{cars[cid]['name']} ({cars[cid]['price']}$)",
                                                  callback_data=f"buy_{cid}"))
        bot.send_message(call.message.chat.id, "Выбери авто для покупки:", reply_markup=markup)
    elif call.data.startswith("buy_"):
        cid = call.data.split("_")[1]
        if u["money"] < cars[cid]["price"]:
            bot.send_message(call.message.chat.id, "❌ Недостаточно денег")
            return
        u["money"] -= cars[cid]["price"]
        u["inventory"].append(cid)
        save("users.json", users)
        bot.send_message(call.message.chat.id, f"✅ Куплена {cars[cid]['name']}")
    # После любого действия возвращаем главное меню
    main_menu(call.message.chat.id)

bot.infinity_polling()