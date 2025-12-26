import sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLineEdit,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QButtonGroup,
)
from PySide6.QtGui import QColor, QPainter, QPen, QIcon, QMovie, QPixmap
from PySide6.QtCore import Qt, QPropertyAnimation, Signal, QSize , QDateTime
from PySide6.QtCharts import QChart, QChartView, QLineSeries ,QValueAxis ,QDateTimeAxis


# ---------- Mock Data ----------

key = bytes.fromhex("6acbe2c3a12c9fbf8a76cd1185dc874f8def2b8f0a81bf146ae39405a357ef79")
iv = bytes.fromhex("a96808845430d3e213c059a6c9979f39")


def decrypt_data(enc_data: str):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decoded = base64.b64decode(enc_data)
    decrypted = unpad(cipher.decrypt(decoded), AES.block_size)
    return decrypted.decode()


DATA = {
    "Gold": [1.1, 1.4, 2.5, 2.1, 3.0, 2.8, 3.5, 5.5, 6.7, 7.2],
    "Coin": [0.8, 1.2, 1.9, 2.8, 2.4, 2.8, 3.5, 5.6, 6.8, 7.2],
    "USD": [1.5, 1.6, 1.7, 1.8, 1.9, 2.8, 3.5, 5.2, 6.1, 7.2],
    "USDT": [1.2, 1.3, 1.6, 2.0, 2.6, 2.8, 3.5, 4.3, 6.6, 7.2],
}

COLORS = {
    "Gold": "#F97316",
    "Coin": "#3B82F6",
    "USD": "#6366F1",
    "USDT": "#22C55E",
}

buttons = [
    ("Gold", COLORS["Gold"], "D:/Programing/GCPMS/pics/gold.png", False),
    ("Coin", COLORS["Coin"], "D:/Programing/GCPMS/pics/coin.png", False),
    ("USD", COLORS["USD"], "D:/Programing/GCPMS/pics/dollar.png", False),
    ("USDT", COLORS["USDT"], "D:/Programing/GCPMS/pics/tether.png", True),  # GIF
]


#! ---------- Card ----------
class Card(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            """
            QFrame {
                background-color: #FFFFFF;
                border-radius: 14px;
                border: 1px solid #E5E7EB;
            }
        """
        )

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 25))
        self.setGraphicsEffect(shadow)


#! ---------- Animated Chart ----------
class AnimatedChart(QChartView):
    chartChanged = Signal(str)

    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.setFocusPolicy(Qt.NoFocus)
        self.setInteractive(False)

        self.setStyleSheet(
            """
            QChartView {
                
                background: transparent;
                border: none;
            }
        """
        )

        self.chart = QChart()
        self.chart.legend().hide()

        self.setChart(self.chart)

        # ? fade effect
        self.opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)
        self.anim = QPropertyAnimation(self.opacity, b"opacity")
        self.anim.setDuration(300)
        self.anim.finished.connect(self._on_fade_finished)
        self.next_key = None

        self._set_data("Gold")

    def update_chart(self, key):
        self.chartChanged.emit(key)
        self.next_key = key
        self.anim.stop()
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.start()

    def _on_fade_finished(self):
        if self.opacity.opacity() == 0.0 and self.next_key:
            self._set_data(self.next_key)
            self.next_key = None
            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)
            self.anim.start()

    def _set_data(self, key):
        self.chart.removeAllSeries()
        series = QLineSeries()
        series.setPen(QPen(QColor("#9CA3AF"), 3))

        for i, v in enumerate(DATA[key]):
            series.append(i, v)

        self.chart.addSeries(series)
        self.chart.createDefaultAxes()

        for axis in self.chart.axes():
            axis.setGridLineColor(QColor("#EDEDF1"))
            axis.setLabelsColor(QColor("#55585E"))


#! ---------- Coin Button ----------
class CoinButton(QWidget):
    def __init__(self, name, color, img_path=None, icon_size=30):
        super().__init__()
        self.name = name
        self.color = color

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.icon_label = QLabel()
        self.icon_label.setStyleSheet("background: transparent;border: none;")
        if img_path:
            pixmap = QPixmap(img_path).scaled(
                icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.icon_label.setPixmap(pixmap)
        self.icon_label.setFixedSize(icon_size, icon_size)
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)

        self.button = QPushButton(name)
        self.button.setCheckable(True)
        self.button.setFixedHeight(42)
        self.button.setStyleSheet(
            f"""
            QPushButton {{
                color: #374151;
                border-radius: 10px;
                padding-left: 10px;
                text-align: left;
                font-weight: 500;
                background-color: #F9FAFB;
            }}
            QPushButton:hover {{
                background-color: #F3F4F6;
            }}
            QPushButton:checked {{
                background-color: {color};
                color: white;
            }}
        """
        )
        layout.addWidget(self.button)


