import os
import json
import time
import google.generativeai as genai
import pyttsx3
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Hardcoded Google API Key
GOOGLE_API_KEY = "AIzaSyCDUmcsmkOTh8NVq7gMejd7vHZ05UyK9Io"
genai.configure(api_key=GOOGLE_API_KEY)


class ImageFolderHandler(FileSystemEventHandler):
    """
    Handles events for the folder where images are stored.
    """
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            process_image(event.src_path)  # Process the new image immediately


def process_image(image_path):
    """
    Processes the newly added image.
    Args:
        image_path (str): Path to the new image.
    """
    print(f"Processing image: {image_path}")

    # Retry mechanism for upload
    uploaded_file = upload_to_gemini(image_path, mime_type="image/jpeg", retries=3, delay=2)
    if not uploaded_file:
        print(f"Failed to upload the image: {image_path}")
        return  # Do not delete the image if upload fails

    # Configure the generative model
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 100,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )

    # Analyze the image
    analysis_response = analyze_image(model, uploaded_file)
    print(f"Analysis Response: {analysis_response}")

    # Speak the response aloud
    speak_text(analysis_response)

    # Save the response to image_analyzer_history.json
    save_to_chat_history(image_path, analysis_response, "materials/image_analyzer_history.json")

    # Delete the image after processing
    delete_image(image_path)


def upload_to_gemini(path, mime_type=None, retries=3, delay=2):
    """
    Uploads the given file to Gemini with retry mechanism.

    Args:
        path (str): Path to the file to be uploaded.
        mime_type (str, optional): MIME type of the file.
        retries (int): Number of retry attempts for upload.
        delay (int): Delay in seconds between retries.

    Returns:
        UploadedFile: The uploaded file object from Gemini or None if failed.
    """
    for attempt in range(retries):
        try:
            file = genai.upload_file(path, mime_type=mime_type)
            print(f"Uploaded file '{file.display_name}' as: {file.uri}")
            return file
        except Exception as e:
            print(f"Upload attempt {attempt + 1} failed for {path}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    print(f"All upload attempts failed for {path}.")
    return None


def analyze_image(model, image_file):
    """
    Sends the image to Gemini for analysis and returns the response.

    Args:
        model (GenerativeModel): Configured Gemini generative model.
        image_file (UploadedFile): The uploaded image file object.

    Returns:
        str: The analysis response from Gemini.
    """
    try:
        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        image_file,
                        "What are you seeing? Answer me in a single line.",
                    ],
                },
            ]
        )
        response = chat_session.send_message("What are you seeing?")
        return response.text
    except Exception as e:
        print(f"Error during image analysis: {e}")
        return "I encountered an error while analyzing the image."


def speak_text(text):
    """
    Converts the given text to speech and plays it aloud.

    Args:
        text (str): The text to be spoken.
    """
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)  # Adjust the speech rate
        engine.setProperty('volume', 1.0)  # Maximize volume

        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Error during text-to-speech: {e}")


def delete_image(path):
    """
    Deletes the specified image file from the filesystem.

    Args:
        path (str): Path to the image file to be deleted.
    """
    try:
        os.remove(path)
        print(f"Deleted image: {path}")
    except Exception as e:
        print(f"Error deleting image '{path}': {e}")


def save_to_chat_history(image_path, content, history_path):
    """
    Saves the given content to the image_analyzer_history.json file, keeping only the last two messages.

    Args:
        image_path (str): Path of the analyzed image.
        content (str): The content to be saved.
        history_path (str): Path to the image_analyzer_history.json file.
    """
    entry = {
        "heading": "Image Analysis Record",
        "analyze image": os.path.basename(image_path),
        "after seeing the image": content,
        "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        os.makedirs(os.path.dirname(history_path), exist_ok=True)

        if not os.path.isfile(history_path):
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump([entry], f, indent=4)
        else:
            with open(history_path, 'r+', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
                data.append(entry)
                data = data[-2:]  # Keep only the last two messages

                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
    except Exception as e:
        print(f"Error saving to chat history: {e}")


def start_image_analyzer(folder_path="analyzer"):
    """
    Starts the image analyzer by monitoring the folder.
    Args:
        folder_path (str): Path to the folder to monitor.
    """
    print(f"Monitoring folder: {folder_path}")
    observer = Observer()
    event_handler = ImageFolderHandler()
    observer.schedule(event_handler, folder_path, recursive=False)
    observer.start()

    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
        print("Stopped monitoring the folder.")
    observer.join()


if __name__ == "__main__":
    start_image_analyzer("analyzer")
