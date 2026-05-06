import subprocess
import RPi.GPIO as GPIO

GPIO_PIN = 18
AUDO_FILE = "/home/pi/Good-Morning-Bot/"

GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.OUT)

def play_audio(file_path):
    try:
        GPIO.output(GPIO_PIN, GPIO.HIGH)

        subprocess.run(
            ["aplay", "-D", "plughw:1,0", file_path],   
            check=True
        )

    except Exception as e:
        print("Audio playback error:", e)

    finally:
        GPIO.output(GPIO_PIN, GPIO.LOW)

if __name__ == "__main__":
    play_audio("output.wav")
    GPIO.cleanup()