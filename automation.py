global engine  # inserted
import sys
import os
import time
import json
import subprocess
import threading
import queue
import speech_recognition as sr
import pyttsx3
import psutil
import pyautogui
import requests
from datetime import datetime, timedelta
from cryptography.fernet import Fernet, InvalidToken
import google.generativeai as genai
import webbrowser
import re
import urllib.parse
import screen_brightness_control as sbc
import image_analyzer
from pygame import mixer
import logging
import camera_module
from speech import speak, is_speaking
import pygetwindow as gw
import pyautogui
import time
import win32gui
import win32con
import logging
logging.disable(logging.CRITICAL)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:  # inserted
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MATERIALS_PATH = os.path.join(BASE_DIR, 'materials')
BACKGROUND_MUSIC_FILE = os.path.join(MATERIALS_PATH, 'brain_power_music.mp3')
WEATHER_API_KEY_FILE = os.path.join(MATERIALS_PATH, 'weather_api_key.txt')
PHONE_NUMBERS_FILE = os.path.join(MATERIALS_PATH, 'PhoneNumbers.txt')
REMINDERS = []
reminder_lock = threading.Lock()
engine = None

def init_tts():
    """Initialize pyttsx3 engine only once."""  # inserted
    global engine  # inserted
    if engine is None:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
init_tts()
is_speaking = threading.Event()

def close_window_by_name(target_name):
    """\n    Close any window whose title contains the given target_name.\n    """  # inserted

    def enum_handler(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            if window_title and target_name.lower() in window_title.lower():
                print(f'Found matching window: \'{window_title}\' (hwnd={hwnd})')
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        win32gui.EnumWindows(enum_handler, None)

def send_whatsapp_message(contact_name, message):
    """\n    Sends a WhatsApp message to the specified contact.\n    """  # inserted
    try:
        if not os.path.exists(PHONE_NUMBERS_FILE):
            speak('Phone numbers file is missing.')
            logging.error('PhoneNumbers.txt file is missing.')
            return
        with open(PHONE_NUMBERS_FILE, 'r') as f:
            lines = f.readlines()
            contact_found = False
            phone_number = ''
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if ':' not in line:
                    logging.warning(f'Incorrectly formatted line: {line}')
                    continue
                name, number = line.split(':', 1)
                name = name.strip().lower()
                number = number.strip()
                if name == contact_name.lower():
                    contact_found = True
                    phone_number = number
                    break
            if not contact_found:
                speak(f'The contact {contact_name} does not exist in the phone numbers file.')
                logging.warning(f'Contact \'{contact_name}\' not found.')
                return
            if not re.match('^\\+\\d{10,15}$', phone_number):
                    speak(f'The phone number for {contact_name} is incorrectly formatted.')
                    logging.warning(f'Incorrectly formatted phone number for {contact_name}: {phone_number}')
                    return
            encoded_message = urllib.parse.quote(message)
            whatsapp_url = f'https://web.whatsapp.com/send?phone={phone_number}&text={encoded_message}'
            webbrowser.open(whatsapp_url)
            speak(f'Sending your message to {contact_name} on WhatsApp.')
            logging.info(f'Opened WhatsApp URL for {contact_name} with message: {message}')
            time.sleep(20)
            pyautogui.press('enter')
    except Exception as e:
        logging.error(f'Error sending WhatsApp message: {e}')
        speak('An error occurred while trying to send the WhatsApp message.')

def play_song_on_youtube(song_name):
    """\n    Searches YouTube for the given song name and plays the most relevant video.\n    """  # inserted
    search_query = '+'.join(song_name.split())
    search_url = f'https://www.youtube.com/results?search_query={search_query}'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}
    try:
        response = requests.get(search_url, headers=headers)
        if response.status_code!= 200:
            speak('Sorry, I couldn\'t reach YouTube.')
            logging.error(f'Failed to reach YouTube. Status code: {response.status_code}')
            return False
        html = response.text
        video_ids = re.findall('watch\\?v=(\\S{11})', html)
        if video_ids:
            video_id = video_ids[0]
            video_url = f'https://www.youtube.com/watch?v={video_id}&autoplay=1'
            webbrowser.open(video_url)
            speak(f'Playing {song_name} on YouTube.')
            logging.info(f'Playing song \'{song_name}\' on YouTube with video ID: {video_id}')
            time.sleep(7)
            pyautogui.press('k')
            return True
        speak('Sorry, I couldn\'t find the song on YouTube.')
        logging.warning(f'No video IDs found for song \'{song_name}\' on YouTube.')
        return False
    except Exception as e:
        logging.error(f'Error in play_song_on_youtube: {e}')
        speak('An error occurred while trying to play the song.')
        return False  

