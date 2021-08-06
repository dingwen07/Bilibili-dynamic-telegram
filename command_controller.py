import sqlite3
import importlib
from typing import Text

from config import DB_PATH
from constants import MESSAGES
from utilities import print_stack_trace
UploaderDynamic = importlib.import_module(
    'Bilibili-dynamic.updynamic').UploaderDynamic

class CommandController:
    def __init__(self, bot, bot_controller) -> None:
        self.bot = bot
        self.bot_controller = bot_controller
        self.db = sqlite3.connect(DB_PATH)
        self.db_cursor = self.db.cursor()

    def process_command(self, update):
        # print(update)
        if not 'message' in update:
            print('Invalid update:')
            print(update)
            return
        chat_id = update['message']['chat']['id']
        command = update['message']['text'].lower().split()

        if command[0] == "/start":
            print("/start")
            response = self.bot_controller.send_message(chat_id=chat_id, text=MESSAGES.WELCOME, parse_mode="MarkdownV2")
            print(response)
        elif command[0] == "/help":
            print("/help")
            response = self.bot_controller.send_message(chat_id=chat_id, text=MESSAGES.HELP, parse_mode="MarkdownV2")
            print(response)
        elif command[0] == "/list":
            print("/list")
            response = self._list_subscriptions(chat_id)
            print(response)
        elif command[0] == "/subscribe":
            print("/subscribe")
            self._subscribe(chat_id, command)
        elif command[0] == "/unsubscribe":
            print("/unsubscribe")
            self._unsubscribe(chat_id, command)
        else:
            response = self.bot_controller.send_message(chat_id=chat_id, text=MESSAGES.UNKNOWN_COMMAND, parse_mode="MarkdownV2")
            print(response)

    
    def _list_subscriptions(self, chat_id):
        subscriptions = self.db_cursor.execute('''SELECT "id", "uploader_uid" FROM subscriptions WHERE "is_active"=1 AND "chat_id"=?''', (chat_id,)).fetchall()
        if len(subscriptions) == 0:
            self.bot_controller.send_message(chat_id=chat_id, text=MESSAGES.SUBS_EMPTY, parse_mode="MarkdownV2")
        else:
            message_body = ''
            for subscription in subscriptions:
                try:
                    uploader_name = self.bot.updynamic_table[subscription[1]].uploader_name
                except Exception as e:
                    uploader_name = 'Unknown'
                    print_stack_trace(e)
                message_body += MESSAGES.SUBS_LIST_ITEM.format(subscription[0], uploader_name, str(subscription[1]))
            response =  self.bot_controller.send_message(chat_id=chat_id, text=MESSAGES.SUBS_LIST.format(message_body), parse_mode="MarkdownV2", disable_web_page_preview=True)
            return response
    
    def _subscribe(self, chat_id, command):
        if len(command) < 2:
            response = self.bot_controller.send_message(chat_id=chat_id, text=MESSAGES.UNKNOWN_COMMAND, parse_mode="MarkdownV2")
            print(response)
        else:
            try:
                uploader_uid = int(command[1])
                subscription = self.db_cursor.execute('''SELECT "id" FROM subscriptions WHERE "is_active"=1 AND "chat_id"=? AND "uploader_uid"=?''', (chat_id, uploader_uid)).fetchone()
                if not subscription is None:
                    response = self.bot_controller.send_message(chat_id=chat_id, text=MESSAGES.SUBS_EXISTS.format(str(subscription[0])), parse_mode="MarkdownV2")
                    print(response)
                    return
                try:
                    up = UploaderDynamic(uploader_uid, cache_resource=False)
                    print(up)
                    up.refresh_info()
                except Exception as e:
                    print_stack_trace(e)
                    response = self.bot_controller.send_message(chat_id=chat_id, text=MESSAGES.SUBS_ADD_ERR.format(str(uploader_uid), '请确认UP主存在, 并重试'), parse_mode="MarkdownV2")
                    print(response)
                    return
                self.db_cursor.execute('''INSERT INTO subscriptions ("chat_id", "uploader_uid", "is_active") VALUES (?,?,?)''', (chat_id, uploader_uid, 1))
                self.db.commit()
                response = self.bot_controller.send_message(chat_id=chat_id, text=MESSAGES.SUBS_ADD_OK.format(up.uploader_name), parse_mode="MarkdownV2")
                print(response)
                self.bot.refresh()
            except Exception as e:
                print_stack_trace(e)
                response = self.bot_controller.send_message(chat_id=chat_id, text=MESSAGES.SUBS_ADD_ERR.format(str(uploader_uid), '请联系Bot开发者'), parse_mode="MarkdownV2")
                print(response)
                return
    def _unsubscribe(self, chat_id, command):
        if len(command) < 2:
            response = self.bot_controller.send_message(chat_id=chat_id, text=MESSAGES.UNKNOWN_COMMAND, parse_mode="MarkdownV2")
            print(response)
        else:
            try:
                subscription_id = int(command[1])
                subscription = self.db_cursor.execute('''SELECT "id", "uploader_uid" FROM subscriptions WHERE "is_active"=1 AND "chat_id"=? AND "id"=?''', (chat_id, subscription_id)).fetchone()
                if subscription is None:
                    response = self.bot_controller.send_message(chat_id=chat_id, text=MESSAGES.SUBS_DEL_ERR.format(str(subscription_id)), parse_mode="MarkdownV2")
                    print(response)
                    return
                self.db_cursor.execute('''UPDATE subscriptions SET "is_active"=0 WHERE "id"=?''', (subscription_id,))
                self.db.commit()
                try:
                    uploader_name = self.bot.updynamic_table[subscription[1]].uploader_name
                except Exception as e:
                    uploader_name = 'UID:' + str(subscription[1])
                    print_stack_trace(e)
                response = self.bot_controller.send_message(chat_id=chat_id, text=MESSAGES.SUBS_DEL_OK.format(str(uploader_name)), parse_mode="MarkdownV2")
                print(response)
                self.bot.refresh()
            except Exception as e:
                print_stack_trace(e)
                response = self.bot_controller.send_message(chat_id=chat_id, text=MESSAGES.SUBS_DEL_ERR.format(str(subscription_id)), parse_mode="MarkdownV2")
                print(response)
                return
