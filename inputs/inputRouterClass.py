######
#   InputRouter: the single place the game reads player input from.
#
#   It does three jobs:
#     1. Owns the one InputSource a level uses (keyboard, gesture, ...) and
#        switches between them when the level changes.
#     2. Turns raw device timestamps into song time, corrected for the player's
#        calibration and for how slow the source itself is.
#     3. Hands the result to the rest of the game as RoutedInputs.
#
#   HOW THE GAME USES IT:
#     router = InputRouter({"keyboard": KeyboardInput(), "gesture": GestureInput()})
#     router.set_calibration_offset(player_calibration)
#     router.choose_source_for_level("keyboard")
#     router.set_song_start(InputSource.now())      # when the song actually starts
#     every frame:  for hit in router.update(): hit_judge.judge(hit)
#     router.stop()
#
#   The router never looks at input_id, so a source that emits lane names
#   ("lane_0") and one that emits sign names ("Open_Palm") both work unchanged.
######
from dataclasses import dataclass
from typing import Dict, List, Optional

from inputs.inputSourceClass import InputSource, InputAction


# Extra delay per source type, in seconds: how long after the player's real
# action the source reports it. Keyboard is immediate; a camera has to grab a
# frame and run the model first. Tunable per source via set_source_latency().
DEFAULT_SOURCE_LATENCY: Dict[str, float] = {
    "keyboard": 0.0,
    "gesture": 0.10,
}


@dataclass(frozen=True)
class RoutedInput:
    input_id: str          # what was hit, straight from the source, e.g. "lane_2" or "Open_Palm"
    action: InputAction    # PRESSED or RELEASED (releases are kept for hold notes later)
    song_time: float       # seconds into the song, calibration- and latency-corrected
    raw_timestamp: float   # the original InputSource.now() timestamp, for debugging
    source: str            # name of the InputSource that produced it, e.g. "keyboard"


class InputRouter:

    def __init__(self, sources: Dict[str, InputSource],
                 calibration_offset: float = 0.0,
                 source_latency: Optional[Dict[str, float]] = None):
        """sources maps an input type ("keyboard", "gesture", ...) to the InputSource
        that handles it. Passing them in means tests can hand over fakes.
        calibration_offset and source_latency are both in seconds."""
        self._sources: Dict[str, InputSource] = dict(sources)
        self._active_type: Optional[str] = None
        self._song_start_time: Optional[float] = None
        self.calibration_offset = calibration_offset
        self.source_latency: Dict[str, float] = (
            dict(DEFAULT_SOURCE_LATENCY) if source_latency is None else dict(source_latency)
        )

    # ---- source management ----
    def choose_source_for_level(self, input_type: str) -> InputSource:
        """Make the source for input_type the active one: the previous source is
        stopped and the new one started. Returns the now-active source.
        Raises KeyError if no source was registered for input_type."""
        if input_type not in self._sources:
            raise KeyError(
                "no input source registered for %r (have: %s)"
                % (input_type, ", ".join(sorted(self._sources)) or "none")
            )

        source = self._sources[input_type]
        if self._active_type != input_type:
            self.stop()                  # only one source may listen at a time
            self._active_type = input_type
        source.start()                   # no-op if it is already running
        return source

    def stop(self):
        """Stop the active source. Does nothing if none is active."""
        if self._active_type is None:
            return
        self._sources[self._active_type].stop()
        self._active_type = None

    def active_input_type(self) -> Optional[str]:
        """The input type currently being read, or None."""
        return self._active_type

    def active_source(self) -> Optional[InputSource]:
        """The InputSource currently being read, or None."""
        if self._active_type is None:
            return None
        return self._sources[self._active_type]

    # ---- timing ----
    def set_song_start(self, t: float):
        """Tell the router when the song started. t is an InputSource.now() value,
        taken at the moment the first beat of the song is heard."""
        self._song_start_time = t

    def clear_song_start(self):
        """Forget the song start, e.g. between songs. update() goes quiet again."""
        self._song_start_time = None

    def song_has_started(self) -> bool:
        return self._song_start_time is not None

    def set_calibration_offset(self, seconds: float):
        """Set the player's calibration offset. Positive means the player's inputs
        land late, so this much is taken off every input's song time."""
        self.calibration_offset = seconds

    def set_source_latency(self, input_type: str, seconds: float):
        """Set the extra delay to subtract for one source type."""
        self.source_latency[input_type] = seconds

    def to_song_time(self, raw_timestamp: float) -> float:
        """Convert an InputSource.now() timestamp into corrected song time.
        Only valid once the song has started."""
        latency = self.source_latency.get(self._active_type, 0.0)  # unknown types: no correction
        return (raw_timestamp - self._song_start_time) - self.calibration_offset - latency

    # ---- per frame ----
    def update(self) -> List[RoutedInput]:
        """Poll the active source and return its events as RoutedInputs, oldest first.
        Call once per frame. Returns an empty list when no source is active.
        While the song hasn't started there is nothing to time inputs against, so
        events are drained and dropped instead of arriving at a negative song time."""
        source = self.active_source()
        if source is None:
            return []

        events = source.poll()
        if self._song_start_time is None:
            return []

        routed = [
            RoutedInput(
                input_id=event.input_id,
                action=event.action,
                song_time=self.to_song_time(event.timestamp),
                raw_timestamp=event.timestamp,
                source=event.source,
            )
            for event in events
        ]
        # poll() is already in order, but a threaded source can queue device
        # timestamps slightly out of order; sorting keeps the contract.
        routed.sort(key=lambda hit: hit.raw_timestamp)
        return routed
