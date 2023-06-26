import io
import PIL.Image as Image
import cv2
import numpy
import base64
import socket
from picamera2 import Picamera2, Preview
import socket
import time
import threading
from threading import Thread
import RPi.GPIO as GPIO

sock = socket.socket()
sock.connect(('192.168.5.2', 8000))
print("connect")

UDP_IP = "0.0.0.0"
UDP_PORT = 12345
sock2 = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock2.bind((UDP_IP, UDP_PORT))

max_wait_time = 15
working_lane = 25
active_lane = -1
wait_time = max_wait_time
max_switch_time = 10
switch_time = max_switch_time
def light_switching(running):
    print("something")
    switch = True
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT) #power
    GPIO.output(18, GPIO.HIGH)
    GPIO.setup(17, GPIO.OUT)
    GPIO.setup(22, GPIO.OUT)
    GPIO.setup(25, GPIO.OUT)
    GPIO.setup(27, GPIO.OUT)
    global active_lane
    global max_wait_time
    global wait_time
    global switch_time
    while running.is_set():
        if active_lane == -1:
            if switch:
                GPIO.output(22, GPIO.HIGH) #red
                GPIO.output(27, GPIO.HIGH) #red
                
                GPIO.output(25, GPIO.LOW) #green
                GPIO.output(17, GPIO.LOW) #green
            else:
                GPIO.output(22, GPIO.LOW) #green
                GPIO.output(27, GPIO.LOW) #green
                
                GPIO.output(25, GPIO.HIGH) #red
                GPIO.output(17, GPIO.HIGH) #red
            time.sleep(1)
            switch_time -= 1
            if switch_time <= 0:
                switch = not switch
                switch_time = max_switch_time
        else:
            GPIO.output(22, GPIO.LOW)
            GPIO.output(27, GPIO.LOW)
            GPIO.output(25, GPIO.LOW)
            GPIO.output(17, GPIO.LOW)
            print(wait_time)
            LED_PIN = active_lane
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(1)
            wait_time -= 1
            if wait_time <= 0:
                GPIO.output(LED_PIN, GPIO.LOW)
                active_lane = -1
    GPIO.cleanup()
running = threading.Event()
running.set()
t = Thread(target=light_switching, args=(running,))
t.start()

img_name ='./videoImages/frame0.jpg'
camera = Picamera2()
config = camera.create_preview_configuration(main={"size": (1920, 1080)})
camera.configure(config)
camera.start()

for i in range(100):
    try:
        data, addr = sock2.recvfrom(512)
        if data ==b'start':
            camera.capture_file(img_name)
            frame = cv2.imread(img_name, cv2.IMREAD_COLOR)
            encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]
            result, imgencode = cv2.imencode('.jpg', frame, encode_param)
            data = numpy.array(imgencode)
            stringData = base64.b64encode(data)
            length = str(len(stringData))
            sock.sendall(length.encode('utf-8').ljust(64))
            sock.send(stringData)
        elif data ==b'found':
            print("Found an active emergency vehicle")
            wait_time = max_wait_time
            active_lane = working_lane
    except Exception as e:
        print(e)
        sock.close()



