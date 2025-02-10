import os
import pyautogui
import time

def write_to_notepad(content):
    """Open Notepad and write the given content with line breaks after every 12 words."""
    try:
        # Open Notepad
        os.system("start notepad")
        time.sleep(1)  # Ensure Notepad is ready

        # Split content into lines with 12 words each
        words = content.split()
        lines = [' '.join(words[i:i+12]) for i in range(0, len(words), 12)]
        
        # Write content line by line
        for line in lines:
            pyautogui.write(line)
            pyautogui.press('enter')  # Move to the next line

    except Exception as e:
        raise RuntimeError(f"Error writing to Notepad: {e}")
