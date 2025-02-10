import pyttsx3
import logging
import threading
import re
engine = None
is_speaking = threading.Event()

def init_tts():
    """Initialize pyttsx3 engine only once."""
    global engine
    if engine is None:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)

def remove_emojis(text):
    """Remove emojis and other non-text characters from the given text."""
    emoji_pattern = re.compile('[😀-🙏🌀-🗿🚀-\U0001f6ff\U0001f1e0-🇿✂-➰Ⓜ-🉑🤀-🧿🩰-\U0001faff─-⯯🀘-\U0001f270🙐-🙿]+', flags=re.UNICODE)
    return emoji_pattern.sub('', text)

def speak(text):
    """Speak the given text and toggle speaking state."""
    text_without_emojis = remove_emojis(text)
    is_speaking.set()
    logging.info('is_speaking set to True')
    try:
        engine.say(text_without_emojis)
        engine.runAndWait()
    except Exception as e:
        is_speaking.clear()
        logging.info('is_speaking set to False')
        logging.error(f'Error in speak function: {e}')
init_tts()