######
#   MAIN PURPOSE OF SCRIPT:
#    1. Testing hand tracking using OpenCV and MediaPipe
#    2. Verifying if Hand Symbols can be used as input by having a box pop up when a specific hand signal is detected
#    3. Pressing 'q' will exit the program
######
#   PREREQUISITES
#   1. Install the required packages:
#      pip install opencv-python mediapipe
#   2. Ensure you have a webcam connected to your computer for hand tracking
#   3. To run this script, a virtual environment may be required to avoid conflicts with other packages
######

import cv2
from mediapipe import Image, ImageFormat
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# Initialize hand tracker
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)


def classify_hand_gesture(landmarks):
    index_open = landmarks[8].y < landmarks[6].y
    middle_open = landmarks[12].y < landmarks[10].y
    ring_open = landmarks[16].y < landmarks[14].y
    pinky_open = landmarks[20].y < landmarks[18].y
    
    
    if not any([index_open, middle_open, ring_open, pinky_open]):
        return "THIS IS A CLOSED FIRST"
    elif index_open and not any([middle_open, ring_open, pinky_open]):
        return "THIS IS A POINTED FINGER"
    elif all([index_open, middle_open, ring_open, pinky_open]):
        return "THIS IS AN OPEN HAND"
    
    return "UNKNOWN GESTURE"


cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab camera frame.")
        break

    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

            gesture_text = classify_hand_gesture(hand_landmarks.landmark)

            min_y = min([lm.y for lm in hand_landmarks.landmark])
            wrist_x = hand_landmarks.landmark[0].x

            text_x = int(wrist_x * w) - 50
            text_y = int(min_y * h) - 20

            text_x = max(10, min(text_x, w - 200))
            text_y = max(30, text_y)

            cv2.rectangle(frame, (text_x - 5, text_y - 25), (text_x + 220, text_y + 5), (0, 0, 0), -1)
            cv2.putText(
                frame,
                gesture_text,
                (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA
            )

    cv2.imshow("Hand Symbol Tracking", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()