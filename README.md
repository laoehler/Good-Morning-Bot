# Good-Morning-Bot
# 🐀 Talking Rat — Good Morning Bot

> A Raspberry Pi-powered morning briefing system housed inside an stuffed animal.  
> Speaks the day's weather and schedule aloud.
> Initially triggered by motion, but the final iteration uses a simple switch.

**By Lars**

---

## Some Photos
| | |
|---|---|
| <img width="400" alt="IMG_2689" src="https://github.com/user-attachments/assets/25aa1c92-c305-4760-89ee-13f6b3fc427e" /> | <img width="400" alt="IMG_2603" src="https://github.com/user-attachments/assets/74daed1a-a604-4f78-aa73-a8683b647273" /> |
| *Finished build* | *Testing the fit* |

https://github.com/user-attachments/assets/b4e93849-9198-4ea1-9237-5e8b6342bc25

 — demo of the rat greeting in action  

---

## Table of Contents

- [Mission Statement](#mission-statement)
- [Inspiration & Related Work](#inspiration--related-work)
- [Hardware](#hardware)
- [Wiring](#wiring)
- [Software Overview](#software-overview)
- [Development Process](#development-process)
- [Usage](#usage)
- [File Reference](#file-reference)

---

## Mission Statement

Build a programmable morning briefing system using the **Raspberry Pi 3B+** with an integrated speaker system. The system loads the users schedule and weather daily, then when activated delivers a customized briefing covering weather and calendar obligations all spoken aloud using the Piper TTS library.

---

## Inspiration & Related Work

**Why this project?**  
People have difficulty planning their mornings and keeping track of their schedules. A physical device that speaks your day to you removes friction — no phone to unlock, no app to open.

**Related projects that informed this build:**

- [Raspberry Pi Wall Calendar Dashboard](https://www.hanselman.com/blog/how-to-build-a-wall-mounted-family-calendar-and-dashboard-with-a-raspberry-pi-and-cheap-monitor) — Scott Hanselman
- [Raspberry Pi Google Calendar Display](https://www.instructables.com/Raspberry-Pi-Wall-Mounted-Google-Calendar/) — Instructables
- [Integrating Piper TTS with Raspberry Pi](https://www.youtube.com/watch?v=rjq5eZoWWSo) — YouTube
- [Morning Piper TTS Briefing for Weather & Google Calendar](https://community.home-assistant.io/t/help-simple-morning-piper-tts-briefing-for-weather-and-google-calendar-events/876261) — Home Assistant Community

---

## Hardware

| Component | Part | Notes |
|---|---|---|
| Single Board Computer | Raspberry Pi 3B+ | Controls everything |
| Speaker | Small JBL Clip 3 | Not the most elegant but functional |
| Motion sensor | PIR | Detects presence in front of rat |
| Toggle switch | Manual arm/disarm of motion detection | The only way to trigger the speech in final iteration of project |
| Enclosure | Stuffed Animal | Houses Pi and Switch |
| Power | 5V 3A USB-C supply | Powers Pi + Speaker |

---

## Wiring 
(PIR sensor removed in final version)

```
Raspberry Pi 3B+ (BCM numbering)
─────────────────────────────────────────────────────
  BCM 23  (Physical Pin 16)  ←  Toggle Switch signal
                                 (pull-down, HIGH = ON)

  BCM 17  (Physical Pin 11)  ←  PIR sensor OUT

  BCM 18  (Physical Pin 12)  →  Amplifier ENABLE pin

  Pin 2   (5V)               →  PIR VCC
  Pin 4   (5V)               →  Amplifier VCC
  Pin 6   (GND)              →  PIR GND / Amp GND / Switch GND

  3.5mm audio jack           →  Amplifier audio input
                                 (ALSA device: plughw:1,0)
```


Early prototype without enclosure

https://github.com/user-attachments/assets/7b22ad97-532f-45b7-b264-b93257ba664e



---

## Software Overview

The project uses three main pieces of software:

### 1. Piper TTS
Generates the spoken audio (`output.wav`) from a text script. Piper runs locally on the Pi and produces natural-sounding speech without an internet connection.

```bash
echo "Good morning. Today is Monday..." | piper --model en_US-lessac-medium --output_file output.wav
```

### 2. Python scripts (GPIO control)

Two trigger modes are available:

| Script | Trigger | Use case |
|---|---|---|
| `monitor_detect_speak.py` | PIR motion sensor, armed by switch | Automatic — fires when someone scratches the rat's belly (glitched out before final iteration) |
| `switch_speak.py` | Toggle switch ON | Manual — flip switch to play immediately |

### 3. Google Calendar + Weather API
A separate script fetches the day's events from Google Calendar and current weather data, formats them into a morning briefing script, and passes it to Piper to regenerate `output.wav` each morning via `cron`.

---

## Development Process

### Phase 1 — Getting Piper TTS working

The starting point was getting speech generation working on the Pi at all. Piper TTS was installed and multiple voice models were tested in order for me to decide which one I liked the best. The output of this phase was a simple shell command that could take any text and produce a clean WAV file.

```bash
echo "Good morning. Today is Monday..." | \
  piper --model en_US-lessac-medium --output_file output.wav
```

### Phase 2 — Connecting the Pi to the right libraries

With speech working, the next step was wiring up the Pi's GPIO pins and connecting all the supporting Python libraries — `RPi.GPIO` for pin control, the Google Calendar API client, and the weather API. This phase involved a lot of audio file path troubleshooting and confirming that audio was routing to the correct ALSA device (`plughw:1,0` — the headphone jack, not the HDMI port).

### Phase 3 — Getting cron jobs working

The TTS loading script needed to run automatically each morning before the rat was likely to be used. This meant configuring `cron` to call a shell script every morning that fetches the day's weather and Google Calendar events, formats them into a spoken briefing, and regenerates `output.wav` using Piper. Getting the code to work correctly inside a cron environment (no interactive terminal, different working directory) was the main challenge here.

```
# Cron entry — regenerate briefing audio at 6:45 AM daily
45 6 * * * /home/pi/Good-Morning-Bot/generate_briefing.sh
```

### Phase 4 — Enclosure

With the software stable, everything was fitted inside the stuffed animal. The JBL Clip 3 speaker was free outside of the body, the Pi was secured inside a 3d printed base, and the toggle switch was mounted to this base. Cable management inside a stuffed animal was challenging but not too bad. A patch was sewn to the outside of the rat over top of the switch denoting off and on to the user. 3d printing was a challenge but after a couple prototypes I reached a functional final version.

| | | |
|---|---|---|
| <img width="260" alt="IMG_2598" src="https://github.com/user-attachments/assets/e340de06-df64-4585-ac07-3757cf893534" /> | <img width="260" alt="IMG_2706" src="https://github.com/user-attachments/assets/9fc9e651-5fed-47e4-be15-2951a9766dff" /> | <img width="260" alt="IMG_2707" src="https://github.com/user-attachments/assets/fdd86317-9633-48fd-9af2-b2809cabc950" /> |
| *Early failed print (ran out of filament)* | *First successful prototype* | *Final enclosure* |

### Phase 5 — Refinement & adaptation

Two things changed in the final iteration. First, the threading model in the trigger script was removed in favour of a simpler single-loop polling approach. Second, the PIR motion sensor did not reliably trigger for an unknown reason, so at the last minute the entire project switched to a switch.

---

## Usage
(Pre PIR fiasco)

| Action | Result |
|---|---|
| Flip switch ON (motion mode) | Arms PIR — rat speaks when it detects you |
| Flip switch OFF | Disarms PIR — rat stays silent |
| Flip switch ON (switch mode) | Rat speaks immediately |
| Ctrl-C / SIGTERM | Clean GPIO shutdown |

The rat will not re-trigger during playback or within the cooldown window (equal to audio duration) after playback ends.

---

## File Reference

| File | Purpose |
|---|---|
| `monitor_detect_speak.py` | Main script — switch + PIR motion trigger |
| `switch_speak.py` | Simplified script — switch toggle trigger only |
| `generate_briefing.sh` | Cron script — fetches data, generates `output.wav` |
| `output.wav` | Generated audio file played by the rat |
| `credentials.json` | Google Calendar API credentials *(not committed)* |
| `token.json` | OAuth token, auto-generated on first run *(not committed)* |

---
