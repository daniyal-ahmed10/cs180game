######
#   InputSource: abstract base class for every way a player can give input
#   (keyboard, controller, touch, motion tracking, ...).
#
#   HOW SUBCLASSES USE IT:
#     1. Implement _start_capture() and _stop_capture() (open/close the device or listener).
#     2. Whenever the device reports something, call self._emit(input_id, InputAction.PRESSED / RELEASED).
#
#   HOW THE GAME USES IT:
#     source.start()
#     every frame:  for event in source.poll(): ...
#     source.stop()
######
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from queue import Queue, Empty


class InputAction(Enum):
    PRESSED = "pressed"
    RELEASED = "released"


@dataclass(frozen=True)
class InputEvent:
    input_id: str          # what was hit, e.g. "d", "button_a", "lane_2" (meaning is up to the subclass)
    action: InputAction    # PRESSED or RELEASED
    timestamp: float       # seconds on the InputSource.now() clock
    source: str            # name of the InputSource that produced it, e.g. "keyboard"


class InputSource(ABC):

    def __init__(self, name: str):
        self.name = name
        self._active = False
        self._events = Queue()     # thread-safe: device listeners often run on their own thread

    # ---- clock ----
    @staticmethod
    def now() -> float:
        """Shared clock for all input timestamps (high resolution, never goes backwards)."""
        return time.perf_counter()

    # ---- public API ----
    def start(self):
        """Begin capturing input. Does nothing if already active."""
        if self._active:
            return
        self._clear()                # don't hand out stale events from a previous session
        self._start_capture()
        self._active = True

    def stop(self):
        """Stop capturing input. Does nothing if already stopped."""
        if not self._active:
            return
        self._active = False
        self._stop_capture()

    def is_active(self) -> bool:
        return self._active

    def poll(self) -> list:
        """Return all InputEvents since the last poll (oldest first) and remove them from the queue.
        Meant to be called once per frame by the game loop."""
        events = []
        while True:
            try:
                events.append(self._events.get_nowait())
            except Empty:
                return events

    # ---- for subclasses ----
    def _emit(self, input_id: str, action: InputAction, timestamp: float = None):
        """Queue an input event. Ignored when the source isn't active.
        Pass a timestamp if the device gives one; otherwise the current time is used."""
        if not self._active:
            return
        if timestamp is None:
            timestamp = self.now()
        self._events.put(InputEvent(input_id, action, timestamp, self.name))

    @abstractmethod
    def _start_capture(self):
        """Open the device / start the listener."""

    @abstractmethod
    def _stop_capture(self):
        """Close the device / stop the listener."""

    # ---- internal ----
    def _clear(self):
        while True:
            try:
                self._events.get_nowait()
            except Empty:
                return
