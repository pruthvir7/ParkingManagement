import cv2
import sqlite3
from datetime import datetime, timedelta
import easyocr  # For OCR to extract text from the plate
import numpy as np  # For preprocessing enhancements
import re  # For validating license plate format

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

# SQLite Database Configuration
DATABASE = 'parking.db'

# Function to connect to the database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Function to save parking session
def save_parking_session(plate, lot_name, slot_name, start_time, end_time, duration):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO parking_sessions (license_plate, lot_name, slot_name, start_time, end_time, duration)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (plate, lot_name, slot_name, start_time.strftime('%Y-%m-%d %H:%M:%S'),
          end_time.strftime('%Y-%m-%d %H:%M:%S'), duration))
    conn.commit()
    conn.close()

# Preprocess the license plate image for OCR
def preprocess_image(img_roi):
    # Convert to grayscale
    gray = cv2.cvtColor(img_roi, cv2.COLOR_BGR2GRAY)
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # Apply sharpening
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(blurred, -1, kernel)
    # Apply adaptive thresholding
    threshold = cv2.adaptiveThreshold(
        sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    # Morphological operations to remove noise
    kernel = np.ones((3, 3), np.uint8)
    processed = cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, kernel)
    return processed

# Validate license plate format
def is_valid_license_plate(plate_text):
    pattern = r"^[A-Z]{2} \d{2} [A-Z]{2} \d{4}$"
    return re.match(pattern, plate_text)

# Load the Haar Cascade model for number plate detection
harcascade = "model/haarcascade_russian_plate_number.xml"
plate_cascade = cv2.CascadeClassifier(harcascade)

if plate_cascade.empty():
    print("Error: Cascade Classifier could not be loaded.")
    exit()

# Start video capture
cap = cv2.VideoCapture(0)  # Use 0 for the primary camera
cap.set(3, 640)  # Set width
cap.set(4, 480)  # Set height

# Minimum area for detected plates
min_area = 500
grace_period = timedelta(seconds=3)  # Extended grace period to handle instability
iou_threshold = 0.5  # Intersection over Union threshold for bounding box similarity

# Helper function to calculate IoU
def calculate_iou(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    xi1 = max(x1, x2)
    yi1 = max(y1, y2)
    xi2 = min(x1 + w1, x2 + w2)
    yi2 = min(y1 + h1, y2 + h2)
    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)

    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - inter_area

    return inter_area / union_area if union_area > 0 else 0

# Track timers, detection status, and view status for plates
active_timers = {}
last_seen_timestamps = {}
last_detected_boxes = {}
plates_in_view = set()  # To track plates that have already displayed "in view" message

try:
    while True:
        success, img = cap.read()
        if not success:
            print("Failed to grab frame. Exiting.")
            break

        # Convert the image to grayscale for plate detection
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        plates = plate_cascade.detectMultiScale(img_gray, 1.1, 4)

        detected_plates = []

        for (x, y, w, h) in plates:
            area = w * h
            if area > min_area:
                # Check for stability using IoU with previously detected boxes
                matched_plate = None
                for plate, last_box in last_detected_boxes.items():
                    iou = calculate_iou((x, y, w, h), last_box)
                    if iou > iou_threshold:
                        matched_plate = plate
                        break

                if matched_plate:
                    plate_text = matched_plate
                else:
                    # Save the detected plate as an image
                    img_roi = img[y: y + h, x: x + w]
                    plate_image_path = f"Plate_{x}_{y}_entry.jpg"
                    cv2.imwrite(plate_image_path, img_roi)

                    # Preprocess the image for better OCR
                    processed_img = preprocess_image(img_roi)
                    cv2.imwrite(f"Processed_{x}_{y}.jpg", processed_img)  # Save for debugging

                    # Use EasyOCR to extract text from the preprocessed image
                    output = reader.readtext(processed_img)
                    number_plate = [
                        text[1] for text in output
                        if any(char.isdigit() for char in text[1]) and any(char.isalpha() for char in text[1])
                    ]
                    plate_text = number_plate[0] if number_plate else f"Unknown_{x}_{y}"

                # Validate license plate format
                if is_valid_license_plate(plate_text):
                    # Update the detected bounding box
                    last_detected_boxes[plate_text] = (x, y, w, h)
                    detected_plates.append(plate_text)

                    # Draw rectangle around the detected plate
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(img, plate_text, (x, y - 5), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 0, 255), 2)

                    # Handle plate entry
                    if plate_text not in active_timers:
                        active_timers[plate_text] = datetime.now()
                        print(f"Plate {plate_text} detected and entry image saved.")
                    elif plate_text not in plates_in_view:
                        print(f"Plate {plate_text} still in view.")
                        plates_in_view.add(plate_text)

                    # Update the last seen timestamp
                    last_seen_timestamps[plate_text] = datetime.now()

        # Handle plate exit
        plates_to_remove = []
        current_time = datetime.now()
        for plate, last_seen_time in last_seen_timestamps.items():
            if plate not in detected_plates and current_time - last_seen_time > grace_period:
                start_time = active_timers.pop(plate, None)
                if start_time:
                    end_time = current_time
                    duration = (end_time - start_time).total_seconds()
                    if duration > 30:  # Save only if duration > 30 seconds
                        print(f"Plate {plate} left. Duration: {duration} seconds.")

                        # Save the parking session to the database
                        save_parking_session(
                            plate,
                            "Lot_A",  # Placeholder for lot name
                            "Slot_1",  # Placeholder for slot name
                            start_time,
                            end_time,
                            duration
                        )
                        print(f"Parking session for {plate} saved to database.")
                plates_to_remove.append(plate)

        # Remove plates that have exited
        for plate in plates_to_remove:
            last_seen_timestamps.pop(plate, None)
            last_detected_boxes.pop(plate, None)
            plates_in_view.discard(plate)

        # Display the camera feed
        cv2.imshow('Camera Feed', img)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Release the camera and close OpenCV windows
    cap.release()
    cv2.destroyAllWindows()
    print("Camera released.")