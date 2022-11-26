import telebot
from fuzzywuzzy import process
from telebot import types
from random import randint

bot = telebot.TeleBot('здесь должен быть токен')

layout = dict(zip(map(ord, "qwertyuiop[]asdfghjkl;'zxcvbnm,./`"
                           'QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?~'),
                           "йцукенгшщзхъфывапролджэячсмитьбю.ё"
                           'ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,Ё'))

capybara_msg = "Я устал. Мне надо отвлечься."
hello_msg = "Привет, я КапиМетрия бот. Напиши о чем ты хочешь узнать."
smile_msg = "Хорошенько отдохни и снова спроси меня."
result_msg = "Может быть ты искал это:"
notfound_msg = "Извините, не нашёл подходящей информации. \nПопробуй сформулировать иначе."
error_msg = "Кажется я устал (что-то пошло не так)"
help_msg = "Чтобы найти нужную теорему введи её название,\nесли забыл я могу найти теорему по ключевым словам."
# считываем url каритиное из файла построчно и кладём в массив
def readPicture(file_name):
    res_arr = []
    img_file = open(file_name, "r")    
    for line in img_file: 
        res_arr.append(line.strip())
    img_file.close
    return res_arr

# считываем данные из файлы, файлы разбиты на группы по 3 строки: 1 - ключ, 2,3 - данные 
def readData(file_name):
    result_dic = {}
    data_file = open(file_name, "r", encoding="utf-8")
    data_arr=[]
    for line in data_file: 
        data_arr.append(line.strip())
    data_file.close
    for i in range (0, len(data_arr)//3):
        result_dic[data_arr[3*i]] = [data_arr[3*i+1], data_arr[3*i+2]]
    return result_dic
    
# С помощью fuzzywuzzy вычисляем наиболее похожие фразы
def answer(text):
    #a = process.extractOne(text, g_data.values())
    a = process.extractBests(text, g_data, score_cutoff=45)
    return a

# команда help
@bot.message_handler(commands=["help"])
def helpcmd(m):
    print("help")
    bot.send_message(m.chat.id,help_msg)
    
# Стартуем бот /start
@bot.message_handler(commands=["start"])
def start(m):
    print("start")
    # создаём основное меню
    markup_main=types.ReplyKeyboardMarkup(resize_keyboard=True)
    # создаёс кнопку для основного меню
    item_show_picture=types.KeyboardButton(capybara_msg)
    markup_main.add(item_show_picture)
    #тправляем приветсвенное сообщение    
    bot.send_message(m.chat.id, hello_msg, reply_markup=markup_main)

# Обработчик для inline меню
# может быть передано сообщение с кодом определения/теоремы "0015" или с кодом доказательства "proof_0015" или "proof_no"
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    print("callback_" + call.data)
    try:
        infa = g_data.get(call.data)
        if infa:  # если передан код получения текста  определения/теоремы
            # краткое название
            bot.send_message(call.message.chat.id, "<b>" + infa[0] + ":</b>", parse_mode="html")
            # текст определения/свойства/теоремы
            bot.send_message(call.message.chat.id, infa[1].replace('|','\n'))
            
            proof = proof_data.get("proof_" + call.data)
            if proof: # если в наличии есть доказательство            
                # делаем inline меню для доказательства
                keyboard_proof = types.InlineKeyboardMarkup()
                yes_btn = types.InlineKeyboardButton("Да", callback_data="proof_"+call.data)                    
                no_btn = types.InlineKeyboardButton("Нет", callback_data="proof_no")        
                keyboard_proof.add(yes_btn, no_btn)
                bot.send_message(call.message.chat.id, "Доказать?", reply_markup=keyboard_proof)            
        else: 
            proof = proof_data.get(call.data)
            if proof: # если передан код для получения доказательства
                # удаляем сообщение в котором предлагали доказательство
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)            
                if proof[0]!="noimage":  # доказательство с картинкой             
                    img = open("imgs/"+proof[0], 'rb')
                    bot.send_photo(call.message.chat.id, img)
                bot.send_message(call.message.chat.id, proof[1].replace('|','\n'))
            elif call.data=="proof_no": # отказ от доказательства
                bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except:
        bot.send_message(call.message.chat.id, error_msg)
    # фиксируем окончание обработки
    bot.answer_callback_query(call.id)
    
# Получение сообщений от юзера
@bot.message_handler(content_types=["text"])
def handle_text(message):
    print("handle_text_" + message.text)
    try:
        msgtext = message.text.strip()
        if msgtext == capybara_msg: # показываем фотографию капибары, выбранную случайным образом
            i_img = randint(1, len(img_arr))-1
            bot.send_photo(message.chat.id, img_arr[i_img])
            bot.send_message(message.chat.id, smile_msg)
        else:
            if msgtext.lower() == "привет":
                bot.send_message(message.chat.id,hello_msg)
            else :
                answ = answer(message.text)
                answ_cnt = len(answ)
                
                # если ничего не нашли пробуем "сменить раскладку" запроса
                if answ_cnt<=0:
                    trans_text = msgtext.translate(layout)
                    answ = answer(trans_text)
                    answ_cnt = len(answ)
                    
                keyboard = types.InlineKeyboardMarkup()
                
                # формируем inline меню по найденным подходящим ответам
                for x in answ:
                    # Пример элемента x (['Две прямые, имеющие общую точку, называют пересекающимися.', '0002'], 35, '0002')
                    u_btn = types.InlineKeyboardButton(g_data.get(x[2])[0], callback_data=x[2])
                    keyboard.add(u_btn)
                
                if answ_cnt>0:        
                    bot.send_message(message.chat.id, result_msg, reply_markup=keyboard) 
                else:
                    bot.send_message(message.chat.id, notfound_msg)
    except:
        bot.send_message(message.chat.id, error_msg)

# загружаем в массив ссылки на картинки
img_arr = readPicture("pictures.txt")
# загружаем в словарь теорию
g_data = readData("data.txt")
#загружаем доказательства
proof_data = readData("proof.txt")
# Запускаем бота
bot.polling(none_stop=True, interval=0)