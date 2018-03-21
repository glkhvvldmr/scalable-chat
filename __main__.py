from tornado import web, ioloop, options
from tornado.httpserver import HTTPServer
from conf import settings
import handlers


class Application(web.Application):
    def __init__(self):
        h = [
            (r"/login", handlers.LoginHandler),
            (r"/logout", handlers.LogoutHandler),
            (r"/chat", handlers.ChatSocketHandler),
        ]
        super(Application, self).__init__(handlers=h, **settings)


def main():
    options.parse_command_line()
    app = Application()
    server = HTTPServer(app)
    # single thread && single process
    server.listen(8888)

    loop = ioloop.IOLoop.current()
    loop.start()


if __name__ == "__main__":
    main()
