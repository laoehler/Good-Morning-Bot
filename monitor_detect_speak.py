#!/usr/bin/env python3
"""
monitor_detect_speak.py
-----------------------
GPIO pin layout
  BCM 18  : transistor control pin for the lights
  BCM 24  : LED positive lead   
  BCM 17  : PIR sensor input
  BCM 23  : condition/switch input (sound enabled when HIGH)
"""

import signal
import subprocess
import sys
import time
import logging
import RPi.GPIO as GPIO

condition_pin = 23  # switch: HIGH = sound enabled    
led = 24            # LED positive lead  ← make sure this matches your wiring!
sensor = 17         # PIR sensor output
previousState = GPIO.LOW
interval = 10       # number of loop ticks to keep lights on (10 * 0.1s = 1s)
counter = 0
DELAY = 0.1
AUDIO_FILE = "/home/pi/Good-Morning-Bot/output.wav"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def setup() -> None:
    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(condition_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(led, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(sensor, GPIO.IN)
    log.info(
        "GPIO ready — condition=%d led=%d sensor=%d",
        condition_pin, led, sensor,
    )


def play_audio() -> None:
    try:
        subprocess.run(["aplay", AUDIO_FILE], check=True)
    except subprocess.CalledProcessError as exc:
        log.error("Audio playback failed: %s", exc)
    except Exception as exc:
        log.error("Unexpected audio error: %s", exc)


def flash_led() -> None:
    """Blink LED once to indicate motion."""
    print(f"[DEBUG] Driving LED HIGH on BCM pin {led}")
    GPIO.output(led, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(led, GPIO.LOW)
    print(f"[DEBUG] LED LOW again")


def loop() -> None:
    global previousState, counter

    val = GPIO.input(sensor)
    sound_enabled = GPIO.input(condition_pin) == GPIO.HIGH

    if val == GPIO.HIGH:
        if previousState == GPIO.LOW:
            # Rising edge — motion just started
            print(">>> MOTION DETECTED <<<")
            log.info("Motion detected — LED + lights on")
            flash_led()
            if sound_enabled:
                play_audio()
            else:
                print("Sound disabled by condition pin")
        previousState = GPIO.HIGH

    else:
        print("No motion detected")
        previousState = GPIO.LOW

    time.sleep(DELAY)


def shutdown(signum=None, frame=None) -> None:
    log.info("Shutdown requested — cleaning up …")
    GPIO.output(led, GPIO.LOW)
    GPIO.cleanup()
    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    setup()
    flash_led()  # Blink once on startup to indicate we're running

    time.sleep(2) # Allow PIR sensor to stabilize
    print("Motion monitor ready. Press Ctrl-C to exit.")
    while True:
        loop()


if __name__ == "__main__":
    main()