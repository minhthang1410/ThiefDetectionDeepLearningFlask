import socket
from flask import Flask, render_template, Response
from camera import Video

app=Flask(__name__)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
local_ip = s.getsockname()[0]

@app.route('/')
def index():
	return render_template('index.html')

def gen(camera):
	while True:
		frame = camera.get_frame()
		yield(b'--frame\r\n'
			b'Content-type: image/jpeg\r\n\r\n' + frame +
			b'\r\n\r\n')

@app.route('/video')

def video():
	return Response(gen(Video()),
	mimetype='multipart/x-mixed-replace; boundary=frame')

app.run(host=local_ip)
