# -*- Coding: utf-8 -*-
import functools
from PyQt5.QtCore import (
    Qt, 
    pyqtSignal, 
    QCoreApplication, 
    )
from PyQt5.QtWidgets import (
    QDialog, 
    QSpinBox, 
    QDoubleSpinBox, 
    QVBoxLayout, 
    QHBoxLayout, 
    QPushButton, 
    QMessageBox, 
    QLabel, 
    QFormLayout, 
    QComboBox, 
    QProgressBar, 
    QWidget, 
    QCheckBox, 
    )
import numpy as np

from . import draw
from . import general_functions as gf

class RangeSettingsPopup(QDialog):
    def __init__(self, parent=None, initial_values=(1900, 2400), labels=("left", "right"), title="range setting", double=True):
        super().__init__()
        self.parent = parent
        self.setWindowTitle(title)
        # スピンボックス
        if double:
            self.spbx_RS1 = QDoubleSpinBox()
            self.spbx_RS2 = QDoubleSpinBox()
        else:
            self.spbx_RS1 = QSpinBox()
            self.spbx_RS2 = QSpinBox()
        self.spbx_RS1.setMinimum(-65535)
        self.spbx_RS1.setMaximum(65535)
        self.spbx_RS2.setMinimum(-65535)
        self.spbx_RS2.setMaximum(65535)
        # 初期値
        self.setValues(initial_values)
        # self.spbx_size_x.valueChanged.connect(self.size_changed)
        # self.spbx_size_y.valueChanged.connect(self.size_changed)
        # ボタン
        self.btnOK = QPushButton("OK")
        self.btnCancel = QPushButton("cancel")
        self.btnOK.clicked.connect(self.pressedOK)
        self.btnCancel.clicked.connect(self.pressedCancel)
        # レイアウト
        self.spbx_layout = QFormLayout()
        self.spbx_layout.addRow(QLabel(labels[0]), self.spbx_RS1)
        self.spbx_layout.addRow(QLabel(labels[1]), self.spbx_RS2)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btnOK)
        btn_layout.addWidget(self.btnCancel)
        layout = QVBoxLayout()
        layout.addLayout(self.spbx_layout)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    def setValues(self, values):
        self.spbx_RS1.setValue(values[0])
        self.spbx_RS2.setValue(values[1])
    def pressedOK(self, event):
        self.done(1)
    def pressedCancel(self, event):
        self.done(0)
    def set_spinbox_range(self, range, RS_type):
        spbx = getattr(self, "spbx_%s"%RS_type)
        spbx.setMinimum(range[0])
        spbx.setMaximum(range[1])

class CfpSettingsPopup(RangeSettingsPopup):
    def __init__(self, parent=None, initial_values=(1900, 2400), labels=("left", "right"), title="range setting", double=False):
        super().__init__(parent, initial_values, labels, title, double)
        self.isValueChanged = True  # self.parent.map_widget のクロスヘアをクリックした際は、spbx の value も変わるが、その際にクロスヘアが再度updateされるのを防ぐ
        self.parent = parent
        self.spbx_RS1.valueChanged.connect(functools.partial(self.value_changed, xy="x"))
        self.spbx_RS2.valueChanged.connect(functools.partial(self.value_changed, xy="y"))
    def value_changed(self, event, xy):
        if self.isValueChanged:
            if xy == "x":
                self.parent.map_widget.v_crosshair.setValue(event + 0.5)
            elif xy == "y":
                self.parent.map_widget.h_crosshair.setValue(event + 0.5)
            else:
                raise Exception("some error")
    def on_map_widget_click(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()
            # クリックしたときのview boxを取得
            loc_of_QPointF = self.parent.map_widget.img_view_box.mapSceneToView(event.scenePos())
            map_x, map_y, value = self.parent.map_widget.get_map_xy_fm_QpointF(loc_of_QPointF)
            if value is not None:
                self.isValueChanged = False
                self.spbx_RS1.setValue(map_x)
                self.spbx_RS2.setValue(map_y)
                self.isValueChanged = True

class RangeSettingsPopupWithCkbx(RangeSettingsPopup):
    def __init__(self, parent=None, initial_values=(1900, 2400), labels=("left", "right"), title="range setting", double=True, ckbx_messages=[]):
        super().__init__(parent, initial_values, labels, title, double)
        self.ckbxes = []
        for i, ckbx_message in enumerate(ckbx_messages):
            ckbx = QCheckBox()
            ckbx.stateChanged.connect(functools.partial(self.ckbx_state_changed, ckbx_idx = i))
            self.ckbxes.append(ckbx)
            self.spbx_layout.addRow(ckbx, QLabel(ckbx_message))
    def ckbx_state_changed(self, event, ckbx_idx):
        if ckbx_idx == 0:
            if event == 2:
                self.spbx_RS1.setEnabled(False)
                self.spbx_RS2.setEnabled(False)
            elif event == 0:
                self.spbx_RS1.setEnabled(True)
                self.spbx_RS2.setEnabled(True)

class ValueSettingsPopup(QDialog):
    def __init__(self, parent=None, initial_value=gf.value_settings_popups_init, label="enter value", title="", double=True):
        super().__init__()
        self.setWindowTitle(title)
        print(double)
        # スピンボックス
        if double:
            self.spbx_RS = QDoubleSpinBox()
        else:
            self.spbx_RS = QSpinBox()
        self.spbx_RS.setMinimum(0)
        self.spbx_RS.setMaximum(100000)
        # 初期値
        self.spbx_RS.setValue(initial_value)
        # self.spbx_size_x.valueChanged.connect(self.size_changed)
        # self.spbx_size_y.valueChanged.connect(self.size_changed)
        # ボタン
        btnOK = QPushButton("OK")
        btnCancel = QPushButton("cancel")
        btnOK.clicked.connect(self.pressedOK)
        btnCancel.clicked.connect(self.pressedCancel)
        # レイアウト
        spbx_layout = QFormLayout()
        spbx_layout.addRow(QLabel(label), self.spbx_RS)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btnOK)
        btn_layout.addWidget(btnCancel)
        layout = QVBoxLayout()
        layout.addLayout(spbx_layout)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    def pressedOK(self, event):
        self.done(1)
    def pressedCancel(self, event):
        self.done(0)

