import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

import wave
import numpy as np
import json

SAMPLE_SIZE = 2
SAMPLE_RATE = 48000
PATH = '/home/pi/work/tornado/output.wav'

# https://qiita.com/ninomiyt/items/001b496e067ebf216384
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    # https://qiita.com/Hironsan/items/b9375e110dbb9bde7650
    waiters = set()
    logs = []
    def check_origin(self, origin):
        return True
    def open(self, *args, **kwargs):
        print("opened")
        self.waiters.add(self)
        self.write_message({'logs': self.logs})
        self.voice = []

    def on_message(self, message):
        print(f"on_message: {len(self.voice)}")
        #message = json.loads(message)
        #self.logs.append(message)
        self.voice.append(np.frombuffer(message, dtype='float32'))

    def on_close(self):
        print("on_close")
        self.waiters.remove(self)
        v = np.array(self.voice)
        v.flatten()

        # バイナリに16ビットの整数に変換して保存
        arr = (v * 32767).astype(np.int16)
        with wave.open(PATH, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(SAMPLE_SIZE)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(arr.tobytes('C'))
        
        self.voice.clear()
        print("closed")

class MyHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('test_ws.html')

if __name__ == "__main__":
    app = tornado.web.Application([
        (r"/", MyHandler),
        (r"/websocket", WebSocketHandler)
    ])

    print("0")
    http_server = tornado.httpserver.HTTPServer(app, ssl_options={
        "certfile": "web-server.crt",
        "keyfile":  "web-server.key",
    })

    print("1")
    http_server.listen(8000)
    #app.listen(8000)
    print("2")
    #tornado.ioloop.IOLoop.current().start()
    tornado.ioloop.IOLoop.instance().start()
    print("3")

