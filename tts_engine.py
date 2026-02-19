import pyttsx3
import threading
import queue

class TTSEngine:
    def __init__(self):
        self.queue = queue.Queue()
        self.is_running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _worker(self):
        print("TTS Worker Started (Thread Safe)")
        
        # Initialize Engine INSIDE the thread (Crucial for Windows/COM)
        engine = pyttsx3.init()
        
        # Load Voices here
        voices = engine.getProperty('voices')
        english_voice = None
        hindi_voice = None
        
        print("--- Available Systems Voices ---")
        for voice in voices:
            print(f"Name: {voice.name}, ID: {voice.id}")
            v_name = voice.name.lower()
            
            # Check for Hindi
            if "hindi" in v_name or "india" in v_name or "kalpana" in v_name or "hemant" in v_name:
                hindi_voice = voice.id
                print(f" -> Found Hindi Voice: {voice.name}")
                
            # Check for English (US Preferred)
            if "english" in v_name and "us" in v_name:
                 english_voice = voice.id
            elif "english" in v_name and not english_voice:
                 english_voice = voice.id

        print("--------------------------------")
                 
        # Fallback
        if not english_voice and voices:
            english_voice = voices[0].id
        if not hindi_voice:
            hindi_voice = english_voice
            print("WARNING: No Hindi voice found. Install 'Hindi' language pack in Windows Settings.")

        # Default voice
        engine.setProperty('voice', english_voice)

        while True:
            try:
                if not self.is_running:
                    # Clean shutdown
                    engine.stop()
                    break

                # Item: (text, language_code)
                try:
                    data = self.queue.get(timeout=0.5)
                except queue.Empty:
                    # Must pump loop occasionally? No, only needed if using event loop based methods
                    # But runAndWait does it.
                    continue
                    
                text, lang = data
                
                # Switch voice based on lang
                if lang == 'hi':
                    if hindi_voice:
                        engine.setProperty('voice', hindi_voice)
                else:
                    if english_voice:
                        engine.setProperty('voice', english_voice)
                
                print(f"TTS Saying: {text}")
                engine.say(text)
                engine.runAndWait()
                
            except Exception as e:
                print(f"TTS Hub Error: {e}")

    def speak(self, text, lang='en'):
        self.queue.put((text, lang))

    def stop(self):
        self.is_running = False
        print("Stopping TTS...")
        if self.thread.is_alive():
            self.thread.join(timeout=2)
