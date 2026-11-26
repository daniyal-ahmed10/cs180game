######
#   Tests for inputs/inputRouterClass.py using a fake InputSource (test only),
#   so nothing here touches a real keyboard or camera.
#   Run from the cs180game folder:  python -m pytest tests/test_input_router.py -v
######
import pytest

from inputs.inputSourceClass import InputSource, InputAction
from inputs.inputRouterClass import InputRouter, RoutedInput


SONG_START = 1000.0        # a pretend InputSource.now() value; the clock's zero is arbitrary


class FakeInput(InputSource):
    """Fake device: the test 'presses' inputs by calling press() / release(),
    and counts start/stop so source switching can be checked."""

    def __init__(self, name="fake"):
        super().__init__(name)
        self.start_calls = 0
        self.stop_calls = 0

    def _start_capture(self):
        self.start_calls += 1

    def _stop_capture(self):
        self.stop_calls += 1

    def press(self, input_id, timestamp):
        self._emit(input_id, InputAction.PRESSED, timestamp)

    def release(self, input_id, timestamp):
        self._emit(input_id, InputAction.RELEASED, timestamp)


@pytest.fixture
def sources():
    """One fake source per input type the router knows about."""
    return {"keyboard": FakeInput("keyboard"), "gesture": FakeInput("gesture")}


@pytest.fixture
def router(sources):
    """A router already reading the keyboard, with the song running."""
    router = InputRouter(sources)
    router.choose_source_for_level("keyboard")
    router.set_song_start(SONG_START)
    return router


# ---- song time conversion ----
def test_song_time_is_measured_from_the_start_time(router, sources):
    sources["keyboard"].press("lane_0", SONG_START + 2.5)
    [hit] = router.update()
    assert hit.song_time == pytest.approx(2.5)
    assert hit.raw_timestamp == pytest.approx(SONG_START + 2.5)
    assert hit.input_id == "lane_0"
    assert hit.action is InputAction.PRESSED
    assert hit.source == "keyboard"
    assert isinstance(hit, RoutedInput)


def test_releases_are_routed_too(router, sources):
    sources["keyboard"].press("lane_1", SONG_START + 1.0)
    sources["keyboard"].release("lane_1", SONG_START + 1.4)
    press, release = router.update()
    assert press.action is InputAction.PRESSED
    assert release.action is InputAction.RELEASED
    assert release.song_time == pytest.approx(1.4)


# ---- calibration offset ----
def test_calibration_offset_is_subtracted(router, sources):
    router.set_calibration_offset(0.05)
    sources["keyboard"].press("lane_2", SONG_START + 3.0)
    [hit] = router.update()
    assert hit.song_time == pytest.approx(2.95)


def test_negative_calibration_offset_shifts_the_other_way(router, sources):
    router.set_calibration_offset(-0.05)
    sources["keyboard"].press("lane_2", SONG_START + 3.0)
    [hit] = router.update()
    assert hit.song_time == pytest.approx(3.05)


def test_calibration_offset_defaults_to_zero(sources):
    assert InputRouter(sources).calibration_offset == 0.0


# ---- per-source latency ----
def test_gesture_latency_is_subtracted(sources):
    router = InputRouter(sources)
    router.choose_source_for_level("gesture")
    router.set_song_start(SONG_START)

    sources["gesture"].press("Open_Palm", SONG_START + 4.0)
    [hit] = router.update()
    assert hit.song_time == pytest.approx(3.90)      # 4.0 - 0.10 gesture latency


def test_keyboard_has_no_latency_correction(router, sources):
    sources["keyboard"].press("lane_3", SONG_START + 4.0)
    [hit] = router.update()
    assert hit.song_time == pytest.approx(4.0)


def test_latency_and_calibration_both_apply(sources):
    router = InputRouter(sources)
    router.choose_source_for_level("gesture")
    router.set_song_start(SONG_START)
    router.set_calibration_offset(0.02)

    sources["gesture"].press("Open_Palm", SONG_START + 4.0)
    [hit] = router.update()
    assert hit.song_time == pytest.approx(3.88)      # 4.0 - 0.02 - 0.10


