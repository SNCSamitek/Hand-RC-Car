# GestureBot

Control a 4-wheeled robot car in real time using nothing but your hand. A webcam watches your gestures, MediaPipe reads your finger count, and the command travels over WiFi to an ESP32, which relays it over a wired serial link to an Arduino driving four motors. No remote, no app, no buttons. Just your hand.

## How It Works

1. A webcam feed is passed through Google's MediaPipe HandLandmarker model, which tracks 21 points on your hand in real time.
2. The number of extended fingers is calculated using distance-from-wrist ratios (not simple pixel comparisons), which stays accurate even when your hand is tilted or at an angle.
3. A temporal smoothing filter requires several consecutive frames to agree before a command is confirmed, killing flicker and false triggers.
4. The confirmed gesture is mapped to a drive command and sent over a TCP socket from the PC to the ESP32 on the local WiFi network.
5. The ESP32 receives the command over WiFi and forwards it over a wired serial connection to the Arduino.
6. The Arduino parses the command and drives the motors directly, PWM-controlling speed on each wheel through its H-bridge driver.

The pipeline in short:

```
PC (webcam + gesture detection) --WiFi/TCP--> ESP32 --Serial--> Arduino --> Motors
```

The ESP32's only job is to be the WiFi bridge. All motor logic and pin control lives on the Arduino.

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

- ESP32 development board, used purely as a WiFi-to-serial bridge
- Arduino board, wired to the ESP32 over serial (TX/RX), running the motor control logic
- 4x DC motors with a compatible dual-pin H-bridge driver (IN1/IN2 style, PWM-capable)
- Robot chassis, wheels, battery pack
- A computer with a webcam for the vision pipeline

## Software Stack

**Vision / control side (Python, runs on PC)**
- OpenCV for camera capture and display
- MediaPipe Tasks (HandLandmarker) for hand tracking
- Standard library `socket` for WiFi communication with the ESP32

**Bridge side (ESP32)**
- Listens for TCP connections on the local network
- Forwards received commands directly over serial to the Arduino, no parsing or logic of its own

**Motor control side (Arduino)**
- Reads commands over serial
- Parses forward, left, right, back, and stop
- Drives motor pins directly via digitalWrite/analogWrite

## Project Structure

```
.
├── hand_control.py      # Webcam capture, gesture detection, command sender (PC)
├── hand_landmarker.task # MediaPipe hand landmark model file
├── esp32_bridge.ino     # ESP32 firmware: WiFi server, forwards commands over serial
├── main.cpp             # Arduino firmware: command parsing and motor control
└── def.h                # Pin definitions and function declarations (Arduino side)
```

## Setup

### 1. Wire the ESP32 to the Arduino

Connect the ESP32's TX/RX pins to a serial input on the Arduino (e.g. `Serial1` if your Arduino board supports a second hardware serial port). Make sure both boards share a common ground.

### 2. Flash the Arduino

Wire your motor driver to the pins defined in `def.h`, update `motor_pins[]` to match your actual wiring, then flash `main.cpp` using PlatformIO or the Arduino IDE.

### 3. Flash the ESP32

Flash the ESP32 with a simple WiFi server sketch that listens for incoming TCP connections and forwards any received bytes straight to its serial output toward the Arduino. Note the IP address it prints to its own serial monitor on boot; you will need that for the Python script.

### 4. Configure the Python side

Install dependencies:

```bash
pip install opencv-python mediapipe
```

Download the `hand_landmarker.task` model file from MediaPipe's model zoo and place it in the project directory.

Update the IP address in `hand_control.py` to match your ESP32:

```python
ESP32_IP = "192.168.1.96"
```

### 5. Run it

```bash
python hand_control.py
```

Hold your hand up to the camera, palm facing the lens, fingers pointing up for best accuracy. Press `q` to quit; the car will automatically be sent a stop command on exit.

## Tuning

If gestures feel unreliable, a few knobs are worth adjusting:

- `STABLE_FRAMES_REQUIRED` in `hand_control.py` controls how many consecutive frames must agree before a command is sent. Raise it for more stability at the cost of a little latency.
- The `0.15 * mcp_dist` threshold in `count_extended_fingers` controls how far a fingertip must extend past the palm to count as "extended." Raise it if fingers register as extended too easily, lower it if extended fingers are being missed.
- `min_hand_detection_confidence`, `min_hand_presence_confidence`, and `min_tracking_confidence` can all be raised for stricter detection in noisy environments.

## Safety Notes

- The system defaults to stop on any unrecognized command, dropped connection, or missing hand, rather than continuing the last known motion.
- On script exit (including Ctrl+C or window close), a stop command is sent through the ESP32 to the Arduino before the socket closes.
- If the ESP32-to-Arduino serial link drops or the Arduino stops receiving bytes, it will not automatically know to stop; consider adding a serial timeout/watchdog on the Arduino side that brakes the motors if no command has been received in the last second or two.
- Test with wheels off the ground before running on the floor for the first time, especially after changing pin mappings or driver logic.

## Roadmap

- Add a watchdog timeout on the Arduino so it stops automatically if the ESP32 goes silent
- Add reverse-specific motor tuning distinct from the forward function
- Add speed control via hand distance from camera or a second gesture axis
- Add a debounced connection-loss indicator on the Python side so the operator knows immediately if the TCP link to the ESP32 drops

## License

Do whatever you want with it. Just do not run it over your cat.
