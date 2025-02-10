import sys
import os
import time
import json
import threading
import psutil
import pyautogui
import requests
from datetime import datetime, timedelta
from cryptography.fernet import Fernet, InvalidToken
import webbrowser
import re
import urllib.parse
import pygame
import screen_brightness_control as sbc
from groq import Groq
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QGridLayout, QPushButton, QHBoxLayout, QMessageBox, QGraphicsDropShadowEffect
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QFontDatabase, QFont, QColor, QLinearGradient, QPalette, QBrush
from Gui import AtlasUI
from automation import perform_automation_action, check_reminders, speak, is_speaking
from listening import Listener

def get_base_path():
    """Get the base path for the current execution."""  # inserted
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        return base_path
    base_path = os.path.dirname(os.path.abspath(__file__))
    return base_path

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""  # inserted
    base_path = get_base_path()
    return os.path.join(base_path, relative_path)
MATERIALS_PATH = resource_path('materials')
print(f'[DEBUG] MATERIALS_PATH resolved to: {MATERIALS_PATH}')
if not os.path.exists(MATERIALS_PATH):
    raise FileNotFoundError(f'Materials folder not found at: {MATERIALS_PATH}')
KEY_FILE = os.path.join(MATERIALS_PATH, 'system.cfg')
RECOVER_FILE = os.path.join(MATERIALS_PATH, 'recover.txt')
BACKGROUND_MUSIC_FILE = os.path.join(MATERIALS_PATH, 'brain_power_music.mp3')
PHONE_NUMBERS_FILE = os.path.join(MATERIALS_PATH, 'PhoneNumbers.txt')
WEATHER_API_KEY_FILE = os.path.join(MATERIALS_PATH, 'weather_api_key.txt')
INITIAL_PROMPT_FILE = os.path.join(MATERIALS_PATH, 'system.initialize')
for file_path, description in [(KEY_FILE, 'System Configuration File'), (RECOVER_FILE, 'Recovery File'), (BACKGROUND_MUSIC_FILE, 'Background Music File'), (PHONE_NUMBERS_FILE, 'Phone Numbers File'), (WEATHER_API_KEY_FILE, 'Weather API Key File'), (INITIAL_PROMPT_FILE, 'Initial Prompt File')]:
    if not os.path.exists(file_path):
        print(f'[ERROR] {description} not found at: {file_path}')
    else:  # inserted
        print(f'[DEBUG] {description} found at: {file_path}')
PREDEFINED_SECURITY_KEY = '99ChEATlATdU510LwVpGllMROGguHSKyGk-z0GB3sRw='
CHAT_HISTORY_FILE = os.path.join(MATERIALS_PATH, 'chat_history.json')
IMAGE_ANALYZER_HISTORY_FILE = os.path.join(MATERIALS_PATH, 'image_analyzer_history.json')
REMINDERS = []
reminder_lock = threading.Lock()
KEY_DURATIONS = {'atlas-weekly-pro': timedelta(days=7), 'atlas-monthly-elite': timedelta(days=30), 'atlas-lifetime-master': None, 'atlas-testing-key': timedelta(minutes=5)}
try:
    fernet = Fernet(PREDEFINED_SECURITY_KEY.encode())
except ValueError as e:
    pass  # postinserted
