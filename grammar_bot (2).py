import os
import logging
from random import choices, randint, choice
from collections import defaultdict
from dotenv import load_dotenv
from telebot import TeleBot, types
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('7638805645:AAGVHS0Yr1yxn34LTtZ14tTL8R0ADHZmR9I')

# Инициализация базы данных
Base = declarative_base()
engine = create_engine('sqlite:///english_bot.db')
Session = sessionmaker(bind=engine)
session = Session()

# Модели данных
class User(Base):
    tablename = 'users'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, unique=True)
    test_count = Column(Integer, default=0)
    exercise_history = Column(JSON, default=[])

class ExerciseResult(Base):
    tablename = 'exercise_results'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    rule = Column(String)
    question = Column(String)
    is_correct = Column(Integer)

Base.metadata.create_all(engine)

# Инициализация бота
bot = telebot.TeleBot('7638805645:AAGVHS0Yr1yxn34LTtZ14tTL8R0ADHZmR9I')

# Словарь с грамматическими правилами
grammar_rules = {
    "Present Simple": "Используется для обычных, регулярных действий или общеизвестных фактов.\nПример: He plays tennis every Sunday.",
    "Past Simple": "Используется для завершенных действий в прошлом.\nПример: I bought a car yesterday.",
    "Future Simple": "Используется для действий, которые произойдут в будущем.\nПример: She will visit her parents next week."
}

# Словарь с упражнениями и правильными ответами
exercises = {
    "Present Simple": [
        {"question": "Составьте предложение: He/play/tennis", "answer": "He plays tennis."},
        {"question": "Выберите правильный вариант: She (is/are) happy", "answer": "is"},
        {"question": "Составьте отрицательное предложение: We/like/coffee", "answer": "We don't like coffee."}
    ],
    "Past Simple": [
        {"question": "Составьте предложение: I/buy/a car", "answer": "I bought a car."},
        {"question": "Выберите правильный вариант: They (was/were) tired", "answer": "were"},
        {"question": "Составьте вопрос: you/see/that movie", "answer": "Did you see that movie?"}
    ],
    "Future Simple": [
        {"question": "Составьте предложение: I/travel/to Paris", "answer": "I will travel to Paris."},
        {"question": "Выберите правильный вариант: They (will/would) come tomorrow", "answer": "will"},
        {"question": "Составьте отрицательное предложение: She/call/you", "answer": "She won't call you."}
    ]
}

# Хранение текущего упражнения для каждого пользователя
user_exercises = {}

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📋 Правила грамматики")
    btn2 = types.KeyboardButton("📝 Упражнения")
    btn3 = types.KeyboardButton("🏆 Проверить знания")
    btn4 = types.KeyboardButton("ℹ️ О проекте")
    markup.add(btn1, btn2, btn3, btn4)
    
    bot.reply_to(message, "Привет! Я бот для изучения грамматики английского языка!\n"
                         "Выбери, что хочешь сделать:", reply_markup=markup)

# Обработчик текста
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "📋 Правила грамматики":
        show_grammar_rules(message)
    elif message.text == "📝 Упражнения":
        send_exercise(message)
    elif message.text == "🏆 Проверить знания":
        test_knowledge(message)
    elif message.text == "ℹ️ О проекте":
        about_project(message)
    else:
        check_answer(message)

# Показать правила грамматики
def show_grammar_rules(message):
    markup = types.InlineKeyboardMarkup()
    for rule in grammar_rules:
        btn = types.InlineKeyboardButton(text=rule, callback_data=rule)
        markup.add(btn)
    
    bot.send_message(message.chat.id, "Выбери правило грамматики:", reply_markup=markup)

# Обработчик callback
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data in grammar_rules:
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"{call.data}:\n{grammar_rules[call.data]}")

# Отправить упражнение
def send_exercise(message):
    rule = choice(list(exercises.keys()))
    exercise = choice(exercises[rule])
    
    user_exercises[message.chat.id] = {
        "rule": rule,
        "question": exercise["question"],
        "correct_answer": exercise["answer"]
    }
    
    bot.send_message(message.chat.id, f"Выполни упражнение ({rule}):\n\n{exercise['question']}\n\n"
                                    "Напиши свой ответ ниже.")

# Проверить ответ пользователя
def check_answer(message):
    if message.chat.id in user_exercises:
        user_answer = message.text.strip().lower()
        correct_answer = user_exercises[message.chat.id]["correct_answer"].lower()
        
        if user_answer.endswith('.'):
            user_answer = user_answer[:-1]
        if correct_answer.endswith('.'):
            correct_answer = correct_answer[:-1]
            
        if user_answer == correct_answer:
            bot.reply_to(message, "✅ Правильно! Молодец!")
        else:
            bot.reply_to(message, f"❌ Неправильно. Правильный ответ: {user_exercises[message.chat.id]['correct_answer']}")
        
        del user_exercises[message.chat.id]

# ... (остальной код без изменений до user_exercises)

# Настройки вероятностей
user_test_counts = defaultdict(int)


# Вероятности (0.2% на спецчисло, 99.2% на обычные)
INIT_SPECIAL_PROB = 0.002  # 0.2% на каждое спецчисло
INIT_NORMAL_PROB = 0.992    # 99.2% на обычные
MAX_SPECIAL_PROB = 0.005    # Максимум 0.5% на спецчисло (5% всего)
BOOST_STEP = 0.0001         # +0.01% за каждые 3 нажатия

def test_knowledge(message):
    user_id = message.chat.id
    user_test_counts[user_id] += 1
    
    # Рассчет буста (очень медленный рост)
    boost = BOOST_STEP * (user_test_counts[user_id] // 3)
    
    # Текущие вероятности с ограничениями
    current_special_prob = min(INIT_SPECIAL_PROB + boost, MAX_SPECIAL_PROB)
    current_normal_prob = max (0.90,  # Минимум 90% для обычных чисел
        INIT_NORMAL_PROB - (boost * len(special_numbers)))
    
    # Формируем распределение
    probs = [current_special_prob] * len(special_numbers) + [current_normal_prob]
    outcomes = list(special_numbers.keys()) + ["normal"]
    
    # Выбираем результат
    result = choices(outcomes, weights=probs, k=1)[0]
    
    if result in special_numbers:
        bot.send_message(message.chat.id, special_numbers[result])
    else:
        score = randint(0, 10000)
        if score < 3000:
            msg = f"🎉 {score}/10000. Продолжайте практиковаться!"
        elif score < 7000:
            msg = f"🎉 {score}/10000. Хороший результат!"
        else:
            msg = f"🎉 {score}/10000. Отлично! Так держать!"
        bot.send_message(message.chat.id, msg)

# ... (остальной код без изменений)

# Информация о проекте
def about_project(message):
    project_info = """
ℹ️ <b>О проекте</b>

Этот проект был создан студентами направления "Перевод и переводоведение" для цифровой кафлеты.

Бот направлен на изучение грамматики английского языка и включает в себя:
- Описание 3 времен: Present Simple, Past Simple, Future Simple
- Практические задания для каждого из времен
- Проверку правильности выполнения упражнений

Используйте кнопки меню для навигации по функциям бота.
"""
    bot.send_message(message.chat.id, project_info, parse_mode='HTML')

# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
