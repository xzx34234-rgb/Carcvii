import os
import random
from flask import Flask, request
import telebot
from telebot import types

TOKEN = os.getenv("7918361952:AAEFKZ05dpjO0OO3yyzzZGaBwRE3Us5W5D0")  # токен бота от BotFather
CHANNEL = "@https://t.me/carcvi"     # Вписываем твой канал с @

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ------------------ ДАННЫЕ ------------------
users = {}
pending_trades = {}

# Пример авто, вставляй свои картинки и характеристики
CARS = [
    {"name": "BMW M2", "hp": 450, "speed": 280, "rarity": "Common", "image": "https://i.postimg.cc/1t9Pfr8F/IMG-20251224-140330.jpg"},
    {"name": "Ferrari F8", "hp": 720, "speed": 340, "rarity": "Legendary", "image": "https://i.postimg.cc/xyz.jpg"},
    {"name": "Toyota Supra", "hp": 420, "speed": 250, "rarity": "Uncommon", "image": "https://i.postimg.cc/abc.jpg"},
]

RARITY_CHANCES = {"Common":55,"Uncommon":25,"Rare":12,"Epic":6,"Legendary":2,"Mythic":0.5}
STAGE_COSTS = {1:10000,2:35000,3:300}  # Stage3 за звёзды
DONATE_CASES_COST = {"Japan":250,"USA":250,"EU":250}
DAILY_CASES_PER_HOUR = 2

# ------------------ ФУНКЦИИ ------------------
def get_user(uid):
    if uid not in users:
        users[uid] = {"money":10000,"stars":0,"cars":[],"last_daily_case":0}
    return users[uid]

def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎁 Открыть кейс","🚗 Гараж")
    kb.add("🔄 Обмен","💎 Донат")
    kb.add("🛠 Тюнинг","🏪 Автосалон")
    return kb

def select_car_by_rarity(container=None):
    rnd = random.uniform(0,100)
    cum = 0
    for r,chance in RARITY_CHANCES.items():
        cum += chance
        if rnd <= cum:
            cars = [c for c in CARS if c["rarity"]==r]
            if container:
                cars = [c for c in cars if container in c.get("country","")]
            return random.choice(cars) if cars else random.choice(CARS)
    return random.choice(CARS)

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL,user_id)
        return member.status in ['member','creator','administrator']
    except:
        return False

# ------------------ /start ------------------
@bot.message_handler(commands=['start'])
def start(message):
    if not check_subscription(message.from_user.id):
        bot.send_message(message.chat.id,f"🔒 Подпишись на канал {CHANNEL}")
        return
    get_user(message.from_user.id)
    bot.send_message(message.chat.id,"🚗 Добро пожаловать в Car Case Bot!",reply_markup=main_keyboard())

# ------------------ ОТКРЫТИЕ КЕЙСА ------------------
@bot.message_handler(func=lambda m:m.text=="🎁 Открыть кейс")
def open_case(msg):
    user = get_user(msg.from_user.id)
    car = select_car_by_rarity()
    user["cars"].append(car)
    text = f"🎉 Ты получил авто!\n🚗 {car['name']}\n⚡ {car['hp']} HP\n🏁 {car['speed']} км/ч\nРедкость: {car['rarity']}"
    bot.send_photo(msg.chat.id,car["image"],caption=text)

# ------------------ ГАРАЖ ------------------
@bot.message_handler(func=lambda m:m.text=="🚗 Гараж")
def garage(msg):
    user = get_user(msg.from_user.id)
    if not user["cars"]:
        bot.send_message(msg.chat.id,"🚫 Гараж пуст")
        return
    for idx,car in enumerate(user["cars"],1):
        text = f"{idx}. {car['name']} | {car['hp']} HP | {car['rarity']} | Stage: {car.get('stage',0)}"
        bot.send_photo(msg.chat.id,car["image"],caption=text)

# ------------------ ТЮНИНГ ------------------
@bot.message_handler(func=lambda m:m.text=="🛠 Тюнинг")
def tuning(msg):
    user = get_user(msg.from_user.id)
    if not user["cars"]:
        bot.send_message(msg.chat.id,"🚫 Гараж пуст")
        return
    kb = types.InlineKeyboardMarkup()
    for idx,car in enumerate(user["cars"]):
        for stage in range(1,4):
            cost = STAGE_COSTS[stage]
            kb.add(types.InlineKeyboardButton(f"{car['name']} Stage{stage} ({cost})", callback_data=f"tune_{idx}_{stage}"))
    bot.send_message(msg.chat.id,"Выбери авто и Stage для покупки:",reply_markup=kb)

@bot.callback_query_handler(func=lambda c:c.data.startswith("tune"))
def tuning_callback(call):
    user = get_user(call.from_user.id)
    idx,stage = map(int,call.data.split("_")[1:])
    car = user["cars"][idx]
    cost = STAGE_COSTS[stage]
    if stage==3 and user["stars"]<cost:
        bot.send_message(call.from_user.id,"❌ Недостаточно звёзд")
        return
    if stage<3 and user["money"]<cost:
        bot.send_message(call.from_user.id,"❌ Недостаточно денег")
        return
    if stage==3:
        user["stars"]-=cost
    else:
        user["money"]-=cost
    car["stage"]=stage
    bot.send_message(call.from_user.id,f"✅ {car['name']} улучшен до Stage {stage}")

