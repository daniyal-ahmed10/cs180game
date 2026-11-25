import unittest

from song.scoreMgrClass import ScoreMgr


def make(notecount=10):
    mgr = ScoreMgr()
    mgr.notecount = notecount
    return mgr


class TestTapScoring(unittest.TestCase):
    def test_perfect(self):
        m = make()
        m.addscore(0)
        self.assertEqual(m.score, 100)

    def test_great(self):
        m = make()
        m.addscore(50)
        self.assertEqual(m.score, 50)

    def test_okay(self):
        m = make()
        m.addscore(100)
        self.assertEqual(m.score, 25)

    def test_miss_outside_okay_window(self):
        m = make()
        m.addscore(130)
        self.assertEqual(m.score, 0)

    def test_window_boundaries_are_inclusive(self):
        for err, expected in [(20.0, 100), (70.0, 50), (110.0, 25)]:
            with self.subTest(err=err):
                m = make()
                m.addscore(err)
                self.assertEqual(m.score, expected)

    def test_just_past_boundaries(self):
        for err, expected in [(20.01, 50), (70.01, 25), (110.01, 0)]:
            with self.subTest(err=err):
                m = make()
                m.addscore(err)
                self.assertEqual(m.score, expected)

    def test_early_hits_use_absolute_error(self):
        m = make()
        m.addscore(-15)
        self.assertEqual(m.score, 100)
        m.addscore(-60)
        self.assertEqual(m.score, 150)
        m.addscore(-500)
        self.assertEqual(m.score, 150)


class TestCombo(unittest.TestCase):
    def test_combo_increments_on_hits(self):
        m = make()
        for _ in range(3):
            m.addscore(0)
        self.assertEqual(m.combo, 3)
        self.assertEqual(m.max_combo, 3)

    def test_miss_resets_combo_but_keeps_max(self):
        m = make()
        for _ in range(4):
            m.addscore(0)
        m.addscore(999)
        self.assertEqual(m.combo, 0)
        self.assertEqual(m.max_combo, 4)

    def test_max_combo_only_updates_when_beaten(self):
        m = make()
        for _ in range(5):
            m.addscore(0)
        m.addscore(999)
        for _ in range(2):
            m.addscore(0)
        self.assertEqual(m.combo, 2)
        self.assertEqual(m.max_combo, 5)
        for _ in range(4):
            m.addscore(0)
        self.assertEqual(m.max_combo, 6)

    def test_okay_hit_keeps_combo(self):
        m = make()
        m.addscore(0)
        m.addscore(100)
        self.assertEqual(m.combo, 2)

    def test_initial_state(self):
        m = make()
        self.assertEqual((m.score, m.combo, m.max_combo), (0, 0, 0))
        self.assertEqual(m.accuracy, 1)


class TestAccuracy(unittest.TestCase):
    def test_all_perfect_is_one(self):
        m = make(notecount=5)
        for _ in range(5):
            m.addscore(0)
        self.assertAlmostEqual(m.accuracy, 1.0)

    def test_mixed_hits(self):
        m = make(notecount=4)
        m.addscore(0)    # 100
        m.addscore(50)   # 50
        m.addscore(100)  # 25
        m.addscore(999)  # 0
        self.assertAlmostEqual(m.accuracy, 175 / 400)

    def test_all_misses_is_zero(self):
        m = make(notecount=3)
        for _ in range(3):
            m.addscore(999)
        self.assertEqual(m.accuracy, 0)

    def test_accuracy_updates_after_every_call(self):
        m = make(notecount=2)
        m.addscore(0)
        self.assertAlmostEqual(m.accuracy, 0.5)
        m.addscore(0)
        self.assertAlmostEqual(m.accuracy, 1.0)

    def test_zero_notecount_does_not_divide_by_zero(self):
        m = make(notecount=0)
        m.addscore(0)  # should not raise ZeroDivisionError
        self.assertEqual(m.accuracy, 100)  # score / 1 fallback


class TestHoldNotes(unittest.TestCase):
    def test_full_hold_perfect(self):
        m = make()
        m.addscore(0, "hold", 1.0)
        self.assertEqual(m.score, 100)

    def test_half_hold_perfect(self):
        m = make()
        m.addscore(0, "hold", 0.5)
        self.assertEqual(m.score, 50)

    def test_hold_scaled_by_window(self):
        m = make()
        m.addscore(50, "hold", 0.5)  # great = 50 * 0.5
        self.assertEqual(m.score, 25)

    def test_hold_miss_scores_zero_and_breaks_combo(self):
        m = make()
        m.addscore(0)
        m.addscore(500, "hold", 1.0)
        self.assertEqual(m.score, 100)
        self.assertEqual(m.combo, 0)

    def test_zero_hold_pct_scores_zero_but_counts_as_hit(self):
        m = make()
        m.addscore(0, "hold", 0.0)
        self.assertEqual(m.score, 0)
        self.assertEqual(m.combo, 1)

    def test_hold_contributes_to_accuracy(self):
        m = make(notecount=2)
        m.addscore(0, "hold", 0.5)  # 50
        m.addscore(0)               # 100
        self.assertAlmostEqual(m.accuracy, 150 / 200)


