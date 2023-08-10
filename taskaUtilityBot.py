import telebot
from telebot import types
import sqlite3
from mcstatus import JavaServer
import subprocess
import datetime
import glob
import os
import psutil

bot = telebot.TeleBot('6366976096:AAG-ouDXdOASxnB0WRuqeZf-BO3RLbrfeRQ')
bot_version = '1.1.3'



#add


@bot.message_handler(commands=['status'])
def server_status(message):
    cpu_usage = psutil.cpu_percent(interval=1)
    avg_cpu_load = psutil.getloadavg()[1]  # Средняя загрузка за 5 минут
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage("/")
    battery = psutil.sensors_battery()

    bot_message = f'Status: \n\n' \
                  f'CPU: \n' \
                  f'Текущая загрузка CPU: {cpu_usage}% \n' \
                  f'Средняя загрузка CPU за 5 минут: {avg_cpu_load}% \n\n' \
                  f'RAM: \n' \
                  f'Всего оперативной памяти: {memory.total / (1024 ** 3):.2f} ГБ \n' \
                  f'Используется оперативной памяти: {memory.used / (1024 ** 3):.2f} ГБ \n' \
                  f'Доля используемой памяти: {memory.percent}% \n\n' \
                  f'SWAP: \n' \
                  f'Общий объем SWAP: {swap.total / (1024 ** 3):.2f} ГБ \n' \
                  f'Используется SWAP: {swap.used / (1024 ** 3):.2f} ГБ \n' \
                  f'Доля используемого SWAP: {swap.percent}% \n\n' \
                  f'ROM: \n' \
                  f'Общий объем диска: {disk.total / (1024 ** 3):.2f} ГБ \n' \
                  f'Свободное место на диске: {disk.free / (1024 ** 3):.2f} ГБ \n' \
                  f'Использовано места на диске: {disk.percent}%\n\n' \
                  f'Battery: \n' \

    if battery:
        power_plugged = battery.power_plugged
        if power_plugged:
            status = "заряжается"
        else:
            status = "не заряжается"

        bot_message += f'Заряд батареи: {battery.percent}%\n'
        bot_message += f'Состояние: {status}\n'
    else:
        bot_message += "Информация о батарее недоступна на данной системе."

    bot.send_message(message.chat.id, bot_message)

@bot.message_handler(commands=['stop'])
def stop_bot(message):
    bot.send_message(message.chat.id, 'Bot is stopping...')
    bot.stop_polling()



@bot.message_handler(commands=['alias'])
def alias(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Сгенерировать alias.txt', callback_data='alias'))
    output_text = format_sequence(message.text)
    bot.send_message(message.chat.id, output_text, reply_markup=markup)
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"resources/alias/alias_{current_datetime}.txt"
    try:
        with open(file_name, "w") as file:
            file.write(output_text)

        print(f"Файл '{file_name}' успешно сохранен.")
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")

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

    if get_perm_level_by_id(message.from_user.id) > 10:

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Запустить Сервер', callback_data='start_minecraft_server'))
        markup.add(types.InlineKeyboardButton('Перезапустить Сервер', callback_data='restart_minecraft_server'))
        markup.add(types.InlineKeyboardButton('Остановить Сервер', callback_data='stop_minecraft_server'))
        initial_message = bot.send_message(message.chat.id, f'Мониторинг состояния сервера Minecraft \n Pinging...')
        bot.send_chat_action(message.chat.id, "find_location")

        try:
            server = JavaServer.lookup("192.168.0.125:25565")
            status = server.status()
            query = server.query()

            if status.players.online > 0:
                bot.edit_message_text(chat_id=message.chat.id, message_id=initial_message.message_id, text= f'Мониторинг состояния сервера Minecraft \n \n Статус: Active \n IP: 176.38.114.39:25565 \n Версия: {query.software.brand}, {query.software.version} \n Игроков: {status.players.online} / {status.players.max} \n Игроки: {", ".join(query.players.names)} \n \n Управление сервером:', reply_markup = markup)
            else:
                bot.edit_message_text(chat_id=message.chat.id, message_id=initial_message.message_id, text= f'Мониторинг состояния сервера Minecraft \n \n Статус: Active(Sleep) \n IP: 176.38.114.39:25565 \n Версия: {query.software.brand}, {query.software.version} \n Игроков: {status.players.online} / {status.players.max} \n Игроки: {", ".join(query.players.names)} \n \n Управление сервером:', reply_markup = markup)


        except (ConnectionRefusedError, BrokenPipeError):
            bot.edit_message_text(chat_id=message.chat.id, message_id=initial_message.message_id, text= f'Мониторинг состояния сервера Minecraft \n \n Статус: Inactive \n Версия: Null, Null \n Игроков: Null / Null \n Игроки:  \n \n Управление сервером:',reply_markup=markup)

    else:
        bot.send_message(message.chat.id, "Ты кто такой, что бы это делать?")



@bot.message_handler(commands=['version'])
def version_of_bot(message):
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
        bot.send_chat_action(callback.message.chat.id, "find_location")

    elif callback.data == 'restart_minecraft_server':
        subprocess.call('screen -S minecraft -X quit', shell=True)
        subprocess.call('screen -dmS minecraft java -Xms1G -Xmx7G -jar server.jar nogui', shell=True)
        bot.send_chat_action(callback.message.chat.id, "find_location")

    elif callback.data == 'stop_minecraft_server':
        subprocess.call('screen -S minecraft -X quit', shell=True)
        bot.send_chat_action(callback.message.chat.id, "find_location")

    elif callback.data == 'alias':
        bot.send_chat_action(callback.message.chat.id, "upload_document")
        folder_path = "resources/alias/"
        file_pattern = os.path.join(folder_path, "alias_*.txt")
        try:
            files = glob.glob(file_pattern)
            sorted_files = sorted(files, key=os.path.getmtime, reverse=True)
            if sorted_files:
                newest_file = sorted_files[0]
                print(f"Самый новый файл: {newest_file}")
                with open(newest_file, 'rb') as file:
                    bot.send_document(callback.message.chat.id, file)


            else:
                print("Нет сгенерированных файлов.")
        except Exception as e:
            print(f"Ошибка при поиске нового файла: {e}")


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


def format_sequence(sequence):
    sequence = sequence.replace(',', '').replace('.', '').replace('/', '').replace(';', '')
    sequence = sequence.replace(' ', '\n')
    return sequence



bot.polling(none_stop=True)