def close_unwanted_processes(wait_seconds=3):
    """\n    Closes common browser processes (Chrome, Edge, Firefox, Opera, Brave),\n    Notepad & Calculator, then waits a few seconds.\n    """  # inserted
    try:
        logging.info('Closing unwanted processes...')
        print('\n[Cleaning Initialization] Closing browsers, notepad, and calculator...\n')
        processes_to_close = {'notepad.exe', 'brave.exe', 'chrome.exe', 'msedge.exe', 'opera.exe', 'calc.exe', 'firefox.exe'}
        for proc in psutil.process_iter(['pid', 'name']):
            name = (proc.info['name'] or '').lower().strip()
            if name in processes_to_close:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                    logging.info(f'Terminated process: {name} (PID: {proc.pid})')
                except psutil.NoSuchProcess:
                    logging.warning(f'''Process {name} (PID: {proc.pid}) already closed.''')

            time.sleep(wait_seconds)
            logging.info(f'Closed unwanted processes and waited for {wait_seconds} seconds.')
            print(f'[Cleaning Initialization] Done. Waited {wait_seconds}s.\n')
    except psutil.AccessDenied:
        logging.error(f'Access denied terminating {name} (PID: {proc.pid}).')
    except psutil.TimeoutExpired:
        logging.error(f'Timeout: {name} (PID: {proc.pid}) did not close in time.')
    except Exception as e:
        logging.error(f'Failed to terminate {name} (PID: {proc.pid}). Error: {e}')

def get_weather_api_key():
    """\n    Retrieves the OpenWeatherMap API key from weather_api_key.txt.\n    """  # inserted
    if not os.path.exists(WEATHER_API_KEY_FILE):
        speak('Weather API key file is missing.')
        logging.error('weather_api_key.txt file is missing.')
        return
    try:
        with open(WEATHER_API_KEY_FILE, 'r') as f:
            api_key = f.read().strip()
            if not api_key:
                speak('Weather API key is empty.')
                logging.warning('Weather API key is empty.')
                return
            else: 
                return api_key
    except Exception as e:
        speak('Failed to read weather API key.')
        logging.error(f'Error reading weather API key file: {e}')

def get_weather_info(city):
    """\n    Fetches weather information for the specified city using OpenWeatherMap API\n    and speaks the current weather conditions.\n    """  # inserted
    if not city:
        speak('No city specified for weather checking.')
        logging.warning('No city specified for weather checking.')
        return
    api_key = get_weather_api_key()
    if not api_key:
        return
    base_url = 'http://api.openweathermap.org/data/2.5/weather?'
    params = {'q': city, 'appid': api_key, 'units': 'metric'}
    try:
        response = requests.get(base_url, params=params)
        if response.status_code!= 200:
            speak(f'Sorry, I couldn\'t retrieve the weather information for {city}.')
            logging.error(f'Failed to fetch weather data for {city}. Status code: {response.status_code}')
            return
        data = response.json()
        if data.get('cod')!= 200:
            message = data.get('message', '')
            speak(f'Sorry, I couldn\'t find weather information for {city}. {message}')
            logging.error(f'Weather API error for {city}: {message}')
            return
        weather_desc = data['weather'][0]['description']
        temperature = data['main']['temp']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        weather_info = f'The current weather in {city} is {weather_desc} with a temperature of {temperature} degrees Celsius, humidity at {humidity}%, and wind speed of {wind_speed} meters per second.'
        logging.info(f'Weather info for {city}: {weather_info}')
        print(weather_info)
        speak(weather_info)
    except Exception as e:
        speak('An error occurred while fetching the weather information.')
        logging.error(f'Exception in get_weather_info for {city}: {e}')


