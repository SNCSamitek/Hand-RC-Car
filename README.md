# GestureBot

Control a 4-wheeled robot car in real time using nothing but your hand. A webcam watches your gestures, MediaPipe reads your finger count, and the command flies over WiFi to an ESP32 driving four motors. No remote, no app, no buttons. Just your hand.

## How It Works

1. A webcam feed is passed through Google's MediaPipe HandLandmarker model, which tracks 21 points on your hand in real time.
2. The number of extended fingers is calculated using distance-from-wrist ratios (not simple pixel comparisons), which stays accurate even when your hand is tilted or at an angle.
3. A temporal smoothing filter requires several consecutive frames to agree before a command is confirmed, killing flicker and false triggers.
4. The confirmed gesture is mapped to a drive command and sent over a TCP socket to an ESP32 on your WiFi network.
5. The ESP32 parses the command and drives the motors directly, PWM-controlling speed on each wheel through its H-bridge driver.

## Gesture Map

| Fingers | Command | Action |
|---|---|---|
| 1 | forward | Drive forward |
| 2 | left | Pivot left |
| 3 | right | Pivot right |
| 4 | back | Reverse |
| 0 or 5 | stop | Stop / brake |
| No hand detected | stop | Stop / brake |

The system fails safe by design. Anything unrecognized, including no hand in frame at all, defaults to stop rather than continuing the last command or guessing.

## Hardware

- ESP32 development board (WiFi client/server)
- 4x DC motors with a compatible dual-pin H-bridge driver (IN1/IN2 style, PWM-capable)
- Robot chassis, wheels, battery pack
- A computer with a webcam for the vision pipeline

## Software Stack

**Vision / control side (Python)**
- OpenCV for camera capture and display
- MediaPipe Tasks (HandLandmarker) for hand tracking
- Standard library `socket` for WiFi communication with the ESP32

**Firmware side (C++ / Arduino framework)**
- Direct pin control of the motor driver
- Command parser for forward, left, right, back, and stop

## Project Structure

```
.
├── hand_control.py      # Webcam capture, gesture detection, command sender
├── hand_landmarker.task # MediaPipe hand landmark model file
├── main.cpp             # ESP32 firmware: command parsing and motor control
└── def.h                # Pin definitions and function declarations
```

## Setup

### 1. Flash the ESP32

Wire your motor driver to the pins defined in `def.h`, update `motor_pins[]` to match your actual wiring, then flash `main.cpp` using PlatformIO or the Arduino IDE. Note the IP address the ESP32 prints to its serial monitor on boot.

### 2. Configure the Python side

Install dependencies:

```bash
pip install opencv-python mediapipe
```

Download the `hand_landmarker.task` model file from MediaPipe's model zoo and place it in the project directory.

Update the IP address in `hand_control.py` to match your ESP32:

```python
ESP32_IP = "192.168.1.96"
```

### 3. Run it

```bash
python hand_control.py
```

Hold your hand up to the camera, palm facing the lens, fingers pointing up for best accuracy. Press `q` to quit; the car will automatically stop on exit.

## Tuning

If gestures feel unreliable, a few knobs are worth adjusting:

- `STABLE_FRAMES_REQUIRED` in `hand_control.py` controls how many consecutive frames must agree before a command is sent. Raise it for more stability at the cost of a little latency.
- The `0.15 * mcp_dist` threshold in `count_extended_fingers` controls how far a fingertip must extend past the palm to count as "extended." Raise it if fingers register as extended too easily, lower it if extended fingers are being missed.
- `min_hand_detection_confidence`, `min_hand_presence_confidence`, and `min_tracking_confidence` can all be raised for stricter detection in noisy environments.

## Safety Notes

- The system defaults to stop on any unrecognized command, dropped connection, or missing hand, rather than continuing the last known motion.
- On script exit (including Ctrl+C or window close), a stop command is sent to the ESP32 before the socket closes.
- Test with wheels off the ground before running on the floor for the first time, especially after changing pin mappings or driver logic.

## Roadmap

- Add reverse-specific motor control tuning distinct from the forward function
- Add speed control via hand distance from camera or a second gesture axis
- Bridge WiFi commands directly on the ESP32 instead of relying on a wired serial hop, if using a two-board setup
- Add a debounced connection-loss indicator so the car can be commanded to stop even if the TCP link drops silently

## License

Do whatever you want with it. Just do not run it over your cat.