# ------------------ АВТОСАЛОН ------------------
@bot.message_handler(func=lambda m:m.text=="🏪 Автосалон")
def car_shop(msg):
    user = get_user(msg.from_user.id)
    kb = types.InlineKeyboardMarkup()
    for idx,car in enumerate(CARS):
        kb.add(types.InlineKeyboardButton(f"{car['name']} ({car.get('price',10000)}€)", callback_data=f"shop_{idx}"))
    bot.send_message(msg.chat.id,"Выбери авто для покупки:",reply_markup=kb)

@bot.callback_query_handler(func=lambda c:c.data.startswith("shop"))
def shop_callback(call):
    user = get_user(call.from_user.id)
    idx=int(call.data.split("_")[1])
    car=CARS[idx].copy()
    price = car.get("price",10000)
    if user["money"]<price:
        bot.send_message(call.from_user.id,"❌ Недостаточно денег")
        return
    user["money"]-=price
    user["cars"].append(car)
    bot.send_message(call.from_user.id,f"✅ Куплено {car['name']} за {price}€")

# ------------------ ОБМЕН ------------------
@bot.message_handler(func=lambda m:m.text=="🔄 Обмен")
def trade_start(msg):
    bot.send_message(msg.chat.id,"✏️ Введи @username игрока:")
    bot.register_next_step_handler(msg, trade_get_user)

def trade_get_user(msg):
    if not msg.text.startswith("@"): return bot.send_message(msg.chat.id,"❌ Неверный username")
    pending_trades[msg.from_user.id]={"to":msg.text,"price":0,"car":None}
    bot.send_message(msg.chat.id,"💰 Введи цену (€), 0 = обмен:")
    bot.register_next_step_handler(msg,trade_get_price)

def trade_get_price(msg):
    if not msg.text.isdigit(): return bot.send_message(msg.chat.id,"❌ Введи число")
    pending_trades[msg.from_user.id]["price"]=int(msg.text)
    bot.send_message(msg.chat.id,"🚗 Введи номер авто из гаража:")
    bot.register_next_step_handler(msg,trade_get_car)

def trade_get_car(msg):
    user=get_user(msg.from_user.id)
    idx=int(msg.text)-1
    if idx<0 or idx>=len(user["cars"]): return bot.send_message(msg.chat.id,"❌ Неверный номер")
    trade=pending_trades[msg.from_user.id]
    trade["car"]=idx
    car=user["cars"][idx]
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Принять",callback_data=f"trade_yes_{msg.from_user.id}"),
           types.InlineKeyboardButton("❌ Отказ",callback_data="trade_no"))
    text=f"🔄 Запрос на покупку\n🚗 {car['name']}\n💰 {trade['price']}€"
    bot.send_message(trade["to"],text,reply_markup=kb)
    bot.send_message(msg.chat.id,"📨 Запрос отправлен")

@bot.callback_query_handler(func=lambda c:c.data.startswith("trade"))
def trade_callback(call):
    bot.answer_callback_query(call.id)
    if call.data=="trade_no":
        bot.send_message(call.message.chat.id,"❌ Обмен отменён")
        return
    seller_id=int(call.data.split("_")[2])
    buyer_id=call.from_user.id
    trade=pending_trades.get(seller_id)
    if not trade: return
    seller=get_user(seller_id)
    buyer=get_user(buyer_id)
    price=trade["price"]
    idx=trade["car"]
    if buyer["money"]<price:
        bot.send_message(buyer_id,"❌ Недостаточно денег")
        bot.send_message(seller_id,"❌ У покупателя недостаточно средств")
        return
    car=seller["cars"].pop(idx)
    buyer["cars"].append(car)
    buyer["money"]-=price
    seller["money"]+=price
    bot.send_message(buyer_id,f"✅ Ты получил {car['name']}")
    bot.send_message(seller_id,f"💰 Авто продано за {price}€")
    del pending_trades[seller_id]

# ------------------ ДОНАТ ------------------
@bot.message_handler(func=lambda m:m.text=="💎 Донат")
def donate(msg):
    kb=types.InlineKeyboardMarkup()
    for name,cost in DONATE_CASES_COST.items():
        kb.add(types.InlineKeyboardButton(f"{name} кейс {cost} звёзд",callback_data=f"donate_{name}"))
    bot.send_message(msg.chat.id,"Выбери кейс для покупки:",reply_markup=kb)

@bot.callback_query_handler(func=lambda c:c.data.startswith("donate_"))
def donate_callback(call):
    user=get_user(call.from_user.id)
    name=call.data.split("_")[1]
    cost=DONATE_CASES_COST[name]
    if user["stars"]<cost:
        bot.send_message(call.from_user.id,"❌ Недостаточно звёзд")
        return
    user["stars"]-=cost
    car=select_car_by_rarity(container=name)
    user["cars"].append(car)
    bot.send_photo(call.from_user.id,car["image"],caption=f"🎉 Вы получили {car['name']}!")

# ------------------ WEBHOOK ------------------
@app.route("/", methods=["POST"])
def webhook():
    json_str=request.get_data().decode("UTF-8")
    update=telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK",200

# ------------------ ЗАПУСК ------------------
if __name__=="__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/")
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port)