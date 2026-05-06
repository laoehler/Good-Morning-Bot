"""
switch_speak.py
---------------
GPIO pin layout
  BCM 23  (physical 16) : switch input  (pull-down, reads HIGH when ON)
  BCM 18  (physical 12) : amplifier enable output

Flow:
  Switch toggled ON → play audio once → done
  Switch toggled OFF → nothing
"""

import subprocess
import signal
import sys
import time
import logging
import RPi.GPIO as GPIO

# ── Configuration ──────────────────────────────────────────────────────────────
SWITCH_PIN = 23
AMP_PIN    = 18
AUDIO_FILE = "/home/pi/Good-Morning-Bot/output.wav"
BOUNCE_MS  = 50
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def gpio_setup() -> None:
    GPIO.setwarnings(False)
    GPIO.cleanup()
    time.sleep(0.1)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(AMP_PIN,    GPIO.OUT, initial=GPIO.LOW)
    log.info("GPIO ready — Switch: BCM %d | Amp: BCM %d", SWITCH_PIN, AMP_PIN)


def gpio_cleanup() -> None:
    GPIO.output(AMP_PIN, GPIO.LOW)
    GPIO.cleanup()
    log.info("GPIO cleaned up.")


def play_audio(file_path: str) -> None:
    try:
        GPIO.output(AMP_PIN, GPIO.HIGH)
        subprocess.run(["aplay", "-D", "plughw:1,0", file_path], check=True)
    except subprocess.CalledProcessError as exc:
        log.error("aplay exited with error: %s", exc)
    except Exception as exc:
        log.error("Unexpected playback error: %s", exc)
    finally:
        GPIO.output(AMP_PIN, GPIO.LOW)


def shutdown(signum=None, frame=None) -> None:
    log.info("Shutdown requested — cleaning up …")
    gpio_cleanup()
    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    gpio_setup()

    last_state = GPIO.input(SWITCH_PIN)
    log.info("Ready — waiting for switch toggle. (Ctrl-C to exit)")

    while True:
        current_state = GPIO.input(SWITCH_PIN)

        if current_state != last_state:
            time.sleep(BOUNCE_MS / 1000)              # debounce
            current_state = GPIO.input(SWITCH_PIN)    # confirm it held

            if current_state != last_state:
                last_state = current_state
                if current_state == GPIO.HIGH:
                    log.info("Switch ON — playing audio.")
                    play_audio(AUDIO_FILE)
                    log.info("Playback done.")
                else:
                    log.info("Switch OFF.")

        time.sleep(0.05)


if __name__ == "__main__":
    main()