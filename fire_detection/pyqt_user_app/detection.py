from PyQt5.QtWidgets import QMainWindow
from PyQt5.uic import loadUi
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
import cv2
import numpy as np
import time
import os
import requests
from ultralytics import YOLO
import time
import platform

if platform.system() == 'Windows':
    import winsound

def play_alert_sound(file_path):
	try:
		if platform.system() == 'Windows':

			
			# winsound.PlaySound chỉ hỗ trợ file .wav. Với file .mp3 nó sẽ không kêu.
			# Sử dụng tiếng Beep mặc định của hệ thống để đảm bảo luôn phát ra âm thanh.
			winsound.Beep(2500, 1000) # Phát tiếng bíp ở tần số 2500Hz trong 1 giây (1000ms)
	except Exception as e:
		print(f"Error: {e}")

class Detection(QThread):

	def __init__(self, token, location, receiver):
		super(Detection, self).__init__()	

		self.token = token
		self.location = location
		self.receiver = receiver
		self.yolo = YOLO('./models/best.pt')
		self.running = True
		self.last_alert_time = time.time() - 11 # Thời gian gửi email lần cuối (để chống spam 10s)
		self.fire_start_time = None # Đồng hồ bấm giờ khi bắt đầu thấy lửa
	
	changePixmap = pyqtSignal(QImage)

	


	def run(self):
		cap = cv2.VideoCapture(0)
		classes = ['Fire', 'Smoke']
		while self.running:
			ret, frame = cap.read()
			if ret:

				height, width, channels = frame.shape
				results = self.yolo(frame)
				
				danger_detected_in_frame = False # Cờ kiểm tra xem có lửa/khói trong khung hình hiện tại không

				for result in results:
					boxes = result.boxes.numpy()
					for box in boxes:
						cls = int(box.cls.item())
						conf = box.conf.item()
						print("Confident: ",conf)
						x, y, x2, y2 = map(int, box.xyxy[0])

						if conf > 0.5:
							
							danger_detected_in_frame = True
							
							# Luôn vẽ khung xanh ngay lập tức để người dùng biết AI đang làm việc
							cv2.rectangle(frame, (x, y), (x2, y2), (0, 255, 0), 2)
							cv2.putText(frame, f"{classes[cls]}: {conf:.2f}", (x, y - 20), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)

				# Xử lý logic 5 giây
				if danger_detected_in_frame:
					if self.fire_start_time is None:
						self.fire_start_time = time.time() # Bắt đầu bấm giờ
					elif time.time() - self.fire_start_time >= 5.0:
						# Đã phát hiện liên tục từ 5 giây trở lên!
						play_alert_sound('./sound/emergency_sound.mp3') # Kêu bíp
						
						# Gửi lên server (giới hạn 10 giây gửi 1 lần để không bị spam email)
						if time.time() - self.last_alert_time >= 10:
							self.last_alert_time = time.time()
							self.save_detection(frame)
				else:
					self.fire_start_time = None # Nếu không thấy lửa nữa, reset lại đồng hồ bấm giờ về 0

				rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
				bytesPerLine = channels * width
				convertToQtFormat = QImage(rgbImage.data, width, height, bytesPerLine, QImage.Format_RGB888)
				p = convertToQtFormat.scaled(854, 480, Qt.KeepAspectRatio)
				self.changePixmap.emit(p)
			else:
				pass
	def save_detection(self, frame):

		# Kiểm tra và tạo thư mục lưu ảnh nếu chưa có
		if not os.path.exists("saved_frames"):
			os.makedirs("saved_frames")
		cv2.imwrite("saved_frames/frame.jpg", frame)
		print('Frame Saved')
		self.post_detection()

	# Gửi cảnh báo đến server
	def post_detection(self):

			url = 'http://127.0.0.1:8000/api/images/'
			headers = {'Authorization': 'Token ' + self.token}
			files = {'image': open('saved_frames/frame.jpg', 'rb')}
			data = {'user_ID': self.token,'location': self.location, 'alert_receiver': self.receiver}
			response = requests.post(url, files=files, headers=headers, data=data)

			# HTTP 200
			if response.ok:
				print('Đã gửi cảnh báo đến server')
			# Bad response
			else:
				print('Không thể gửi cảnh báo đến server')
				
