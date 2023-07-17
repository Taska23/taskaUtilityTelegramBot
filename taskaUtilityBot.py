import telebot
from telebot import types
import sqlite3
from mcstatus import JavaServer
import subprocess

bot = telebot.TeleBot('6366976096:AAG-ouDXdOASxnB0WRuqeZf-BO3RLbrfeRQ')
bot_version = '1.0.11'



#add


@bot.message_handler(commands=['start'])
def main(message):
    conn = sqlite3.connect('tub_db.sql')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id int primary key, username varchar(50), perm_level int)')
    if check_user_exists_by_id(message.from_user.id):
        bot.send_message(message.chat.id, f'Привет, ты уже был зарегистрирован ранее. \n\n Username: {message.from_user.username}, \n id: {message.from_user.id}, \n Permission Level: {get_perm_level_by_id(message.from_user.id)}' )
    else:
        query = "INSERT INTO users (id, username, perm_level) VALUES (?, ?, ?)"
        cur.execute(query, (message.from_user.id, message.from_user.username, 0))
        bot.send_message(message.chat.id, f'Привет. \nРегистрация прошла успешно с такими данными: \n\n Username: {message.from_user.username}, \n id: {message.from_user.id}, \n Permission Level: {get_perm_level_by_id(message.from_user.id)}')

    conn.commit()
    cur.close()
    conn.close()

    print(message)

@bot.message_handler(commands=['evalute'])
def evalute(message):
    if get_perm_level_by_id(message.from_user.id) >= 10:
        bot.send_message(message.chat.id, 'Кого повышаем? \nПришли мне username того, кто заслужил повышение')
        bot.register_next_step_handler(message, check_user_to_evalute)
    else:
        bot.send_message(message.chat.id, 'Ты кто такой что бы это делать?')

global_username = ''

def check_user_to_evalute(message):
    username = message.text.strip()
    if check_user_exists_by_username(username):
        bot.send_message(message.chat.id, f'Пользователь {username} сейчас имеет {get_perm_level_by_username(username)} уровень доступа.\nКакой уровень необходимо установить? (int)')
        global global_username
        global_username = username
        bot.register_next_step_handler(message, edit_user_perm_to_evalute)
    else:
        bot.send_message(message.chat.id, 'Такой пользователь у нас не зарегистрирован. Ублюдок.')



def edit_user_perm_to_evalute(message):
    message_text = message.text.strip()


    if type(int(message_text)) == int:
        global global_username
        username = global_username
        update_perm_level_by_username(username, message.text.strip())
        global_username = ''
    else:
        bot.send_message(message.chat.id, 'Число введи, блять')


@bot.message_handler(commands=['minecraft'])
def minecraft(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Запустить Сервер', callback_data='start_minecraft_server'))
    markup.add(types.InlineKeyboardButton('Перезапустить Сервер', callback_data='restart_minecraft_server'))
    markup.add(types.InlineKeyboardButton('Остановить Сервер', callback_data='stop_minecraft_server'))

    try:
        server = JavaServer.lookup("192.168.0.125:25565")
        status = server.status()
        query = server.query()

        if status.players.online > 0:
            bot.reply_to(message, f'Мониторинг состояния сервера Minecraft \n \n Статус: Active \n Версия: {query.software.brand}, {query.software.version} \n Игроков: {status.players.online} / {status.players.max} \n Игроки: {", ".join(query.players.names)} \n \n Управление сервером:', reply_markup = markup)
        else:
            bot.reply_to(message, f'Мониторинг состояния сервера Minecraft \n \n Статус: Active(Sleep) \n Версия: {query.software.brand}, {query.software.version} \n Игроков: {status.players.online} / {status.players.max} \n Игроки: {", ".join(query.players.names)} \n \n Управление сервером:', reply_markup = markup)
    except ConnectionRefusedError:
        bot.reply_to(message, f'Мониторинг состояния сервера Minecraft \n \n Статус: Inactive \n Версия: Null, Null \n Игроков: Null / Null \n Игроки:  \n \n Управление сервером:', reply_markup = markup)


@bot.message_handler(commands=['version'])
def version(message):
    bot.reply_to(message, f'Version: {str(bot_version)}')
    print(f'Version: {str(bot_version)}')

@bot.message_handler(commands=['id'])
def main(message):
    bot.reply_to(message, f'ID: {message.from_user.id}')




@bot.message_handler()
def info(message):
    if message.text.lower() == 'привет':
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}')




@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    if callback.data == 'start_minecraft_server':
        subprocess.call('screen -dmS minecraft java -Xms1G -Xmx7G -jar server.jar nogui', shell=True)
    elif callback.data == 'restart_minecraft_server':
        subprocess.call('screen -S minecraft -X quit', shell=True)
        subprocess.call('screen -dmS minecraft java -Xms1G -Xmx7G -jar server.jar nogui', shell=True)
    elif callback.data == 'stop_minecraft_server':
        subprocess.call('screen -S minecraft -X quit', shell=True)

def check_user_exists_by_id(user_id):
    conn = sqlite3.connect('tub_db.sql')
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM users WHERE id = ?"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    user_count = result[0]
    cursor.close()
    conn.close()

    if user_count > 0:
        return True
    else:
        return False


def check_user_exists_by_username(username):
    conn = sqlite3.connect('tub_db.sql')
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    user_count = result[0]
    cursor.close()
    conn.close()

    if user_count > 0:
        return True
    else:
        return False


def get_perm_level_by_id(user_id):
    conn = sqlite3.connect('tub_db.sql')
    cursor = conn.cursor()
    query = "SELECT perm_level FROM users WHERE id = ?"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        return result[0]
    else:
        return None


def update_perm_level_by_id(user_id, new_perm_level):
    conn = sqlite3.connect('tub_db.sql')
    cursor = conn.cursor()
    query = "UPDATE users SET perm_level = ? WHERE id = ?"
    cursor.execute(query, (new_perm_level, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def update_perm_level_by_username(username, new_perm_level):
    conn = sqlite3.connect('tub_db.sql')
    cursor = conn.cursor()
    query = "UPDATE users SET perm_level = ? WHERE username = ?"
    cursor.execute(query, (new_perm_level, username))
    conn.commit()
    cursor.close()
    conn.close()


def get_perm_level_by_username(username):
    conn = sqlite3.connect('tub_db.sql')
    cursor = conn.cursor()
    query = "SELECT perm_level FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        return result[0]
    else:
        return None




bot.polling(none_stop=True)