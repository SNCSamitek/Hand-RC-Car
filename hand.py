import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import socket
import math
from collections import deque

# --- WiFi setup instead of serial ---
ESP32_IP = "192.168.1.96"
ESP32_PORT = 80

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
sock.connect((ESP32_IP, ESP32_PORT))
sock.send(b"on\n")
print("Connected to ESP32")

last_state = None

def send_command(cmd):
    global last_state
    if cmd != last_state:
        try:
            sock.send((cmd + "\n").encode())
            print("Sent:", cmd)
            last_state = cmd
        except Exception as e:
            print("Send failed:", e)

# --- Hand tracking setup ---
base_options = mp_python.BaseOptions(model_asset_path="hand_landmarker.task")
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7,
)
landmarker = vision.HandLandmarker.create_from_options(options)

# Landmark indices
WRIST = 0
TIPS = [8, 12, 16, 20]      # index, middle, ring, pinky tips
PIPS = [6, 10, 14, 18]      # corresponding second-knuckle joints
MCPS = [5, 9, 13, 17]       # corresponding base knuckle joints

def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)

def count_extended_fingers(landmarks):
    """More robust finger-extension check using distance-from-wrist
    ratios instead of raw y-comparison, which is angle-sensitive."""
    wrist = landmarks[WRIST]
    count = 0
    for tip_i, pip_i, mcp_i in zip(TIPS, PIPS, MCPS):
        tip = landmarks[tip_i]
        pip = landmarks[pip_i]
        mcp = landmarks[mcp_i]

        # A finger is "extended" if its tip is meaningfully farther
        # from the wrist than its own middle knuckle is.
        tip_dist = dist(tip, wrist)
        pip_dist = dist(pip, wrist)
        mcp_dist = dist(mcp, wrist)

        # Require the tip to clearly extend past the PIP joint,
        # scaled against the palm size (mcp_dist) so it works at
        # any distance from the camera.
        if tip_dist > pip_dist and (tip_dist - mcp_dist) > 0.15 * mcp_dist:
            count += 1
    return count

# Map finger count -> command
GESTURE_MAP = {
    1: "forward",
    2: "left",
    3: "right",
    4: "back",
}
DEFAULT_STATE = "stop"

# --- Temporal smoothing: require N consecutive matching frames ---
HISTORY_LEN = 6
STABLE_FRAMES_REQUIRED = 5  # out of HISTORY_LEN, must agree
history = deque(maxlen=HISTORY_LEN)
confirmed_state = DEFAULT_STATE

cap = cv2.VideoCapture(0)

try:
    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect(mp_image)

        finger_count = 0
        raw_state = DEFAULT_STATE

        if result.hand_landmarks:
            for hand_landmarks in result.hand_landmarks:
                finger_count = count_extended_fingers(hand_landmarks)
                raw_state = GESTURE_MAP.get(finger_count, DEFAULT_STATE)

                h, w, _ = frame.shape
                for lm in hand_landmarks:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)

        history.append(raw_state)

        # Only switch confirmed_state if the new state dominates
        # recent history — filters out single-frame flicker.
        if len(history) == HISTORY_LEN:
            most_common = max(set(history), key=history.count)
            if history.count(most_common) >= STABLE_FRAMES_REQUIRED:
                confirmed_state = most_common

        send_command(confirmed_state)

        color = (0, 255, 0) if confirmed_state != DEFAULT_STATE else (0, 0, 255)
        cv2.putText(frame, f"{finger_count} FINGERS -> raw:{raw_state}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        cv2.putText(frame, confirmed_state.upper(), (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)

        cv2.imshow("Hand Control", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    cap.release()
    cv2.destroyAllWindows()
    try:
        sock.send(b"stop\n")
    except:
        pass
    sock.close()