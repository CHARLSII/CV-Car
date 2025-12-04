import pickle
import cv2
import mediapipe as mp
import numpy as np
from bleak import BleakClient, BleakScanner
import asyncio

# ----------------------------
# LOAD MODEL
# ----------------------------
model_dict = pickle.load(open('./model.p', 'rb'))
model = model_dict['model']

# ----------------------------
# CAMERA SETUP
# ----------------------------
cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ----------------------------
# LABELS
# ----------------------------
labels_dict = {
    0: 'Forward',
    1: 'Stop',
    2: 'Left',
    3: 'Right',
    4: 'Reverse'
}

# ----------------------------
# BLE UUIDs (match ESP32)
# ----------------------------
SERVICE_UUID = "0000181c-0000-1000-8000-00805f9b34fb"
CHAR_UUID     = "00002a56-0000-1000-8000-00805f9b34fb"

previous_gesture = None


async def main():
    print("Scanning for ESP32_RC_CAR...")
    device = await BleakScanner.find_device_by_name("ESP32_RC_Car")

    if device is None:
        print("ESP32 not found!")
        return

    print("Connecting...")
    async with BleakClient(device) as client:
        print("Connected to ESP32 over BLE!")

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            H, W, _ = frame.shape
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)

            features = [0.0] * 84
            hand_dict = {"Left": None, "Right": None}

            if results.multi_hand_landmarks and results.multi_handedness:

                for idx, handed in enumerate(results.multi_handedness):
                    label = handed.classification[0].label
                    hand_dict[label] = results.multi_hand_landmarks[idx]

                if hand_dict["Left"]:
                    index = 0
                    x_list = [lm.x for lm in hand_dict["Left"].landmark]
                    y_list = [lm.y for lm in hand_dict["Left"].landmark]
                    min_x, min_y = min(x_list), min(y_list)
                    for lm in hand_dict["Left"].landmark:
                        features[index] = lm.x - min_x
                        features[index+1] = lm.y - min_y
                        index += 2

                if hand_dict["Right"]:
                    index = 42
                    x_list = [lm.x for lm in hand_dict["Right"].landmark]
                    y_list = [lm.y for lm in hand_dict["Right"].landmark]
                    min_x, min_y = min(x_list), min(y_list)
                    for lm in hand_dict["Right"].landmark:
                        features[index] = lm.x - min_x
                        features[index+1] = lm.y - min_y
                        index += 2

                prediction = model.predict([np.asarray(features)])
                gesture_id = int(prediction[0])
                predicted_gesture = labels_dict.get(gesture_id, "Unknown")

                # Send only if changed
                global previous_gesture
                if predicted_gesture != previous_gesture:
                    await client.write_gatt_char(CHAR_UUID, predicted_gesture.encode())
                    print("Sent BLE:", predicted_gesture)
                    previous_gesture = predicted_gesture

                cv2.putText(frame, predicted_gesture, (30, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

            cv2.imshow("Gesture Recognition", frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break

        cap.release()
        cv2.destroyAllWindows()


asyncio.run(main())
