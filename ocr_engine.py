import pytesseract
from PIL import Image
import cv2
import os
import sys

class OCREngine:
    def __init__(self, tesseract_cmd=None):
        self.available = False
        # Set tesseract path if provided or try default Windows path
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        else:
            # Common default path on Windows
            default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(default_path):
                pytesseract.pytesseract.tesseract_cmd = default_path
            
        # Verify if tesseract is actually callable
        try:
            # Check version to verify existence
            pytesseract.get_tesseract_version()
            self.available = True
        except Exception:
            self.available = False

    def is_available(self):
        return self.available

    def extract_text(self, image, lang='eng+hin'):
        """
        Extract text from the given image using Tesseract with confidence filtering.
        """
        if not self.available:
            return "ERR: Tesseract Missing"

        try:
            # Tesseract expects RGB (but we might be passing grayscale from preprocess)
            if len(image.shape) == 2:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Configuration:
            # --psm 6: Assume a single uniform block of text. (Better for signs)
            # --oem 3: Default OCR Engine Mode.
            config = '--psm 6 --oem 3'
            
            # Get detailed data including confidence
            data = pytesseract.image_to_data(rgb_image, lang=lang, config=config, output_type=pytesseract.Output.DICT)
            
            detected_words = []
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                # Filter by confidence (e.g., > 50%)
                # Note: 'conf' can be '-1' for empty/structure blocks
                conf = int(data['conf'][i])
                text = data['text'][i].strip()
                
                # Check confidence AND text validity
                if conf > 40 and len(text) > 1:
                    # Basic alphanumeric check to remove pure symbol noise
                    if any(c.isalnum() for c in text):
                         detected_words.append(text)
            
            return " ".join(detected_words)

        except pytesseract.TesseractNotFoundError:
            self.available = False
            return "ERR: Tesseract Not Found"
        except Exception as e:
            return f"OCR Error: {str(e)}"
