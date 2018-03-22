import logging
import datetime
import aioredis
import asyncio
import json

from tornado import web, websocket, escape
from tornado.options import options
from tornado.escape import native_str

logger = logging.getLogger('handlers')
# logger.disabled = True
REDIS_PUB_SUB_CHANNEL = 'chan'


class UserMixin:
    """
    Миксин, добавляет свойство current_user
    """
    @property
    def current_user(self):
        """
        :return: возвращает текущего пользователя, берет из кук
        """
        return native_str(self.get_secure_cookie('user'))


class LoginHandler(UserMixin, web.RequestHandler):
    def post(self):
        """
        Пишет логин в куку, отправляет ответ-приветсвие
        :return:
        """
        data = json.loads(self.request.body.decode('utf-8'))
        self.set_secure_cookie('user', data.get('name'))
        resp = {'msg': 'Hello {user}!'.format(user=data.get('name'))}
        self.write(resp)


class LogoutHandler(UserMixin, web.RequestHandler):
    @web.authenticated
    def get(self):
        """
        Чистит куку, отправляет ответ
        :return:
        """
        self.clear_cookie('user')
        self.write({'msg': 'Success logout!'})


class ChatSocketHandler(UserMixin, websocket.WebSocketHandler):
    async def subscribe_handler(self, ch):
        """
        Корутина, слушает канал в редисе, и отправляет сообщение в вебсокет
        :param ch:
        :return:
        """
        while await ch.wait_message():
            try:
                msg = await ch.get_json()
                await self.write_message(msg)
            except Exception as e:
                logger.error('USER {} throws exception {}'.format(self.current_user, e))

    @staticmethod
    def get_redis_conn_string():
        return '{scheme}://{host}:{port}'.format(scheme='redis', host=options.redis_host, port=options.redis_port)

    @web.authenticated
    async def open(self, *args, **kwargs):
        """
        При открытии вебсокета откарывает pub sub соедения с редисом, подписывается на канал и активирует subscribe_handler
        :param args:
        :param kwargs:
        :return:
        """
        self.log('JOINED')
        self.pub = await aioredis.create_redis(self.get_redis_conn_string())
        self.sub = await aioredis.create_redis(self.get_redis_conn_string())
        res = await self.sub.subscribe(REDIS_PUB_SUB_CHANNEL)
        ch1 = res[0]
        tsk = asyncio.ensure_future(self.subscribe_handler(ch1))
        await tsk

    @web.authenticated
    def on_close(self):
        """
        При закрытии вебсокета отписывается от канала редиса и закрывает pub/sub соединения
        :return:
        """
        self.log('LEFT')
        self.sub.unsubscribe(REDIS_PUB_SUB_CHANNEL)
        self.sub.close()
        self.pub.close()

    @web.authenticated
    async def on_message(self, message):
        """
        При получении сообщения от вебсокета публикует его в канал редиса
        :param message:
        :return:
        """
        parsed = escape.json_decode(message)
        logger.warning('GOT MESSAGE %s' % parsed)

        chat = {
            'msg': parsed['msg'],
            'user': parsed['user'],
            'time': datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y')
            }

        await self.pub.publish_json(REDIS_PUB_SUB_CHANNEL, chat)

    def log(self, event):
        logger.info('USER {} {}'.format(self.current_user, event))

