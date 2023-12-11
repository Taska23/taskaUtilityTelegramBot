import telebot
from telebot import types
import sqlite3
from mcstatus import JavaServer
import subprocess
import datetime
import glob
from PIL import Image
import os
import psutil



bot = telebot.TeleBot('6366976096:AAG-ouDXdOASxnB0WRuqeZf-BO3RLbrfeRQ')
bot_version = '1.5.1'



#add









waiting_for_conversion = {}  # Словарь для хранения статуса ожидания конвертации по каждому пользователю

@bot.message_handler(commands=['convert'])
def convert_command(message):
    user_id = message.from_user.id
    waiting_for_conversion[user_id] = True
    bot.reply_to(message, "Отправьте файлы, которые нужно конвертировать\n Для выхода из режима конвертации используй /cancel (Иначе бот будет пытаться конвертировать любую отправленную ему фотографию)")

@bot.message_handler(commands=['cancel'])
def cancel_command(message):
    user_id = message.from_user.id
    if user_id in waiting_for_conversion:
        waiting_for_conversion[user_id] = False
        bot.reply_to(message, "Режим ожидания файлов отменен")

@bot.message_handler(content_types=['photo', 'document'])
def handle_files(message):
    user_id = message.from_user.id
    if user_id in waiting_for_conversion and waiting_for_conversion[user_id]:
        if message.content_type == 'photo':
            bot.reply_to(message, "Во избежании потери качества изображения в дальнейшем отправляйте картинки файлом")

            # Создание папки для пользователя, если ее нет
        user_folder = f"user_{user_id}"
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)

        # Сохранение файлов на диск
        file_id = None
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
        elif message.content_type == 'document':
            file_id = message.document.file_id

        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_ext = file_info.file_path.split('.')[-1]

        file_path = f"{user_folder}/{file_id}.{file_ext}"
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Отправка клавиатуры выбора расширения
        markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
        markup.add('.jpg', '.png', '.heic')  # Добавьте другие форматы по желанию
        bot.send_message(message.chat.id, "Выберите целевое расширение:", reply_markup=markup)

    else:
        bot.send_message(message.chat.id, "Пожалуйста, начните с команды /convert для конвертации файлов.")

@bot.message_handler(func=lambda message: True)
def handle_conversion(message):
    user_id = message.from_user.id
    user_folder = f"user_{user_id}"

    if message.text.startswith('.') and user_id in waiting_for_conversion and waiting_for_conversion[user_id]:
        target_extension = message.text
        files = os.listdir(user_folder)

        for file in files:
            if file != user_folder:
                image = Image.open(f"{user_folder}/{file}")
                converted_file_path = f"{user_folder}/{file.split('.')[0]}{target_extension}"
                image.save(converted_file_path, quality=95)  # Максимальные настройки качества

                with open(converted_file_path, 'rb') as converted_file:
                    bot.send_document(message.chat.id, converted_file)

                os.remove(f"{user_folder}/{file}")
                os.remove(converted_file_path)

        os.rmdir(user_folder)
        bot.send_message(message.chat.id, "Конвертация завершена. Файлы удалены с сервера.")
        waiting_for_conversion[user_id] = False
    else:
        bot.send_message(message.chat.id, "Пожалуйста, начните с команды /convert для конвертации файлов.")


bot.polling()












# Обработчик команды /convert
def convert_command(update, context):
    user_id = update.message.from_user.id
    context.user_data[user_id] = {'photos': []}  # Создаем пустой список для хранения фотографий пользователя

    # Отправляем пользователю сообщение
    update.message.reply_text("Отправьте файлы, которые нужно конвертировать")

