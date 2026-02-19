import cv2
import numpy as np

class ShapeDetector:
    def __init__(self):
        pass

    def detect_text_regions(self, image):
        """
        Uses MSER (Maximally Stable Extremal Regions) or contours to find 
        potential text regions/billboards.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # MSER is great for text detection
        try:
            mser = cv2.MSER_create()
            regions, _ = mser.detectRegions(gray)
            hulls = [cv2.convexHull(p.reshape(-1, 1, 2)) for p in regions]
            
            # This returns specific text characters/blobs. 
            # We want to group them into "billboards".
            # For simplicity in this 'Classical' phase, let's look for large rectangular contours
            # that might contain these regions, or just return the MSER bounding boxes.
            
            # Alternative: Canny Edge + Contours for Billboards
            return self.detect_rectangular_signs(image)
            
        except AttributeError:
             # Fallback if MSER (patent issues in some OpenCV builds) isn't available
             return self.detect_rectangular_signs(image)

    def detect_rectangular_signs(self, image):
        """
        Finds large rectangular contours which could be billboards.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        
        # Dilate to connect edges
        kernel = np.ones((5,5), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        bboxes = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Increased minimum area to reduce noise from small objects
            if area > 5000: 
                # Approx polygon
                epsilon = 0.04 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                
                # Check if it has 4 corners (rectangle)
                if len(approx) == 4:
                    x, y, w, h = cv2.boundingRect(approx)
                    aspect_ratio = float(w) / h
                    # Billboards are usually somewhat wide or tall, but not extremely thin
                    if 0.2 < aspect_ratio < 5.0:
                         bboxes.append((x, y, w, h, "billboard_candidate"))
        
        return bboxes
