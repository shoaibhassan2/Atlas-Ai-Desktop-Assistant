import cv2
import threading
import os
from datetime import datetime
import logging
from image_analyzer import start_image_analyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [Camera Module] - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

camera_thread = None
camera_running = threading.Event()
capture_device = None

def open_camera():
    """
    Opens the camera and starts displaying the video feed in a separate thread.
    """
    global camera_thread
    if camera_running.is_set():
        logging.warning('Camera is already running.')
        return 'Camera is already open.'

    def camera_feed():
        global capture_device
        capture_device = cv2.VideoCapture(0)
        if not capture_device.isOpened():
            logging.error('Failed to open the camera.')
            camera_running.clear()
            return None
        logging.info('Camera opened successfully.')
        if camera_running.is_set():
            ret, frame = capture_device.read()
            if not ret:
                logging.error('Failed to read frame from camera.')
            else:
                cv2.imshow('Camera Feed', frame)
                if cv2.waitKey(1) & 255 == ord('q'):
                    logging.info('Manual exit from camera feed.')
        capture_device.release()
        cv2.destroyAllWindows()
        logging.info('Camera feed closed.')
        return None

    camera_running.set()
    camera_thread = threading.Thread(target=camera_feed, daemon=True)
    camera_thread.start()
    logging.info('Camera thread started.')
    return 'Camera has been opened.'

def capture_image(folder_path='analyzer'):
    """
    Captures a single image from the camera feed and saves it to the specified folder.

    Args:
        folder_path (str): Path to the folder where the image will be saved.
    """
    # Check that the camera is running and open
    if not camera_running.is_set() or not (capture_device and capture_device.isOpened()):
        logging.warning('Cannot capture image because the camera is not open.')
        return 'Cannot capture image because the camera is not open.'
    ret, frame = capture_device.read()
    if not ret:
        logging.error('Failed to capture image from camera.')
        return 'Failed to capture image from camera.'
    os.makedirs(folder_path, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'captured_image_{timestamp}.jpg'
    filepath = os.path.join(folder_path, filename)
    cv2.imwrite(filepath, frame)
    logging.info(f'Image captured and saved to {filepath}.')
    return f'Image captured and saved as {filename}.'

def close_camera():
    """
    Closes the camera feed and stops the camera thread.
    """
    if not camera_running.is_set():
        logging.warning('Camera is not running.')
        return 'Camera is not open.'
    camera_running.clear()
    logging.info('Signaling camera thread to stop.')
    camera_thread.join()
    logging.info('Camera thread has been terminated.')
    return 'Camera has been closed.'

logging.info('Starting image analyzer as a standalone process.')
analyzer_thread = threading.Thread(target=start_image_analyzer, daemon=True)
analyzer_thread.start()
