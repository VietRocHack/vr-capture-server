from flask import Flask, send_file, jsonify
import win32gui
import win32ui
from ctypes import windll
from PIL import Image
import numpy as np
import io

app = Flask(__name__)

WINDOW_NAME = "casting"

def capture_window(window_title):
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        raise Exception(f'Window not found: {window_title}')

    # Get window size
    # left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    capture_width = 1000
    capture_height = 1000

    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, capture_width, capture_height)

    saveDC.SelectObject(saveBitMap)

    result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)

    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)

    im = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1)

    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)

    if result == 1:
        return np.array(im)
    else:
        return None

@app.route('/screenshot', methods=['GET'])
def get_casting_window_screenshot():
    try:
        # Capture the window
        screenshot = capture_window(WINDOW_NAME)
        
        if screenshot is None:
            return jsonify({"error": f"Failed to capture window '{WINDOW_NAME}'"}), 500

        # Convert numpy array to PIL Image
        img = Image.fromarray(screenshot)

        # Save screenshot to a bytes buffer
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)

        # Send the image
        return send_file(img_buffer, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
