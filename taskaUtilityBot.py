import telebot
from telebot import types

bot = telebot.TeleBot('6366976096:AAG-ouDXdOASxnB0WRuqeZf-BO3RLbrfeRQ')
bot_version = '1.0.6'

#add

@bot.message_handler(commands=['minecraft'])
def minecraft(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Запустить Сервер', callback_data='start_minecraft_server'))
    markup.add(types.InlineKeyboardButton('Перезапустить Сервер', callback_data='restart_minecraft_server'))
    markup.add(types.InlineKeyboardButton('Остановить Сервер', callback_data='stop_minecraft_server'))
    bot.reply_to(message, 'Мониторинг состояния сервера Minecraft \n \n Статус: Active/Sleep/Inactive \n Версия: NaN \n Игроков: N/N \n Игроки: NaN \n \n Управление сервером:', reply_markup = markup)



@bot.message_handler(commands=['version'])
def version(message):
    bot.reply_to(message, f'Version: {str(bot_version)}')
    print(f'Version: {str(bot_version)}')


@bot.message_handler(commands=['start'])
def main(message):
    bot.send_message(message.chat.id, 'Привет')\

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
        None #TODO


bot.polling(none_stop=True)
