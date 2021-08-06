import sys
import os
import sqlite3
import importlib

from bot import Bot
from config import DB_PATH, API_TOKEN


def init_db(database_file='bot_data.db'):
    db = sqlite3.connect(database_file)
    db_cursor = db.cursor()
#   db_cursor.execute('''CREATE TABLE "uploaders" (
#                           "uid"	INTEGER NOT NULL UNIQUE,
#                           "is_active"	INTEGER NOT NULL,
#                           PRIMARY KEY("uid")
#                        );''')
    db_cursor.execute('''CREATE TABLE "subscriptions" (
                            "id"	INTEGER NOT NULL UNIQUE,
                            "chat_id"	INTEGER NOT NULL,
                            "uploader_uid"	TEXT NOT NULL,
                            "is_active"	INTEGER NOT NULL,
                            PRIMARY KEY("id" AUTOINCREMENT)
                        );''')
    db_cursor.execute('''CREATE TABLE "bots" (
                            "id"	INTEGER NOT NULL UNIQUE,
                            "offset"	INTEGER NOT NULL,
                            PRIMARY KEY("id")
                        );''')
    db.commit()
    db.close()


if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        init_db(database_file=DB_PATH)
    bot = Bot(API_TOKEN)
    bot.start()
