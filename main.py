import telebot
import webbrowser

bot = telebot.TeleBot('6366976096:AAG-ouDXdOASxnB0WRuqeZf-BO3RLbrfeRQ')

#add
@bot.message_handler(commands=['site'])
def site(message):
    webbrowser.open('https://google.com')

@bot.message_handler(commands=['start'])
def main(message):
    bot.send_message(message.chat.id, 'Привет')

@bot.message_handler()
def info(message):
    if message.text.lower() == 'привет':
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}')
    elif message.text.lower() == 'id':
        bot.reply_to(message, f'ID: {message.from_user.id}')


bot.polling(none_stop=True)
