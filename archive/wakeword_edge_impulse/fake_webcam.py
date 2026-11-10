import pyfakewebcam
import numpy as np
import cv2

# Path to your static image or use OpenCV to create one
image_path = "/home/solana/bot_ui/idle_smiley.png"

# Initialize the virtual webcam (adjust /dev/video0 as needed)
device = "/dev/video0"
width, height = 640, 480
camera = pyfakewebcam.FakeWebcam(device, width, height)

# Load the image and resize to webcam dimensions
frame = cv2.imread(image_path)
frame = cv2.resize(frame, (width, height))

# Convert to RGB (required by pyfakewebcam)
frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

# Send the frame to the virtual webcam in a loop
print("Virtual webcam feed started. Press Ctrl+C to stop.")
while True:
    camera.schedule_frame(frame)
