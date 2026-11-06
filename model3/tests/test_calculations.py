import math
import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtWidgets import QApplication  # noqa: E402

from const import PERIOD_OPTIONS  # noqa: E402
from main import MainWindow, _clamp_percent, calculate_model3  # noqa: E402


def select_data(combo, value):
    index = combo.findData(value)
    if index < 0:
        raise AssertionError(f"Значение {value!r} не найдено в списке")
    combo.setCurrentIndex(index)


class Model3CalculationTests(unittest.TestCase):
    def test_equation_values(self):
        # 4 года, билирубин 30 мкмоль/л, АЛТ 40 Ед/л.
        self.assertAlmostEqual(
            calculate_model3(0.91, 30, 40, 1), 74.20707577804365
        )
        self.assertAlmostEqual(
            calculate_model3(0.91, 30, 40, 2), 40.15951933319292
        )
        self.assertAlmostEqual(
            calculate_model3(0.91, 31, 40, 1), 74.72834763145187
        )
        self.assertAlmostEqual(
            calculate_model3(3.723, 50, 100, 1), 471.3966956751294
        )

    def test_all_periods_are_finite(self):
        for _label, h0 in PERIOD_OPTIONS:
            value = calculate_model3(h0, 30, 40, 1)
            self.assertTrue(math.isfinite(value))
            self.assertGreater(value, 0)

    def test_tactic_lowers_risk(self):
        self.assertLess(
            calculate_model3(0.91, 30, 40, 2),
            calculate_model3(0.91, 30, 40, 1),
        )

    def test_clamp(self):
        self.assertEqual(_clamp_percent(471.3966956751294), 100.0)
        self.assertEqual(_clamp_percent(74.20707577804365), 74.20707577804365)
        self.assertEqual(_clamp_percent(float("inf")), 100.0)


class Model3UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()
        self.output = self.window.outputs["model3"]

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def fill(self, h0=0.91, bilirubin="30", alt="40", tactic=1):
        select_data(self.window.inputs["h0"], h0)
        self.window.inputs["bilirubin"].setText(bilirubin)
        self.window.inputs["alt"].setText(alt)
        select_data(self.window.inputs["tactic"], tactic)
        self.app.processEvents()

    def test_empty_result(self):
        self.assertEqual(self.output.text(), "---")

    def test_result_and_baseline(self):
        self.fill()
        self.assertEqual(self.output.text(), "74.21%")
        self.assertNotIn("red", self.output.styleSheet())
        self.assertEqual(
            self.window.baseline_labels["h0"].text(), "h0(t) = 0.91"
        )

    def test_tactic_changes_result(self):
        self.fill(tactic=2)
        self.assertEqual(self.output.text(), "40.16%")

    def test_cutoff_crossing(self):
        self.fill(bilirubin="31")
        self.assertEqual(self.output.text(), "74.73%")
        self.assertIn("red", self.output.styleSheet())

    def test_result_is_capped_at_100(self):
        self.fill(h0=3.723, bilirubin="50", alt="100", tactic=1)
        self.assertEqual(self.output.text(), "100.00%")
        self.assertIn("red", self.output.styleSheet())

    def test_clear_resets_fields(self):
        self.fill()
        self.window.clear_button.click()
        self.app.processEvents()

        self.assertEqual(self.output.text(), "---")
        self.assertEqual(self.window.inputs["h0"].currentIndex(), 0)
        self.assertEqual(
            self.window.baseline_labels["h0"].text(), "h0(t) = —"
        )
        self.assertEqual(self.window.inputs["bilirubin"].text(), "")


if __name__ == "__main__":
    unittest.main()
