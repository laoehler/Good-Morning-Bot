from __future__ import print_function
import datetime
import os
import os.path
import subprocess
from pathlib import Path

import requests
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Load environment variables from .env
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Load configuration from environment
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
CALENDAR_ID = os.getenv('CALENDAR_ID', 'primary')
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE', 'calendar_credentials.json')
TOKEN_FILE = os.getenv('TOKEN_FILE', 'token.json')
PIPER_MODEL = os.getenv('PIPER_MODEL_PATH', './en_US-danny-low.onnx')
PIPER_BIN = os.getenv('PIPER_BIN_PATH', './venv/bin/piper')
OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'output.wav')

USERNAME = os.getenv('USERNAME')

# Weather configuration
LATITUDE = os.getenv('LATITUDE')
LONGITUDE = os.getenv('LONGITUDE')
TEMPERATURE_UNIT = os.getenv('TEMPERATURE_UNIT', 'celsius')

def speak_to_file(text):
    try:
        process = subprocess.Popen(
            [PIPER_BIN, "--model", PIPER_MODEL, "--output_file", OUTPUT_FILE],
            stdin=subprocess.PIPE,
            text=True
        )
        process.communicate(text)
    except Exception as e:
        print("TTS error:", e)

# def play_audio(file_path):
#     try:
#         subprocess.run(["aplay", "-D", "plughw:1,0", "output.wav"], check=True)
#     except Exception as e:
#         print("Audio playback error:", e)

def get_weather():
    """Fetch weather data from Open-Meteo API (free, no API key needed)"""
    if not LATITUDE or not LONGITUDE:
        print("Warning: LATITUDE and LONGITUDE not configured. Skipping weather.")
        return None
    
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "daily": "temperature_2m_max,temperature_2m_min,cloudcover_mean",  # Changed cloudcover_max to cloudcover_mean
            "temperature_unit": TEMPERATURE_UNIT,  # Added to convert temperatures automatically
            "timezone": "auto"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Get today's weather (first day in the response)
        daily = data.get('daily', {})
        if daily and 'temperature_2m_max' in daily and 'temperature_2m_min' in daily:
            high_temp = daily['temperature_2m_max'][0]
            low_temp = daily['temperature_2m_min'][0]
            cloud_cover = daily.get('cloudcover_mean', [0])[0]  # Updated key to match new parameter
            
            return {
                'high': round(high_temp),
                'low': round(low_temp),
                'cloud_cover': round(cloud_cover),
                'unit': TEMPERATURE_UNIT.capitalize()
            }
    except requests.exceptions.RequestException as e:
        print(f"Weather API error: {e}")
    except (KeyError, IndexError) as e:
        print(f"Error parsing weather data: {e}")
    
    return None


def main():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    now = datetime.datetime.now(datetime.timezone.utc)
    local_now = now.astimezone()

    start_of_day = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + datetime.timedelta(days=1)

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_of_day.isoformat(),
        timeMax=end_of_day.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    message = f"Good morning, {USERNAME} "
    
    # Add weather information
    weather = get_weather()
    if weather:
        message += f"Today's forecast: high of {weather['high']} {weather['unit'].lower()}, "
        message += f"low of {weather['low']} {weather['unit'].lower()}, "
        message += f"and {weather['cloud_cover']} percent cloud cover. "
    
    message += "Here is your schedule for today. "

    if not events:
        message += "You have no events today."
        print(message)
        speak_to_file(message)
        return

    for event in events:
        start_raw = event['start'].get('dateTime', event['start'].get('date'))
        title = event.get('summary', 'No Title')

        if 'T' in start_raw:
            dt = datetime.datetime.fromisoformat(start_raw.replace('Z', '+00:00')).astimezone()
            time_str = dt.strftime('%I:%M %p')
            message += f"At {time_str}, {title}. "
        else:
            message += f"All day: {title}. "

    print(message)
    speak_to_file(message)

if __name__ == '__main__':
    main()