# Обработчик для файлов и фотографий, отправленных пользователем
def handle_files(update, context):
    user_id = update.message.from_user.id
    user_data = context.user_data[user_id]

    # Получаем список файлов/фотографий, отправленных пользователем
    files = update.message.document or update.message.photo

    for file in files:
        file_id = file.file_id
        file_obj = context.bot.get_file(file_id)
        file_obj.download(f"photos/{user_id}/{file_id}.jpg")  # Сохраняем файл на диск (в формате jpg)

        if isinstance(file, update.message.photo):
            update.message.reply_text("Во избежании потери качества изображения в дальнейшем отправляйте картинки файлом")
        else:
            user_data['photos'].append(file_id)  # Добавляем файл в список для конвертации

    if user_data['photos']:
        # Предлагаем пользователю выбрать целевое расширение для конвертации файлов
        keyboard = [['.jpg', '.png', '.heic']]  # Возможные варианты расширений
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        update.message.reply_text("Выберите целевое расширение для отправляемых файлов", reply_markup=reply_markup)

# Обработчик для выбора целевого расширения
def handle_extension(update, context):
    user_id = update.message.from_user.id
    user_data = context.user_data[user_id]

    chosen_extension = update.message.text
    files_to_convert = user_data['photos']

    # Конвертируем выбранные файлы
    for file_id in files_to_convert:
        file_path = f"photos/{user_id}/{file_id}.jpg"  # Путь к файлу на диске
        image = Image.open(file_path)
        converted_file_path = f"photos/{user_id}/{file_id}{chosen_extension}"  # Путь для конвертированного файла
        image.save(converted_file_path, quality=95)  # Сохраняем с максимальным качеством

        # Отправляем конвертированный файл пользователю
        context.bot.send_document(chat_id=user_id, document=open(converted_file_path, 'rb'))

        # Удаляем скачанные и конвертированные фотографии пользователя
        os.remove(file_path)
        os.remove(converted_file_path)

    del context.user_data[user_id]  # Удаляем данные пользователя из контекста

# Добавляем обработчики команды /convert и файлов/фотографий
dispatcher.add_handler(CommandHandler('convert', convert_command))
dispatcher.add_handler(MessageHandler(Filters.document | Filters.photo, handle_files))
dispatcher.add_handler(MessageHandler(Filters.regex(r'^\.(jpg|png|heic)$'), handle_extension))


















@bot.message_handler(commands=['patchlog'])
def patchlog(message):
    bot.send_message(message.chat.id, f'Patchlog: \n\n' \
                                      f'1.4.4: \n Добавлен /help  \n\n' \
                                      f'1.4.3: \n Добавлен патчлог :) \n\n' \
                                      f'1.4.2: \n Фикс системы обновления бота\n\n' \
                                      f'1.4.1:  \n Фикс уровней доступа для некоторых команд\n\n' \
                                      f'1.4.0:  \n Система автоматических обновлений\n\n' \
                                      f'1.3.0:  \n QOL, Добавлен модный лаунчер майнкрафта\n\n' \
                                      f'1.2.0:  \n alias, статус железа\n\n' \
                                      f'1.1.0:  \n Система рангов, бд\n\n' \
                     )

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, f'# Welcome to Taska Utility Bot!\n\n' \
                                    f'Привет. Этот бот я написал сам, по большей части - для себя. Некторые функции написаны специально для моих друзей, но даже если мы не знакомы - ты всё ещё можешь найти тут полезные функции.\n' \
                                    f'Большая часть функционала доступна всем пользователям, но некоторые функции доступны только пользователям с определённым permission_level. Ниже приведены доступные тебе команды.\n' \
                                    f'Твой permission_level = {get_perm_level_by_id(message.from_user.id)}, tier = {get_perm_level_by_id(message.from_user.id) // 10}\n\n' \
                                    f'\nTier 0\n' \
                                      f'/start \n'
                                      f'/help\n'
                                      f'/version\n'
                                      f'/status\n'
                                      f'/alias '
                     )
    if get_perm_level_by_id(message.from_user.id) >= 10: bot.send_message(message.chat.id,
                                    f'\n\nTier 1\n' \
                                    f'#WIP' \
                    )
    if get_perm_level_by_id(message.from_user.id) >= 20: bot.send_message(message.chat.id,
                                      f'\n\nTier 2\n'
                                      f'/minecraft' \
                    )
    if get_perm_level_by_id(message.from_user.id) >= 30: bot.send_message(message.chat.id,
                                      f'\n\nTier 3\n'
                                      f'/minecraft_atm7'
                                      f'/save\t#WIP\n' \
                    )
    if get_perm_level_by_id(message.from_user.id) >= 80: bot.send_message(message.chat.id,
                                    f'\n\nTier 8\n'
                                    f'/evalute'
                    )

    if (message.from_user.username == "Taska2399" or message.from_user.username == "DarkMagorik"): bot.send_message(message.chat.id,
                                    f'\n\n# Tier Extra\n/pass'
                    )


