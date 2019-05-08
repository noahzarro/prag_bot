import json
import requests
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters


# create Bot
with open("token.json","r") as read_file:
    TOKEN = json.load(read_file)[0]
updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher

# load people
people = []
with open("people.json", "r") as read_file:
    people = json.load(read_file)

admin_ids = [186885633]

# next actions
next_actions = {}

# last post
last_post = {}

# posts to review
to_review = []
with open("to_review.json", "r") as read_file:
    to_review = json.load(read_file)

# posted posts
posted = []
with open("posted.json", "r") as read_file:
    posted = json.load(read_file)

# discarded posts
discarded = []
with open("discarded.json", "r") as read_file:
    discarded = json.load(read_file)

# current reviewed
current_review = {}

# post ids
post_id = 0


def write_to_review():
    with open("to_review.json", "w") as write_file:
        json.dump(to_review, write_file)


def write_posted():
    with open("posted.json", "w") as write_file:
        json.dump(posted, write_file)


def write_discarded():
    with open("discarded.json", "w") as write_file:
        json.dump(discarded, write_file)


def send_to_server():
    url = "http://people.ee.ethz.ch/~zarron/prag/blog_api_send.php"

    # load passwort
    with open("password.json", "r") as read_file:
        password = json.load(read_file)[0]

    with open("posted.json", "r") as read_file:
        payload_string = json.dumps(json.load(read_file))

    payload = {"load": payload_string, "password": password}

    try:
        r = requests.post(url, data=payload)
        #print(r.text)
    except:
        print("failed")


def start(bot, update):
    if update.message.from_user.id in people:
        bot.send_message(update.message.from_user.id, text="Welcome back")
    else:
        bot.send_message(update.message.from_user.id, text="Hi " + update.message.from_user.first_name)
        people.append(update.message.from_user.id)
        with open("people.json", "w") as write_file:
            json.dump(people, write_file)


def new_post(bot, update):
    bot.send_message(update.message.from_user.id, text="Send me the text to post")
    next_actions[update.message.from_user.id] = "new_post"


def answer_handler(bot, update):
    next_action = next_actions[update.message.from_user.id]
    next_actions[update.message.from_user.id] = ""

    if next_action == "new_post":
        localtime = time.asctime( time.localtime(time.time()) )
        global post_id
        post_id = post_id + 1
        new_post = {"id": post_id, "user_id": update.message.from_user.id, "name": update.message.from_user.first_name, "content": update.message.text, "time": localtime, "photo": []}
        to_review.append(new_post)
        bot.send_message(update.message.from_user.id, text="Thanks for your post, it will be reviewed")
        write_to_review()
        return

    bot.send_message(update.message.from_user.id, text="Use a command!")


def add_photo(bot, update):
    if update.message.from_user.id in last_post:
        for i in range(0, len(to_review)):
            if to_review[i]["id"] == last_post[update.message.from_user.id]:
                print("gitter")
                #to_review[i]["photo"][] = #photo file path
    else:
        bot.send_message(update.message.from_user.id, text="Send a photo first, fagitoli")


def photo_handler(bot, update):
    print("got photo")


def review(bot, update):
    if update.message.from_user.id in admin_ids:
        if len(to_review) != 0:
            current_review[update.message.from_user.id] = to_review.pop(0)
            text = current_review[update.message.from_user.id]["content"]
            # setup answer buttons
            keyboard = []
            row1 = []
            row1.append(InlineKeyboardButton("accept", callback_data="{} {}".format("review", "accept")))
            row1.append(InlineKeyboardButton("discard", callback_data="{} {}".format("review", "discard")))
            row1.append(InlineKeyboardButton("view later", callback_data="{} {}".format("review", "later")))
            keyboard.append(row1)
            bot.send_message(chat_id=update.message.chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))
            write_to_review()
        else:
            bot.send_message(update.message.from_user.id, text="No posts to review")
    else:
        bot.send_message(update.message.from_user.id, text="Ur no admin, fagitoli")


def inline_handler(bot, update):
    query = update.callback_query
    action = query.data.split(" ")[0]
    value = query.data.split(" ")[1]

    bot.deleteMessage(chat_id=query.message.chat_id, message_id=query.message.message_id)

    if action == "review":
        current = current_review[query.message.chat_id]
        del current_review[query.message.chat_id]
        bot.send_message(query.message.chat_id, text=current["content"])
        if value == "accept":
            posted.append(current)
            bot.send_message(query.message.chat_id, text="Post posted")
            poster_id = current["user_id"]
            bot.send_message(poster_id, text="Your post has been reviewed and is now posted")
            write_posted()
            send_to_server()

        if value == "discard":
            discarded.append(current)
            bot.send_message(query.message.chat_id, text="Post discarded")
            poster_id = current["user_id"]
            bot.send_message(poster_id, text="Your post is crap and was now discarded")
            write_discarded()

        if value == "later":
            to_review.append(current)
            write_to_review()


# register command handler
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('review', review))
dispatcher.add_handler(CommandHandler('new', new_post))

# register handler for plain messages
dispatcher.add_handler(MessageHandler(Filters.text, answer_handler))

# register handler for photo messages
dispatcher.add_handler(MessageHandler(Filters.photo, photo_handler))

# register inline query handler
updater.dispatcher.add_handler(CallbackQueryHandler(inline_handler))

telegramBot = updater.bot
updater.start_polling()