import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

import wave
import numpy as np
import json
import subprocess
import socket

SAMPLE_SIZE = 2
SAMPLE_RATE = 8000 # 48000
PATH = '/tmp/recv_wav_play.wav'

# https://qiita.com/ninomiyt/items/001b496e067ebf216384
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    # https://qiita.com/Hironsan/items/b9375e110dbb9bde7650
    def check_origin(self, origin):
        return True
    def open(self, *args, **kwargs):
        print("opened")
        self.voice = []

    def on_message(self, message):
        print(f"on_message: {len(self.voice)}")
        #message = json.loads(message)
        self.voice.append(np.frombuffer(message, dtype='float32'))

    def on_close(self):
        print("on_close")
        v = np.array(self.voice)
        v.flatten()
        v = v[::,::6] # 48kHz -> 8kHz
        size = v.shape[1]
        noise = np.random.rand(1, size) - 0.5 # White noise
        v = v * 4 + noise * 0.06

        # バイナリに16ビットの整数に変換して保存
        arr = (v * 32767).astype(np.int16)
        with wave.open(PATH, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(SAMPLE_SIZE)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(arr.tobytes('C'))
        
        self.voice.clear()
        print("closed")

        # Play .wav file
        command = ["play", "-q", PATH]
        subprocess.call(command)

class MyHandler(tornado.web.RequestHandler):

    def get(self):
        global g_ipaddr
        global g_port_num
        self.render('audio.html', ipaddr=g_ipaddr, port_num=g_port_num)

if __name__ == "__main__":

    global g_ipaddr
    global g_port_num

    # Get host IP address
    conn_if = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    conn_if.connect(("8.8.8.8", 80))
    ipaddr = conn_if.getsockname()[0]
    g_ipaddr = ipaddr
    port_num = 8000
    g_port_num = port_num

    app = tornado.web.Application([
        (r"/", MyHandler),
        (r"/websocket", WebSocketHandler)
    ])

    http_server = tornado.httpserver.HTTPServer(app, ssl_options={
        "certfile": "web-server.crt",
        "keyfile":  "web-server.key",
    })

    http_server.listen(port_num)
    print("Info: Listening to https://{}:{}".format(ipaddr, port_num))

    tornado.ioloop.IOLoop.instance().start()