@bot.message_handler(commands=['update'])
def handle_update(message):
    if get_perm_level_by_id(message.from_user.id) >= 80:  # Проверка разрешений пользователя
        update_bot(message)
    else:
        bot.send_message(message.chat.id, "Недостаточно прав для обновления бота.")

def update_bot(message):
    # Установка зависимостей из requirements.txt
    try:
        os.chdir('/home/taska/taskaUtilityTelegramBot')
        bot.send_message(message.chat.id, f'Текущая версия бота: {str(bot_version)}' )
        subprocess.run(["pip", "install", "-r", "requirements.txt"])
        bot.send_message(message.chat.id, "Зависимости обновлены успешно.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при установке зависимостей: {e}")

    # Обновление кода из репозитория GitHub
    try:
        os.chdir('/home/taska/taskaUtilityTelegramBot')
        subprocess.run(["git", "pull"])  # Обновление кода из репозитория
        bot.send_message(message.chat.id, "Бот успешно обновлен. Перезапускаюсь...")

        # Команда для перезапуска бота
        os.chdir('/home/taska/taskaUtilityTelegramBot')

        subprocess.run(["python3", "taskaUtilityBot.py"])
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при обновлении бота: {e}")

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
                  f'Средняя загрузка CPU за 5 минут: {avg_cpu_load * 10}% \n\n' \
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
    if get_perm_level_by_id(message.from_user.id) >= 80:
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

@bot.message_handler(commands=['pass'])
def pass_management(message):
    if message.from_user.username != "Taska2399" and message.from_user.username != "DarkMagorik":
        return

    conn = sqlite3.connect('tub_db.sql')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS ph_pass (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, text TEXT)')
    conn.commit()

    if message.text.lower() == '/pass add':
        bot.send_message(message.chat.id, 'Введите название для новой строки:')
        bot.register_next_step_handler(message, add_new_pass)

    if message.text == '/pass':
        cur.execute('SELECT * FROM ph_pass')
        passes = cur.fetchall()

        if not passes:
            bot.send_message(message.chat.id, 'База данных пуста.')
            return
        else:
            keyboard = types.InlineKeyboardMarkup()
            for row in passes:
                pass_id = row[0]
                pass_name = row[1]
                pass_text = row[2]

                keyboard.add(types.InlineKeyboardButton(pass_name, callback_data=f'show_pass_{pass_id}'))

            bot.send_message(message.chat.id, 'Известные пароли:', reply_markup=keyboard)
            return

def add_new_pass(message):
    pass_name = message.text

    conn = sqlite3.connect('tub_db.sql')
    cur = conn.cursor()
    cur.execute('INSERT INTO ph_pass (name, text) VALUES (?, ?)', (pass_name, 'Пусто'))
    conn.commit()

    bot.send_message(message.chat.id, f'Добавлена новая запись с названием "{pass_name}" и текстом "Пусто".')
    cur.close()
    conn.close()

