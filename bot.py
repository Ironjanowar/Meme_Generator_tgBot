import telebot
import requests
import json
import shutil
import os
import sys

# Listener


def listener(messages):
    # When new messages arrive TeleBot will call this function.
    for m in messages:
        if m.content_type == 'text':
            # Prints the sent message to the console
            if m.chat.type == 'private':
                print("Chat -> " + str(m.chat.first_name) +
                      " [" + str(m.chat.id) + "]: " + m.text)
        else:
            print("Group -> " + str(m.chat.title) +
                  " [" + str(m.chat.id) + "]: " + m.text)

# Funicones


def update_memes():
    # Update the meme file
    r = requests.get("https://api.imgflip.com/get_memes")
    request_json = r.json()
    with open('./request.json', 'w') as json_file:
        json.dump(request_json, json_file)


def get_meme_id(name, memes):
    # Returns the id of the meme named 'name'
    for meme in memes:
        if meme['name'] == name:
            return str(meme['id'])


def get_meme_list(memes):
    # Get a list of names of memes
    meme_list = []
    for meme in memes:
        meme_list.append(meme['name'])
    return meme_list


def get_meme_id_list(memes):
    # Get a list of names of memes
    meme_list = []
    for meme in memes:
        meme_list.append(meme['id'])
    return meme_list


def get_meme_string(memes):
    # Get a string of names of memes with their IDs
    meme_list = ""
    for meme in memes:
        meme_list += meme['name'] + " -> ID: " + meme['id'] + "\n"
    return meme_list


def isAdmin_fromPrivate(message):
    if message.chat.type == 'private':
        userID = message.from_user.id
        if str(userID) in admins:
            return True
    return False


def help_message():
    commands = {
        'newmeme': "Crea un meme. \"/newmeme [id | nombre]\" o \"/newmeme\" escribiendo después [id | nombre]\n",
        'memelist': "Muestra los distintos memes disponibles con sus IDs\n",
        'start': "Empieza el bot\n",
        'help': "Muestra esta ayuda\n",
        'cancel': "Cancela el proceso de crear meme en cualquier punto\n"
    }
    message = "Estos son los comandos disponibles:\n\n"
    for key in commands.keys():
        message += "- /" + key + " -> " + commands[key]
    return message

# Creamos el bot
with open('./bot.token', 'r') as TOKEN:
    bot = telebot.TeleBot(TOKEN.readline().strip())

# Cargamos los administradores
with open('./data/admins.json', 'r') as adminData:
    admins = json.load(adminData)

# Inicializamos el listener
bot.set_update_listener(listener)

# Preparamos el json de memes
with open('./data/request.json', 'r') as json_memes:
    full_json = json.load(json_memes)
    global memes
    memes = full_json['data']['memes']

# Login en imgflip
with open('./data/api_login.json', 'r') as json_login:
    full_json = json.load(json_login)
    global api_username
    api_username = full_json['username']
    global api_pass
    api_pass = full_json['pass']

# imgflip.com API URL
global url
url = "https://api.imgflip.com/caption_image"

# User tracking
global users_tracked
users_tracked = {}

# Memes que no han sido enviados
global users_memes
users_memes = {}

# Handlers


@bot.message_handler(commands=['cancel'])
def cancel(m):
    uid = m.from_user.id
    users_memes.pop(uid)
    users_tracked.pop(uid)
    bot.reply_to(m, "Cancelado!")


@bot.message_handler(commands=['newmeme'])
def create_meme(m):
    uid = m.from_user.id
    if len(m.text.split()) == 1:
        bot.reply_to(m, "¿Cuál es el nombre o ID del meme que quieres crear?")
        users_memes[uid] = {}
        users_tracked[uid] = 0
    else:
        meme = m.text.split(' ', 1)[1]
        if meme in get_meme_list(memes) or meme in get_meme_id_list(memes):
            users_tracked[uid] = 1
            users_memes[uid] = {}
            users_memes[uid]['template_id'] = get_meme_id(meme, memes) if meme in get_meme_list(memes) else int(meme)
            users_memes[uid]['username'] = api_username
            users_memes[uid]['password'] = api_pass
            bot.reply_to(m, "Okkay! Mandame lo que quieres que aparezca en el texto de arriba.\nSi solo quieres texto de abajo escribe /abajo")
        else:
            reply = "\"" + meme + "\" no es un meme que esté disponible.\nPrueba /memelist para ver los memes disponibles."
            bot.reply_to(m, reply)


@bot.message_handler(func=lambda m: m.from_user.id in users_tracked.keys() and users_tracked[m.from_user.id] == 0)
def create_meme_step0(m):
    meme = m.text
    uid = m.from_user.id
    if meme in get_meme_list(memes) or meme in get_meme_id_list(memes):
        users_memes[uid]['template_id'] = get_meme_id(meme, memes) if meme in get_meme_list(memes) else int(meme)
        users_memes[uid]['username'] = api_username
        users_memes[uid]['password'] = api_pass
        bot.reply_to(m, "Okkay! Mandame lo que quieres que aparezca en el texto de arriba.\nSi solo quieres texto de abajo escribe /abajo")
        users_tracked[uid] = 1
    else:
        reply = "\"" + meme + "\" no es un meme que esté disponible."
        bot.reply_to(m, reply)


@bot.message_handler(func=lambda m: m.from_user.id in users_tracked.keys() and users_tracked[m.from_user.id] == 1)
def create_meme_step1(m):
    upper_text = m.text
    uid = m.from_user.id
    if m.text == "/abajo":
        users_memes[uid]['text0'] = ""
        bot.send_message(m.chat.id, "En ese caso, escribe lo que quieras que aparezca solo abajo.")
    else:
        users_memes[uid]['text0'] = upper_text
        bot.send_message(m.chat.id, "Bien! Ahora lo que quieres que aparezca abajo.")
    users_tracked[uid] = 2


@bot.message_handler(func=lambda m: m.from_user.id in users_tracked.keys() and users_tracked[m.from_user.id] == 2)
def create_meme_step2(m):
    lower_text = m.text
    uid = m.from_user.id
    users_memes[uid]['text1'] = lower_text
    users_tracked.pop(uid)
    post = users_memes[uid]
    meme_to_send = requests.post(url, data=post).json()
    image_url = meme_to_send['data']['url']
    response = requests.get(image_url, stream=True)
    image_name = str(uid) + ".jpg"
    with open(image_name, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
        del response

    bot.send_message(m.chat.id, "Aqui esta tu nuevo meme!")
    bot.send_photo(m.chat.id, open(image_name, 'rb'))
    users_memes.pop(uid)
    os.remove(image_name)


@bot.message_handler(commands=['memelist'])
def send_meme_list(m):
    bot.send_message(m.chat.id, "Estos son los memes disponibles:\n\n" + get_meme_string(memes) + "\n\nhttps://imgflip.com/memetemplates")


@bot.message_handler(commands=['help'])
def help(m):
    bot.send_message(m.chat.id, help_message())


@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "Hey! Este es un bot para crear tus propios memes!\n\nHecho por @CesharPaste\n\nLink: https://github.com/Ironjanowar/Meme_Generator_tgBot")

# Only admins!!


@bot.message_handler(commands=['update'])
def auto_update(message):
    if isAdmin_fromPrivate(message):
        bot.reply_to(message, "Reiniciando..\n\nPrueba algun comando en 10 segundos")
        print("Updating..")
        sys.exit()
    else:
        bot.reply_to(message, "Este comando es solo para admins y debe ser enviado por privado")


# Ignoramos los mensajes anteriores
bot.skip_pending = True


# Corremos el bot
print("Running...")
bot.polling()
