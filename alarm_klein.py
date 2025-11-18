#Raspberry Pi Projekt - Alarmanlage
import RPI.GPIO as GPIO
import time

Sensor_PIN = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(Sensor_PIN, GPIO.IN)

def mein_callback(channel):
    print("ALARM! Eine Bewegung wurde detektiert")

try: 
    GPIO.add_event_detect(Sensor_PIN, GPIO.RISING, callback=mein_callback)
    while True:
        time.sleep(100)
except KeyboardInterrupt:
    print("Beende das System")

GPIO.cleanup()