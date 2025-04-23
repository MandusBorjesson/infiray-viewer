import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk, ImageOps


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

class ThermalCamera():
    def __init__(self, path):
        self._path = path
        self._size = (256, 384)
        self._cam = None

    def init_cam(self):
        cap = cv2.VideoCapture(self._path)
        if not cap.isOpened():
            return False

        # Set the camera resolution to 256x384 explicitly
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._size[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._size[1])
        cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)

        # Fetch undecoded RAW video streams
        cap.set(cv2.CAP_PROP_FORMAT, -1)

        self._cam = cap
        return True

    def read(self):
        if not self._cam:
            if not self.init_cam():
                print("Failed to initialize camera")
                return

        ret, frame = self._cam.read()
        if not ret:
            self._cam = None
            print("Failed to read camera")
            return None

        # Split the frame into upper and lower halves
        h_half = self._size[1]//2
        upper_frame = frame[:h_half, :, :]
        lower_frame = frame[h_half:, :, :]

        return upper_frame, lower_frame

    def close(self):
        if self._cam:
            self._cam.release()


cap = ThermalCamera("/dev/video-infiray")

selected_cmap = "COLORMAP_MAGMA"
temp_scale = 4

# cv2.resizeWindow("Grayscale", 800, 600)


# Initialize cursor position
cursor_x, cursor_y = 0, 0


def handle_keypress(event):
    """Print the character associated to the key pressed"""
    print(event.char)

def update_camera_feed(webcam, widget):

    # Capture the video frame by frame
    ret = webcam.read()
    if not ret:
        widget.after(5000, update_camera_feed, webcam, widget)
        return

    # Split the frame into upper and lower halves
    upper_frame, _ = ret

    # Convert the upper frame to grayscale
    gray_upper = yuyv422_to_gray(upper_frame)
    opencv_image = gray_upper

    # Apply the selected color map to the grayscale image
    opencv_image = cv2.applyColorMap(gray_upper, cv2.COLORMAP_MAGMA)
    captured_image = Image.fromarray(opencv_image)

    widget_size = (widget.winfo_width(), widget.winfo_height())
    captured_image = ImageOps.contain(captured_image, widget_size, method=Image.Resampling.NEAREST)

    photo_image = ImageTk.PhotoImage(image=captured_image)

    # Displaying photoimage in the label
    widget.photo_image = photo_image

    # Configure image in the label
    widget.configure(image=photo_image)

    widget.after(1, update_camera_feed, webcam, widget)

def main():
    window = tk.Tk()
    # window["bg"] = "black"
    window.bind('<q>', lambda e: window.quit())

    camera_feed = tk.Label(master=window, bg="black", borderwidth=0, highlightthickness=0)
    camera_feed.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

    frame2 = tk.Frame(master=window, width=100, bg="yellow")
    frame2.pack(fill=tk.BOTH, side=tk.LEFT)

    update_camera_feed(cap, camera_feed)
    try:
        window.mainloop()
    finally:
        cap.close()


if __name__ == "__main__":
    main()
