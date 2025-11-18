from gpiozero import MotionSensor
from time import sleep

# Dein OUT-Kabel steckt an GPIO17
pir = MotionSensor(17)

print("PIR Sensor Test gestartet...")
print("Warte auf Bewegung...")

while True:
    pir.wait_for_motion()
    print("Bewegung erkannt!")
    pir.wait_for_no_motion()
    print("Keine Bewegung mehr.")
