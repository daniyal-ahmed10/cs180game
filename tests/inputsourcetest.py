######
#   Tests for inputs/inputSourceClass.py using a dummy subclass (test only).
#   Run from the cs180game folder:  python -m unittest tests.inputsourcetest -v
######
import threading
import unittest

from inputs.inputSourceClass import InputSource, InputEvent, InputAction


class DummyInput(InputSource):
    """Fake device: the test 'presses' inputs by calling simulate()."""

    def __init__(self):
        super().__init__("dummy")
        self.start_calls = 0
        self.stop_calls = 0

    def _start_capture(self):
        self.start_calls += 1

    def _stop_capture(self):
        self.stop_calls += 1

    def simulate(self, input_id, action, timestamp=None):
        self._emit(input_id, action, timestamp)


class InputSourceTest(unittest.TestCase):

    def test_cannot_instantiate_base_class(self):
        with self.assertRaises(TypeError):
            InputSource("base")

    def test_subclass_must_implement_capture_methods(self):
        class Incomplete(InputSource):
            def _start_capture(self):
                pass
        with self.assertRaises(TypeError):
            Incomplete("incomplete")

    def test_start_stop_and_is_active(self):
        src = DummyInput()
        self.assertFalse(src.is_active())
        src.start()
        src.start()                          # second start is a no-op
        self.assertTrue(src.is_active())
        self.assertEqual(src.start_calls, 1)
        src.stop()
        src.stop()                           # second stop is a no-op
        self.assertFalse(src.is_active())
        self.assertEqual(src.stop_calls, 1)

    def test_poll_returns_events_in_order_then_empties(self):
        src = DummyInput()
        src.start()
        src.simulate("a", InputAction.PRESSED, 1.0)
        src.simulate("a", InputAction.RELEASED, 1.2)
        self.assertEqual(src.poll(), [
            InputEvent("a", InputAction.PRESSED, 1.0, "dummy"),
            InputEvent("a", InputAction.RELEASED, 1.2, "dummy"),
        ])
        self.assertEqual(src.poll(), [])

    def test_events_ignored_while_inactive(self):
        src = DummyInput()
        src.simulate("a", InputAction.PRESSED)
        src.start()
        self.assertEqual(src.poll(), [])
        src.stop()
        src.simulate("a", InputAction.PRESSED)
        self.assertEqual(src.poll(), [])

    def test_default_timestamp_uses_clock(self):
        src = DummyInput()
        src.start()
        before = InputSource.now()
        src.simulate("a", InputAction.PRESSED)
        after = InputSource.now()
        (event,) = src.poll()
        self.assertTrue(before <= event.timestamp <= after)

    def test_restart_drops_stale_events(self):
        src = DummyInput()
        src.start()
        src.simulate("a", InputAction.PRESSED)
        src.stop()
        src.start()
        self.assertEqual(src.poll(), [])

    def test_emit_from_another_thread(self):
        src = DummyInput()
        src.start()
        workers = [threading.Thread(target=lambda: [src.simulate("x", InputAction.PRESSED) for _ in range(100)])
                   for _ in range(4)]
        for w in workers:
            w.start()
        for w in workers:
            w.join()
        self.assertEqual(len(src.poll()), 400)


if __name__ == "__main__":
    unittest.main()
