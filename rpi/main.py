import serial 
import asyncio
import tornado.web
import tornado.websocket
import os
import json
import datetime

import random
from serial_asyncio import open_serial_connection

class Store(object):
    def __init__(self, name):
        self.name = name.strip()
        self._store = {}
        self.buffer = []
        self.filename = "data_%s.json" % self.name
        print("store for %s created" % self.name)

    def load(self):
        pass

    def save(self, entry):
        pass

    def insert(self, sensor_value, now=None):
        pass

class DefaultHandler(tornado.web.RequestHandler):
    def initialize(self, manager):
        self.manager = manager
    def get(self):
        self.render("index2.html")

class LiveSocket(tornado.websocket.WebSocketHandler):
    clients = set()
    def initialize(self, manager):
        self.manager = manager

    def open(self):
        LiveSocket.clients.add(self)

    def on_message(self, message):
        # self.write_message(u"You said: " + message)
        print("got", message)

    def on_close(self):
        LiveSocket.clients.remove(self)

    @classmethod
    def send_message(cls, message: str):
        # print(f"Sending message {message} to {len(cls.clients)} client(s).")
        for client in cls.clients:
            client.write_message(message)


class Application(tornado.web.Application):
    def __init__(self, manager):
        handlers = [
            (r"/ws", LiveSocket, dict(manager=manager)),
            (r'/favicon.ico', tornado.web.StaticFileHandler),
            (r'/static/', tornado.web.StaticFileHandler),
            (r"/.*", DefaultHandler, dict(manager=manager)),

        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "html"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/auth/login",
            debug=True,
        )
        super(Application, self).__init__(handlers, **settings)


class Serial:
    async def setup(self):
        self.reader, self.writer = await open_serial_connection(url='/dev/ttyACM0')
    async def run(self):
        while True:
            line = await self.reader.readline()
            msg = str(line.strip(), 'utf-8')
            try:
                number = float(msg)
                LiveSocket.send_message(msg)
                print(msg)
            except ValueError:
                print("bad value: %s" % msg)
            # print(msg)
    async def send(self, string):
        self.writer.write(string.encode("utf-8"))
        await self.writer.drain()
    async def periodic(self):
        # await self.send("oxxxx\r\n")
        await asyncio.sleep(1)
        asyncio.create_task(self.periodic())

async def main():
    manager = Store("filename")
    app = Application(manager)
    app.listen(8080)

    ser = Serial()
    await ser.setup()
    asyncio.create_task(ser.periodic())
    await ser.run()
    
    shutdown_event = asyncio.Event()
    await shutdown_event.wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("exiting")



