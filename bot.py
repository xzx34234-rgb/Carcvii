import telebot
import json
import random
import os

TOKEN = "7918361952:AAEFKZ05dpjO0OO3yyzzZGaBwRE3Us5W5D0"

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
        users[uid] = {
            "money": 20000,
            "inventory": [],
            "stages": {}
        }
        save("users.json", users)
    return users[uid]

@bot.message_handler(commands=["start"])
def start(msg):
    get_user(msg.from_user.id)
    bot.send_message(msg.chat.id,
        "🚗 Добро пожаловать в Car Case Bot!\n\n"
        "/profile — профиль\n"
        "/cases — кейсы\n"
        "/inventory — инвентарь\n"
        "/shop — автосалон"
    )

@bot.message_handler(commands=["profile"])
def profile(msg):
    u = get_user(msg.from_user.id)
    bot.send_message(msg.chat.id,
        f"💰 Баланс: {u['money']} $\n"
        f"🚗 Машин: {len(u['inventory'])}"
    )

@bot.message_handler(commands=["cases"])
def show_cases(msg):
    text = "🎁 Кейсы:\n"
    for c in cases:
        text += f"{c} — {cases[c]['price']}$\n"
    text += "\nНапиши: open ИМЯ_КЕЙСА"
    bot.send_message(msg.chat.id, text)

@bot.message_handler(func=lambda m: m.text.startswith("open "))
def open_case(msg):
    case = msg.text.split(" ")[1]
    u = get_user(msg.from_user.id)

    if case not in cases:
        return bot.send_message(msg.chat.id, "❌ Нет такого кейса")

    price = cases[case]["price"]
    if u["money"] < price:
        return bot.send_message(msg.chat.id, "❌ Недостаточно денег")

    u["money"] -= price
    car_id = random.choice(cases[case]["drops"])
    u["inventory"].append(car_id)
    save("users.json", users)

    bot.send_message(msg.chat.id, f"🎉 Ты получил {cars[car_id]['name']}")

@bot.message_handler(commands=["inventory"])
def inventory(msg):
    u = get_user(msg.from_user.id)
    if not u["inventory"]:
        return bot.send_message(msg.chat.id, "❌ Инвентарь пуст")

    text = "🚗 Твои авто:\n"
    for i in u["inventory"]:
        text += f"- {cars[i]['name']}\n"
    bot.send_message(msg.chat.id, text)

@bot.message_handler(commands=["shop"])
def shop(msg):
    text = "🏬 Автосалон:\n"
    for cid in cars:
        text += f"{cars[cid]['name']} — {cars[cid]['price']}$\n"
    text += "\nНапиши: buy ИМЯ_АВТО"
    bot.send_message(msg.chat.id, text)

@bot.message_handler(func=lambda m: m.text.startswith("buy "))
def buy(msg):
    name = msg.text.replace("buy ", "").lower()
    u = get_user(msg.from_user.id)

    for cid in cars:
        if cars[cid]["name"].lower() == name:
            if u["money"] < cars[cid]["price"]:
                return bot.send_message(msg.chat.id, "❌ Недостаточно денег")
            u["money"] -= cars[cid]["price"]
            u["inventory"].append(cid)
            save("users.json", users)
            return bot.send_message(msg.chat.id, f"✅ Куплена {cars[cid]['name']}")

    bot.send_message(msg.chat.id, "❌ Авто не найдено")

bot.infinity_polling()