def validate_and_set_reminder(reminder_time_str):
    """\n    Validates and sets a reminder time. Accepts multiple time formats\n    and normalizes to a full datetime object for the next occurrence.\n    """  # inserted
    reminder_time_str = reminder_time_str.lower().replace('.', '').replace('!', '').replace('?', '').strip()
    if (reminder_time_str.endswith('am') or reminder_time_str.endswith('pm')) and (not reminder_time_str.endswith(' am')) and (not reminder_time_str.endswith(' pm')):
        reminder_time_str = reminder_time_str[:(-2)] + ' ' + reminder_time_str[(-2):]
    time_formats = ['%I:%M %p', '%I:%M%p', '%H:%M']
    parsed_time = None
    for fmt in time_formats:
        try:
            parsed_time = datetime.strptime(reminder_time_str, fmt)
        except ValueError:
            logging.warning(f'Invalid time format for reminder: \'{reminder_time_str}\'.')
            speak('Sorry, I cannot set a reminder for that time.')
            return False
    if parsed_time:
        now = datetime.now()
        reminder_datetime = now.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
        if reminder_datetime <= now:
            reminder_datetime += timedelta(days=1)
        with reminder_lock:
            REMINDERS.append({'time': reminder_datetime, 'triggered': False})
        logging.info(f"Reminder scheduled for {reminder_datetime.strftime('%Y-%m-%d %I:%M %p')}.")
        speak(f"Sir, your reminder has been scheduled for {reminder_datetime.strftime('%I:%M %p')}.")
        return True


def check_reminders():
    """\n    Background loop that checks if it\'s time for any reminder every 30 seconds.\n    """  # inserted
    while True:
        now = datetime.now()
        with reminder_lock:
            for reminder in REMINDERS:
                pass  # postinserted
                if not reminder['triggered'] and now >= reminder['time']:
                    reminder_time_formatted = reminder['time'].strftime('%I:%M %p')
                    speak(f'Sir, this is your scheduled reminder for {reminder_time_formatted}.')
                    logging.info(f'Reminder triggered for {reminder_time_formatted}.')
                    reminder['triggered'] = True
            REMINDERS[:] = [r for r in REMINDERS if not r['triggered']]

