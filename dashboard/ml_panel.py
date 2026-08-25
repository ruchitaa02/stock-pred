from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QLabel, QSplitter, QAbstractItemView
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt
from app.ml.train import model_trainer
from dashboard.trade_panel import MetricCard

class MLModelPanel(QWidget):
    """
    AI / Machine Learning Analysis Dashboard:
    - Model Performance Metrics (Accuracy, Precision, Recall, F1, ROC-AUC)
    - Strategy Comparison (All Raw Signals vs AI-Filtered Signals)
    - Feature Importance Ranking Table
    - Model Retraining & Synthetic Dataset Generation Controls
    """
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Top Control Bar
        control_bar = QHBoxLayout()
        self.lbl_model_title = QLabel("MODEL: Random Forest Classifier (Time-Series Chronological Split)")
        self.lbl_model_title.setFont(QFont("Arial", 12, QFont.Bold))
        self.lbl_model_title.setStyleSheet("color: #cba6f7;")

        self.btn_retrain = QPushButton("Retrain Model")
        self.btn_retrain.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        self.btn_retrain.clicked.connect(self.run_retrain)

        control_bar.addWidget(self.lbl_model_title)
        control_bar.addStretch()
        control_bar.addWidget(self.btn_retrain)
        self.layout.addLayout(control_bar)

        # Metric Cards Row
        metrics_bar = QHBoxLayout()
        self.card_acc = MetricCard("ACCURACY", "--", "#a6e3a1")
        self.card_prec = MetricCard("PRECISION", "--", "#89b4fa")
        self.card_rec = MetricCard("RECALL", "--", "#f9e2af")
        self.card_f1 = MetricCard("F1 SCORE", "--", "#cba6f7")
        self.card_auc = MetricCard("ROC-AUC", "--", "#94e2d5")

        metrics_bar.addWidget(self.card_acc)
        metrics_bar.addWidget(self.card_prec)
        metrics_bar.addWidget(self.card_rec)
        metrics_bar.addWidget(self.card_f1)
        metrics_bar.addWidget(self.card_auc)
        self.layout.addLayout(metrics_bar)

        # Main Splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left Frame: Strategy Comparison
        left_frame = QFrame()
        left_frame.setStyleSheet("background-color: #181825; border-radius: 8px; padding: 10px;")
        left_layout = QVBoxLayout(left_frame)

        lbl_comp_title = QLabel("Strategy Comparison: Raw Signals vs AI-Filtered")
        lbl_comp_title.setFont(QFont("Arial", 11, QFont.Bold))
        lbl_comp_title.setStyleSheet("color: #f9e2af;")

        self.table_comp = QTableWidget(2, 3)
        self.table_comp.setHorizontalHeaderLabels(["Strategy", "Total Signals", "Win Rate (%)"])
        self.table_comp.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_comp.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                gridline-color: #313244;
            }
            QHeaderView::section {
                background-color: #11111b;
                color: #a6adc8;
            }
        """)

        left_layout.addWidget(lbl_comp_title)
        left_layout.addWidget(self.table_comp)

        # Right Frame: Feature Importance Table
        right_frame = QFrame()
        right_frame.setStyleSheet("background-color: #181825; border-radius: 8px; padding: 10px;")
        right_layout = QVBoxLayout(right_frame)

        lbl_feat_title = QLabel("Feature Importance Ranking")
        lbl_feat_title.setFont(QFont("Arial", 11, QFont.Bold))
        lbl_feat_title.setStyleSheet("color: #94e2d5;")

        self.table_feat = QTableWidget()
        self.table_feat.setColumnCount(2)
        self.table_feat.setHorizontalHeaderLabels(["Quantitative Feature", "Importance Score"])
        self.table_feat.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_feat.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                gridline-color: #313244;
            }
            QHeaderView::section {
                background-color: #11111b;
                color: #a6adc8;
            }
        """)

        right_layout.addWidget(lbl_feat_title)
        right_layout.addWidget(self.table_feat)

        splitter.addWidget(left_frame)
        splitter.addWidget(right_frame)
        self.layout.addWidget(splitter)

        self.run_retrain()

    def run_retrain(self):
        metrics = model_trainer.train_models()

        self.card_acc.set_value(f"{metrics['accuracy']*100:.1f}%")
        self.card_prec.set_value(f"{metrics['precision']*100:.1f}%")
        self.card_rec.set_value(f"{metrics['recall']*100:.1f}%")
        self.card_f1.set_value(f"{metrics['f1']*100:.1f}%")
        self.card_auc.set_value(f"{metrics['roc_auc']:.3f}")

        # Fill Strategy Comparison
        raw = metrics['raw_signals']
        ai = metrics['ai_filtered_signals']

        self.table_comp.setItem(0, 0, QTableWidgetItem("Strategy A: All SMMA Signals"))
        self.table_comp.setItem(0, 1, QTableWidgetItem(str(raw['total_trades'])))
        self.table_comp.setItem(0, 2, QTableWidgetItem(f"{raw['win_rate']:.1f}%"))

        self.table_comp.setItem(1, 0, QTableWidgetItem("Strategy B: AI-Filtered Signals"))
        self.table_comp.setItem(1, 1, QTableWidgetItem(str(ai['total_trades'])))
        
        ai_item = QTableWidgetItem(f"{ai['win_rate']:.1f}%")
        ai_item.setForeground(QColor("#a6e3a1"))
        ai_item.setFont(QFont("Arial", 10, QFont.Bold))
        self.table_comp.setItem(1, 2, ai_item)

        # Fill Feature Importances
        importances = metrics['feature_importances']
        self.table_feat.setRowCount(len(importances))
        for r_idx, (f_name, score) in enumerate(importances.items()):
            item_name = QTableWidgetItem(f_name.upper())
            item_score = QTableWidgetItem(f"{score:.4f}")
            item_score.setTextAlignment(Qt.AlignCenter)
            
            self.table_feat.setItem(r_idx, 0, item_name)
            self.table_feat.setItem(r_idx, 1, item_score)
