import importlib
import time
import threading
import sqlite3
import sys
import os

# from updynamic import UploaderDynamic
sys.path.append(os.path.abspath('./Bilibili-dynamic'))
from config import DB_PATH
from constants import MESSAGES
from bot_controller import BotController
from command_controller import CommandController
from utilities import print_stack_trace
UploaderDynamic = importlib.import_module(
    'Bilibili-dynamic.updynamic').UploaderDynamic
DynamicParser = importlib.import_module('Bilibili-dynamic.dynamic_parser').DynamicParser


class Bot:
    def __init__(self, api_token):
        self.api_token = api_token
        self.subscription_table = {} # {uploader_uid: [chat_id, chat_id, ...]}
        self.updynamic_table = {} # {uploader_uid: UploaderDynamic}
        self.db = sqlite3.connect(DB_PATH)
        self.db_cursor = self.db.cursor()
        self.refresh_required = False
        # self.bot_controller = BotController(api_token)
        # self.command_controller = CommandController(self, self.bot_controller)
        try:
            self.refresh()
        except Exception as e:
            print('Exception at Bot.__init__')
            print_stack_trace(e)

    def start(self):
        threading.Thread(target=self._dynamic_thread_runner).start()
        threading.Thread(target=self._updates_thread_runner).start()
    
    def refresh(self):
        self._reload_subscription_table()
        self.refresh_required = True

    def _dynamic_thread_runner(self):
        while True:
            try:
                dynamic_thread = threading.Thread(target=self._dynamic_polling)
                dynamic_thread.start()
                dynamic_thread.join()
            except Exception as e:
                print('Exception at Bot._dynamic_thread_runner, thread dead')
                print_stack_trace(e)
                self.updynamic_table = {}
                self.refresh()
                continue
    
    def _updates_thread_runner(self):
        while True:
            try:
                updates_thread = threading.Thread(target=self._updates_processing)
                updates_thread.start()
                updates_thread.join()
            except Exception as e:
                print('Exception at Bot._updates_thread_runner, thread dead')
                print_stack_trace(e)
                continue

    def _updates_processing(self):
        bot_controller = BotController(self.api_token)
        while True:
            try:
                updates = bot_controller.get_updates()
            except Exception as e:
                print('Exception at Bot._updates_processing, after bot_controller.get_updates()')
                print_stack_trace(e)
                time.sleep(10)
                continue
            if not updates['ok']:
                print(updates)
                time.sleep(10)
                continue
            if not len(updates['result']) > 0:
                continue
            for update in updates['result']:
                try:
                    threading.Thread(target=self._updates_single, args=(update,)).start()
                except Exception as e:
                    print('Exception at Bot._updates_processing, after Bot._updates_single')
                    print_stack_trace(e)
            time.sleep(0.3)

    def _updates_single(self, update):
        bot_controller = BotController(self.api_token)
        command_controller = CommandController(self, bot_controller)
        command_controller.process_command(update)

    def _dynamic_polling(self):
        bot_controller = BotController(self.api_token)
        while True:
            print('polling...')
            if self.refresh_required:
                self.refresh_required = False
                for i in range(0, len(self.updynamic_table)):
                    updynamic = self.updynamic_table[i]
                    try:
                        updynamic.refresh_info()
                    except Exception as e:
                        print('Exception at Bot._dynamic_polling, after updynamic.refresh_info()')
                        print_stack_trace(e)
                        if updynamic is not None:
                            self.updynamic_table[i] = new = UploaderDynamic(updynamic.uploader_uid)
                        else:
                            print('updynamic is None')

            for uploader_uid in self.subscription_table.keys():
                if not uploader_uid in self.updynamic_table.keys():
                    self.updynamic_table[uploader_uid] = UploaderDynamic(uploader_uid, cache_resource=False, fetch=False)
                try:
                    updates = self.updynamic_table[uploader_uid].get_update()
                except Exception as e:
                    print('Exception at Bot._dynamic_polling')
                    print_stack_trace(e)
                    self.updynamic_table[uploader_uid] = UploaderDynamic(uploader_uid, cache_resource=False, fetch=False)
                    updates = self.updynamic_table[uploader_uid].get_update()
                if len(updates) > 0:
                    for update in updates:
                        self._broadcast_dynamic(bot_controller, update, self.subscription_table[uploader_uid])
            time.sleep(30)

    def _broadcast_dynamic(self, bot_controller, dynamic, chat_ids):
        text = '<b>{}</b>\n\n'.format(MESSAGES.NOTIFICATION_TITLE)
        text += DynamicParser.html_parser(dynamic)
        for chat_id in chat_ids:
            try:
                response = bot_controller.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
                print(response)
            except Exception as e:
                print('Exception at Bot._broadcast_dynamic')
                print_stack_trace(e)

    def _reload_subscription_table(self):
        print('reload subscription table...')
        db = sqlite3.connect(DB_PATH)
        db_cursor = db.cursor()
        self.subscription_table = {}
        subscriptions = db_cursor.execute('''SELECT "chat_id", "uploader_uid" FROM "subscriptions" WHERE "is_active"=1;''').fetchall()
        for subscription in subscriptions:
            print(subscription)
            chat_id = subscription[0]
            uploader_uid = subscription[1]
            if not uploader_uid in self.subscription_table.keys():
                self.subscription_table[uploader_uid] = [chat_id]
            else:
                self.subscription_table[uploader_uid].append(chat_id)
        print(self.subscription_table)
