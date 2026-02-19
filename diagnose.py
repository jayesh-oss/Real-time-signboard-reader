import sys
import os

print(f"Python: {sys.version}")
print(f"CWD: {os.getcwd()}")

try:
    import cv2
    print(f"OpenCV: {cv2.__version__}")
except ImportError as e:
    print(f"OpenCV Import Error: {e}")

try:
    import pytesseract
    print(f"Pytesseract: {pytesseract.__version__}")
    
    # Check for Tesseract Binary
    default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(default_path):
        print(f"Tesseract Binary found at: {default_path}")
        pytesseract.pytesseract.tesseract_cmd = default_path
        try:
            print("Testing Tesseract...")
            # Create a dummy image
            import numpy as np
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.putText(img, "Test", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            text = pytesseract.image_to_string(img)
            print("Tesseract Test Output:", text.strip())
        except Exception as e:
            print(f"Tesseract Execution Error: {e}")
    else:
        print(f"WARNING: Tesseract executable not found at {default_path}")
        print("Please ensure Tesseract-OCR is installed and added to PATH or updated in code.")

except ImportError as e:
    print(f"Pytesseract Import Error: {e}")

try:
    import pyttsx3
    engine = pyttsx3.init()
    print("pyttsx3 initialized successfully")
except ImportError as e:
    print(f"pyttsx3 Import Error: {e}")
except Exception as e:
    print(f"pyttsx3 Init Error: {e}")

try:
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("Camera: Accessible")
        cap.release()
    else:
        print("Camera: Not Accessible")
except Exception as e:
    print(f"Camera Error: {e}")
