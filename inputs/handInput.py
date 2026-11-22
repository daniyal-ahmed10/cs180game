import math
import socket
import threading
import cv2
from mediapipe import Image, ImageFormat
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from inputs.inputSourceClass import InputSource, InputAction


def _finger_states(landmarks) -> tuple[bool, bool, bool, bool]:
    return (
        landmarks[8].y < landmarks[6].y,   
        landmarks[12].y < landmarks[10].y,  
        landmarks[16].y < landmarks[14].y,  
        landmarks[20].y < landmarks[18].y, 
    )


NORMAL_GESTURES = {
    (False, False, False, False): "fist",
    (True, False, False, False): "pointing",
    (True, True, False, False): "peace",
    (True, False, False, True): "rock_on",
}


#THIS FUNC FOR THE SPECIAL MOVES****** FIGURE OUT LATEr
def _dist(lm1, lm2) -> float:
    return math.hypot(lm1.x - lm2.x, lm1.y - lm2.y)


def classify_hands(all_hand_landmarks) -> str | None:
    if not all_hand_landmarks:
        return None

    if len(all_hand_landmarks) >= 2:
        h1, h2 = all_hand_landmarks[0], all_hand_landmarks[1]
        _, m1, r1, p1 = _finger_states(h1)
        _, m2, r2, p2 = _finger_states(h2)
        other_fingers_curled = not any([m1, r1, p1, m2, r2, p2])

        #SPECIAL MOVE NO.1 
        if other_fingers_curled and _dist(h1[8], h2[8]) < 0.07:
            return "index_touch"

    hand = all_hand_landmarks[0]
    idx, mid, ring, pinky = _finger_states(hand)

    #SPECIAL MOVE NO.2
    if not any([mid, ring, pinky]) and _dist(hand[4], hand[8]) < 0.06:
        return "korean_heart"

    return NORMAL_GESTURES.get((idx, mid, ring, pinky))