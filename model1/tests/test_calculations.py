import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtWidgets import QApplication  # noqa: E402

from main import MainWindow, _clamp_percent, calculate_model1  # noqa: E402


def select_data(combo, value):
    index = combo.findData(value)
    if index < 0:
        raise AssertionError(f"Значение {value!r} не найдено в списке")
    combo.setCurrentIndex(index)


class Model1CalculationTests(unittest.TestCase):
    def test_equation_values(self):
        self.assertAlmostEqual(calculate_model1(0, 0), 4.563524285327653e-05)
        self.assertAlmostEqual(calculate_model1(3, 1), 1.5217121208656283)
        self.assertAlmostEqual(calculate_model1(3, 2), 2.5580788312007665)
        self.assertAlmostEqual(calculate_model1(4, 0), 19.78161114414182)

    def test_cutoff_crossing(self):
        self.assertLess(calculate_model1(3, 1), 2.04)
        self.assertGreaterEqual(calculate_model1(3, 2), 2.04)

    def test_clamp(self):
        self.assertEqual(_clamp_percent(-5), 0.0)
        self.assertEqual(_clamp_percent(42.5), 42.5)
        self.assertEqual(_clamp_percent(150), 100.0)
        self.assertEqual(_clamp_percent(float("inf")), 100.0)
        self.assertEqual(_clamp_percent(float("nan")), 0.0)


class Model1UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()
        self.output = self.window.outputs["model1"]

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_empty_result(self):
        self.assertEqual(self.output.text(), "---")

    def test_high_risk_is_red(self):
        select_data(self.window.inputs["indication"], 3)
        self.window.inputs["bleed_count"].setText("2")
        self.app.processEvents()
        self.assertEqual(self.output.text(), "2.56%")
        self.assertIn("red", self.output.styleSheet())

    def test_low_risk_is_normal(self):
        select_data(self.window.inputs["indication"], 3)
        self.window.inputs["bleed_count"].setText("1")
        self.app.processEvents()
        self.assertEqual(self.output.text(), "1.52%")
        self.assertNotIn("red", self.output.styleSheet())

    def test_clear_resets_fields(self):
        select_data(self.window.inputs["indication"], 4)
        self.window.inputs["bleed_count"].setText("0")
        self.app.processEvents()
        self.assertEqual(self.output.text(), "19.78%")

        self.window.clear_button.click()
        self.app.processEvents()

        self.assertEqual(self.output.text(), "---")
        self.assertEqual(self.window.inputs["indication"].currentIndex(), 0)
        self.assertEqual(self.window.inputs["bleed_count"].text(), "")


if __name__ == "__main__":
    unittest.main()
