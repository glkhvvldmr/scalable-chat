import logging
import datetime

from tornado import web, websocket, escape
import aioredis
import asyncio
import json

logger = logging.getLogger('handlers')
# logger.disabled = True


class UserMixin:
    @property
    def current_user(self):
        return str(self.get_secure_cookie('user'))


class LoginHandler(UserMixin, web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body.decode('utf-8'))
        self.set_secure_cookie('user', data.get('name'))
        resp = {'msg': 'Hello {user}!'.format(user=data.get('name'))}
        self.write(resp)


class LogoutHandler(UserMixin, web.RequestHandler):
    @web.authenticated
    def get(self):
        self.clear_cookie('user')
        self.write({'msg': 'Success logout!'})


class ChatSocketHandler(UserMixin, websocket.WebSocketHandler):
    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    async def subscribe_handler(self, ch):
        while await ch.wait_message():
            try:
                msg = await ch.get_json()
                self.write_message(msg)
            except Exception as e:
                logger.error('Error sending message', exc_info=True)
                print(123)
                print(e)

    async def open(self, *args, **kwargs):
        self.log('JOINED')
        self.pub = await aioredis.create_redis('redis://localhost')
        self.sub = await aioredis.create_redis('redis://localhost')
        res = await self.sub.subscribe('chan')
        ch1 = res[0]
        tsk = asyncio.ensure_future(self.subscribe_handler(ch1))
        await tsk

    def on_close(self):
        self.log('LEFT')
        self.sub.unsubscribe('chan')

        self.sub.close()
        self.pub.close()

    async def on_message(self, message):
        parsed = escape.json_decode(message)
        logger.warning('GOT MESSAGE %s' % parsed)

        chat = {
            'msg': parsed['msg'],
            'user': parsed['user'],
            'time': datetime.datetime.now().strftime('%H:%M:%S %Y-%m-%d')
            }

        await self.pub.publish_json('chan', chat)

    def log(self, event):
        logger.info('USER {} {}'.format(self.current_user, event))

