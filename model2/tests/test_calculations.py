import math
import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtWidgets import QApplication  # noqa: E402

from const import PERIOD_OPTIONS  # noqa: E402
from main import MainWindow, _clamp_percent, calculate_model2  # noqa: E402


def select_data(combo, value):
    index = combo.findData(value)
    if index < 0:
        raise AssertionError(f"Значение {value!r} не найдено в списке")
    combo.setCurrentIndex(index)


class Model2CalculationTests(unittest.TestCase):
    def test_equation_values(self):
        # 3 года, ВРВП 30 мм, тактика 1.
        self.assertAlmostEqual(
            calculate_model2(0.582, 30, 1, 0, 1), 4.962379456007354
        )
        self.assertAlmostEqual(
            calculate_model2(0.582, 30, 2, 0, 1), 0.9047336886587062
        )
        self.assertAlmostEqual(
            calculate_model2(0.582, 30, 1, 3, 1), 34.983809009808354
        )
        self.assertAlmostEqual(
            calculate_model2(0.582, 30, 1, 4, 1), 67.0799609448537
        )
        self.assertAlmostEqual(
            calculate_model2(0.582, 30, 1, 5, 1), 128.62296267114638
        )
        self.assertAlmostEqual(
            calculate_model2(0.13, 30, 1, 0, 1), 1.1084352736786187
        )

    def test_equation_signs_match_description(self):
        # По описанию и таблице 26: количество ВРВЖ увеличивает риск,
        # тип Sarin — уменьшает.
        type_1 = calculate_model2(0.582, 30, 1, 0, 1)
        type_2 = calculate_model2(0.582, 30, 2, 0, 1)
        count_2 = calculate_model2(0.582, 30, 1, 2, 1)
        count_3 = calculate_model2(0.582, 30, 1, 3, 1)

        self.assertLess(type_2, type_1)
        self.assertGreater(count_3, count_2)

    def test_all_periods_are_finite(self):
        for _label, h0 in PERIOD_OPTIONS:
            value = calculate_model2(h0, 30, 1, 0, 1)
            self.assertTrue(math.isfinite(value))
            self.assertGreater(value, 0)

    def test_clamp(self):
        self.assertEqual(_clamp_percent(128.62296267114638), 100.0)
        self.assertEqual(_clamp_percent(4.962379456007354), 4.962379456007354)
        self.assertEqual(_clamp_percent(float("inf")), 100.0)


class Model2UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()
        self.output = self.window.outputs["model2"]

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def fill(self, h0=0.582, length="30", sarin_type=1, count="0", tactic=1):
        select_data(self.window.inputs["h0"], h0)
        self.window.inputs["varices_length"].setText(length)
        select_data(self.window.inputs["sarin_type"], sarin_type)
        self.window.inputs["gastric_varices_count"].setText(count)
        select_data(self.window.inputs["tactic"], tactic)
        self.app.processEvents()

    def test_empty_result(self):
        self.assertEqual(self.output.text(), "---")

    def test_result_and_baseline(self):
        self.fill()
        self.assertEqual(self.output.text(), "4.96%")
        self.assertNotIn("red", self.output.styleSheet())
        self.assertEqual(
            self.window.baseline_labels["h0"].text(), "h0(t) = 0.582"
        )

    def test_result_is_capped_at_100(self):
        self.fill(count="5")
        self.assertEqual(self.output.text(), "100.00%")
        self.assertIn("red", self.output.styleSheet())

    def test_count_raises_result(self):
        self.fill(count="3")
        self.assertEqual(self.output.text(), "34.98%")
        self.assertNotIn("red", self.output.styleSheet())

    def test_type_lowers_result(self):
        self.fill(sarin_type=2)
        self.assertEqual(self.output.text(), "0.90%")
        self.assertNotIn("red", self.output.styleSheet())

    def test_clear_resets_fields(self):
        self.fill()
        self.window.clear_button.click()
        self.app.processEvents()

        self.assertEqual(self.output.text(), "---")
        self.assertEqual(self.window.inputs["h0"].currentIndex(), 0)
        self.assertEqual(
            self.window.baseline_labels["h0"].text(), "h0(t) = —"
        )
        self.assertEqual(self.window.inputs["varices_length"].text(), "")


if __name__ == "__main__":
    unittest.main()