#! ---------- Main Window ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gold & Currency Price Monitoring System")
        self.resize(1350, 800)

        central = QWidget()
        central.setStyleSheet("background-color: #F6F7F9;")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(20)

        root.addWidget(self.sidebar(), 1)
        root.addLayout(self.main_content(), 9)

    #! ---------- Sidebar ----------
    def sidebar(self):
        frame = Card()
        frame.setFixedWidth(80)
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(20)

        # دکمه‌ها
        buttons = []
        icons = ["🏠", "⚙"]
        names = ["Home", "Settings"]

        group = QButtonGroup(self)
        group.setExclusive(True)

        for icon, name in zip(icons, names):
            btn = QPushButton(icon)
            btn.setCheckable(True)
            btn.setFixedSize(48, 48)
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #EEF2FF; 
                    border-radius: 12px;
                    font-size: 18px;
                }
                QPushButton:hover {
                    background-color: #E0E7FF;
                }
                QPushButton:checked {
                    background-color: #3B82F6; 
                    color: white;
                }
            """
            )
            layout.addWidget(btn, alignment=Qt.AlignHCenter)
            # layout.addWidget(btn)
            group.addButton(btn)
            buttons.append(btn)

        buttons[0].setChecked(True)

        layout.addStretch()
        return frame

    #! ---------- Main Content ----------
    def main_content(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        layout.addWidget(self.header())

        body = QHBoxLayout()
        body.setSpacing(20)

        body.addWidget(self.chart_card(), 3)
        body.addWidget(self.right_panel(), 1)

        layout.addLayout(body)
        return layout

    #! ---------- Header ----------
    def header(self):
        frame = Card()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 14, 20, 14)

        title = QLabel("Gold & Currency Price Monitoring System")
        title.setStyleSheet(
            "font-size: 18px; font-weight: 600;color: #111827;border: none;background: transparent;"
        )

        layout.addWidget(title)

        return frame

    #! ---------- Chart Card ----------
    def chart_card(self):
        frame = Card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        self.chart_title = QLabel("Gold Chart")
        self.chart_title.setStyleSheet(
            "font-weight: 600;background: transparent;border: none;font-size: 16px;color: #111827;padding-left: 40px;"
        )
        self.chart_view = AnimatedChart()
        self.chart_view.setMinimumHeight(420)
        self.chart_view.chartChanged.connect(self.update_chart_title)

        layout.addWidget(self.chart_title)
        layout.addWidget(self.chart_view)

        return frame

    #! ---------- Right Panel ----------
    def right_panel(self):
        wrapper = QVBoxLayout()
        wrapper.setSpacing(20)

        coin_card = Card()
        coin_layout = QVBoxLayout(coin_card)
        coin_layout.setContentsMargins(20, 16, 20, 20)
        coin_layout.setSpacing(12)

        group = QButtonGroup(self)
        group.setExclusive(True)

        buttons = [
            ("Gold", COLORS["Gold"], "D:/Programing/GCPMS/pics/gold.png"),
            ("Coin", COLORS["Coin"], "D:/Programing/GCPMS/pics/coin.png"),
            ("USD", COLORS["USD"], "D:/Programing/GCPMS/pics/dollar.png"),
            ("USDT", COLORS["USDT"], "D:/Programing/GCPMS/pics/tether.png"),
        ]

        for name, color, path in buttons:
            btn_widget = CoinButton(name, color, path)
            group.addButton(btn_widget.button)
            btn_widget.button.clicked.connect(
                lambda _, n=name: self.chart_view.update_chart(n)
            )
            coin_layout.addWidget(btn_widget)

        group.buttons()[0].setChecked(True)

        update_card = Card()
        update_card.setFixedHeight(180)
        up_layout = QVBoxLayout(update_card)
        up_layout.setContentsMargins(20, 16, 20, 20)
        up_layout.setSpacing(12)

        label = QLabel("<b>Update Price</b>")
        label.setStyleSheet(
            "color: #111827;background: transparent;border: none;font-size: 14px;"
        )
        label.setAlignment(Qt.AlignCenter)
        up_layout.addWidget(label)

        key = QLineEdit()
        key.setPlaceholderText("Enter API Key")
        key.setStyleSheet(
            """
            color: #374151;
            padding: 10px;
            border-radius: 10px;
            border: 1px solid #E5E7EB;
        """
        )
        up_layout.addWidget(key)

        btn = QPushButton("Download")
        btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2563EB;
                color: white;
                padding: 12px;
                border-radius: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """
        )
        up_layout.addWidget(btn)

        wrapper.addWidget(coin_card)
        wrapper.addWidget(update_card)
        wrapper.addStretch()

        panel = QWidget()
        panel.setLayout(wrapper)
        return panel

    def update_chart_title(self, name):
        self.chart_title.setText(f"{name} Chart")


# ---------- Run ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
