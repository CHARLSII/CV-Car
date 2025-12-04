import os
import pickle
import mediapipe as mp
import cv2

DATA_DIR = "./data"

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=2,
    min_detection_confidence=0.3
)

data = []
labels = []

# HAND LANDMARK COUNT = 21 points
# We extract: x and y for each → 42 per hand → 84 total for two hands.

for dir_name in sorted(os.listdir(DATA_DIR), key=lambda x: int(x)):
    class_id = int(dir_name)
    class_path = os.path.join(DATA_DIR, dir_name)

    for img_file in os.listdir(class_path):
        img_path = os.path.join(class_path, img_file)
        img = cv2.imread(img_path)

        if img is None:
            continue

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        # Prepare 84-long feature vector
        features = [0.0] * 84

        # Dictionary to store left/right hand
        hand_dict = {"Left": None, "Right": None}

        if results.multi_hand_landmarks and results.multi_handedness:

            # Assign each detected hand as Left or Right
            for idx, handed in enumerate(results.multi_handedness):
                label = handed.classification[0].label  # "Left" or "Right"
                hand_dict[label] = results.multi_hand_landmarks[idx]

            # Left hand → features[0:42]
            if hand_dict["Left"]:
                index = 0
                x_list = [lm.x for lm in hand_dict["Left"].landmark]
                y_list = [lm.y for lm in hand_dict["Left"].landmark]
                min_x, min_y = min(x_list), min(y_list)

                for lm in hand_dict["Left"].landmark:
                    features[index]     = lm.x - min_x
                    features[index + 1] = lm.y - min_y
                    index += 2

            # Right hand → features[42:84]
            if hand_dict["Right"]:
                index = 42
                x_list = [lm.x for lm in hand_dict["Right"].landmark]
                y_list = [lm.y for lm in hand_dict["Right"].landmark]
                min_x, min_y = min(x_list), min(y_list)

                for lm in hand_dict["Right"].landmark:
                    features[index]     = lm.x - min_x
                    features[index + 1] = lm.y - min_y
                    index += 2

        # Save feature vector + label
        data.append(features)
        labels.append(class_id)

# Save dataset
with open("data.pickle", "wb") as f:
    pickle.dump({"data": data, "labels": labels}, f)

print("Dataset created → data.pickle")
