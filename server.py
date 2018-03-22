import handlers

from tornado import web, ioloop
from tornado.options import define, options
from tornado.httpserver import HTTPServer
from conf import settings


class Application(web.Application):
    def __init__(self):
        h = [
            (r"/login", handlers.LoginHandler),
            (r"/logout", handlers.LogoutHandler),
            (r"/chat", handlers.ChatSocketHandler),
        ]
        super(Application, self).__init__(handlers=h, **settings)


def main():
    define("port", default=8888, help="port to listen on for server")
    define("redis_host", default='localhost', help="redis server host")
    define("redis_port", default=6379, help="redis server port")

    options.parse_command_line()
    app = Application()
    server = HTTPServer(app)
    # single thread && single process
    server.listen(options.port)

    loop = ioloop.IOLoop.current()
    loop.start()


if __name__ == "__main__":
    main()
