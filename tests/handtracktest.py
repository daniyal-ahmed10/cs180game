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

base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    num_hands=2
)
detector = vision.HandLandmarker.create_from_options(options)

### Defines which hand landmarks define which fingers
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Pinky
]





### Defines the hand skeleton function, which draws lines between fingers using the hand landmarks
def draw_hand_skeleton(frame, landmarks, w, h):
    points = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]

    for p1_idx, p2_idx in HAND_CONNECTIONS:
        cv2.line(frame, points[p1_idx], points[p2_idx], (0, 255, 0), 2)

    for pt in points:
        cv2.circle(frame, pt, 4, (0, 0, 255), -1)


def main():
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Success in Running. Press 'q' to quit.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab webcam frame")
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = Image(image_format=ImageFormat.SRGB, data=rgb_frame)

        detection_result = detector.detect(mp_image)

        if detection_result.hand_landmarks:
            for hand_landmarks in detection_result.hand_landmarks:
                draw_hand_skeleton(frame, hand_landmarks, w, h)

                min_y = min([lm.y for lm in hand_landmarks])
                wrist_x = hand_landmarks[0].x



 
        cv2.imshow("handtracktest.py", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()