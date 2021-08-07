API_BASE_URL = 'https://api.telegram.org/bot{}/{}'

class MESSAGES:
    WELCOME = '欢迎使用哔哩哔哩动态推送机器人\!'
    HELP = "可用命令:\n"
    HELP += "/start - Start the bot\n"
    HELP += "/help - 获取帮助\n"
    HELP += "/list - 获取订阅列表\n"
    HELP += "/subscribe &lt;UP主 UID&gt; - 订阅UP主更新\n"
    HELP += "/unsubscribe &lt;订阅ID&gt; - 取消订阅UP主更新, 请通过 /list 查询订阅ID\n"
    SUBS_LIST = "当前订阅的UP主有:\n{}\n\n*如出现UP主昵称更新不及时, 请进行任意订阅/取消操作, 这将刷新UP主昵称*"
    SUBS_LIST_ITEM = '- [<code>{0}</code>] <b><a href="https://space.bilibili.com/{2}">{1}</a></b> (<code>{2}</code>)\n'
    SUBS_EMPTY = "当前没有订阅的UP主"
    SUBS_ADD_OK = "已添加订阅UP主: <b>{}</b>"
    SUBS_ADD_ERR = "添加订阅UP主失败: <b>{}</b>, {}"
    SUBS_EXISTS = "已经订阅该UP主, 订阅ID为: <b>{}</b>"
    SUBS_DEL_OK = "已取消订阅UP主: <b>{}</b>"
    SUBS_DEL_ERR = "取消订阅UP主失败: <b>{}</b>, 请确认订阅ID是否存在且属于您"
    UNKNOWN_COMMAND = "命令无效, 尝试 /help 获取帮助"
    NOTIFICATION_TITLE = '您关注的UP主发送了新的动态'