else:  # inserted
    def remove_emojis(text):
        """Remove emojis from the given text."""  # inserted
        emoji_pattern = re.compile('[😀-🙏🌀-🗿🚀-🛿🇠-🇿✂-➰Ⓜ-🉑]+', flags=re.UNICODE)
        return emoji_pattern.sub('', text)

    class SubscriptionGUI(QDialog):
        def __init__(self, materials_path, parent=None):
            super(SubscriptionGUI, self).__init__(parent)
            self.materials_path = materials_path
            self.setWindowTitle('Atlas - Subscription Key')
            self.setFixedSize(500, 300)
            self.init_ui()

        def init_ui(self):
            self.setStyleSheet('background-color: #000000;')
            roboto_font_path = resource_path(os.path.join('materials', 'Roboto-Regular.ttf'))
            if os.path.exists(roboto_font_path):
                QFontDatabase.addApplicationFont(roboto_font_path)
            else:  # inserted
                print(f'Font file \'{roboto_font_path}\' not found.')
            try:
                sci_fi_title_font = QFont('Audiowide', 22)
            except:
                sci_fi_title_font = QFont('Arial', 22)
            else:  # inserted
                pass  # postinserted
            professional_font = QFont('Roboto', 12)
            input_font = QFont('Orbitron', 12)
            layout = QGridLayout()
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)
            self.title_label = QLabel('ENTER SUBSCRIPTION KEY')
            self.title_label.setFont(sci_fi_title_font)
            self.title_label.setAlignment(Qt.AlignCenter)
            self.title_label.setStyleSheet('color: #00FFFF;')
            self.apply_glow_effect(self.title_label, QColor(0, 255, 255, 160))
            layout.addWidget(self.title_label, 0, 0, 1, 2)
            label_style = '\n            QLabel {\n                color: #39FF14; /* Neon Green */\n                font-weight: bold;\n                font-size: 14px;\n            }\n        '
            input_style = '\n            QLineEdit {\n                color: #00FFFF;                  /* Electric Cyan Blue text */\n                background-color: #000000;       /* Black background */\n                border: 2px solid #39FF14;       /* Neon Green border */\n                padding: 10px;\n                font-size: 14px;\n                border-radius: 8px;\n            }\n            QLineEdit:focus {\n                border: 2px solid #00FF7F;       /* Spring Green border on focus */\n                background-color: #1A1A1A;       /* Darker black on focus */\n            }\n        '
            self.key_label = QLabel('Subscription Key:')
            self.key_label.setFont(professional_font)
            self.key_label.setStyleSheet(label_style)
            layout.addWidget(self.key_label, 1, 0)
            self.key_input = QLineEdit()
            self.key_input.setFont(input_font)
            self.key_input.setPlaceholderText('Enter your subscription key')
            self.key_input.setStyleSheet(input_style)
            layout.addWidget(self.key_input, 1, 1)
            self.submit_button = QPushButton('Save')
            self.submit_button.setFont(QFont('Orbitron', 14))
            self.submit_button.setStyleSheet('\n            QPushButton {\n                color: #FFFFFF;\n                background-color: qlineargradient(\n                    x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #00FFFF, stop:1 #1E90FF\n                );\n                border: none;\n                border-radius: 8px;\n                padding: 10px 20px;\n            }\n            QPushButton:hover {\n                background-color: qlineargradient(\n                    x1:0, y1:0, x2:0, y2:1,\n                    stop:0 #1E90FF, stop:1 #00BFFF\n                );\n            }\n        ')
            self.submit_button.clicked.connect(self.submit_key)
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(self.submit_button)
            button_layout.addStretch()
            layout.addLayout(button_layout, 2, 0, 1, 2)
            self.setLayout(layout)
            self.enable_enter_key_navigation()

        def apply_glow_effect(self, widget, color):
            """Applies a glowing effect to a widget."""  # inserted
            glow = QGraphicsDropShadowEffect()
            glow.setBlurRadius(20)
            glow.setColor(color)
            glow.setOffset(0)
            widget.setGraphicsEffect(glow)

        def enable_enter_key_navigation(self):
            """Connect Enter key to move focus to the next input field or trigger save."""  # inserted
            self.key_input.returnPressed.connect(self.submit_key)

        def submit_key(self):
            """Validate and accept the subscription key."""  # inserted
            subscription_key = self.key_input.text().strip()
            if not subscription_key:
                QMessageBox.warning(self, 'Input Error', 'Subscription key cannot be empty.')
                return
            self.subscription_key = subscription_key
            self.accept()

        def get_subscription_key(self):
            """Retrieve the entered subscription key."""  # inserted
            return self.subscription_key

    class UserInfoGUI(QDialog):
        def __init__(self, materials_path, parent=None):
            super(UserInfoGUI, self).__init__(parent)
            self.materials_path = materials_path
            self.setWindowTitle('Atlas - User Information')
            self.setFixedSize(600, 400)
            self.init_ui()

        def init_ui(self):
            self.setStyleSheet('background-color: #000000;')
            audiowide_font_path = resource_path(os.path.join('materials', 'Audiowide-Regular.ttf'))
            roboto_font_path = resource_path(os.path.join('materials', 'Roboto-Regular.ttf'))
            if os.path.exists(audiowide_font_path):
                QFontDatabase.addApplicationFont(audiowide_font_path)
            else:  # inserted
                print(f'Font file \'{audiowide_font_path}\' not found.')
            if os.path.exists(roboto_font_path):
                QFontDatabase.addApplicationFont(roboto_font_path)
            else:  # inserted
                print(f'Font file \'{roboto_font_path}\' not found.')
            try:
                sci_fi_title_font = QFont('Audiowide', 24)
            except:
                sci_fi_title_font = QFont('Arial', 24)
            else:  # inserted
                pass  # postinserted
            professional_font = QFont('Roboto', 12)
            input_font = QFont('Orbitron', 12)
            layout = QGridLayout()
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)
            self.title_label = QLabel('USER INFORMATION')
            self.title_label.setFont(sci_fi_title_font)
            self.title_label.setAlignment(Qt.AlignCenter)
            self.title_label.setStyleSheet('color: #00FFFF;')
            self.apply_glow_effect(self.title_label, QColor(0, 255, 255, 160))
            layout.addWidget(self.title_label, 0, 0, 1, 2)
            label_style = '\n            QLabel {\n                color: #39FF14; /* Neon Green */\n                font-weight: bold;\n                font-size: 14px;\n            }\n        '
            input_style = '\n            QLineEdit {\n                color: #FFFFFF;\n                background-color: #000000;       /* Black background */\n                border: 2px solid #00FFFF;       /* Electric Cyan Blue border */\n                padding: 10px;\n                font-size: 14px;\n                border-radius: 8px;\n            }\n            QLineEdit:focus {\n                border: 2px solid #1E90FF;       /* Dodger Blue border on focus */\n                background-color: #1A1A1A;       /* Darker black on focus */\n            }\n        '
            self.name_label = QLabel('Name:')
            self.name_label.setFont(professional_font)
            self.name_label.setStyleSheet(label_style)
            layout.addWidget(self.name_label, 1, 0)
            self.name_input = QLineEdit()
            self.name_input.setFont(input_font)
            self.name_input.setPlaceholderText('Enter your name')
            self.name_input.setStyleSheet(input_style)
            layout.addWidget(self.name_input, 1, 1)
            self.age_label = QLabel('Age:')
            self.age_label.setFont(professional_font)
            self.age_label.setStyleSheet(label_style)
            layout.addWidget(self.age_label, 2, 0)
            self.age_input = QLineEdit()
            self.age_input.setFont(input_font)
            self.age_input.setPlaceholderText('Enter your age')
            self.age_input.setStyleSheet(input_style)
            layout.addWidget(self.age_input, 2, 1)
            self.city_label = QLabel('City:')
            self.city_label.setFont(professional_font)
            self.city_label.setStyleSheet(label_style)
            layout.addWidget(self.city_label, 3, 0)
            self.city_input = QLineEdit()
            self.city_input.setFont(input_font)
            self.city_input.setPlaceholderText('Enter your city')
            self.city_input.setStyleSheet(input_style)
            layout.addWidget(self.city_input, 3, 1)
            self.interests_label = QLabel('Interests:')
            self.interests_label.setFont(professional_font)
            self.interests_label.setStyleSheet(label_style)
            layout.addWidget(self.interests_label, 4, 0)
            self.interests_input = QLineEdit()
            self.interests_input.setFont(input_font)
            self.interests_input.setPlaceholderText('Enter your interests (comma-separated)')
            self.interests_input.setStyleSheet(input_style)
            layout.addWidget(self.interests_input, 4, 1)
            self.save_button = QPushButton('Save')
            self.save_button.setFont(QFont('Orbitron', 14))
            self.save_button.setFixedWidth(150)
            self.save_button.setStyleSheet('\n            QPushButton {\n                color: #FFFFFF;\n                background-color: qlineargradient(\n                    x1:0, y1:0, x2:1, y2:1,\n                    stop:0 #00FFFF, stop:1 #1E90FF\n                );\n                border: none;\n                border-radius: 8px;\n                padding: 10px 20px;\n            }\n            QPushButton:hover {\n                background-color: qlineargradient(\n                    x1:0, y1:0, x2:1, y2:1,\n                    stop:0 #1E90FF, stop:1 #00BFFF\n                );\n            }\n        ')
            self.save_button.clicked.connect(self.save_user_info)
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(self.save_button)
            button_layout.addStretch()
            layout.addLayout(button_layout, 5, 0, 1, 2)
            self.setLayout(layout)
            self.enable_enter_key_navigation()

        def apply_glow_effect(self, widget, color):
            """Applies a glowing effect to a widget."""  # inserted
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(20)
            shadow.setColor(color)
            shadow.setOffset(0)
            widget.setGraphicsEffect(shadow)

        def enable_enter_key_navigation(self):
            """Connect Enter key to move focus to the next input field or trigger save."""  # inserted
            self.name_input.returnPressed.connect(self.age_input.setFocus)
            self.age_input.returnPressed.connect(self.city_input.setFocus)
            self.city_input.returnPressed.connect(self.interests_input.setFocus)
            self.interests_input.returnPressed.connect(self.save_user_info)

        def save_user_info(self):
            """Save user information and close the dialog."""  # inserted
            name = self.name_input.text().strip()
            age = self.age_input.text().strip()
            city = self.city_input.text().strip()
            interests = self.interests_input.text().strip()
            if not name or not age or (not city) or (not interests):
                QMessageBox.warning(self, 'Input Error', 'All fields must be filled out.')
                return
            if not age.isdigit():
                QMessageBox.warning(self, 'Input Error', 'Age must be a number.')
                return
            user_data = {'name': name, 'age': int(age), 'city': city, 'interests': [interest.strip() for interest in interests.split(',')]}
            self.user_data = user_data
            self.accept()

        def get_user_data(self):
            """Retrieve the entered user data."""  # inserted
            return self.user_data

    class ConversationWorker(QThread):
        userMessageSignal = pyqtSignal(str)
        botResponseSignal = pyqtSignal(str)
        finishedSignal = pyqtSignal()

        def __init__(self, user_details=None, parent=None):
            super().__init__(parent)
            self._running = True
            self.user_details = user_details or {}
            self.chat_history = load_chat_history()
            self.groq_client = None
            self.initialize_groq_client()

        def initialize_groq_client(self):
            """Initialize the Groq API client."""  # inserted
            API_KEY = get_current_api_key()
            if not API_KEY:
                speak('API key is missing. Please provide a valid API key.')
                print('API key is missing.')
                sys.exit(1)
            self.groq_client = Groq(api_key=API_KEY)

        def process_user_input(self, command):
            """\n        All the logic that used to be in the \'while True\' loop for processing recognized user speech.\n        This method can be called externally whenever new text is recognized.\n        """  # inserted
            print(f'[Worker] Received user command: {command}')
            self.userMessageSignal.emit(command)
            if 'exit' in command or 'quit' in command:
                speak('Goodbye! Have a great day.')
                self.stop()
                return
            try:
                if not self.groq_client:
                    self.initialize_groq_client()
                messages = prepare_messages_for_groq(command, CHAT_HISTORY_FILE, IMAGE_ANALYZER_HISTORY_FILE, user_details=self.user_details)
                completion = self.groq_client.chat.completions.create(model='llama3-70b-8192', messages=messages, temperature=1, max_tokens=1024, top_p=1, stream=False, stop=None)
                response_text = completion.choices[0].message.content.strip()
                if response_text:
                    filtered_response = remove_emojis(response_text)
                    if not response_text.startswith('#writing'):
                        self.botResponseSignal.emit(response_text)
                        speak(filtered_response)
                    self.chat_history.append({'role': 'assistant', 'content': response_text})
                    perform_automation_action(response_text, self.user_details)
                    save_response_to_file(response_text)
                    self.chat_history.append({'role': 'user', 'content': command})
                    save_chat_history(self.chat_history)
                else:  # inserted
                    print('No valid response from Atlas.')
            except Exception as e:
                err_msg = f'Error with Groq API: {e}'
                print(err_msg)
                speak('Sorry, I encountered an error while processing your request.')



        def run(self):
            """\n        If you still need a separate thread for any background tasks,\n        you can keep them here. But the microphone listening no longer lives here.\n        """  # inserted
            while self._running:
                time.sleep(0.1)
            self.finishedSignal.emit()

        def stop(self):
            self._running = False
            print('[Worker] Stopping conversation worker...')

    def load_initial_prompt():
        """\n    Load the initial prompt from the system.initialize file.\n    Returns the content as a string.\n    """  # inserted
        INITIAL_PROMPT_FILE = os.path.join(MATERIALS_PATH, 'system.initialize')
        if not os.path.exists(INITIAL_PROMPT_FILE):
            error_message = f'Initial prompt file not found at: {INITIAL_PROMPT_FILE}'
            print(f'[ERROR] {error_message}')
            speak('Initial prompt file is missing. Please contact support.')
            sys.exit(1)
        try:
            with open(INITIAL_PROMPT_FILE, 'r', encoding='utf-8') as f:
                initial_prompt = f.read().strip()
                if not initial_prompt:
                    raise ValueError('Initial prompt file is empty.')
                print('[DEBUG] Initial prompt loaded successfully.')
                return initial_prompt
        except Exception as e:
            error_message = f'Failed to load initial prompt: {e}'
            print(f'[ERROR] {error_message}')
            speak('Failed to load the initial prompt. Please contact support.')
            sys.exit(1)

    def load_chat_history():
        if os.path.exists(CHAT_HISTORY_FILE):
            try:
                with open(CHAT_HISTORY_FILE, 'r') as f:
                    history = json.load(f)
                    if isinstance(history, list):
                        return history[(-30):]
                    else:  # inserted
                        print(f'[ERROR] Expected a list in {CHAT_HISTORY_FILE}, got {type(history)}.')
                        return []
            except json.JSONDecodeError:
                speak('Chat history file is corrupted.')
                print(f'[ERROR] Chat history file {CHAT_HISTORY_FILE} is corrupted.')
                return []
                    
        else:
            return []
            

    def save_chat_history(history):
        recent_history = history[(-30):]
        try:
            with open(CHAT_HISTORY_FILE, 'w') as f:
                json.dump(recent_history, f, indent=2)
                print(f'[DEBUG] Chat history saved with {len(recent_history)} messages.')
        except Exception as e: 
            print(f'[ERROR] Failed to save chat history: {e}')

    def save_response_to_file(response_text):
        clean_response = ''.join((c for c in response_text if c.isprintable()))
        sci_fi_response = f'[96m{clean_response}[0m'
        print(sci_fi_response)

    def get_time_based_greeting():
        hour = datetime.now().hour
        if 4 <= hour < 12:
            return 'Good morning'
        if 12 <= hour < 17:
            return 'Good afternoon'
        if 17 <= hour < 21:
            return 'Good evening'
        else:  # inserted
            return 'Hello'

    def is_subscription_valid(subscription_data, user_data):
        subscription_key = subscription_data.get('subscription_key')
        subscription_start = subscription_data.get('subscription_start')
        if not subscription_key or not subscription_start:
            return (False, 'No subscription details found.')
        if subscription_key not in KEY_DURATIONS:
            return (False, 'Invalid subscription key.')
        start_time = datetime.strptime(subscription_start, '%Y-%m-%d %H:%M:%S')
        if KEY_DURATIONS[subscription_key] is None:
            return (True, 'Initializing lifetime access.')
        expire_time = start_time + KEY_DURATIONS[subscription_key]
        if datetime.now() > expire_time:
            return (False, 'Your subscription has expired. Please renew your access.\n\nFor assistance, contact:\nEmail: Shoaibhassanfacebook@gmail.com\nWhatsApp: 03208623171.')
        elif subscription_key == 'atlas-weekly-pro':
            activation_message = 'Initializing weekly access.'
        elif subscription_key == 'atlas-monthly-elite':
            activation_message = 'Initializing monthly access.'
        elif subscription_key == 'atlas-testing-key':
            activation_message = '5-minute test mode activated successfully.'
        else:
            activation_message = 'Subscription activated successfully.'
        if not user_data.get('activation_notified', False):
            return (True, activation_message, True)
        return (True, activation_message, False)

    def collect_subscription_key():
        print('Launching Subscription Key GUI...')
        speak('Enter your subscription key')
        subscription_dialog = SubscriptionGUI(materials_path=MATERIALS_PATH)
        result = subscription_dialog.exec_()
        if result == QDialog.Accepted:
            subscription_key = subscription_dialog.get_subscription_key()
            if subscription_key:
                return subscription_key
            print('No subscription key entered.')
            speak('No subscription key entered. Exiting.')
            sys.exit(1)
        else:  # inserted
            print('Subscription key dialog was canceled.')
            speak('Subscription key entry was canceled. Exiting.')
            sys.exit(1)

    def collect_user_details():
        print('Launching User Information GUI...')
        speak('Please enter your user information')
        user_info_dialog = UserInfoGUI(materials_path=MATERIALS_PATH)
        result = user_info_dialog.exec_()
        if result == QDialog.Accepted:
            user_data = user_info_dialog.get_user_data()
            if user_data:
                return user_data
            print('No user information entered.')
            speak('No user information entered. Exiting.')
            sys.exit(1)
        else:  # inserted
            print('User information dialog was canceled.')
            speak('User information entry was canceled. Exiting.')
            sys.exit(1)

    def encrypt_and_append_subscription_key(subscription_key):
        encrypted_key = fernet.encrypt(subscription_key.encode()).decode()
        if not os.path.exists(KEY_FILE):
            with open(KEY_FILE, 'w') as f:
                f.write(PREDEFINED_SECURITY_KEY)
        with open(KEY_FILE, 'r') as f:
            content = f.read().strip()
        if content.count('/.') < 1:
            new_content = f'{content}/.{encrypted_key}'
            with open(KEY_FILE, 'w') as f:
                f.write(new_content)
            print('[DEBUG] Subscription key encrypted and appended to system.cfg.')

    def save_user_data(user_data):
        user_data_json = json.dumps(user_data).encode()
        encrypted_user_data = fernet.encrypt(user_data_json).decode()
        with open(KEY_FILE, 'r') as f:
            content = f.read().strip()
        if content.count('/.') < 2:
            new_content = f'{content}/.{encrypted_user_data}'
            with open(KEY_FILE, 'w') as f:
                f.write(new_content)
            print('[DEBUG] User data encrypted and appended to system.cfg.')

    def load_data_from_system_cfg():
        if not os.path.exists(KEY_FILE):
            error_message = 'Error: system solution file not found. Please contact the Atlas team.'
            print(error_message)
            speak(error_message)
            sys.exit(1)
        with open(KEY_FILE, 'r') as f:
            content = f.read().strip()
        if not content.startswith(PREDEFINED_SECURITY_KEY):
            error_message = 'Error: system solution file not found. Please contact the Atlas team.'
            print(error_message)
            speak(error_message)
            sys.exit(1)
        parts = content.split('/.')
        if len(parts) == 1:
            return (False, False, None, None)
        if len(parts) == 2:
            encrypted_sub_key = parts[1]
            try:
                subscription_key = fernet.decrypt(encrypted_sub_key.encode()).decode()
            except InvalidToken:
                pass  # postinserted
            else:  # inserted
                return (True, False, subscription_key, None)
        if len(parts) == 3:
            encrypted_sub_key = parts[1]
            encrypted_user_data = parts[2]
            try:
                subscription_key = fernet.decrypt(encrypted_sub_key.encode()).decode()
            except InvalidToken:
                pass
            else:  # inserted
                try:
                    decrypted_user_data = fernet.decrypt(encrypted_user_data.encode()).decode()
                    user_data = json.loads(decrypted_user_data)
                    return (True, True, subscription_key, user_data)
                except InvalidToken:
                    pass  # postinserted

        error_message = 'Error: system solution file not found. Please contact the Atlas team.'
        print(error_message)
        speak(error_message)
        sys.exit(1)


    def get_current_api_key():
        default_api_key = ''
        recover_file_path = os.path.join(MATERIALS_PATH, 'recover.txt')
        if os.path.exists(recover_file_path):
            try:
                with open(recover_file_path, 'r', encoding='utf-8') as f:
                    user_api_key = f.read().strip()
                    return user_api_key if user_api_key else default_api_key
            except Exception as e:         
                print(f'[ERROR] Error reading {recover_file_path}: {e}')
                return default_api_key

    def play_background_music(music_file, volume=0.05):
        music_path = os.path.join(MATERIALS_PATH, music_file)
        try:
            pygame.mixer.init()
            if not os.path.exists(music_path):
                print(f'[WARNING] Music file \'{music_file}\' not found in materials folder. Skipping.')
            else:  # inserted
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play((-1))
                print('[DEBUG] Background music started.')
        except ImportError:
            print('[ERROR] pygame is not installed. Background music will be disabled.')
        except Exception as e:
            print(f'[ERROR] Failed to play background music: {e}')

    def load_last_n_entries(file_path, n):
        """\n    Load the last n entries from a JSON file. If the file does not exist, create it with an empty list.\n\n    Args:\n        file_path (str): Path to the JSON file.\n        n (int): Number of entries to load.\n\n    Returns:\n        list: A list of the last n entries.\n    """  # inserted
        if not os.path.exists(file_path):
            print(f'[WARNING] {file_path} does not exist. Creating a new empty history file.')
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
                return []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    print(f'[ERROR] Expected a list in {file_path}, but got {type(data)}. Resetting to empty list.')
                    data = []
                    with open(file_path, 'w', encoding='utf-8') as fw:
                        json.dump(data, fw, indent=2)
                    return []
                else:  
                    return data[-n:]
        except json.JSONDecodeError:
            print(f'[ERROR] Failed to decode JSON from {file_path}. Resetting to empty list.')
            with open(file_path, 'w', encoding='utf-8') as fw:
                json.dump([], fw, indent=2)
            return []    
            
        except Exception as e:
            print(f'[ERROR] An unexpected error occurred while loading {file_path}: {e}')
            return []

    def prepare_messages_for_groq(command, chat_history_file, image_history_file, user_details=None):
        """\n    Prepare the messages list for the Groq API by combining chat and image analyzer histories with the current command.\n\n    Args:\n        command (str): The current user query.\n        chat_history_file (str): Path to chat_history.json.\n        image_history_file (str): Path to image_analyzer_history.json.\n        user_details (dict, optional): User details to include in the first API prompt.\n\n    Returns:\n        list: A list of message dictionaries.\n    """  # inserted
        messages = []
        initial_prompt = load_initial_prompt()
        messages.append({'role': 'system', 'content': initial_prompt})
        if user_details:
            user_details_str = json.dumps(user_details, indent=2)
            messages.append({'role': 'system', 'content': f'### User Details\n{user_details_str}'})
        messages.append({'role': 'system', 'content': '### Chat History (Last 6 Messages)'})
        chat_history = load_last_n_entries(chat_history_file, 6)
        if chat_history:
            for idx, msg in enumerate(chat_history, start=1):
                role = msg.get('role')
                content = msg.get('content')
                if role not in ('user', 'assistant'):
                    print(f'[DEBUG] Invalid role in chat_history.json at index {idx}: {role}')
                else:  # inserted
                    if not content:
                        print(f'[DEBUG] Missing content in chat_history.json at index {idx}.')
                    else:  # inserted
                        messages.append({'role': role, 'content': content})
        else:  # inserted
            print('[DEBUG] No chat history available to load.')
        messages.append({'role': 'system', 'content': '### Image Analysis History (Last 2 Messages)'})
        image_history_entries = load_last_n_entries(image_history_file, 2)
        if image_history_entries:
            for idx, entry in enumerate(image_history_entries, start=1):
                response = entry.get('after seeing the image')
                if response:
                    messages.append({'role': 'assistant', 'content': response})
                else:  # inserted
                    print(f'[DEBUG] Image analyzer history entry missing \'response\' at index {idx}: {entry}')
        else:  # inserted
            print('[DEBUG] No image analyzer history available to load.')
        messages.append({'role': 'system', 'content': '### Current Query'})
        if command:
            messages.append({'role': 'user', 'content': command})
        else:  # inserted
            print('[DEBUG] No user command provided.')
        print('[DEBUG] Prepared messages for Groq API:')
        for i, msg in enumerate(messages):
            role = msg.get('role')
            content_preview = msg.get('content')[:50] + ('...' if len(msg.get('content', '')) > 50 else '')
            print(f'  Message {i}: Role={role}, Content={content_preview}')
        valid_roles = {'assistant', 'user', 'system'}
        for i, msg in enumerate(messages):
            role = msg.get('role')
            content = msg.get('content')
            if role not in valid_roles:
                print(f'[ERROR] Invalid role \'{role}\' in message {i}.')
            if not isinstance(content, str) or not content.strip():
                print(f'[ERROR] Invalid or empty content in message {i}.')
        return messages

    def main():
        app = QApplication(sys.argv)
        app.setFont(QFont('Orbitron', 14))
        try:
            has_valid_cfg, has_user_data, subscription_key, user_data = load_data_from_system_cfg()
            reminder_thread = threading.Thread(target=check_reminders, daemon=True)
            reminder_thread.start()
            if not has_valid_cfg and (not has_user_data):
                entered_key = collect_subscription_key()
                encrypt_and_append_subscription_key(entered_key)
                speak('Subscription key saved. Please restart the application.')
                print('Subscription key saved. Please restart.')
                time.sleep(5)
                sys.exit(0)
        except SystemExit:
            pass  # postinserted
            
        if has_valid_cfg and (not has_user_data):
            user_details = collect_user_details()
            subscription_start = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            duration = None
            unit = None
            if subscription_key == 'atlas-weekly-pro':
                duration = 7
                unit = 'days'
            elif subscription_key == 'atlas-monthly-elite':
                duration = 30
                unit = 'days'
            elif subscription_key == 'atlas-lifetime-master':
                duration = None
                unit = None
            elif subscription_key == 'atlas-testing-key':
                duration = 5
                unit = 'minutes'
            new_data = {'subscription_data': {'subscription_key': subscription_key, 'subscription_start': subscription_start, 'duration': duration, 'unit': unit}, 'user_details': user_details, 'activation_notified': False}
            save_user_data(new_data)
            speak('User details saved. Please restart the application.')
            print('User details saved. Please restart.')
            time.sleep(5)
            sys.exit(0)
        subscription_data = user_data.get('subscription_data')
        user_details = user_data.get('user_details')
        valid_response = is_subscription_valid(subscription_data, user_data)
        valid = valid_response[0]
        message = valid_response[1]
        rest = valid_response[2:] if len(valid_response) > 2 else []
        if not valid:
            speak(message)
            print(message)
            time.sleep(5)
            sys.exit(0)
        else:  # inserted
            if len(rest) > 0 and rest[0]:
                print(message)
        greeting = get_time_based_greeting()
        user_name = user_details.get('name', 'User')
        welcome_message = f'{greeting}, {user_name}! How can I assist you today?'
        play_background_music('brain_power_music.mp3', volume=0.05)
        try:
            ui = AtlasUI()
            ui.show()

            def delayed_speak():
                print(f'[DEBUG] Speaking welcome message: {welcome_message}')
                speak(welcome_message)
                print('[DEBUG] Finished speaking welcome message.')
            QTimer.singleShot(100, delayed_speak)
            conv_worker = ConversationWorker(user_details=user_details)
            conv_worker.userMessageSignal.connect(ui.update_user_said_in_gui)
            conv_worker.botResponseSignal.connect(ui.append_bot_response_in_gui)
            conv_worker.start()

            def on_recognized_text(command):
                conv_worker.process_user_input(command)

            def on_listening_error(error_msg):
                print(f'[Main] Listening Error: {error_msg}')
            listener = Listener(on_recognized_callback=on_recognized_text, on_error_callback=on_listening_error, phrase_time_limit=30, pause_threshold=1.0)
            listener.start()
            ui.set_listener(listener)

            def on_app_close():
                listener.stop()
                listener.join()
                conv_worker.stop()
                conv_worker.wait(3000)
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
                except Exception as e:
                    print(f'[ERROR] Error stopping pygame mixer: {e}')
            app.aboutToQuit.connect(on_app_close)
            sys.exit(app.exec_())
            return
        except Exception as e:
            print(f'[ERROR] Failed to initialize AtlasUI: {e}')
            speak('Failed to initialize the main interface. Please contact support.')
            sys.exit(1)

            
           
if __name__ == '__main__':
    main()
    print(f'Invalid security key format: {e}')
    sys.exit(1)