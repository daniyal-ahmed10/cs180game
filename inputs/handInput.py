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


# Sends gestures to GODOT
class HandInputSource(InputSource):
    def __init__(
        self,
        model_path: str = "hand_landmarker.task",
        camera_index: int = 0,
        udp_host: str = "127.0.0.1",
        udp_port: int = 4242,
        show_preview: bool = True,
    ):
        super().__init__("hand_tracker")
        self.model_path = model_path
        self.camera_index = camera_index
        self.udp_addr = (udp_host, udp_port)
        self.show_preview = show_preview

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._active_gesture: str | None = None

    # Camera On
    def _start_capture(self):
        self._stop_event.clear()
        self._active_gesture = None
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    #Camera Off
    def _stop_capture(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _send_to_godot(self, gesture: str):
        self._sock.sendto(gesture.encode("utf-8"), self.udp_addr)

    def _capture_loop(self):
        base_options = python.BaseOptions(model_asset_path=self.model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=2,
        )
        detector = vision.HandLandmarker.create_from_options(options)
        cap = cv2.VideoCapture(self.camera_index)

        try:
            while not self._stop_event.is_set() and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    continue

                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = Image(image_format=ImageFormat.SRGB, data=rgb)
                result = detector.detect(mp_image)

                detected = classify_hands(result.hand_landmarks)

                if detected != self._active_gesture:
                    now = self.now()
                    if self._active_gesture is not None:
                        self._emit(self._active_gesture, InputAction.RELEASED, now)
                    if detected is not None:
                        self._emit(detected, InputAction.PRESSED, now)
                        self._send_to_godot(detected)
                    self._active_gesture = detected

                if self.show_preview:
                    label = self._active_gesture or "none"
                    cv2.putText(
                        frame, f"Gesture: {label}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2
                    )
                    cv2.imshow("Ritmo Hand Input (Press Q to quit)", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        self._stop_event.set()
                        break
        finally:
            cap.release()
            if self.show_preview:
                cv2.destroyAllWindows()