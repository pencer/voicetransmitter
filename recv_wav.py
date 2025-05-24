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
DECIMATION_FACTOR=1
SAMPLE_RATE = 48000 // DECIMATION_FACTOR # 8000 # 48000
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
        vol_voice = 0.525
        vol_noise = 0.06
        vol_beep  = 0.1
        beep_freq = 880 # Hz
        v = np.array(self.voice)
        v.flatten()

        # voice change
        # https://zenn.dev/niisan/articles/0caef4a3cf1a9a
        frame_rate = 48000
        period = 32 # 16
        move = 30
        keep = 2
        span = frame_rate // period
        nfft = v.shape[1] // span
        r_wave = np.reshape(v[0,:nfft*span], (nfft, span)) # convert to x[nfft][span]
        fv = np.fft.fft(r_wave)
        sfv = np.concatenate((fv[:,:keep], np.zeros((nfft,move)), fv[:,keep:]), 1)
        temp = sfv[:, :span//2]
        tempi = temp[:,::-1]
        tempi.imag = -temp.imag[:,::-1]
        temps = np.concatenate([temp, tempi], 1)
        ifv = np.fft.ifft(temps).real
        res = np.reshape(ifv, (-1))
        v = np.array([res])

        # Lower quality voice with noise
        v = v[::,::DECIMATION_FACTOR] # 48kHz -> 48/DECIMATION_FACTOR kHz
        size = v.shape[1]
        vmax = np.max(v)
        noise = np.random.rand(1, size) - 0.5 # White noise
        beep = np.sin(np.linspace(0, beep_freq*2*np.pi, SAMPLE_RATE))
        beep = np.pad(beep, (0, size-SAMPLE_RATE)) # first one second only
        v = v * vol_voice / vmax + noise * vol_noise + [beep * vol_beep]

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

