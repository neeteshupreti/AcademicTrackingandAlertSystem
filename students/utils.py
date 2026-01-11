import pytesseract
import cv2
import numpy as np
from PIL import Image

def scan_image_for_gpa(image_path):
    # 1. Load and Preprocess for better accuracy
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Binary thresholding (makes text pop out)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    
    # 2. Extract Text
    text = pytesseract.image_to_string(thresh)
    
    # 3. Logic to find GPA (Simplified example)
    # We look for lines containing numbers and check if they are < 2.0
    lines = text.split('\n')
    results = []
    for line in lines:
        if "GPA" in line.upper():
            # Use regex or splitting to find the numeric value
            # Example logic: if gpa < 2.0 -> add to list
            pass 
    return text