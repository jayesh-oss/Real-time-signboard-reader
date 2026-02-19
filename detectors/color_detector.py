import cv2
import numpy as np

class ColorDetector:
    def __init__(self):
        # Define color ranges in HSV
        # Red has two ranges in HSV (0-10 and 170-180)
        self.red_lower1 = np.array([0, 70, 50])
        self.red_upper1 = np.array([10, 255, 255])
        self.red_lower2 = np.array([170, 70, 50])
        self.red_upper2 = np.array([180, 255, 255])

        # Blue (for information signs)
        self.blue_lower = np.array([100, 150, 0])
        self.blue_upper = np.array([140, 255, 255])

        # Yellow (for warning signs)
        self.yellow_lower = np.array([15, 100, 100]) # Tuned for day
        self.yellow_upper = np.array([35, 255, 255])

    def detect_traffic_signs(self, image):
        """
        Returns a list of bounding boxes (x, y, w, h) for potential traffic signs
        based on color.
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Create masks
        mask1 = cv2.inRange(hsv, self.red_lower1, self.red_upper1)
        mask2 = cv2.inRange(hsv, self.red_lower2, self.red_upper2)
        mask_red = cv2.add(mask1, mask2)
        
        mask_blue = cv2.inRange(hsv, self.blue_lower, self.blue_upper)
        mask_yellow = cv2.inRange(hsv, self.yellow_lower, self.yellow_upper)

        # Combine all masks for general "sign" detection
        combined_mask = cv2.bitwise_or(mask_red, mask_blue)
        combined_mask = cv2.bitwise_or(combined_mask, mask_yellow)

        # Morphological operations to remove noise
        kernel = np.ones((5,5), np.uint8)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        bboxes = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 500: # Minimum area filter
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = float(w) / h
                # Basic shape filter (square-ish, circle-ish, or slight rectangle)
                if 0.5 < aspect_ratio < 2.0:
                    bboxes.append((x, y, w, h, "traffic_sign_candidate"))

        return bboxes
