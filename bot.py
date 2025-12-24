import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import random
import time

# ===== ПЕРЕМЕННЫЕ =====
TOKEN = '7918361952:AAEFKZ05dpjO0OO3yyzzZGaBwRE3Us5W5D0'  # Вставь сюда свой токен
CHANNEL = '@carcvi'     # Тег канала для подписки

bot = telebot.TeleBot(TOKEN)

# ===== БАЗА ДАННЫХ =====
cars = {
    "Common": [{"name": "BMW M2", "image": "ссылка_на_картинку", "price": 100000, "stage": 0}],
    "Uncommon": [{"name": "Audi RS5", "image": "ссылка_на_картинку", "price": 150000, "stage": 0}],
    "Rare": [{"name": "Ferrari F8", "image": "ссылка_на_картинку", "price": 500000, "stage": 0}],
    "Epic": [{"name": "Lamborghini Huracan", "image": "ссылка_на_картинку", "price": 800000, "stage": 0}],
    "Legendary": [{"name": "Porsche 911 GT3", "image": "ссылка_на_картинку", "price": 1200000, "stage": 0}],
    "Mythic": [{"name": "Bugatti Chiron", "image": "ссылка_на_картинку", "price": 3000000, "stage": 0}]
}

players = {}  # user_id: {"balance":0,"stars":0,"garage":[],"containers_opened":0,"last_case_time":0}
pending_trades = {}  # trade_id: {"from":id,"to":id,"car_index":int,"price":int}
STAGE_COSTS = {1:10000, 2:35000, 3:300}  # Stage3 за звёзды

# ===== ФУНКЦИИ =====
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status != 'left'
    except:
        return False

def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Открыть кейс"))
    kb.add(KeyboardButton("Гараж"))
    kb.add(KeyboardButton("Обмен"))
    kb.add(KeyboardButton("Донат"))
    return kb

def open_case(user_id):
    now = time.time()
    if user_id not in players:
        players[user_id] = {"balance":0,"stars":0,"garage":[],"containers_opened":0,"last_case_time":0}
    elapsed = now - players[user_id]["last_case_time"]
    if elapsed >= 3600:
        players[user_id]["containers_opened"] = 0
        players[user_id]["last_case_time"] = now
    if players[user_id]["containers_opened"] >= 2:
        return "Вы уже открыли 2 кейса за последний час"
    players[user_id]["containers_opened"] += 1

    if random.random() < 0.5:
        earned = random.randint(1000,10000)
        players[user_id]["balance"] += earned
        return f"Вам выпало {earned}€ игровой валюты!"
    else:
        rarities = ["Common","Uncommon","Rare","Epic","Legendary","Mythic"]
        weights = [0.57,0.225,0.11,0.055,0.015,0.005]
        rarity = random.choices(rarities,weights=weights)[0]
        car = random.choice(cars[rarity])
        players[user_id]["garage"].append(car.copy())
        return f"Вам выпала карточка: {car['name']} (редкость {rarity})"

def garage_keyboard(user_id):
    kb = InlineKeyboardMarkup()
    for i, car in enumerate(players[user_id]["garage"]):
        kb.add(InlineKeyboardButton(f"{car['name']} Stage {car['stage']}", callback_data=f"garage_{i}"))
    return kb

def stage_keyboard(car_index):
    kb = InlineKeyboardMarkup()
    for stage in range(1,4):
        if stage < 3:
            kb.add(InlineKeyboardButton(f"Купить Stage {stage} за {STAGE_COSTS[stage]}€", callback_data=f"stage_{car_index}_{stage}"))
        else:
            kb.add(InlineKeyboardButton(f"Купить Stage 3 за 300 звезд", callback_data=f"stage_{car_index}_{stage}"))
    kb.add(InlineKeyboardButton("Назад", callback_data="garage_back"))
    return kb

# ===== ХЭНДЛЕРЫ =====
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not check_subscription(user_id):
        bot.send_message(message.chat.id, f"Подпишитесь на канал {CHANNEL} чтобы пользоваться ботом.")
        return
    if user_id not in players:
        players[user_id] = {"balance":0,"stars":0,"garage":[],"containers_opened":0,"last_case_time":0}
    bot.send_message(message.chat.id,"Добро пожаловать!",reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: True)
