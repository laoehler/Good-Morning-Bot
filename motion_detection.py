
import RPi.GPIO as GPIO
import time
import subprocess
import wave

with wave.open('output.wav', 'rb') as f:
    frames = f.getnframes()
    rate = f.getframerate()
    duration = frames / float(rate)
    print(f"Duration: {duration:.2f} seconds")

PIR_PIN = 17          # GPIO pin connected to PIR OUT
COOLDOWN = duration         # seconds between activations


last_trigger = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

print("Motion detection active. ")


try:
    while True:
        motion = GPIO.input(PIR_PIN)

        if motion:
            now = time.time()
            #print(now)
            #time.sleep(2)

            if now - last_trigger > COOLDOWN:
                print("Motion detected")

                subprocess.Popen(["python3", "/home/pi/Good-Morning-Bot/speak.py"])
                last_trigger = now

            while GPIO.input(PIR_PIN):
                time.sleep(0.2)

        time.sleep(0.2)

except KeyboardInterrupt:
    GPIO.cleanup()