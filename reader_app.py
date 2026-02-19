import cv2
import time
import threading
import queue
from utils import resize_image, preprocess_for_ocr, contains_devanagari, merge_close_rectangles
from detectors.color_detector import ColorDetector
from detectors.shape_detector import ShapeDetector
from ocr_engine import OCREngine
from tts_engine import TTSEngine

class SignboardReaderApp:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        
        # Initialize Detectors
        self.color_detector = ColorDetector()
        self.shape_detector = ShapeDetector()
        self.ocr_engine = OCREngine()
        
        # TTS Engine (Custom)
        self.tts_engine = TTSEngine()
        
        # Queues for Asynchronous Processing
        self.ocr_queue = queue.Queue()
        self.last_spoken = {} # format: {text: timestamp}
        self.cooldown = 2.0   # seconds before repeating same word
        self.is_running = False
        
        # Start OCR Worker Thread
        self.ocr_thread = threading.Thread(target=self.ocr_worker, daemon=True)
        self.ocr_thread.start()

    def ocr_worker(self):
        """
        Consumes ROIs from ocr_queue and runs OCR Engine.
        """
        print("OCR Worker Started")
        while True:
            try:
                # Wait for an ROI
                if not self.is_running:
                    time.sleep(0.5)
                    self.last_spoken.clear() # Reset memory on stop
                    continue

                roi_data = self.ocr_queue.get(timeout=1) 
                roi, label = roi_data
                
                if self.ocr_engine.is_available():
                    # Preprocess
                    processed_roi = preprocess_for_ocr(roi)
                    # Extract
                    text = self.ocr_engine.extract_text(processed_roi)
                    
                    # Filter: Length > 1 and alphanumeric content
                    if len(text) > 1 and not text.startswith("ERR"):
                        # Aggressive cleaning: Remove punctuation edges
                        clean_text = text.replace("\n", " ").strip(" .,!?:;'\"()[]{}|\\/-_")
                        
                        # Must have at least 2 alphanumeric chars
                        if sum(c.isalnum() for c in clean_text) < 2:
                            continue

                        current_time = time.time()
                        
                        # Check Cooldown
                        if (clean_text not in self.last_spoken or 
                            (current_time - self.last_spoken[clean_text] > self.cooldown)):
                            
                            print(f"OCR Result: {clean_text} ({label})")
                            self.last_spoken[clean_text] = current_time
                            
                            # Language Check
                            lang = 'hi' if contains_devanagari(clean_text) else 'en'
                            print(f"Speaking ({lang}): {clean_text}")
                            self.tts_engine.speak(f"{clean_text}", lang)
            
            except queue.Empty:
                continue
            except Exception as e:
                print(f"OCR Worker Error: {e}")

    # process_tts method removed as it is now inside TTSEngine

    def run(self):
        print("Starting Signboard Reader Loop...")
        self.is_running = True
        
        # For limiting OCR frequency per region, we might need logic.
        # Simple approach: Fire OCR whenever we see a candidate, but queue handles load.
        # Better approach: Only add to queue if queue is empty (drop frames if busy)
        
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            display_frame = frame.copy()
            
            # 1. Detection
            # Combine candidates from Color (Traffic Signs) and Shape (Billboards)
            candidates = []
            candidates.extend(self.color_detector.detect_traffic_signs(frame))
            candidates.extend(self.shape_detector.detect_text_regions(frame))
            
            # Merge close candidates (e.g. "YOUR" + "DESIGN" -> "YOUR DESIGN")
            candidates = merge_close_rectangles(candidates)
            
            # Display Tesseract Error
            if not self.ocr_engine.is_available():
                cv2.putText(display_frame, "ERROR: Tesseract OCR not found!", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            for (x, y, w, h, label) in candidates:
                # Draw
                color = (0, 255, 0) if "traffic" in label else (255, 0, 0)
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(display_frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                # Check OCR Queue Status - Don't overload
                # Only add if we aren't backed up (queue size < 4)
                if self.ocr_queue.qsize() < 4:
                    # Expand ROI slightly to give context for OCR
                    margin = 10
                    h_img, w_img = frame.shape[:2]
                    
                    x_start = max(0, x - margin)
                    y_start = max(0, y - margin)
                    x_end = min(w_img, x + w + margin)
                    y_end = min(h_img, y + h + margin)
                    
                    roi = frame[y_start:y_end, x_start:x_end]
                    
                    if roi.size > 0:
                        self.ocr_queue.put((roi.copy(), label))
                        cv2.putText(display_frame, "Queued", (x, y + h + 20), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

            cv2.imshow("Real Time Signboard Reader", display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.is_running = False
        
        self.cap.release()
        cv2.destroyAllWindows()
        print("Reader Stopped.")
        self.tts_engine.stop()

    def stop(self):
        self.is_running = False

if __name__ == "__main__":
    app = SignboardReaderApp()
    app.run()
