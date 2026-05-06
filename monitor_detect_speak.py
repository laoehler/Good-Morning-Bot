#!/usr/bin/env python3
"""
monitor_detect_speak.py
-----------------------
GPIO pin layout
  BCM 23  (physical 16) : switch input  (pull-down, reads HIGH when ON)
  BCM 17  (physical 11) : PIR sensor input
  BCM 18  (physical 12) : amplifier enable output

Flow (single loop, no threads):
  Poll the switch → if ON, poll the PIR → if HIGH, play audio → cooldown → repeat
"""

import subprocess
import signal
import sys
import time
import wave
import logging
import RPi.GPIO as GPIO

# ── Configuration ──────────────────────────────────────────────────────────────
SWITCH_PIN = 23
PIR_PIN    = 17
AMP_PIN    = 18
AUDIO_FILE = "/home/pi/Good-Morning-Bot/output.wav"
BOUNCE_MS  = 50
POLL_INTERVAL = 0.05   # seconds between each main loop iteration
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def get_audio_duration(path: str) -> float:
    """Return WAV duration in seconds, with a safe fallback."""
    try:
        with wave.open(path, "rb") as f:
            return f.getnframes() / float(f.getframerate())
    except Exception as exc:
        log.warning("Could not read WAV duration (%s) — defaulting to 20 s.", exc)
        return 20.0


COOLDOWN: float = get_audio_duration(AUDIO_FILE)
log.info("Audio duration / motion cooldown: %.2f s", COOLDOWN)


def gpio_setup() -> None:
    GPIO.setwarnings(False)
    GPIO.cleanup()          # clear any stale state from a previous run
    time.sleep(0.1)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(PIR_PIN,    GPIO.IN)
    GPIO.setup(AMP_PIN,    GPIO.OUT, initial=GPIO.LOW)
    log.info("GPIO ready — Switch: BCM %d | PIR: BCM %d | Amp: BCM %d",
             SWITCH_PIN, PIR_PIN, AMP_PIN)


def gpio_cleanup() -> None:
    """Always bring the amp low before releasing GPIO."""
    GPIO.output(AMP_PIN, GPIO.LOW)
    GPIO.cleanup()
    log.info("GPIO cleaned up.")


def play_audio(file_path: str) -> None:
    """
    Enable the amplifier, play the file (blocking), then disable the amplifier.
    Any error leaves the amp safely turned off via the finally block.
    """
    try:
        GPIO.output(AMP_PIN, GPIO.HIGH)
        subprocess.run(["aplay", "-D", "plughw:0,0", file_path], check=True)
    except subprocess.CalledProcessError as exc:
        log.error("aplay exited with error: %s", exc)
    except Exception as exc:
        log.error("Unexpected playback error: %s", exc)
    finally:
        GPIO.output(AMP_PIN, GPIO.LOW)


def read_switch() -> bool:
    """Return True if the switch is ON, with debounce."""
    if GPIO.input(SWITCH_PIN) == GPIO.HIGH:
        time.sleep(BOUNCE_MS / 1000)
        return GPIO.input(SWITCH_PIN) == GPIO.HIGH
    return False


def shutdown(signum=None, frame=None) -> None:
    log.info("Shutdown requested — cleaning up …")
    gpio_cleanup()
    log.info("Goodbye.")
    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    gpio_setup()
    log.info("good_morning_bot ready. Polling … (Ctrl-C to exit)")

    last_trigger: float = 0.0

    while True:
        # ── 1. Check the switch ────────────────────────────────────────────────
        if not read_switch():
            last_trigger = 0.0   # reset so first motion after switch-ON fires instantly
            time.sleep(POLL_INTERVAL)
            continue

        # ── 2. Switch is ON — check the PIR ───────────────────────────────────
        if not GPIO.input(PIR_PIN):
            time.sleep(POLL_INTERVAL)
            continue

        # ── 3. PIR is HIGH — apply cooldown guard ─────────────────────────────
        now = time.time()
        if now - last_trigger < COOLDOWN:
            # Still within the cooldown window; wait for the PIR to go LOW, then loop
            while GPIO.input(PIR_PIN):
                time.sleep(0.2)
            time.sleep(POLL_INTERVAL)
            continue

        # ── 4. Play audio ──────────────────────────────────────────
        log.info("Motion detected — playing audio.")
        play_audio(AUDIO_FILE)   # blocks until aplay finishes
        last_trigger = time.time()  # Set AFTER playback completes

        # ── 5. Ready for next detection ────────────────────────────────────────
        log.info("Playback done — resuming monitoring.")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()