import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import random
import os

# ===== ПЕРЕМЕННЫЕ =====
TOKEN = os.getenv('7918361952:AAEFKZ05dpjO0OO3yyzzZGaBwRE3Us5W5D0')  # Токен бота
CHANNEL = os.getenv('https://t.me/carcvi')  # Тег канала для подписки

bot = telebot.TeleBot(TOKEN)

# ===== БАЗА ДАННЫХ =====
# Авто: редкость, цена, ссылка на картинку, текущий stage
cars = {
    "Common": [{"name": "BMW M2", "image": "ссылка_на_картинку", "price": 100000, "stage": 0}],
    "Uncommon": [{"name": "Audi RS5", "image": "ссылка_на_картинку", "price": 150000, "stage": 0}],
    "Rare": [{"name": "Ferrari F8", "image": "ссылка_на_картинку", "price": 500000, "stage": 0}],
    "Epic": [{"name": "Lamborghini Huracan", "image": "ссылка_на_картинку", "price": 800000, "stage": 0}],
    "Legendary": [{"name": "Porsche 911 GT3", "image": "ссылка_на_картинку", "price": 1200000, "stage": 0}],
    "Mythic": [{"name": "Bugatti Chiron", "image": "ссылка_на_картинку", "price": 3000000, "stage": 0}]
}

# Игровые данные игроков
players = {}  # {user_id: {"balance": 0, "stars":0, "garage": [], "containers_opened": 0}}

# ===== ФУНКЦИИ =====
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status != 'left'
    except:
        return False

def get_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Открыть кейс"))
    markup.add(KeyboardButton("Гараж"))
    markup.add(KeyboardButton("Обмен"))
    markup.add(KeyboardButton("Донат"))
    return markup

def get_stage_keyboard(user_id, car_index, rarity):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    car = players[user_id]["garage"][car_index]
    # Stage 1-3 кнопки, если не куплено
    for stage in range(1, 4):
        markup.add(KeyboardButton(f"Купить Stage {stage}"))
    markup.add(KeyboardButton("Назад"))
    return markup

def open_daily_case(user_id):
    # Ограничение: 2 кейса в час
    if players[user_id]["containers_opened"] >= 2:
        return "Вы уже открыли 2 кейса за последний час"
    players[user_id]["containers_opened"] += 1
    # Шанс выпадения авто или валюты 50/50
    if random.random() < 0.5:
        # Выпала валюта
        earned = random.randint(1000, 10000)
        players[user_id]["balance"] += earned
        return f"Вам выпало {earned}€ игровой валюты!"
    else:
        # Выпала случайная карточка
        rarity_list = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic"]
        chances = [0.57, 0.225, 0.11, 0.055, 0.015, 0.005]  # шанс выпадения
        rarity = random.choices(rarity_list, weights=chances)[0]
        car = random.choice(cars[rarity])
        players[user_id]["garage"].append(car.copy())
        return f"Вам выпала карточка: {car['name']} (редкость {rarity})"

# ===== ХЭНДЛЕРЫ =====
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not check_subscription(user_id):
        bot.send_message(message.chat.id, f"Подпишитесь на канал {CHANNEL} чтобы пользоваться ботом.")
        return
    if user_id not in players:
        players[user_id] = {"balance": 0, "stars": 0, "garage": [], "containers_opened": 0}
    bot.send_message(message.chat.id, "Добро пожаловать в бота!", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: True)
def menu(message):
    user_id = message.from_user.id
    text = message.text
    if text == "Открыть кейс":
        bot.send_message(message.chat.id, open_daily_case(user_id))
    elif text == "Гараж":
        if not players[user_id]["garage"]:
            bot.send_message(message.chat.id, "Ваш гараж пуст.")
        else:
            msg = "Ваши авто:\n"
            for i, car in enumerate(players[user_id]["garage"]):
                msg += f"{i+1}. {car['name']} Stage {car['stage']}\n"
            bot.send_message(message.chat.id, msg)
    elif text == "Донат":
        bot.send_message(message.chat.id, "Здесь будут донат-кейсы и Stage за звёзды")
    elif text == "Обмен":
        bot.send_message(message.chat.id, "Здесь будет обмен авто между игроками")
    else:
        bot.send_message(message.chat.id, "Неизвестная команда", reply_markup=get_main_keyboard())

# ===== ЗАПУСК =====
bot.infinity_polling()