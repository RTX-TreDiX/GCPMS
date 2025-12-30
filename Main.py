import sys
import backend

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
    QStackedWidget,
    QMessageBox,
    QToolTip
)
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QIcon ,QCursor
from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    Signal,
    QEasingCurve,
    QDateTime,
    QTimer, 
)
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QDateTimeAxis ,QCategoryAxis , QScatterSeries

#! ---------- Data ----------
key = "7acbe2c3a12c9fbf8a76cd1185dc874f8def2b8f0a81bf146ae39405a357ef79"
iv = bytes.fromhex("b96808845430d3e213c059a6c9979f39")



DATA = {
    "Time": [],
    "Gold": [],
    "Coin": [],
    "USD": [],
    "USDT": [],
}

COLORS = {
    "Gold": "#F97316",
    "Coin": "#3B82F6",
    "USD": "#6366F1",
    "USDT": "#22C55E",
}


buttons = [
    ("Gold", COLORS["Gold"], backend.find_resource_path("pics/gold.png")),
    ("Coin", COLORS["Coin"], backend.find_resource_path("pics/coin.png")),
    ("USD", COLORS["USD"], backend.find_resource_path("pics/dollar.png")),
    ("USDT", COLORS["USDT"], backend.find_resource_path("pics/tether.png")),
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

        self.setMouseTracking(True)

        self.setStyleSheet("""
            QChartView {
                background: transparent;
                border: none;
            }
            QToolTip {
                background-color: white;
                border: 1px solid #E5E7EB;
                padding: 6px;
                border-radius: 6px;
                color: #111827;
                font-weight: 600;
            }
        """)

        self.chart = QChart()
        self.chart.legend().hide()
        self.chart.setBackgroundVisible(False)
        self.setChart(self.chart)

        self._set_data("Gold")

    # -----------------------------
    def update_chart(self, key):
        self._set_data(key)
        self.chartChanged.emit(key)

    # -----------------------------
    def _set_data(self, key):
        self.chart.removeAllSeries()

        line = QLineSeries()
        line.setPen(
            QPen(QColor(COLORS.get(key, "#9CA3AF")), 3, Qt.SolidLine, Qt.RoundCap)
        )

        points = QScatterSeries()
        points.setMarkerSize(10)
        points.setColor(QColor(0, 0, 0, 0))      # کاملاً نامرئی
        points.setBorderColor(QColor(0, 0, 0, 0))

        data = DATA[key]
        times = DATA["Time"]

        self.tooltip_data = []

        for t, v in zip(times, data):
            dt = QDateTime.fromString(t, "yyyy-MM-dd HH:mm:ss")
            x = dt.toMSecsSinceEpoch()

            line.append(x, v)
            points.append(x, v)

            self.tooltip_data.append(
                f"{dt.toString('MM-dd HH:mm')}\nValue: {v}"
            )

        points.hovered.connect(self._show_tooltip)

        self.chart.addSeries(line)
        self.chart.addSeries(points)

        # -------- Axis X --------
        axis_x = QDateTimeAxis()
        axis_x.setFormat("MM-dd HH:mm")
        axis_x.setLabelsColor(QColor("#55585E"))
        axis_x.setGridLineColor(QColor("#EDEDF1"))

        # -------- Axis Y --------
        axis_y = QCategoryAxis()
        axis_y.setLabelsColor(QColor("#55585E"))
        axis_y.setGridLineColor(QColor("#EDEDF1"))

        if data:
            min_y = int(min(data))
            max_y = int(max(data))
            step = max((max_y - min_y) // 6, 1)

            for v in range(min_y, max_y + 1, step):
                axis_y.append(str(v), v)
        else:
            axis_y.append("0", 0)

        for a in self.chart.axes():
            self.chart.removeAxis(a)

        self.chart.addAxis(axis_x, Qt.AlignBottom)
        self.chart.addAxis(axis_y, Qt.AlignLeft)

        line.attachAxis(axis_x)
        line.attachAxis(axis_y)
        points.attachAxis(axis_x)
        points.attachAxis(axis_y)

    # -----------------------------
    def _show_tooltip(self, point, state):
        if state:
            index = self.sender().points().index(point)
            if 0 <= index < len(self.tooltip_data):
                QToolTip.showText(
                    QCursor.pos(),
                    self.tooltip_data[index],
                    self,
                    self.rect(),
                    3000
                )
        else:
            QToolTip.hideText()


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

        chart_page = self.chart_card()
        settings_page = self.settings_page()

        self.stack = QStackedWidget()
        self.stack.addWidget(chart_page)
        self.stack.addWidget(settings_page)

        self.settings_opacity = QGraphicsOpacityEffect()
        settings_page.setGraphicsEffect(self.settings_opacity)
        self.settings_anim = QPropertyAnimation(self.settings_opacity, b"opacity")
        self.settings_anim.setDuration(300)
        self.settings_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.next_index = 0

        root = QHBoxLayout(central)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(20)

        root.addWidget(self.sidebar(), 1)

        main_area = QHBoxLayout()
        main_area.setSpacing(20)
        main_area.setContentsMargins(0, 0, 0, 0)
        main_area.addWidget(self.stack, 3)
        main_area.addWidget(self.right_panel(), 1)
        main_wrapper = QVBoxLayout()
        main_wrapper.addWidget(self.header())
        main_wrapper.addLayout(main_area)
        main_wrapper.setSpacing(20)
        root.addLayout(main_wrapper, 9)

        self.home_btn.clicked.connect(lambda: self.switch_page(0))
        self.settings_btn.clicked.connect(lambda: self.switch_page(1))
        self.home_btn.setChecked(True)

    def switch_page(self, index):
        if index == self.stack.currentIndex():
            return
        self.next_index = index

        if index == 1:
            self.settings_opacity.setOpacity(0)
            self.stack.setCurrentIndex(index)
            self.settings_anim.stop()
            self.settings_anim.setStartValue(0)
            self.settings_anim.setEndValue(1)
            self.settings_anim.start()
        else:
            self.stack.setCurrentIndex(index)

    #! ---------- Sidebar ----------
    def sidebar(self):
        frame = Card()
        frame.setFixedWidth(80)

        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.setSpacing(20)

        self.home_btn = QPushButton("🏠")
        self.settings_btn = QPushButton("⚙")

        for btn in (self.home_btn, self.settings_btn):
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

        group = QButtonGroup(self)
        group.setExclusive(True)
        group.addButton(self.home_btn)
        group.addButton(self.settings_btn)

        self.home_btn.clicked.connect(lambda: self.switch_page(0))
        self.settings_btn.clicked.connect(lambda: self.switch_page(1))

        self.home_btn.setChecked(True)

        layout.addWidget(self.home_btn)
        layout.addWidget(self.settings_btn)
        layout.addStretch()

        return frame

    #! ---------- Main Content ----------
    def main_content(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        layout.addWidget(self.header())

        body = QHBoxLayout()
        body.setSpacing(20)

        body.addWidget(self.stack, 3)
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
        self.chart_view.chartChanged.connect(self.update_chart_title)

        layout.addWidget(self.chart_title)
        layout.setAlignment(self.chart_view, Qt.AlignTop)

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
        
        def get_checked_coin():
            result = ''
            for btn in group.buttons():
                if btn.isChecked():
                    result = btn.text()
                    break
            else:
                result= None
            return result

        for name, color, path in buttons:
            btn_widget = CoinButton(name, color, path)
            group.addButton(btn_widget.button)
            btn_widget.button.clicked.connect(
                lambda _, n=name: self.chart_view.update_chart(n)
            )
            coin_layout.addWidget(btn_widget)

        group.buttons()[0].setChecked(True)

        update_card = Card()

        up_layout = QVBoxLayout(update_card)
        up_layout.setContentsMargins(20, 16, 20, 20)
        up_layout.setSpacing(12)

        label = QLabel("<b>Update Price</b>")
        label.setStyleSheet(
            "color: #111827;background: transparent;border: none;font-size: 14px;"
        )
        label.setAlignment(Qt.AlignCenter)
        up_layout.addWidget(label)

        key_edit = QLineEdit()
        key_edit.setPlaceholderText("Enter Key")
        key_edit.setStyleSheet(
            """
            color: #374151;
            padding: 10px;
            border-radius: 10px;
            border: 1px solid #E5E7EB;
        """
        )

        up_layout.addWidget(key_edit)
        iv_edit = QLineEdit()
        iv_edit.setPlaceholderText("Enter IV")
        iv_edit.setStyleSheet(
            """
            color: #374151;
            padding: 10px;
            border-radius: 10px;
            border: 1px solid #E5E7EB;
        """
        )

        up_layout.addWidget(iv_edit)

        #! --- Notification QLabel  ---
        notif = QLabel("", update_card)
        notif.setStyleSheet(
            "background: transparent; color: white; border: none; padding: 10px;"
        )
        notif.setAlignment(Qt.AlignCenter)
        notif.setVisible(False)
        up_layout.addWidget(notif, alignment=Qt.AlignTop)

        def show_notification(text, color="#22C55E", duration=2000):
            notif.setText(text)
            notif.setStyleSheet(
                f"background: {color}; color: white; padding: 10px; border-radius: 5px;"
            )
            notif.setVisible(True)
            QTimer.singleShot(duration, lambda: notif.setVisible(False))

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

        def download_clicked():
            if not key_edit.text().strip() and not iv_edit.text().strip():
                show_notification("Please enter Key and IV!", color="#F87171")
                return

            confirm = QMessageBox(btn)
            confirm.setWindowIcon(QIcon(backend.find_resource_path("pics/ask.png")))
            confirm.setWindowTitle("Confirm Download")
            confirm.setText("Do you want to download the data using this key?")
            confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            confirm.setDefaultButton(QMessageBox.No)
            confirm.setIcon(QMessageBox.Question)
            confirm.setStyleSheet(
                """
                QMessageBox QLabel {
                    color: #111827;
                    background: transparent;
                    border: none;
                    font-weight: 600;
                    font-size: 13px;
                }
            """
            )

            reply = confirm.exec()

            if reply == QMessageBox.Yes:
                result = backend.try_decrypt(key_edit.text().strip(), iv_edit.text().strip())

                # ❌ Wrong Key
                if result[0] == False and result[1] == 3:
                    error_msg = QMessageBox(btn)
                    error_msg.setWindowIcon(
                        QIcon(backend.find_resource_path("pics/exclamation.png"))
                    )
                    error_msg.setStyleSheet(
                        """
                                QMessageBox QLabel {
                                    color: #111827;
                                    background: transparent;
                                    border: none;
                                    font-weight: 600;
                                    font-size: 13px;
                                }
                            """
                    )

                    error_msg.setWindowTitle("Wrong Key or IV")
                    error_msg.setText("The provided key or IV is incorrect.")
                    error_msg.setIcon(QMessageBox.Critical)
                    error_msg.setStandardButtons(QMessageBox.Ok)
                    error_msg.exec()
                    return
                elif result[0] == False and result[1] == 1:
                    error_msg = QMessageBox(btn)
                    error_msg.setStyleSheet(
                        """
                                QMessageBox QLabel {
                                    color: #111827;
                                    background: transparent;
                                    border: none;
                                    font-weight: 600;
                                    font-size: 13px;
                                }
                            """
                    )
                    error_msg.setWindowTitle("Settings Not Found")
                    error_msg.setText(
                        "Connection settings not found. Please configure settings first."
                    )
                    error_msg.setIcon(QMessageBox.Warning)
                    error_msg.setWindowIcon(QIcon(backend.find_resource_path("pics/warning.png")))
                    error_msg.setStandardButtons(QMessageBox.Ok)
                    error_msg.exec()
                    return
                
                elif result[0] == False and result[1] == 2:
                    connection_error_msg = QMessageBox(btn)
                    connection_error_msg.setStyleSheet(
                        """
                                QMessageBox QLabel {
                                    color: #111827;
                                    background: transparent;
                                    border: none;
                                    font-weight: 600;
                                    font-size: 13px;
                                }
                            """
                    )
                    connection_error_msg.setWindowTitle("Connection Error")
                    connection_error_msg.setText(
                        "Could not connect to the SFTP server. Please check your connection settings."
                    )
                    connection_error_msg.setIcon(QMessageBox.Warning)
                    connection_error_msg.setWindowIcon(QIcon(backend.find_resource_path("pics/warning.png")))
                    connection_error_msg.setStandardButtons(QMessageBox.Ok)
                    connection_error_msg.exec()
                    return

                elif result[0]==True :

                    show_notification("Downloaded successfully!", color="#22C55E")
                    backend.load_data(DATA,key_edit.text().strip(),iv_edit.text().strip())

                    self.chart_view._set_data(get_checked_coin())

        btn.clicked.connect(download_clicked)

        wrapper.addWidget(coin_card)
        wrapper.addWidget(update_card)
        wrapper.addStretch()

        panel = QWidget()
        panel.setLayout(wrapper)
        return panel

    #! ---------- Settings Page ----------
    def settings_page(self):
        frame = Card()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(40, 0, 40, 30)
        layout.setSpacing(18)

        title = QLabel("Settings")
        title.setStyleSheet(
            "font-size: 18px; font-weight: 600;color: #111827;border: none;background: transparent;"
        )
        layout.addWidget(title)

        inputs = []

        def input_row(label_text, placeholder):
            box = QVBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet(
                "font-weight: 500; color: #374151;border: none;background: transparent;"
            )

            edit = QLineEdit()
            
            edit.setFixedWidth(350)
            edit.setPlaceholderText(placeholder)
            edit.setStyleSheet(
                """
                color: #374151;
                padding: 10px;
                border-radius: 10px;
                border: none;
            """
            )
            box.addWidget(lbl, alignment=Qt.AlignCenter)
            box.addWidget(edit, alignment=Qt.AlignCenter)

            inputs.append(edit)
            return box
        
        layout.addLayout(input_row("<b>IP</b>", "127.0.0.1"))
        layout.addLayout(input_row("<b>SFTP Port</b>", "22"))
        layout.addLayout(input_row("<b>Username</b>", "Username"))
        
        loaded_setting = backend.load_local_settings()
        if loaded_setting:
            inputs[0].setText( loaded_setting[0]) 
            inputs[1].setText(loaded_setting[1])


        def password_row(label_text, placeholder):
            box = QVBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet(
                "font-weight: 500; color: #374151;border: none;background: transparent;"
            )
            lbl.setAlignment(Qt.AlignCenter)

            edit = QLineEdit()
            edit.setFixedWidth(350)
            edit.setEchoMode(QLineEdit.Password)
            edit.setPlaceholderText(placeholder)
            edit.setStyleSheet(
                """
                color: #374151;
                padding: 10px;
                border-radius: 10px;
                border: none;
            """
            )
            box.addWidget(lbl, alignment=Qt.AlignCenter)
            box.addWidget(edit, alignment=Qt.AlignCenter)

            inputs.append(edit)
            return box

        layout.addLayout(password_row("<b>Password</b>", "********"))

        #! --- Notification QLabel ---
        notif = QLabel("", frame)
        notif.setStyleSheet(
            "background: transparent; color: white;border: none; padding: 10px; "
        )
        notif.setFixedWidth(350)
        notif.setAlignment(Qt.AlignCenter)
        notif.setVisible(True)
        layout.addWidget(notif, alignment=Qt.AlignCenter)

        opacity_effect = QGraphicsOpacityEffect()
        notif.setGraphicsEffect(opacity_effect)
        opacity_anim = QPropertyAnimation(opacity_effect, b"opacity")
        opacity_anim.setDuration(500)

        def show_notification(text, color="#22C55E"):
            notif.setText(text)
            notif.setStyleSheet(
                f"background: {color}; color: white; padding: 10px; border-radius: 5px;"
            )
            notif.setVisible(True)

            QTimer.singleShot(
                2000,
                lambda: notif.setStyleSheet(
                    "background: transparent; color: white;border: none; padding: 10px; "
                ),
            )

        save = QPushButton("Save")
        save.setFixedWidth(120)
        save.setStyleSheet(
            """
            QPushButton {
                background: #22C55E;
                color: white;
                padding: 10px;
                border-radius: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #16A34A;
            }
        """
        )

        def save_clicked():
            empty_fields = [i for i in inputs if not i.text().strip()]
            if empty_fields:
                show_notification("Please fill in all fields!", color="#F87171")
                return


            row = [
                inputs[0].text().strip(),
                inputs[1].text().strip(),
                inputs[2].text().strip(),
                inputs[3].text().strip(),
            ]
            backend.save_settings(row,key,iv)
            show_notification("Settings saved successfully!", color="#22C55E") 

        save.clicked.connect(save_clicked)
        layout.addWidget(save, alignment=Qt.AlignHCenter)

        return frame

    def _on_fade_out(self):
        self.stack.setCurrentIndex(self.next_index)

        self.stack_anim.finished.disconnect(self._on_fade_out)
        self.stack_anim.setStartValue(0.0)
        self.stack_anim.setEndValue(1.0)
        self.stack_anim.start()

    def update_chart_title(self, name):
        self.chart_title.setText(f"{name} Chart")


#! ---------- Run ----------
if __name__ == "__main__":
    backend.ensure_data_files()
    settings = backend.load_local_settings()
    if len(settings) > 4:
        backend.load_data(DATA,settings[4],settings[5])
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
