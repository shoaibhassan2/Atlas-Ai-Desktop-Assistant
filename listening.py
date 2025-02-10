import time
import speech_recognition as sr
import threading
from pydub import AudioSegment
from pydub.effects import normalize
import io
from speech import speak, is_speaking

class Listener(threading.Thread):
    def __init__(self, on_recognized_callback, on_error_callback=None, phrase_time_limit=30, pause_threshold=2.0):
        super().__init__()
        self._running = True
        self.paused = False
        self.on_recognized_callback = on_recognized_callback
        self.on_error_callback = on_error_callback
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = pause_threshold
        self.phrase_time_limit = phrase_time_limit
        self.lock = threading.Lock()


    def run(self):
        with sr.Microphone() as source:
            self.recognizer.energy_threshold = 10
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print('[Listener] Started listening...')
            while self._running:
                
                if self.paused or is_speaking.is_set():
                    time.sleep(0.1)
                    continue
                try:
                    print('[Listener] Listening for speech...')
                    with self.lock:
                        audio = self.recognizer.listen(source, timeout=None)
                        raw_data = audio.get_wav_data()
                        audio_segment = AudioSegment.from_file(io.BytesIO(raw_data), format='wav')
                        normalized_audio = normalize(audio_segment)
                        processed_audio = sr.AudioData(normalized_audio.raw_data, audio_segment.frame_rate, audio_segment.sample_width)
                        command = self.recognizer.recognize_google(processed_audio).lower()
                        print(f'[Listener] Recognized command: {command}')
                        self.on_recognized_callback(command)
                except sr.UnknownValueError:
                    print("[Listener] Could not understand audio")
                except sr.RequestError as e:
                    err_msg = f'Speech recognition service error: {e}'
                    if self.on_error_callback:
                        self.on_error_callback(err_msg)

    def stop(self):
        self._running = False
        print('[Listener] Stopping listening thread...')

    def pause_listening(self):
        self.paused = True
        print('[Listener] Listening paused.')

    def resume_listening(self):
        self.paused = False
        print('[Listener] Listening resumed.')