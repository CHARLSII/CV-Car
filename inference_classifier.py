import pickle
import cv2
import mediapipe as mp
import numpy as np
import serial
import time

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
# SERIAL TO ESP32
# ----------------------------
esp32 = serial.Serial('COM3', 115200)  # replace COM3 with your ESP32 port
time.sleep(2)  # wait for ESP32 to initialize

previous_gesture = None  # track last sent gesture

# ----------------------------
# MAIN LOOP
# ----------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)  # mirror image
    H, W, _ = frame.shape
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    features = [0.0] * 84  # 2 hands × 21 landmarks × (x,y)
    hand_dict = {"Left": None, "Right": None}

    if results.multi_hand_landmarks and results.multi_handedness:
        # Assign hands
        for idx, handed in enumerate(results.multi_handedness):
            label = handed.classification[0].label
            hand_dict[label] = results.multi_hand_landmarks[idx]

        # Left hand → features[0:42]
        if hand_dict["Left"]:
            index = 0
            x_list = [lm.x for lm in hand_dict["Left"].landmark]
            y_list = [lm.y for lm in hand_dict["Left"].landmark]
            min_x, min_y = min(x_list), min(y_list)
            for lm in hand_dict["Left"].landmark:
                features[index] = lm.x - min_x
                features[index+1] = lm.y - min_y
                index += 2
            mp_drawing.draw_landmarks(
                frame, hand_dict["Left"], mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

        # Right hand → features[42:84]
        if hand_dict["Right"]:
            index = 42
            x_list = [lm.x for lm in hand_dict["Right"].landmark]
            y_list = [lm.y for lm in hand_dict["Right"].landmark]
            min_x, min_y = min(x_list), min(y_list)
            for lm in hand_dict["Right"].landmark:
                features[index] = lm.x - min_x
                features[index+1] = lm.y - min_y
                index += 2
            mp_drawing.draw_landmarks(
                frame, hand_dict["Right"], mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

        # Predict gesture
        prediction = model.predict([np.asarray(features)])
        gesture_id = int(prediction[0])
        predicted_gesture = labels_dict.get(gesture_id, "Unknown")

        # Send to ESP32 only if changed
        if predicted_gesture != previous_gesture:
            esp32.write((predicted_gesture + "\n").encode())
            previous_gesture = predicted_gesture

        # Display on frame
        cv2.putText(frame, predicted_gesture, (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3,
                    cv2.LINE_AA)

    cv2.imshow('Gesture Recognition', frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
        break

cap.release()
cv2.destroyAllWindows()
esp32.close()
