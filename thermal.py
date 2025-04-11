import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk

def yuyv422_to_gray(img):
    return img[..., 0]

def yuyv422_to_gray16le(img):
    height, width, _ = img.shape
    dt = np.dtype(np.uint16).newbyteorder('<')
    # Convert the image to a 1D array of uint16 values
    yuyv_data = np.frombuffer(img.tobytes(), dtype=dt)
    # Reshape the array to form the Gray16LE image
    gray16le = yuyv_data.reshape(height, width)
    return gray16le

def kelvin_to_celsius(kelvin):
    return kelvin - 273.15

def mouse_callback(event, x, y, flags, param):
    global cursor_x, cursor_y
    if event == cv2.EVENT_MOUSEMOVE:
        cursor_x, cursor_y = x, y

min_temp = 20
max_temp = 40
temp_scale = 4

cv2.namedWindow("Grayscale", cv2.WINDOW_NORMAL)

# Set the initial window sizes to 800x600
cv2.resizeWindow("Grayscale", 800, 600)


# Set the mouse callback function for both
cv2.setMouseCallback("Grayscale", mouse_callback)

# Initialize cursor position
cursor_x, cursor_y = 0, 0

def main():
    cap = cv2.VideoCapture("/dev/video-infiray")
    # cap = cv2.VideoCapture(3)
    # Set the camera resolution to 256x384 explicitly
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 256)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 384)
    cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)
    # Fetch undecoded RAW video streams
    cap.set(cv2.CAP_PROP_FORMAT, -1)
    print(cap)

    if not cap.isOpened():
        raise ValueError("Cannot open camera")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Split the frame into upper and lower halves
            upper_frame = frame[:192, :, :]
            lower_frame = frame[192:, :, :]

            # Convert the upper frame to grayscale
            gray_upper = yuyv422_to_gray(upper_frame)

            # Extract the raw non-normalized sensor values from the lower frame
            gray16le_lower = yuyv422_to_gray16le(lower_frame)

            # Convert temperature data to Celsius
            temperature_c = kelvin_to_celsius(gray16le_lower / 64)
            temperature = temperature_c[cursor_y//temp_scale, cursor_x//temp_scale]
            temperature_text = f" {temperature:.1f} C"

            # Normalize the temperature data between the min_temp and max_temp range
            normalized_temperature = np.clip((temperature_c - min_temp) / (max_temp - min_temp), 0, 1)
            normalized_temperature = np.uint8(normalized_temperature * 255)

            # Apply the selected color map to the grayscale image
            colormap_idx = getattr(cv2, "COLORMAP_MAGMA")
            color_mapped_gray = cv2.applyColorMap(gray_upper, colormap_idx)

            color_mapped_gray_resized = cv2.resize(color_mapped_gray, None, fx=temp_scale, fy=temp_scale,
                                                   interpolation=cv2.INTER_NEAREST_EXACT)
            cv2.circle(color_mapped_gray_resized, (cursor_x, cursor_y), 2, (255, 255, 255), 1)
            cv2.putText(color_mapped_gray_resized, temperature_text, (cursor_x, cursor_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow("Grayscale", color_mapped_gray_resized)

            img_with_temp = cv2.resize(normalized_temperature, None, fx=temp_scale, fy=temp_scale,
                                       interpolation=cv2.INTER_NEAREST_EXACT)

            cv2.circle(img_with_temp, (cursor_x, cursor_y), 2, (255, 255, 255), 1)
            cv2.putText(img_with_temp, temperature_text, (cursor_x, cursor_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            if cv2.waitKey(1) == ord("q"):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