class TestHoldCountsAsOneTap(unittest.TestCase):
    """A fully held note (holdPct == 1.0) must score exactly like one tap."""

    def test_full_hold_equals_tap_in_every_window(self):
        for err in [0, 20, 50, 70, 100, 110, 111, 999]:
            with self.subTest(err=err):
                tap, hold = make(), make()
                tap.addscore(err, "tap")
                hold.addscore(err, "hold", 1.0)
                self.assertEqual(hold.score, tap.score)
                self.assertEqual(hold.combo, tap.combo)
                self.assertEqual(hold.max_combo, tap.max_combo)
                self.assertAlmostEqual(hold.accuracy, tap.accuracy)

    def test_full_hold_adds_only_one_combo(self):
        m = make()
        m.addscore(0, "hold", 1.0)
        self.assertEqual(m.combo, 1)

    def test_perfect_run_of_taps_and_full_holds_is_100_percent(self):
        m = make(notecount=4)
        m.addscore(0, "tap")
        m.addscore(0, "hold", 1.0)
        m.addscore(0, "tap")
        m.addscore(0, "hold", 1.0)
        self.assertAlmostEqual(m.accuracy, 1.0)

    def test_partial_hold_never_exceeds_a_tap(self):
        for pct in [0.0, 0.25, 0.5, 0.99]:
            with self.subTest(pct=pct):
                tap, hold = make(), make()
                tap.addscore(0, "tap")
                hold.addscore(0, "hold", pct)
                self.assertLessEqual(hold.score, tap.score)


class TestDefaults(unittest.TestCase):
    def test_notecount_defaults_to_zero(self):
        self.assertEqual(ScoreMgr().notecount, 0)

    def test_addscore_works_without_setting_notecount(self):
        m = ScoreMgr()
        m.addscore(0)  # must not raise
        self.assertEqual(m.score, 100)


class TestValidation(unittest.TestCase):
    def test_invalid_note_type_raises_value_error(self):
        m = make()
        with self.assertRaises(ValueError):
            m.addscore(0, "slide")

    def test_invalid_note_type_does_not_change_state(self):
        m = make()
        try:
            m.addscore(0, "slide")
        except ValueError:
            pass
        self.assertEqual((m.score, m.combo, m.max_combo), (0, 0, 0))


class TestHoldPctValidation(unittest.TestCase):
    def test_hold_pct_below_zero_raises(self):
        m = make()
        with self.assertRaises(ValueError):
            m.addscore(0, "hold", -0.01)

    def test_hold_pct_above_one_raises(self):
        m = make()
        with self.assertRaises(ValueError):
            m.addscore(0, "hold", 1.01)

    def test_hold_pct_bounds_are_accepted(self):
        for pct in [0, 0.0, 1, 1.0]:
            with self.subTest(pct=pct):
                m = make()
                m.addscore(0, "hold", pct)  # must not raise

    def test_out_of_range_hold_pct_does_not_change_state(self):
        m = make()
        m.addscore(0)
        for pct in [-1, 2]:
            with self.subTest(pct=pct):
                with self.assertRaises(ValueError):
                    m.addscore(0, "hold", pct)
                self.assertEqual((m.score, m.combo, m.max_combo), (100, 1, 1))

    def test_out_of_range_hold_pct_raises_even_on_a_miss(self):
        m = make()
        with self.assertRaises(ValueError):
            m.addscore(999, "hold", 5)

    def test_accuracy_never_exceeds_one_with_valid_input(self):
        m = make(notecount=3)
        m.addscore(0, "tap")
        m.addscore(0, "hold", 1.0)
        m.addscore(0, "hold", 1.0)
        self.assertLessEqual(m.accuracy, 1.0)

    def test_negative_notecount_does_not_divide_by_zero_or_flip_sign(self):
        m = make(notecount=-5)
        m.addscore(0)
        self.assertEqual(m.accuracy, 100)  # falls back to maxScore = 1


class TestInstanceIsolation(unittest.TestCase):
    def test_separate_managers_do_not_share_state(self):
        a, b = make(), make()
        a.addscore(0)
        self.assertEqual(b.score, 0)
        self.assertEqual(b.combo, 0)


if __name__ == "__main__":
    unittest.main()