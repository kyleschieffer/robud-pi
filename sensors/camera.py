import cv2
from picamera2 import Picamera2
import paho.mqtt.client as mqtt
import time
from io import BytesIO
import numpy as np
import random
from robud.robud_logging.MQTTHandler import MQTTHandler
import argparse
import logging
from datetime import datetime
import os
import sys
import traceback
from robud.sensors.camera_common import CAMERA_HEIGHT, CAMERA_WIDTH, TOPIC_CAMERA_RAW, CAMERA_FPS
from time import monotonic, sleep

random.seed()

topic_camera_raw = TOPIC_CAMERA_RAW

MQTT_BROKER_ADDRESS = "robud.local"
MQTT_CLIENT_NAME = "camera.py" + str(random.randint(0,999999999))

TOPIC_ROBUD_LOGGING_LOG = "robud/robud_logging/log"
TOPIC_ROBUD_LOGGING_LOG_SIGNED = TOPIC_ROBUD_LOGGING_LOG + "/" + MQTT_CLIENT_NAME
TOPIC_ROBUD_LOGGING_LOG_ALL = TOPIC_ROBUD_LOGGING_LOG + "/#"
LOGGING_LEVEL = logging.ERROR

#parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-o", "--Output", help="Log Ouput Prefix", default="logs/camera_log_")
args = parser.parse_args()

#initialize logger
logger=logging.getLogger()
file_path = args.Output + datetime.now().strftime("%Y-%m-%d") + ".txt"
directory = os.path.dirname(file_path)
if not os.path.exists(directory):
    os.makedirs(directory)
log_file = open(file_path, "a")
myHandler = MQTTHandler(hostname=MQTT_BROKER_ADDRESS, topic=TOPIC_ROBUD_LOGGING_LOG_SIGNED, qos=2, log_file=log_file)
myHandler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(filename)s: %(message)s'))
logger.addHandler(myHandler)
logger.level = LOGGING_LEVEL

logger.info("Starting")
try:
    client = mqtt.Client(MQTT_CLIENT_NAME) #create new instance
    client.connect(MQTT_BROKER_ADDRESS)
    client.loop_start()
#     # Create the Camera instance for 640 by 360
    camera = Picamera2()
    config = camera.create_still_configuration({"size":(CAMERA_WIDTH,CAMERA_HEIGHT)})
    camera.configure(config)
    camera.start()
    loop_min = 1/CAMERA_FPS
    while True:
        loop_start = monotonic()
        frame = cv2.cvtColor(camera.capture_array(),cv2.COLOR_BGR2RGB)
        encoded_frame = cv2.imencode('.jpg',frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        payload=encoded_frame[1].tobytes()
        client.publish(topic=topic_camera_raw,payload=payload,qos=0)
        loop_time = monotonic() - loop_start
        if loop_time < loop_min:
            sleep(loop_min - loop_time)

except Exception as e:
    logger.critical(str(e) + "\n" + traceback.format_exc())
except KeyboardInterrupt:
    logger.info("Exited with Keyboard Interrupt")
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)
# finally:
#        # close the camera instance
#     camera.release()

#         # remove camera object
#     del camera   
