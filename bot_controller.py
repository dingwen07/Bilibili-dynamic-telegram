import requests
import sqlite3

from constants import API_BASE_URL
from config import DB_PATH


class BotController:
    def __init__(self, api_token):
        self.api_token = api_token
        self.db = sqlite3.connect(DB_PATH)
        self.db_cursor = self.db.cursor()
        get_me_response = self.get_me()
        self.authorization_succeed = get_me_response['ok']
        if self.authorization_succeed:
            self.id = get_me_response['result']['id']
            bot = self.db_cursor.execute(
                'SELECT * FROM bots WHERE id=?', (self.id,)).fetchone()
            if bot is None:
                self.offset = 0
                self.db_cursor.execute(
                    'INSERT INTO bots VALUES (?, ?)', (self.id, self.offset))
            else:
                self.offset = bot[1]
            self.db.commit()    
        else:
            raise Exception('Authorization failed')

    def get_me(self):
        return self.invoke_api(self.api_token, 'getMe', {})

    def get_updates(self, offset=None, limit=None, timeout=None, allowed_updates=None):
        if offset is None:
            offset = self.offset
        data = {'offset': offset}
        if not limit is None:
            data['limit'] = limit
        if not timeout is None:
            data['timeout'] = timeout
        if not allowed_updates is None:
            data['allowed_updates'] = allowed_updates
        response = self.invoke_api(self.api_token, 'getUpdates', data)
        if response['ok'] and response['result']:
            self._update_offset(response['result'][-1]['update_id'] + 1)
        return response

    def send_message(self, chat_id, text, parse_mode='', disable_web_page_preview=False, disable_notification=False,
                     reply_to_message_id=None, reply_markup=None):
        data = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode,
                'disable_web_page_preview': disable_web_page_preview,
                'disable_notification': disable_notification}
        if not reply_to_message_id is None:
            data['reply_to_message_id'] = reply_to_message_id
        if not reply_markup is None:
            data['reply_markup'] = reply_markup
        return self.invoke_api(self.api_token, 'sendMessage', data)

    def _update_offset(self, offset=0):
        self.offset = offset
        self.db_cursor.execute('''UPDATE "main"."bots" SET "offset"=? WHERE "id"=?;''', (self.offset, self.id))
        self.db.commit()

    @staticmethod
    def invoke_api(api_token, api_method, data):
        request_url = API_BASE_URL.format(api_token, api_method)
        response = requests.post(request_url, json=data)
        return response.json()
