import sys
import time
import threading
import keyboard
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QSpinBox,
    QComboBox,
    QPushButton,
    QGroupBox,
    QCheckBox,
    QLineEdit,
    QFrame,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from pynput.mouse import Controller, Button


class AutoClicker(QMainWindow):
    status_updated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Billy Willy Clicky")
        self.setFixedSize(450, 500)
        self.setWindowIcon(QIcon())

        self.mouse = Controller()
        self.clicking = False
        self.click_thread = None
        self.low_latency_mode = True

        self.actual_cps = 0
        self.last_click_time = 0

        self.hotkey = "f6"
        self.hotkey_active = True

        self.init_ui()
        self.status_updated.connect(self.update_status_label)

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        header = QLabel("Billy Willy Clicky")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(divider)

        perf_group = QGroupBox("PERFORMANCE SETTINGS")
        perf_layout = QVBoxLayout()

        interval_layout = QHBoxLayout()
        interval_label = QLabel("Click Interval (ms):")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1000)
        self.interval_spin.setValue(10)
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spin)
        perf_layout.addLayout(interval_layout)

        self.low_latency_check = QCheckBox("Enable Ultra Low Latency Mode")
        self.low_latency_check.setChecked(True)
        perf_layout.addWidget(self.low_latency_check)

        self.cps_label = QLabel("Current Speed: 0 CPS")
        self.cps_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.cps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        perf_layout.addWidget(self.cps_label)

        perf_group.setLayout(perf_layout)
        main_layout.addWidget(perf_group)

        settings_group = QGroupBox("CLICK SETTINGS")
        settings_layout = QVBoxLayout()

        type_layout = QHBoxLayout()
        type_label = QLabel("Click Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Single Click", "Double Click", "Triple Click"])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        settings_layout.addLayout(type_layout)

        button_layout = QHBoxLayout()
        button_label = QLabel("Mouse Button:")
        self.button_combo = QComboBox()
        self.button_combo.addItems(["Left Button", "Right Button", "Middle Button"])
        button_layout.addWidget(button_label)
        button_layout.addWidget(self.button_combo)
        settings_layout.addLayout(button_layout)

        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        hotkey_group = QGroupBox("HOTKEY SETTINGS")
        hotkey_layout = QVBoxLayout()

        self.hotkey_check = QCheckBox(f"Enable Hotkey ({self.hotkey.upper()})")
        self.hotkey_check.setChecked(True)
        hotkey_layout.addWidget(self.hotkey_check)

        hotkey_custom_layout = QHBoxLayout()
        hotkey_label = QLabel("Custom Hotkey:")
        self.hotkey_input = QLineEdit(self.hotkey)
        self.hotkey_input.setMaximumWidth(100)
        hotkey_custom_layout.addWidget(hotkey_label)
        hotkey_custom_layout.addWidget(self.hotkey_input)
        hotkey_layout.addLayout(hotkey_custom_layout)

        hotkey_group.setLayout(hotkey_layout)
        main_layout.addWidget(hotkey_group)

        self.toggle_btn = QPushButton("START CLICKING (F6)")
        self.toggle_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.toggle_btn.clicked.connect(self.toggle_clicking)
        main_layout.addWidget(self.toggle_btn)

        self.status_label = QLabel("Status: Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.hotkey_check.stateChanged.connect(self.toggle_hotkey)
        self.hotkey_input.textChanged.connect(self.update_hotkey)
        self.low_latency_check.stateChanged.connect(self.toggle_low_latency)

        self.start_hotkey_listener()

        self.cps_timer = QTimer()
        self.cps_timer.timeout.connect(self.update_cps_display)
        self.cps_timer.start(100)

    def toggle_low_latency(self):
        self.low_latency_mode = self.low_latency_check.isChecked()

    def toggle_hotkey(self, state):
        self.hotkey_active = state == Qt.CheckState.Checked

    def update_hotkey(self, text):
        self.hotkey = text.lower()

    def show_notification(self, title, message):
        QMessageBox.information(self, title, message)

    def start_hotkey_listener(self):
        def listen():
            while True:
                if self.hotkey_active and keyboard.is_pressed(self.hotkey):
                    self.toggle_clicking()
                    time.sleep(0.5)

        threading.Thread(target=listen, daemon=True).start()

    def toggle_clicking(self):
        if not self.clicking:
            self.clicking = True
            self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
            self.click_thread.start()
            self.status_updated.emit("Status: Clicking...")
            self.toggle_btn.setText("STOP CLICKING")
            self.toggle_btn.setStyleSheet("background-color: #c0392b; color: white;")
            self.show_notification("Billy Willy Clicky", "Started Clicking!")
        else:
            self.clicking = False
            self.status_updated.emit("Status: Stopped")
            self.toggle_btn.setText("START CLICKING")
            self.toggle_btn.setStyleSheet("background-color: #27ae60; color: white;")
            self.show_notification("Billy Willy Clicky", "Stopped Clicking.")

    def click_loop(self):
        try:
            delay = self.interval_spin.value() / 1000
            button_map = {
                "Left Button": Button.left,
                "Right Button": Button.right,
                "Middle Button": Button.middle,
            }
            button = button_map[self.button_combo.currentText()]
            clicks = {"Single Click": 1, "Double Click": 2, "Triple Click": 3}[
                self.type_combo.currentText()
            ]

            while self.clicking:
                now = time.time()
                self.actual_cps = (
                    1 / (now - self.last_click_time) if self.last_click_time else 0
                )
                self.last_click_time = now

                for _ in range(clicks):
                    self.mouse.click(button)
                    if not self.low_latency_mode:
                        time.sleep(0.01)

                time.sleep(delay)
        except Exception as e:
            self.status_updated.emit("Status: Error")
            self.show_notification("Billy Willy Clicky", f"An error occurred: {e}")
            self.clicking = False

    def update_cps_display(self):
        if self.clicking:
            self.cps_label.setText(f"Current Speed: {self.actual_cps:.1f} CPS")
        else:
            self.cps_label.setText("Current Speed: 0 CPS")

    def update_status_label(self, status):
        self.status_label.setText(status)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    dark_style = """
        QWidget { background-color: #1e1e1e; color: #dcdcdc; }
        QGroupBox {
            border: 1px solid #444;
            border-radius: 5px;
            margin-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
            color: #f39c12;
        }
        QLabel { color: #f5f5f5; }
        QCheckBox { color: #f5f5f5; }
        QComboBox, QLineEdit, QSpinBox {
            background-color: #2c2c2c;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 3px;
        }
        QPushButton {
            background-color: #27ae60;
            color: white;
            padding: 8px;
            border: none;
            border-radius: 4px;
        }
        QPushButton:hover { background-color: #2ecc71; }
        QPushButton:pressed { background-color: #1e8449; }
    """
    app.setStyleSheet(dark_style)

    window = AutoClicker()
    window.show()
    sys.exit(app.exec())
