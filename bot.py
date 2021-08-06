import importlib
import time
import threading
import sqlite3


# sys.path.append(os.path.abspath('./Bilibili-dynamic'))
# from updynamic import UploaderDynamic
from config import DB_PATH
from bot_controller import BotController
from command_controller import CommandController
UploaderDynamic = importlib.import_module(
    'Bilibili-dynamic.updynamic').UploaderDynamic


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
            print(e)

    def start(self):
        while True:
            try:
                dynamic_thread = threading.Thread(target=self._dynamic_polling)
                updates_thread =  threading.Thread(target=self._updates_processing)
                dynamic_thread.start()
                updates_thread.start()
                dynamic_thread.join()
                updates_thread.join()
            except Exception as e:
                print(e)
                continue
    
    def refresh(self):
        self._reload_subscription_table()
        self.refresh_required = True

    def _updates_processing(self):
        bot_controller = BotController(self.api_token)
        command_controller = CommandController(self, bot_controller)
        while True:
            try:
                updates = bot_controller.get_updates()
            except Exception as e:
                print(e)
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
                    command_controller.process_command(update)
                except Exception as e:
                    print(e)
            time.sleep(1)

    def _dynamic_polling(self):
        bot_controller = BotController(self.api_token)
        while True:
            print('polling...')
            print(self.subscription_table)
            if self.refresh_required:
                self.refresh_required = False
                for updynamic in self.updynamic_table.values():
                    updynamic.refresh_info()
            for uploader_uid in self.subscription_table.keys():
                if not uploader_uid in self.updynamic_table.keys():
                    self.updynamic_table[uploader_uid] = UploaderDynamic(uploader_uid)
                updates = self.updynamic_table[uploader_uid].get_update()
                if len(updates) > 0:
                    for update in updates:
                        self._broadcast_dynamic(bot_controller, update, self.subscription_table[uploader_uid])
            time.sleep(10)

    def _broadcast_dynamic(self, bot_controller, dynamic, chat_ids):
        for chat_id in chat_ids:
            try:
                bot_controller.send_message(chat_id=chat_id, text=str(dynamic))
            except Exception as e:
                print(e)

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
