from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QDoubleSpinBox, QPushButton, QLabel, QGroupBox
)
from app.utils.config import Config

class SettingsDialog(QDialog):
    """
    Configuration dialog for setting Broker credentials and AI decision thresholds.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Settings & Broker Configuration")
        self.setMinimumWidth(450)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QLabel {
                color: #cdd6f4;
            }
            QLineEdit, QComboBox, QDoubleSpinBox {
                background-color: #181825;
                color: #cdd6f4;
                border: 1px solid #313244;
                border-radius: 4px;
                padding: 4px;
            }
            QGroupBox {
                border: 1px solid #313244;
                border-radius: 6px;
                margin-top: 10px;
                font-weight: bold;
                color: #f9e2af;
            }
        """)

        layout = QVBoxLayout(self)

        # Group 1: Broker Selection & Credentials
        grp_broker = QGroupBox("Broker Feed Configuration")
        flayout_broker = QFormLayout(grp_broker)

        self.cmb_broker = QComboBox()
        self.cmb_broker.addItems(["MOCK", "FYERS", "ANGEL"])
        self.cmb_broker.setCurrentText(Config.BROKER)

        self.txt_fyers_id = QLineEdit(Config.FYERS_CLIENT_ID)
        self.txt_fyers_token = QLineEdit(Config.FYERS_ACCESS_TOKEN)

        self.txt_angel_key = QLineEdit(Config.ANGEL_API_KEY)
        self.txt_angel_code = QLineEdit(Config.ANGEL_CLIENT_CODE)

        flayout_broker.addRow("Selected Broker:", self.cmb_broker)
        flayout_broker.addRow("Fyers Client ID:", self.txt_fyers_id)
        flayout_broker.addRow("Fyers Access Token:", self.txt_fyers_token)
        flayout_broker.addRow("Angel API Key:", self.txt_angel_key)
        flayout_broker.addRow("Angel Client Code:", self.txt_angel_code)

        layout.addWidget(grp_broker)

        # Group 2: AI Model Parameters
        grp_ai = QGroupBox("AI Signal Parameters")
        flayout_ai = QFormLayout(grp_ai)

        self.spn_threshold = QDoubleSpinBox()
        self.spn_threshold.setRange(0.50, 0.95)
        self.spn_threshold.setSingleStep(0.05)
        self.spn_threshold.setValue(Config.AI_DECISION_THRESHOLD)

        flayout_ai.addRow("AI Decision Threshold:", self.spn_threshold)

        layout.addWidget(grp_ai)

        # Buttons
        btn_box = QHBoxLayout()
        self.btn_save = QPushButton("Save & Apply")
        self.btn_save.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 6px 14px;")
        self.btn_save.clicked.connect(self.save_settings)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("background-color: #45475a; color: #cdd6f4; padding: 6px 14px;")
        self.btn_cancel.clicked.connect(self.reject)

        btn_box.addStretch()
        btn_box.addWidget(self.btn_save)
        btn_box.addWidget(self.btn_cancel)

        layout.addLayout(btn_box)

    def save_settings(self):
        Config.BROKER = self.cmb_broker.currentText()
        Config.FYERS_CLIENT_ID = self.txt_fyers_id.text()
        Config.FYERS_ACCESS_TOKEN = self.txt_fyers_token.text()
        Config.ANGEL_API_KEY = self.txt_angel_key.text()
        Config.ANGEL_CLIENT_CODE = self.txt_angel_code.text()
        Config.AI_DECISION_THRESHOLD = self.spn_threshold.value()
        self.accept()
