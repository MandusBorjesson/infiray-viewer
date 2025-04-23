import cv2
import numpy as np

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


selected_cmap = "COLORMAP_MAGMA"
temp_scale = 4

cv2.namedWindow("Grayscale", cv2.WINDOW_NORMAL)
# cv2.resizeWindow("Grayscale", 800, 600)


# Set the mouse callback function for both
cv2.setMouseCallback("Grayscale", mouse_callback)

# Initialize cursor position
cursor_x, cursor_y = 0, 0

cap = cv2.VideoCapture("/dev/video-infiray")

# Set the camera resolution to 256x384 explicitly
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 256)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 384)
cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)

# Fetch undecoded RAW video streams
cap.set(cv2.CAP_PROP_FORMAT, -1)

def main():
    if not cap.isOpened():
        raise ValueError("Cannot open camera")

    try:
        flip_x = False
        flip_y = False
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

            if flip_x and flip_y:
                gray_upper = cv2.flip(gray_upper, -1)
            elif flip_x:
                gray_upper = cv2.flip(gray_upper, 0)
            elif flip_y:
                gray_upper = cv2.flip(gray_upper, 1)

            # Apply the selected color map to the grayscale image
            colormap_idx = getattr(cv2, selected_cmap)
            color_mapped_gray = cv2.applyColorMap(gray_upper, colormap_idx)

            color_mapped_gray_resized = cv2.resize(color_mapped_gray, None, fx=temp_scale, fy=temp_scale,
                                                   interpolation=cv2.INTER_NEAREST_EXACT)
            cv2.circle(color_mapped_gray_resized, (cursor_x, cursor_y), 2, (255, 255, 255), 1)
            cv2.putText(color_mapped_gray_resized, temperature_text, (cursor_x, cursor_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow("Grayscale", color_mapped_gray_resized)

            key = cv2.waitKey(1)
            if key == ord("q"):
                break
            if key == ord("x"):
                flip_x = not flip_x
            if key == ord("y"):
                flip_y = not flip_y

    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