def callback_show_pass(call):
    pass_id = int(call.data.split('_')[-1])

    conn = sqlite3.connect('tub_db.sql')
    cur = conn.cursor()
    cur.execute('SELECT * FROM ph_pass WHERE id = ?', (pass_id,))
    pass_data = cur.fetchone()

    if pass_data:
        pass_name = pass_data[1]
        pass_text = pass_data[2]

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton('Изменить', callback_data=f'edit_pass_{pass_id}'),
            types.InlineKeyboardButton('Удалить', callback_data=f'delete_pass_{pass_id}'),
            types.InlineKeyboardButton('Назад', callback_data=f'back_to_previous')
        )

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f'Название: {pass_name}\n\nТекст: {pass_text}',
                              reply_markup=keyboard)
    else:
        bot.send_message(call.message.chat.id, 'Запись не найдена.')

def callback_back_to_previous(call):
    conn = sqlite3.connect('tub_db.sql')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS ph_pass (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, text TEXT)')
    conn.commit()
    cur.execute('SELECT * FROM ph_pass')
    passes = cur.fetchall()

    if not passes:
        bot.edit_message_text(call.chat.id, 'База данных пуста.')
        return
    else:
        keyboard = types.InlineKeyboardMarkup()
        for row in passes:
            pass_id = row[0]
            pass_name = row[1]
            pass_text = row[2]

            keyboard.add(types.InlineKeyboardButton(pass_name, callback_data=f'show_pass_{pass_id}'))

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,text= 'Известные пароли:', reply_markup=keyboard)
        return

def callback_delete_pass(call):
    pass_id = int(call.data.split('_')[-1])

    conn = sqlite3.connect('tub_db.sql')
    cur = conn.cursor()
    cur.execute('DELETE FROM ph_pass WHERE id = ?', (pass_id,))
    conn.commit()

    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, 'Запись удалена.')

def callback_edit_pass(call):
    pass_id = int(call.data.split('_')[-1])

    bot.send_message(call.message.chat.id, 'Отправьте новый текст для записи.')
    bot.register_next_step_handler(call.message, lambda msg, pid=pass_id: update_pass(msg, pid))

def update_pass(message, pass_id):
    new_text = message.text

    conn = sqlite3.connect('tub_db.sql')
    cur = conn.cursor()
    cur.execute('UPDATE ph_pass SET text = ? WHERE id = ?', (new_text, pass_id))
    conn.commit()

    bot.send_message(message.chat.id, 'Запись обновлена.')

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_previous')
def callback_back_to_previous_handler(call):
    callback_back_to_previous(call)
@bot.callback_query_handler(func=lambda call: call.data.startswith('show_pass_'))
def callback_show_pass_handler(call):
    callback_show_pass(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_pass_'))
def callback_delete_pass_handler(call):
    callback_delete_pass(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_pass_'))
def callback_edit_pass_handler(call):
    callback_edit_pass(call)

@bot.message_handler(commands=['evalute'])
def evalute(message):
    if get_perm_level_by_id(message.from_user.id) >= 80:
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

    if get_perm_level_by_id(message.from_user.id) >= 20:

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

@bot.message_handler(commands=['minecraft_atm7'])
def minecraft(message):

    if get_perm_level_by_id(message.from_user.id) > 30:

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Запустить Сервер', callback_data='start_minecraft_atm7_server'))
        markup.add(types.InlineKeyboardButton('Перезапустить Сервер', callback_data='restart_minecraft_atm7_server'))
        markup.add(types.InlineKeyboardButton('Остановить Сервер', callback_data='stop_minecraft_atm7_server'))
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

    # Vanilla mine:

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


        #ATM 7 mine:



    if callback.data == 'start_minecraft_atm7_server':
        try:

            # /home/taska/atm7/server-1.2.3/run.sh
            os.chdir('/home/taska/atm7/server-1.2.3/')

            subprocess.run(['nohup', './run.sh', '&'])
            os.chdir('/home/taska/taskaUtilityTelegramBot')


        except subprocess.CalledProcessError as e:
            print(f'Error: {e}')

    elif callback.data == 'restart_minecraft_atm7_server':
        #TODO
        None

    elif callback.data == 'stop_minecraft_atm7_server':
        #TODO
        None



    #Alias


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