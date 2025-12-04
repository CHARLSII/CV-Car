import os
import cv2

DATA_DIR = './data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Final 5 gesture classes
GESTURE_CLASSES = [
    "forward_both_open",      # 0
    "stop_both_fist",         # 1
    "left_turn",              # 2
    "right_turn",             # 3
    "reverse_down"            # 4
]

dataset_size = 150   # You can change if needed
cap = cv2.VideoCapture(0)

for class_id, gesture_name in enumerate(GESTURE_CLASSES):

    class_path = os.path.join(DATA_DIR, str(class_id))
    if not os.path.exists(class_path):
        os.makedirs(class_path)

    print(f'Collecting images for gesture: {gesture_name} (Class {class_id})')

    # Wait for Q to start collecting this gesture
    while True:
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)   # <-- MIRROR HERE

        text = f'Ready for: {gesture_name}. Press Q to start!'
        cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 3, cv2.LINE_AA)

        cv2.imshow('frame', frame)
        if cv2.waitKey(25) == ord('q'):
            break

    # Collect images
    counter = 0
    while counter < dataset_size:
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)   # <-- MIRROR HERE TOO

        cv2.putText(frame, f'Capturing {gesture_name}: {counter}/{dataset_size}', 
                    (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)

        cv2.imshow('frame', frame)
        cv2.waitKey(1)

        save_path = os.path.join(class_path, f'{counter}.jpg')
        cv2.imwrite(save_path, frame)

        counter += 1

cap.release()
cv2.destroyAllWindows()
