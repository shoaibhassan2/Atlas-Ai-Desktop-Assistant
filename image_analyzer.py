
import os
import json
import time
import google.generativeai as genai
import pyttsx3
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
GOOGLE_API_KEY = 'AIzaSyCDUmcsmkOTh8NVq7gMejd7vHZ05UyK9Io'
genai.configure(api_key=GOOGLE_API_KEY)

class ImageFolderHandler(FileSystemEventHandler):
    """\n    Handles events for the folder where images are stored.\n    """

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            process_image(event.src_path)

def process_image(image_path):
    """\n    Processes the newly added image.\n    Args:\n        image_path (str): Path to the new image.\n    """  # inserted
    print(f'Processing image: {image_path}')
    uploaded_file = upload_to_gemini(image_path, mime_type='image/jpeg', retries=3, delay=2)
    if not uploaded_file:
        print(f'Failed to upload the image: {image_path}')
        return
    generation_config = {'temperature': 1, 'top_p': 0.95, 'top_k': 40, 'max_output_tokens': 100, 'response_mime_type': 'text/plain'}
    model = genai.GenerativeModel(model_name='gemini-1.5-flash', generation_config=generation_config)
    analysis_response = analyze_image(model, uploaded_file)
    print(f'Analysis Response: {analysis_response}')
    speak_text(analysis_response)
    save_to_chat_history(image_path, analysis_response, 'materials/image_analyzer_history.json')
    delete_image(image_path)

def upload_to_gemini(path, mime_type=None, retries=3, delay=2):
    """\n    Uploads the given file to Gemini with retry mechanism.\n\n    Args:\n        path (str): Path to the file to be uploaded.\n        mime_type (str, optional): MIME type of the file.\n        retries (int): Number of retry attempts for upload.\n        delay (int): Delay in seconds between retries.\n\n    Returns:\n        UploadedFile: The uploaded file object from Gemini or None if failed.\n    """  # inserted
    for attempt in range(retries):
        try:
            file = genai.upload_file(path, mime_type=mime_type)
            print(f'Uploaded file \'{file.display_name}\' as: {file.uri}')
            return file
        except Exception as e:
            print(f'All upload attempts failed for {path}.')
            print(f'Upload attempt {attempt + 1} failed for {path}: {e}')
            if attempt < retries - 1:
                time.sleep(delay)

def analyze_image(model, image_file):
    """\n    Sends the image to Gemini for analysis and returns the response.\n\n    Args:\n        model (GenerativeModel): Configured Gemini generative model.\n        image_file (UploadedFile): The uploaded image file object.\n\n    Returns:\n        str: The analysis response from Gemini.\n    """  # inserted
    try:
        chat_session = model.start_chat(history=[{'role': 'user', 'parts': [image_file, 'What are you seeing? Answer me in a single line.']}])
        response = chat_session.send_message('What are you seeing?')
        return response.text
    except Exception as e:
        print(f'Error during image analysis: {e}')
        return 'I encountered an error while analyzing the image.'

def speak_text(text):
    """\n    Converts the given text to speech and plays it aloud.\n\n    Args:\n        text (str): The text to be spoken.\n    """  # inserted
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 1.0)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f'Error during text-to-speech: {e}')

def delete_image(path):
    """\n    Deletes the specified image file from the filesystem.\n\n    Args:\n        path (str): Path to the image file to be deleted.\n    """  # inserted
    try:
        os.remove(path)
        print(f'Deleted image: {path}')
    except Exception as e:
        print(f'Error deleting image \'{path}\': {e}')

def save_to_chat_history(image_path, content, history_path):
    """
    Saves the given content to the image_analyzer_history.json file, keeping only the last two messages.

    Args:
        image_path (str): Path of the analyzed image.
        content (str): The content to be saved.
        history_path (str): Path to the image_analyzer_history.json file.
    """
    entry = {
        'heading': 'Image Analysis Record',
        'analyze image': os.path.basename(image_path),
        'after seeing the image': content,
        'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Ensure the directory exists
    try:
        os.makedirs(os.path.dirname(history_path), exist_ok=True)
    except Exception as e:
        print(f"Error creating directory for history file: {e}")
        return

    # If file doesn't exist, create it with the entry
    if not os.path.isfile(history_path):
        try:
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump([entry], f, indent=4)
        except Exception as e:
            print(f"Error writing new history file: {e}")
        return

    # If file exists, load its data, append the new entry, keep last two, and write back
    try:
        with open(history_path, 'r+', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            data.append(entry)
            data = data[-2:]  # Keep only the last two entries
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
    except Exception as e:
        print(f"Error saving to chat history: {e}")





def start_image_analyzer(folder_path='analyzer'):
    """\n    Starts the image analyzer by monitoring the folder.\n    Args:\n        folder_path (str): Path to the folder to monitor.\n    """  # inserted
    print(f'Monitoring folder: {folder_path}')
    observer = Observer()
    event_handler = ImageFolderHandler()
    observer.schedule(event_handler, folder_path, recursive=False)
    observer.start()
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.join()
        observer.stop()
        print('Stopped monitoring the folder.')
        
if __name__ == '__main__':
    start_image_analyzer('analyzer')