def test_source_latency_is_tunable(sources):
    router = InputRouter(sources)
    router.choose_source_for_level("gesture")
    router.set_song_start(SONG_START)
    router.set_source_latency("gesture", 0.25)

    sources["gesture"].press("Open_Palm", SONG_START + 4.0)
    [hit] = router.update()
    assert hit.song_time == pytest.approx(3.75)


def test_unknown_source_type_gets_no_latency_correction():
    # A source type missing from source_latency still works, just uncorrected.
    source = FakeInput("drums")
    router = InputRouter({"drums": source})
    router.choose_source_for_level("drums")
    router.set_song_start(SONG_START)

    source.press("tom_1", SONG_START + 1.0)
    [hit] = router.update()
    assert hit.song_time == pytest.approx(1.0)


# ---- source management ----
def test_switching_sources_stops_the_old_one_and_starts_the_new_one(sources):
    router = InputRouter(sources)
    keyboard, gesture = sources["keyboard"], sources["gesture"]

    router.choose_source_for_level("keyboard")
    assert keyboard.is_active() and keyboard.start_calls == 1
    assert not gesture.is_active() and gesture.start_calls == 0

    router.choose_source_for_level("gesture")
    assert not keyboard.is_active() and keyboard.stop_calls == 1
    assert gesture.is_active() and gesture.start_calls == 1
    assert router.active_input_type() == "gesture"
    assert router.active_source() is gesture


def test_choosing_the_same_source_twice_does_not_restart_it(sources):
    router = InputRouter(sources)
    router.choose_source_for_level("keyboard")
    router.choose_source_for_level("keyboard")
    assert sources["keyboard"].start_calls == 1
    assert sources["keyboard"].stop_calls == 0


def test_stop_stops_the_active_source(router, sources):
    router.stop()
    assert not sources["keyboard"].is_active()
    assert sources["keyboard"].stop_calls == 1
    assert router.active_input_type() is None
    assert router.active_source() is None
    router.stop()                                    # second stop is a no-op
    assert sources["keyboard"].stop_calls == 1


def test_unknown_input_type_raises(sources):
    with pytest.raises(KeyError):
        InputRouter(sources).choose_source_for_level("ocarina")


def test_router_only_reads_the_active_source(router, sources):
    sources["gesture"].start()                       # started behind the router
    sources["gesture"].press("Open_Palm", SONG_START + 1.0)
    sources["keyboard"].press("lane_0", SONG_START + 1.0)
    [hit] = router.update()
    assert hit.source == "keyboard"


# ---- nothing to report ----
def test_empty_list_when_no_source_is_active(sources):
    router = InputRouter(sources)
    router.set_song_start(SONG_START)
    assert router.update() == []


def test_empty_list_before_the_song_starts(sources):
    router = InputRouter(sources)
    router.choose_source_for_level("keyboard")
    assert not router.song_has_started()

    sources["keyboard"].press("lane_0", SONG_START - 1.0)
    assert router.update() == []


def test_inputs_from_before_the_song_are_not_held_over(router, sources):
    # Mashing during the countdown must not turn up as a hit once the song starts.
    router.clear_song_start()
    sources["keyboard"].press("lane_0", SONG_START - 1.0)
    assert router.update() == []

    router.set_song_start(SONG_START)
    assert router.update() == []


def test_empty_list_when_nothing_was_pressed(router):
    assert router.update() == []


# ---- ordering ----
def test_events_come_back_oldest_first(router, sources):
    keyboard = sources["keyboard"]
    keyboard.press("lane_0", SONG_START + 1.0)
    keyboard.press("lane_1", SONG_START + 1.5)
    keyboard.press("lane_2", SONG_START + 2.0)

    hits = router.update()
    assert [hit.input_id for hit in hits] == ["lane_0", "lane_1", "lane_2"]
    assert [hit.song_time for hit in hits] == sorted(hit.song_time for hit in hits)


def test_out_of_order_device_timestamps_are_sorted(router, sources):
    # A threaded source (e.g. the camera) can queue timestamps out of order.
    sources["keyboard"].press("late", SONG_START + 2.0)
    sources["keyboard"].press("early", SONG_START + 1.0)
    assert [hit.input_id for hit in router.update()] == ["early", "late"]


def test_update_drains_the_queue(router, sources):
    sources["keyboard"].press("lane_0", SONG_START + 1.0)
    assert len(router.update()) == 1
    assert router.update() == []