class ImageCalculator(QDialog):
    def __init__(self, image2D_list, parent=None):
        self.image2D_list = image2D_list
        self.parent = parent
        self.created_image2D = None
        super().__init__()
        # 画像
        img_name_list = [image2D.name for image2D in self.image2D_list]
        self.cmb_image1 = QComboBox()
        self.cmb_image2 = QComboBox()
        self.cmb_image1.addItems(img_name_list)
        self.cmb_image2.addItems(img_name_list)

        # 計算方法選択
        self.cmb_operation = QComboBox()
        # self.cmb_operation.addItem("Add")
        # self.cmb_operation.addItem("Subtract")
        # self.cmb_operation.addItem("Multiply")
        self.cmb_operation.addItem("Divide")
        # self.cmb_operation.addItem("Difference")

        # ボタン
        btnOK = QPushButton("OK")
        btnCancel = QPushButton("cancel")
        btnOK.clicked.connect(self.pressedOK)
        btnCancel.clicked.connect(self.pressedCancel)
        # レイアウト
        operation_layout = QFormLayout()
        operation_layout.addRow(QLabel("Image1:"), self.cmb_image1)
        operation_layout.addRow(QLabel("Operation:"), self.cmb_operation)
        operation_layout.addRow(QLabel("Image2:"), self.cmb_image2)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btnOK)
        btn_layout.addWidget(btnCancel)
        layout = QVBoxLayout()
        layout.addLayout(operation_layout)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    def pressedOK(self, event):
        operation = self.cmb_operation.currentText()
        img1_idx = self.cmb_image1.currentIndex()
        img2_idx = self.cmb_image2.currentIndex()
        image2D_1 = self.image2D_list[img1_idx]
        image2D_2 = self.image2D_list[img2_idx]
        try:
            function = getattr(image2D_1, operation)
        except:
            print("not yet!")
            self.done(0)
        self.created_image2D = function(image2D_2)
        self.done(1)
    def pressedCancel(self, event):
        self.done(0)

class WarningPopup(QMessageBox):
    def __init__(self, message, title=None, p_type="Normal", icon=QMessageBox.Warning):
        super().__init__()
        self.setIcon(icon)
        self.setWindowTitle(title)
        self.setText(message)
        # self.setInformativeText(invalid_str)
        # self.setDetailedText(formula_explanation)
        if p_type == "Normal":
            self.setStandardButtons(QMessageBox.Ok)
        elif p_type == "Cancel":    # cancel: 4194304, ok: 1024
            self.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        elif p_type == "Bool":      # No: 65536, Yes: 16384
            self.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        # 設定
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(p)

class ProgressBarWidget(QWidget):
    signal = pyqtSignal(int)
    def __init__(self, parent, message="", real_value_max=100):
        super().__init__()
        self.setFixedSize(300, 100)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        # シグナル
        self.real_value_max = real_value_max
        self.signal.connect(self.on_signal_emit)
        # 実質
        self.pbar = QProgressBar(self)
        self.pbar.setGeometry(30, 40, 200, 25)
        self.pbar.setValue(0)
        self.label = QLabel()
        self.setLabel(message)
        # レイアウト
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(QLabel(" "))
        layout.addStretch(1)
        self.setLayout(layout)
        self.is_close_allowed = False
    def get_segment_list(self, n, segment):
        if n > segment:
            return np.arange(n)[::int(n/segment)]
        else:
            return np.arange(n)[::1]
    def show(self):
        super().show()
        QCoreApplication.processEvents()
    def setLabel(self, text):
        self.label.setText(text)
    def setRealValue(self, real_value):
        self.pbar.setValue(100 * real_value / self.real_value_max)
        QCoreApplication.processEvents()
    def addValue(self, value):
        cur_value = self.pbar.value()
        self.pbar.setValue(cur_value + value)
        QCoreApplication.processEvents()
    def closeEvent(self, event=None):
        if self.is_close_allowed:
            event.accept()
        else:
            event.ignore()
    def on_signal_emit(self, real_value):
        print("{0}/{1}".format(real_value, self.real_value_max))
        self.setRealValue(real_value)


# class BoolMessagePopup(QMessageBox):
#     def __init__(self, message, title=None)
#         super().__init__()
#         self.setWindowTitle(title)
#         self.setText(message)

#         btnOK = QPushButton("OK")
#         btnCancel = QPushButton("cancel")
#         btnOK.clicked.connect(self.pressedOK)
#         btnCancel.clicked.connect(self.pressedCancel)









