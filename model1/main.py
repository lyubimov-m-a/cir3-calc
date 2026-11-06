#!/usr/bin/env python3

import logging
import math
import sys
from os import path as os_path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QIcon, QIntValidator, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from const import (
    BUTTONS,
    CALCULATION_CONFIG,
    ICON,
    INPUT_CONFIG,
    LICENSE,
    STYLE_SHEET,
    TITLE,
    TITLE_ABOUT,
)

BASE_DIR = os_path.dirname(os_path.abspath(__file__))


def _logistic_percent(z):
    """Возвращает 100 / (1 + exp(-z)) без переполнения."""
    if z >= 0:
        return 100.0 / (1.0 + math.exp(-z))
    exp_z = math.exp(z)
    return 100.0 * exp_z / (1.0 + exp_z)


def _clamp_percent(value):
    """Ограничивает отображаемое значение диапазоном 0–100%."""
    if not math.isfinite(value):
        return 100.0 if value > 0 else 0.0
    return max(0.0, min(100.0, value))


def calculate_model1(indication, bleed_count):
    z = -14.6 + 3.3 * indication + 0.53 * bleed_count
    return _logistic_percent(z)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(TITLE)
        self.resize(950, 650)

        self.inputs = {}
        self.input_types = {}
        self.baseline_labels = {}
        self.outputs = {}

        self.float_validator = QDoubleValidator(0.0, 1e9, 6)
        self.float_validator.setLocale(self.locale())
        self.float_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.int_validator = QIntValidator(0, 1_000_000)

        self.default_text_color = "color: white;"
        self.risk_text_color = "color: red; font-weight: bold;"

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        columns_layout = QHBoxLayout()

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_widget = QWidget()
        left_layout = QFormLayout(left_widget)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_scroll.setWidget(left_widget)

        unit_label_width = 90

        for item in INPUT_CONFIG:
            label = QLabel(item["label"])
            row_hbox = QHBoxLayout()
            unit_label = QLabel(item.get("unit", ""))
            unit_label.setMinimumWidth(unit_label_width)
            unit_label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )

            tooltip = item.get("tooltip")
            if tooltip:
                label.setToolTip(tooltip)
                unit_label.setToolTip(tooltip)

            if item["type"] in ("number", "integer"):
                widget = QLineEdit()
                if item["type"] == "integer":
                    widget.setValidator(self.int_validator)
                    widget.setPlaceholderText("0")
                else:
                    widget.setValidator(self.float_validator)
                    widget.setPlaceholderText("0.0")
                widget.textChanged.connect(self.update_calculations)
                if tooltip:
                    widget.setToolTip(tooltip)
                self.inputs[item["key"]] = widget
                self.input_types[item["key"]] = item["type"]
                row_hbox.addWidget(widget, 1)
                row_hbox.addWidget(unit_label)

            elif item["type"] in ("combo", "period"):
                widget = QComboBox()
                placeholder = (
                    "— выберите период —"
                    if item["type"] == "period"
                    else "— выберите —"
                )
                widget.addItem(placeholder, None)
                for text, value in item["options"]:
                    widget.addItem(text, value)
                widget.currentIndexChanged.connect(self.update_calculations)
                if tooltip:
                    widget.setToolTip(tooltip)
                self.inputs[item["key"]] = widget
                self.input_types[item["key"]] = item["type"]

                row_hbox.addWidget(widget, 1)

                if item["type"] == "period":
                    baseline_label = QLabel("h0(t) = —")
                    baseline_label.setMinimumWidth(110)
                    if tooltip:
                        baseline_label.setToolTip(tooltip)
                    self.baseline_labels[item["key"]] = baseline_label
                    row_hbox.addWidget(baseline_label)

                row_hbox.addWidget(unit_label)

            left_layout.addRow(label, row_hbox)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)

        right_column_widget = QWidget()
        right_column_widget.setMinimumWidth(260)
        right_column_vbox = QVBoxLayout(right_column_widget)

        right_results_widget = QWidget()
        right_layout = QVBoxLayout(right_results_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(6)

        for name, config in CALCULATION_CONFIG.items():
            self.outputs[name] = self.create_result_label()
            result_caption = QLabel(f"<b>{config['label']}:</b>")
            result_caption.setWordWrap(True)
            right_layout.addWidget(result_caption)
            right_layout.addWidget(self.outputs[name])
            right_layout.addSpacing(18)

        bottom_buttons_layout = QHBoxLayout()
        self.clear_button = QPushButton(BUTTONS["clear"])
        self.clear_button.clicked.connect(self.clear_all_fields)

        self.help_button = QPushButton(BUTTONS["about"])
        self.help_button.setFixedWidth(30)
        self.help_button.clicked.connect(self.show_info)

        bottom_buttons_layout.addStretch()
        bottom_buttons_layout.addWidget(self.clear_button)
        bottom_buttons_layout.addWidget(self.help_button)

        right_column_vbox.addWidget(right_results_widget)
        right_column_vbox.addStretch()
        right_column_vbox.addLayout(bottom_buttons_layout)

        columns_layout.addWidget(left_scroll, 2)
        columns_layout.addWidget(separator)
        columns_layout.addWidget(right_column_widget, 1)

        main_layout.addLayout(columns_layout)

    def create_result_label(self):
        label = QLabel("---")
        font = label.font()
        font.setPointSize(12)
        font.setBold(True)
        label.setFont(font)
        self.default_text_color = (
            f"color: {self.palette().color(QPalette.ColorRole.WindowText).name()};"
        )
        label.setStyleSheet(self.default_text_color)
        return label

    def get_all_input_values(self):
        values = {}
        for key, widget in self.inputs.items():
            if isinstance(widget, QLineEdit):
                text = widget.text().strip().replace(",", ".")
                if not text or text in ("-", ".", "-."):
                    values[key] = None
                    continue
                try:
                    if self.input_types.get(key) == "integer":
                        values[key] = int(text)
                    else:
                        values[key] = float(text)
                except ValueError:
                    values[key] = None
            elif isinstance(widget, QComboBox):
                values[key] = widget.currentData()

        return values

    def update_baseline_labels(self):
        for key, label in self.baseline_labels.items():
            value = self.inputs[key].currentData()
            if value is None:
                label.setText("h0(t) = —")
            else:
                label.setText(f"h0(t) = {value:g}")

    def update_calculations(self):
        self.update_baseline_labels()
        values = self.get_all_input_values()

        for name, config in CALCULATION_CONFIG.items():
            self.update_formula(
                name,
                values,
                globals()[f"calculate_{name}"],
                config["cutoff"],
                config["keys"],
            )

    def update_formula(self, name, values, calc_func, cutoff, keys):
        kwargs = {}
        all_present = True

        for key in keys:
            value = values.get(key)
            if value is None:
                all_present = False
                break
            kwargs[key] = value

        output = self.outputs.get(name)
        if not output:
            return

        if all_present:
            try:
                p = calc_func(**kwargs)
                self.set_result(output, p, cutoff)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logging.error("Ошибка расчета %s: %s", name, e, exc_info=True)
                output.setText("Ошибка")
                output.setStyleSheet(self.risk_text_color)
        else:
            output.setText("---")
            output.setStyleSheet(self.default_text_color)

    def set_result(self, output, value, cutoff):
        displayed_value = _clamp_percent(value)
        output.setText(f"{displayed_value:.2f}%")
        if displayed_value >= cutoff:
            output.setStyleSheet(self.risk_text_color)
        else:
            output.setStyleSheet(self.default_text_color)

    def clear_all_fields(self):
        for widget in self.inputs.values():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
        self.update_calculations()

    def show_info(self):
        try:
            license_path = os_path.join(BASE_DIR, LICENSE)
            with open(license_path, "r", encoding="utf-8") as license_file:
                license_text = license_file.read()
        except FileNotFoundError:
            license_text = f"Файл лицензии {LICENSE} не найден."
            logging.warning(license_text)

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(TITLE_ABOUT)
        msg_box.setText(license_text)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        style_path = os_path.join(BASE_DIR, STYLE_SHEET)
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        logging.warning(
            "Файл стилей %s не найден. Используются стили по умолчанию.", STYLE_SHEET
        )

    window = MainWindow()

    try:
        icon_path = os_path.join(BASE_DIR, ICON)
        window.setWindowIcon(QIcon(icon_path))
    except FileNotFoundError:
        logging.warning("Файл иконки %s не найден.", ICON)

    window.show()
    sys.exit(app.exec())