def menu(message):
    user_id = message.from_user.id
    text = message.text
    if text == "Открыть кейс":
        bot.send_message(message.chat.id, open_case(user_id))
    elif text == "Гараж":
        if not players[user_id]["garage"]:
            bot.send_message(message.chat.id,"Ваш гараж пуст")
        else:
            bot.send_message(message.chat.id,"Ваши авто:",reply_markup=garage_keyboard(user_id))
    elif text == "Донат":
        bot.send_message(message.chat.id,"Купить донат-кейсы или Stage за звёзды")
    elif text == "Обмен":
        bot.send_message(message.chat.id,"Чтобы обменяться, напишите: /trade ID_игрока индекс_карточки сумма")
    else:
        bot.send_message(message.chat.id,"Неизвестная команда",reply_markup=main_keyboard())

# ===== ОБМЕН =====
@bot.message_handler(commands=['trade'])
def trade(message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) != 4:
        bot.send_message(message.chat.id,"Использование: /trade ID_игрока индекс_карточки сумма")
        return
    to_id = int(args[1])
    car_index = int(args[2])
    price = int(args[3])
    if car_index >= len(players[user_id]["garage"]):
        bot.send_message(message.chat.id,"Неверный индекс карточки")
        return
    trade_id = f"{user_id}_{time.time()}"
    pending_trades[trade_id] = {"from":user_id,"to":to_id,"car_index":car_index,"price":price}
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Принять", callback_data=f"accept_{trade_id}"))
    markup.add(InlineKeyboardButton("Отклонить", callback_data=f"decline_{trade_id}"))
    bot.send_message(to_id, f"Игрок {user_id} предлагает купить {players[user_id]['garage'][car_index]['name']} за {price}€", reply_markup=markup)

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data
    if data.startswith("garage_"):
        car_index = int(data.split("_")[1])
        bot.send_message(user_id,f"Вы выбрали {players[user_id]['garage'][car_index]['name']}",reply_markup=stage_keyboard(car_index))
    elif data.startswith("stage_"):
        _, car_index, stage = data.split("_")
        car_index = int(car_index)
        stage = int(stage)
        car = players[user_id]["garage"][car_index]
        if stage < 3:
            cost = STAGE_COSTS[stage]
            if players[user_id]["balance"] >= cost:
                players[user_id]["balance"] -= cost
                car["stage"] = stage
                bot.send_message(user_id,f"Вы купили Stage {stage} за {cost}€ для {car['name']}",reply_markup=garage_keyboard(user_id))
            else:
                bot.send_message(user_id,"Недостаточно баланса")
        else:
            if players[user_id]["stars"] >= 300:
                players[user_id]["stars"] -= 300
                car["stage"] = 3
                bot.send_message(user_id,f"Вы купили Stage 3 за 300 звезд для {car['name']}",reply_markup=garage_keyboard(user_id))
            else:
                bot.send_message(user_id,"Недостаточно звезд")
    elif data=="garage_back":
        bot.send_message(user_id,"Возврат в гараж:",reply_markup=garage_keyboard(user_id))
    elif data.startswith("accept_"):
        trade_id = data.split("_")[1]
        trade = pending_trades.get(trade_id)
        if not trade:
            bot.send_message(user_id,"Трейд уже отменен или истек")
            return
        if players[user_id]["balance"] < trade["price"]:
            bot.send_message(user_id,"Недостаточный баланс")
            bot.send_message(trade["from"],"У игрока недостаточный баланс")
        else:
            players[user_id]["balance"] -= trade["price"]
            players[trade["from"]]["balance"] += trade["price"]
            car = players[trade["from"]]["garage"].pop(trade["car_index"])
            players[user_id]["garage"].append(car)
            bot.send_message(user_id,f"Вы купили {car['name']} за {trade['price']}€")
            bot.send_message(trade["from"],f"Вы продали {car['name']} за {trade['price']}€")
        pending_trades.pop(trade_id)
    elif data.startswith("decline_"):
        trade_id = data.split("_")[1]
        trade = pending_trades.pop(trade_id, None)
        if trade:
            bot.send_message(trade["to"],"Вы отклонили обмен")
            bot.send_message(trade["from"],"Игрок отклонил ваш обмен")

# ===== ЗАПУСК =====
bot.infinity_polling()