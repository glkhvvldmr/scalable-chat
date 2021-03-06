import aiohttp
import asyncio
import json
import sys
import argparse

DEFAULT_SERVER_HOST = 'localhost'
DEFAULT_SERVER_PORT = 8888


class InputReader:
    """
    организует асинхронный ввод
    """
    def __init__(self):
        self.queue = asyncio.Queue()
        asyncio.get_event_loop().add_reader(sys.stdin, self._stdin)

    def _stdin(self):
        """
        Коллбэк для ассинхоронного чтения stdin
        """
        data = sys.stdin.readline()
        asyncio.async(self.queue.put(data))

    async def input(self):
        """
        Корутина асинхронно читает stdin
        :return: stdin без последнего перевода строки
        """
        msg = await self.queue.get()
        return msg[:-1]


class ChatClient:
    def __init__(self, host=None, port=None):
        self.user_name = ''
        self.session = None
        self.ws = None
        self.ir = InputReader()
        self.host = host or DEFAULT_SERVER_HOST
        self.port = port or DEFAULT_SERVER_PORT

    def _get_url(self, route):
        """
        Получить url
        :param route: маршрут
        :return: url
        """
        return '{scheme}://{host}:{port}/{route}'.format(scheme='http', host=self.host, port=self.port, route=route)

    async def _ws_conn_init(self):
        """
        Инициализирует соедение по вебсокету
        """
        self.ws = await self.session.ws_connect(self._get_url('chat'))

    def _session_init(self):
        """
        Инициализирует сессию
        """
        self.session = aiohttp.ClientSession()

    async def _logout_handler(self):
        """
        Обрабатывает команду logout()
        :return:
        """
        if not self.user_name:
            print('You already logout. If you want login press login()')
            return

        logout_response = await self.session.request(self._get_url('logout'))
        resp = await logout_response.json()
        print(resp['msg'])
        self.user_name = ''
        print('If you want login press login()')


    async def _exit_handler(self):
        """
        Обрабатывает команду exit()
        :return:
        """
        await self.ws.close()
        print('WebSocket closed')
        try:
            await asyncio.get_event_loop().stop()
        except:
            pass
        finally:
            print('Asyncio eventloop stopped')

    async def _login(self):
        if self.user_name:
            print('{user_name}, you already logged in. If you want logout press logout()'.format(user_name=self.user_name))
            return
        print('Enter login:')
        self.user_name = await self.ir.input()

        login_response = await self.session.request('post',
                                                    self._get_url('login'),
                                                    data=json.dumps({'name': self.user_name}),
                                                    headers={'Content-Type': 'application/json'})
        resp = await login_response.json()
        print(resp['msg'])

    async def init(self):
        """
        Инициализирует чат
        """

        self._session_init()
        await self._login()
        await self._ws_conn_init()

        print('Now you can chat! If you want exit, press exit(). if you want logout press logout().')

    async def subscribe_task(self):
        """
        Получает сообщения от чат сервера и выводит их
        :return:
        """
        while True:
            ws_msg = await self.ws.receive()
            data = json.loads(ws_msg.data)
            print('{time} {user}: {msg}'.format(time=data['time'],
                                                user=data['user'],
                                                msg=data['msg']))

    async def stdin_listener(self):
        """
        Получает сообщение из stdin и отправляет в вебсокет
        :return:
        """
        while True:
            msg = await self.ir.input()

            if msg == 'exit()':
                await self._exit_handler()
            elif msg == 'logout()':
                await self._logout_handler()
            elif msg == 'login()':
                await self._login()
            elif msg:
                # не пропустим пустые сообщения
                await self.ws.send_str(json.dumps({"msg": msg, "user": self.user_name}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chat server host port')
    parser.add_argument('-host', help='server host', type=str, dest='host')
    parser.add_argument('-port', help='server port', type=int, dest='port')

    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    chat = ChatClient(args.host, args.port)

    loop.run_until_complete(chat.init())
    tasks = [
        asyncio.Task(chat.stdin_listener()),
        asyncio.Task(chat.subscribe_task())
    ]

    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