def perform_automation_action(response, user_details):
    """\n    Check for single-line automation instructions from the LLM\n    and execute them. E.g., \"open youtube\", \"cleaning initializing\", etc.\n    """  # inserted
    raw_response = response.strip()
    logging.info(f'Raw API response: \'{raw_response}\'')
    action = raw_response.lower().rstrip('.!?')
    logging.info(f'Processed action: \'{action}\'')
    action = response.strip().lower().rstrip('.!?')
    user_city = user_details.get('city', '') if user_details else ''
    logging.info(f'Performing automation action: \'{action}\'')
    
    if action == 'cleaning initializing':
        close_unwanted_processes(wait_seconds=3)
    
    if action.startswith('close tab '):
        tab_name = action[len('close tab '):].strip()
        if not tab_name:
            logging.warning('Tab name not specified for \'close tab\' command.')
            speak('Please specify the tab name to close.')
            return
        try:
            close_window_by_name(tab_name)
            logging.info(f'Attempted to close tab: {tab_name}.')
            return
        except Exception as e:
            logging.warning(f'Unrecognized automation action: \'{action}\'')
            logging.error(f'Error closing tab \'{tab_name}\': {e}')
            speak(f'An error occurred while closing the tab \'{tab_name}\'.')
            return
    
    if action.startswith('close app'):
        app_name = action.replace('close app', '').strip()
        if not app_name:
            logging.warning('App name not specified for \'close app\' command.')
            speak('Please specify the app name to close.')
            return
        try:
            for process in psutil.process_iter(['name']):
                if process.info['name'] and app_name.lower() in process.info['name'].lower():
                    process.terminate()
                    logging.info(f"Closed application: {process.info['name']} (PID: {process.pid})")
                    speak(f"Closed application {process.info['name']}.")
                else: 
                    logging.warning(f'Application \'{app_name}\' not found.')
                    speak(f'Application \'{app_name}\' not found.')
        except Exception as e:
            logging.error(f'An error occurred while closing the application \'{app_name}\': {e}')
            speak(f'An error occurred while closing the application \'{app_name}\'.')
            return
    
    if action == 'ok sir. background music turning off':
        try:
            mixer.music.stop()
            logging.info('Background music turned off.')
            speak('Background music has been turned off, sir.')
        except Exception as e:
            logging.error(f'Error turning off background music: {e}')
            speak('An error occurred while turning off the background music.')
            return
    
    if action == 'ok sir. background music turning on':
        try:
            mixer.music.load(BACKGROUND_MUSIC_FILE)
            mixer.music.play((-1))
            logging.info('Background music turned on.')
            speak('Background music has been turned on, sir.')
        except Exception as e:
            logging.error(f'Error turning on background music: {e}')
            speak('An error occurred while turning on the background music.')
            return
    
    if action == 'increase the brightness':
        try:
            current_brightness = sbc.get_brightness()[0]
            new_brightness = min(current_brightness + 10, 100)
            sbc.set_brightness(new_brightness)
            logging.info(f'Brightness increased to {new_brightness}%.')
            speak(f'Brightness increased to {new_brightness} percent, sir.')
        except Exception as e:
            logging.error(f'Error increasing brightness: {e}')
            speak('An error occurred while increasing the brightness.')
            return
    
    if action == 'decrease the brightness':
        try:
            current_brightness = sbc.get_brightness()[0]
            new_brightness = max(current_brightness - 10, 0)
            sbc.set_brightness(new_brightness)
            logging.info(f'Brightness decreased to {new_brightness}%.')
            speak(f'Brightness decreased to {new_brightness} percent, sir.')
        except Exception as e:
            logging.error(f'Error decreasing brightness: {e}')
            speak('An error occurred while decreasing the brightness.')
            return
    
    if action.startswith('increase the brightness ') and '%' in action:
        try:
            percentage = int(action.split(' ')[(-1)].replace('%', ''))
            current_brightness = sbc.get_brightness()[0]
            new_brightness = min(current_brightness + percentage, 100)
            sbc.set_brightness(new_brightness)
            logging.info(f'Brightness increased by {percentage}% to {new_brightness}%.')
            speak(f'Brightness increased by {percentage} percent to {new_brightness} percent, sir.')
        except Exception as e:
            logging.error(f'Error increasing brightness by {percentage}%: {e}')
            speak(f'An error occurred while increasing the brightness by {percentage} percent.')
            return
    
    if action.startswith('decrease the brightness ') and '%' in action:
        try:
            percentage = int(action.split(' ')[(-1)].replace('%', ''))
            current_brightness = sbc.get_brightness()[0]
            new_brightness = max(current_brightness - percentage, 0)
            sbc.set_brightness(new_brightness)
            logging.info(f'Brightness decreased by {percentage}% to {new_brightness}%.')
            speak(f'Brightness decreased by {percentage} percent to {new_brightness} percent, sir.')
        except Exception as e:
            logging.error(f'Error decreasing brightness by {percentage}%: {e}')
            speak(f'An error occurred while decreasing the brightness by {percentage} percent.')
            return
    
    if action == 'increase the volume':
        try:
            for _ in range(4):
                pyautogui.press('volumeup')
            logging.info('Volume increased by 10%.')
            speak('Volume increased by 10 percent, sir.')
        except Exception as e:
            logging.error(f'Error increasing volume: {e}')
            speak('An error occurred while increasing the volume.')
            return
    
    if action == 'decrease the volume':
        try:
            for _ in range(4):
                pyautogui.press('volumedown')
            logging.info('Volume decreased by 10%.')
            speak('Volume decreased by 10 percent, sir.')
        except Exception as e:
            logging.error(f'Error decreasing volume: {e}')
            speak('An error occurred while decreasing the volume.')
            return 
    
    if action.startswith('increase the volume ') and '%' in action:
        try:
            percentage = int(action.split(' ')[(-1)].replace('%', ''))
            steps = int(percentage / 2.5)
            for _ in range(steps):
                pyautogui.press('volumeup')
            logging.info(f'Volume increased by {percentage}%.')
            speak(f'Volume increased by {percentage} percent, sir.')
        except Exception as e:
            logging.error(f'Error increasing volume by {percentage}%: {e}')
            speak(f'An error occurred while increasing the volume by {percentage} percent.')
            return
    
    if action.startswith('decrease the volume ') and '%' in action:
        try:
            percentage = int(action.split(' ')[(-1)].replace('%', ''))
            steps = int(percentage / 2.5)
            for _ in range(steps):
                pyautogui.press('volumedown')
            logging.info(f'Volume decreased by {percentage}%.')
            speak(f'Volume decreased by {percentage} percent, sir.')
            return
        except Exception as e:
            logging.error(f'Error decreasing volume by {percentage}%: {e}')
            speak(f'An error occurred while decreasing the volume by {percentage} percent.')
            return

    if action.startswith('reminder set for'):
        phrase = 'reminder set for'
        start_idx = response.lower().find(phrase)
        if start_idx!= (-1):
            reminder_time_str = response[start_idx + len(phrase):].strip(' .!?')
            if validate_and_set_reminder(reminder_time_str):
                logging.info(f'Reminder scheduled for {reminder_time_str}.')
                print(f'Reminder scheduled for {reminder_time_str}.')
                return
            logging.warning('Invalid time for reminder.')
            print('Invalid time for reminder.')
        return None
    
    if response.startswith('#writing'):
        content = response[len('#writing '):].strip()

        if content:
            try:
                import writing_module
                writing_module.write_to_notepad(content)
                logging.info('Content written to Notepad successfully.')
            except Exception as e:   
                logging.error(f'Error in writing content to Notepad: {e}')
        logging.warning('No content found after \'#writing\'.')

    if action == 'opening camera':
        result = camera_module.open_camera()
        logging.info(result)
    
    if action == 'visual scanning':
        result = camera_module.capture_image(folder_path='analyzer')
        logging.info(result)
                                                                
    if action == 'closing camera':
        result = camera_module.close_camera()
        logging.info(result)

    if action == 'open youtube':
        try:
            subprocess.Popen(['cmd', '/c', 'start', 'chrome', 'https://www.youtube.com'], shell=True)
            logging.info('Opened YouTube.')
            speak('Opening YouTube, sir.')
        except Exception as e:
            logging.error(f'Error opening YouTube: {e}')
            speak('An error occurred while opening YouTube.')
            return 
    
    if action == 'close youtube':
        def close_youtube_tab():
            windows = gw.getAllTitles()
            for window in windows:
                if 'YouTube' in window:
                    print(f'Switching to: {window}')
                    target_window = gw.getWindowsWithTitle(window)[0]
                    target_window.activate()
                    time.sleep(1)
                    pyautogui.hotkey('ctrl', 'w')
                    print('YouTube tab closed.')
                    speak('YouTube tab has been closed, sir.')
                    return True                                                                  
            print('No YouTube tab found.')
            speak('No active YouTube tab found, sir.')
            return False
        if close_youtube_tab():
            logging.info('YouTube tab closed successfully.')
        else:
            logging.warning('Failed to close YouTube tab.')

    if action == 'checking time':
        current_time = datetime.now().strftime('%I:%M %p')
        speak(f'The current time is {current_time}, sir.')
        logging.info(f'Time checked: {current_time}')
    
    if action == 'open google':
        try:
            subprocess.Popen(['cmd', '/c', 'start', 'chrome', 'https://www.google.com'], shell=True)
            logging.info('Opened Google.')
            speak('Opening Google, sir.')
        except Exception as e:
            logging.error(f'Error opening Google: {e}')
            speak('An error occurred while opening Google.')
            return
                                                                                       
    if action == 'open notepad':
        try:
            subprocess.Popen(['cmd', '/c', 'start', 'notepad'], shell=True)
            logging.info('Opened Notepad.')
            speak('Opening Notepad, sir.')
        except Exception as e:
            logging.error(f'Error opening Notepad: {e}')
            speak('An error occurred while opening Notepad.')
            return                   
    
    if action == 'open calculator':
        try:
            subprocess.Popen(['cmd', '/c', 'start', 'calc'], shell=True)
            logging.info('Opened Calculator.')
            speak('Opening Calculator, sir.')
            return
        except Exception as e:
            logging.error(f'Error opening Calculator: {e}')
            speak('An error occurred while opening Calculator.')
            return
    
    if action.startswith('open app '):
        app_name = action.replace('open app', '').strip()
        if not app_name:
            logging.warning('App name not specified for \'open app\' command.')
            speak('Please specify the app name to open.')
            return
        try:
            pyautogui.hotkey('win', 's')
            time.sleep(1)
            pyautogui.typewrite(app_name)
            time.sleep(1)
            pyautogui.press('enter')
            logging.info(f'Opened application: {app_name}.')
            speak(f'Opening {app_name}, sir.')
        except Exception as e:
            logging.error(f'Error opening application \'{app_name}\': {e}')
            speak(f'An error occurred while opening {app_name}.')
            return
    
    if action.startswith('open website '):
        try:
            website_name = action.replace('open website', '').strip()
            if website_name:
                url = f'https://{website_name}'
                subprocess.Popen(['cmd', '/c', 'start', 'chrome', url], shell=True)
                logging.info(f'Opened website: {url}.')
                speak(f'Opening {website_name} in your browser, sir.')
            else:
                logging.warning('Website name not specified for \'open website\' command.')
                speak('Please specify a website name to open.')
        except Exception as e:
            logging.error(f'Error opening website \'{website_name}\': {e}')
            speak(f'An error occurred while opening {website_name}.')
            return
    
    if action == 'checking weather':
        get_weather_info(user_city)
    
    if action == 'opening latest news sir':
        news_url = 'https://www.youtube.com/results?search_query=latest+news'
        try:
            subprocess.Popen(['cmd', '/c', 'start', 'chrome', news_url], shell=True)
            logging.info('Opened latest news on YouTube.')
            speak('Here are the latest news results, sir.')
        except Exception as e:
            logging.error(f'Error opening latest news: {e}')
            speak('An error occurred while opening the latest news.')
            return
    
    if action.startswith('searching on google '):
        search_term = action[len('searching on google '):].strip()
        if search_term:
            encoded_search = '+'.join(search_term.split())
            url = f'https://www.google.com/search?q={encoded_search}'
            try:
                webbrowser.open(url)
                logging.info(f'Searched for \'{search_term}\' on Google.')
                speak(f'Searching for {search_term} on Google, sir.')
            except Exception as e:
                logging.error(f'Error searching for \'{search_term}\' on Google: {e}')
                speak(f'An error occurred while searching for {search_term} on Google.')
                return
        logging.warning('Search term not specified for \'searching on google\' command.')
        speak('Please provide a search term for Google.')

    if action.startswith('searching on youtube '):
        search_term = action[len('searching on youtube '):].strip()
        if search_term:
            encoded_search = '+'.join(search_term.split())
            url = f'https://www.youtube.com/results?search_query={encoded_search}'
            try:
                webbrowser.open(url)
                logging.info(f'Searched for \'{search_term}\' on YouTube.')
                speak(f'Searching for {search_term} on YouTube, sir.')
                return
            except Exception as e:
                logging.error(f'Error searching for \'{search_term}\' on YouTube: {e}')
                speak(f'An error occurred while searching for {search_term} on YouTube.')
                return
        logging.warning('Search term not specified for \'searching on youtube\' command.')
        speak('Please provide a search term for YouTube.')
        return

    if action.startswith('playing song'):
        song_name = action[len('playing song '):].strip()
        if song_name:
            success = play_song_on_youtube(song_name)
            if not success:
                speak('I couldn\'t play the song on YouTube.')
            return None
        logging.warning('Song name not specified for \'playing song\' command.')
        speak('Please specify the song name to play on YouTube.')
        return
    
    if action.startswith('sending ') and ' to ' in action and (' on whatsapp' in action):
        try:
            pattern = '^sending\\s+(.*?)\\s+to\\s+(.*?)\\s+on whatsapp$'
            match = re.match(pattern, action)
            if match:
                message = match.group(1).strip()
                contact_name = match.group(2).strip()
                if message and contact_name:
                    send_whatsapp_message(contact_name, message)
                    return
                else:  
                    logging.warning('Message or contact name is missing for \'sending ... to ... on whatsapp\' command.')
                    speak('Message or contact name is missing.')
                    return
            logging.warning('Failed to parse \'sending ... to ... on whatsapp\' command.')
            speak('I couldn\'t understand the WhatsApp message command.')
        except Exception as e:
            logging.error(f'Error processing WhatsApp message command: {e}')
            speak('An error occurred while trying to send the WhatsApp message.')
                    


def start_reminder_checker():
    reminder_thread = threading.Thread(target=check_reminders, daemon=True)
    reminder_thread.start()
    logging.info('Started reminder checker thread.')

def initialize_background_music():
    """\n    Initializes and starts background music.\n    """  # inserted
    try:
        mixer.init()
        mixer.music.load(BACKGROUND_MUSIC_FILE)
        mixer.music.play((-1))
        logging.info('Background music started.')
    except Exception as e:
        logging.error(f'Error initializing background music: {e}')
        speak('An error occurred while initializing background music.')

def main():
    """\n    Main function to initialize automation tasks.\n    """  # inserted
    logging.info('Automation script started.')
    initialize_background_music()
    start_reminder_checker()
if __name__ == '__main__':
    main()