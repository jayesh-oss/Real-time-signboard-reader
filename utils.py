import cv2
import numpy as np

def resize_image(image, width=None, height=None):
    """
    Resize image to specific width or height while maintaining aspect ratio.
    """
    dim = None
    (h, w) = image.shape[:2]

    if width is None and height is None:
        return image

    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))

    resized = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
    return resized

def preprocess_for_ocr(image):
    """
    Advanced preprocessing for Tesseract OCR.
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Increase contrast/brightness?
    # gray = cv2.equalizeHist(gray) # Sometimes helps, sometimes hurts.
    
    # Use Otsu's thresholding for potential better separation
    # But for general signs, adaptive is often better. Let's try to combine or pick one.
    # Simple binary inverse might be better if text is white on dark.
    # Let's stick to adaptive but tweak block size.
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 31, 2) # Increased block size for larger text
    
    # Noise Removal
    kernel = np.ones((1, 1), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    # Add Padding (White Border) - CRITICAL for Tesseract
    # Tesseract assumes text is inside a page, so edges often get cut off.
    padding = 10
    padded = cv2.copyMakeBorder(thresh, padding, padding, padding, padding, 
                                cv2.BORDER_CONSTANT, value=[255, 255, 255])
    
    return padded

def contains_devanagari(text):
    """
    Checks if the text contains Devanagari (Hindi) characters.
    Range: U+0900 to U+097F
    """
    for char in text:
        if '\u0900' <= char <= '\u097F':
            return True
    return False

def merge_close_rectangles(rects, distance_threshold=30):
    """
    Merges rectangles that are close to each other to form larger regions (e.g., sentences).
    Rect format: (x, y, w, h, label)
    """
    if not rects:
        return []

    # Convert to list of mutable dicts for easier handling
    boxes = []
    for (x, y, w, h, label) in rects:
        boxes.append({
            'x': x, 'y': y, 'w': w, 'h': h, 
            'label': label, 'merged': False
        })

    changed = True
    while changed:
        changed = False
        new_boxes = []
        skip_indices = set()

        for i in range(len(boxes)):
            if i in skip_indices:
                continue
            
            current = boxes[i]
            merged = False
            
            for j in range(i + 1, len(boxes)):
                if j in skip_indices:
                    continue
                
                other = boxes[j]
                
                # Check proximity
                # Horizontal close? (Same line)
                h_dist = min(abs(current['x'] + current['w'] - other['x']), 
                             abs(other['x'] + other['w'] - current['x']))
                             
                # Vertical align? (Same line height approx)
                v_overlap = max(0, min(current['y'] + current['h'], other['y'] + other['h']) - 
                                   max(current['y'], other['y']))
                
                # Simple Euclidean distance between centers?
                c1 = (current['x'] + current['w']/2, current['y'] + current['h']/2)
                c2 = (other['x'] + other['w']/2, other['y'] + other['h']/2)
                dist = ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)**0.5
                
                # Logic: If close distance OR (horizontal close AND vertical overlap)
                is_close = dist < distance_threshold
                is_aligned = (h_dist < distance_threshold) and (v_overlap > min(current['h'], other['h']) * 0.5)
                
                if is_close or is_aligned:
                    # Merge
                    x1 = min(current['x'], other['x'])
                    y1 = min(current['y'], other['y'])
                    x2 = max(current['x'] + current['w'], other['x'] + other['w'])
                    y2 = max(current['y'] + current['h'], other['y'] + other['h'])
                    
                    new_w = x2 - x1
                    new_h = y2 - y1
                    
                    # Prioritize "billboard" label if present
                    new_label = current['label']
                    if "billboard" in other['label']:
                        new_label = other['label']

                    new_boxes.append({
                        'x': x1, 'y': y1, 'w': new_w, 'h': new_h, 
                        'label': new_label, 'merged': False
                    })
                    
                    skip_indices.add(j)
                    merged = True
                    changed = True
                    break # Break inner loop to restart with new merged box
            
            if not merged:
                new_boxes.append(current)
        
        boxes = new_boxes

    # Convert back to tuple format
    final_rects = []
    for b in boxes:
        final_rects.append((b['x'], b['y'], b['w'], b['h'], b['label']))
        
    return final_rects
