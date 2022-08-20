import cv2
import time
import RPi.GPIO as GPIO
from PCA9685 import PCA9685
from tflite_support.task import core
from tflite_support.task import processor
from tflite_support.task import vision
import utils
import telegram
import threading

model = 'thiefmodel2_edgetpu.tflite'
enable_edgetpu = True
#model = 'thiefmodel2.tflite'
#enable_edgetpu = False
num_threads = 4

angle = 90
pwm = PCA9685()
pwm.setPWMFreq(50)
pwm.setRotationAngle(1,angle)
pwm.setRotationAngle(0,50)

camera_id = 0
width = 640
height = 480

counter = 0
fps = 0
start_time = time.time()
fps_avg_frame_count = 10

handleTime = 0
timeBeforeHandle = 0
timeAfterHandle = 0

row_size = 20
left_margin = 24
text_color = (0, 0, 255)
font_size = 1
font_thickness = 1

base_options = core.BaseOptions(file_name=model, use_coral=enable_edgetpu, num_threads=num_threads)
detection_options = processor.DetectionOptions(max_results=1, score_threshold=0.6)
options = vision.ObjectDetectorOptions(base_options=base_options, detection_options=detection_options)
detector = vision.ObjectDetector.create_from_options(options)

telegram_notify = telegram.Bot("api_key")
message = ""


def sendTeleNoti():
	try:
		message = ""
		telegram_notify.send_message(chat_id="chat_id", text=message, parse_mode='Markdown')
	except:
		pass
class Video(object):
	def __init__(self):
		self.video = cv2.VideoCapture(camera_id)
		self.video.set(cv2.CAP_PROP_FRAME_WIDTH, width)
		self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
	def __del__(self):
		self.video.release()
	def get_frame(self):
		global fps
		global counter
		global start_time
		global fps_avg_frame_count
		global angle
		global handleTime
		global timeBeforeHandle
		global timeAfterHandle

		ret, frame = self.video.read()
		
		counter += 1
		frame = cv2.flip(frame, 1)
		
		rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		input_tensor = vision.TensorImage.create_from_array(rgb_image)
		timeBeforeHandle = time.time()
		detection_result = detector.detect(input_tensor)
		frame = utils.visualize(frame, detection_result)

		if len(detection_result.detections) == 1:
			timeAfterHandle = time.time()
			if detection_result.detections[0].classes[0].class_name == "ten_vat_the_muon_nhan_dien":
				tele_thread = threading.Thread(target=sendTeleNoti)
				tele_thread.start()
				x1 = detection_result.detections[0].bounding_box.origin_x
				x2 = x1 + detection_result.detections[0].bounding_box.width
				center = (x1 + x2) / 2
				if center < 280:
					if angle > 0 and angle < 180:
						angle -= 1
					else:
						print("Out of Angle")
				if center > 360:
					if angle > 0 and angle < 180:
						angle += 1
					else:
						print("Out of Angle")
		
		pwm.setRotationAngle(1,angle)
		
		handleTime = timeAfterHandle - timeBeforeHandle
		
		if counter % fps_avg_frame_count == 0:
			end_time = time.time()
			fps = fps_avg_frame_count / (end_time - start_time)
			start_time = time.time()
		
		handleTime_text = 'Handle Time = {:.5f}'.format(handleTime)
		fps_text = 'FPS = {:.1f}'.format(fps)
		text_location = (left_margin, row_size)
		cv2.putText(frame, fps_text, text_location, cv2.FONT_HERSHEY_PLAIN, font_size, text_color, font_thickness)
		cv2.putText(frame, handleTime_text, (300, 20), cv2.FONT_HERSHEY_PLAIN, 1.5, text_color, 2)

		ret, jpg = cv2.imencode('.jpg', frame)
		return jpg.tobytes()
