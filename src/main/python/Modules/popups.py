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
    QLineEdit, 
    QGridLayout, 
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
        self.set_spinbox_range([-65535, 65535], RS_type="RS1")
        self.set_spinbox_range([-65535, 65535], RS_type="RS2")
        # 初期値
        self.setValues(initial_values)
        # ボタン
        self.btnOK = QPushButton("OK")
        self.btnCancel = QPushButton("cancel")
        self.btnOK.clicked.connect(self.pressedOK)
        self.btnCancel.clicked.connect(self.pressedCancel)
        # レイアウト
        self.spbx_layout = QFormLayout()
        self.spbx_layout.addRow(QLabel(labels[0]), self.spbx_RS1)
        self.spbx_layout.addRow(QLabel(labels[1]), self.spbx_RS2)
        self.btn_layout = QHBoxLayout()
        self.btn_layout.addStretch(1)
        self.btn_layout.addWidget(self.btnOK)
        self.btn_layout.addWidget(self.btnCancel)
        layout = QVBoxLayout()
        layout.addLayout(self.spbx_layout)
        layout.addLayout(self.btn_layout)
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

class PoiSettingsPopup(RangeSettingsPopup): # マクロ用
    def __init__(self, parent=None, initial_values=(1900, 2400), labels=("left", "right"), title="range setting", double=False, poi_key="poi1"):
        super().__init__(parent, initial_values, labels, title, double)
        self.is_close_allowed = False
        self.poi_key = QLineEdit(poi_key)
        self.spbx_layout.insertRow(0, "POI name", self.poi_key)
        self.isValueChanged = True  # self.parent.map_widget のクロスヘアをクリックした際は、spbx の value も変わるが、その際にクロスヘアが再度updateされるのを防ぐ
        self.parent = parent
        self.spbx_RS1.valueChanged.connect(functools.partial(self.value_changed, xy="x"))
        self.spbx_RS2.valueChanged.connect(functools.partial(self.value_changed, xy="y"))
        self.btnSkip = QPushButton("skip")
        self.btn_layout.addWidget(self.btnSkip)
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
    def set_poi_key(self, text):
        self.poi_key.setText(text)
    def get_poi_key(self):
        return self.poi_key.text()

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

class RangeSettingsPopupWithCmb(RangeSettingsPopup):
    def __init__(self, parent=None, initial_values=(1900, 2400), labels=("left (cm-1)", "right (cm-1)"), title="range setting", double=True, cmb_title="", cmb_messages=[]):
        super().__init__(parent, initial_values, labels, title, double)
        self.cmb = QComboBox()
        self.cmb.addItems(cmb_messages)
        self.spbx_layout.addRow(QLabel(cmb_title))
        self.spbx_layout.addRow(QLabel("option"), self.cmb)

class MultipleRangeSettingsPopup(QDialog):
    def __init__(self, parent=None, initial_values=(1900, 2400), labels=("left", "right"), title="range setting", double=True, cmb_title=None, cmb_messages=[]):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.parent = parent
        self.double = double
        self.initial_values = initial_values
        self.setWindowTitle(title)
        # スピンボックス
        self.spbx_list1 = []
        self.spbx_list2 = []
        # コンボボックス
        self.cmb = QComboBox()
        self.cmb.addItems(cmb_messages)
        # ボタン
        self.enabled_stylesheet = \
            """
            QPushButton{border:1px solid gray; border-radius: 7px; background-color:light gray; color:black}
            QPushButton:hover:!pressed{border:1px solid gray; background-color:gray; color:black}
            QPushButton:hover{border:1px solid gray; background-color:rgb(255,150,150); color:black}
            """
        self.disabled_stylesheet = \
            """
            QPushButton{border:1px rgba(255, 255, 255, 0); border-radius: 7px; background-color:rgba(255, 255, 255, 0); color:rgba(255, 255, 255, 0)}
            """
        btnAdd = QPushButton("+")
        btnAdd.setFixedSize(15, 15)
        btnAdd.setStyleSheet(self.enabled_stylesheet)
        self.btnOK = QPushButton("OK")
        self.btnCancel = QPushButton("cancel")
        self.btnOK.clicked.connect(self.pressedOK)
        self.btnCancel.clicked.connect(self.pressedCancel)
        # レイアウト
        self.spbx_layout = QGridLayout()
        self.spbx_layout.addWidget(QLabel(labels[0]), 0, 1)
        self.spbx_layout.addWidget(QLabel(labels[1]), 0, 2)
        self.btn_layout1 = QHBoxLayout()
        self.btn_layout1.addStretch(1)
        self.btn_layout1.addWidget(btnAdd)
        self.btn_layout2 = QHBoxLayout()
        self.btn_layout2.addStretch(1)
        self.btn_layout2.addWidget(self.btnOK)
        self.btn_layout2.addWidget(self.btnCancel)
        cmb_layout = QHBoxLayout()
        cmb_layout.addWidget(QLabel("option"))
        cmb_layout.addWidget(self.cmb)
        layout = QVBoxLayout()
        layout.addLayout(self.spbx_layout)
        layout.addLayout(self.btn_layout1)
        if cmb_title is not None:
            layout.addWidget(QLabel(cmb_title))
        layout.addLayout(cmb_layout)
        layout.addLayout(self.btn_layout2)
        self.setLayout(layout)
        # 初期値
        self.spbx_range1 = (-65535, 65535)
        self.spbx_range2 = (-65535, 65535)
        self.add_Row()
        self.setValuesForAll(self.initial_values)
        # イベントコネクト
        btnAdd.clicked.connect(self.add_Row)
    def add_Row(self):
        # スピンボックス
        if self.double:
            spbx_RS1 = QDoubleSpinBox()
            spbx_RS2 = QDoubleSpinBox()
        else:
            spbx_RS1 = QSpinBox()
            spbx_RS2 = QSpinBox()
        # 削除ボタン
        btn_delete = QPushButton("×")
        btn_delete.setFixedSize(15, 15)
        # 配置
        N_row = self.spbx_layout.rowCount()
        self.spbx_layout.addWidget(QLabel("range {0}".format(N_row)), N_row, 0)
        self.spbx_layout.addWidget(spbx_RS1, N_row, 1)
        self.spbx_layout.addWidget(spbx_RS2, N_row, 2)
        self.spbx_layout.addWidget(btn_delete, N_row, 3)
        if N_row > 1:
            btn_delete.setStyleSheet(self.enabled_stylesheet)
        else:
            btn_delete.setStyleSheet(self.disabled_stylesheet)
            btn_delete.setDisabled(True)
        # 最大値、最小値設定
        self.spbx_list1.append(spbx_RS1)
        self.spbx_list2.append(spbx_RS2)
        self.set_spinbox_ranges()
        spbx_RS1.setValue(self.initial_values[0])
        spbx_RS2.setValue(self.initial_values[1])
    def setValuesForAll(self, values):
        for spbx1, spbx2 in zip(self.spbx_list1, self.spbx_list2):
            spbx1.setValue(values[0])
            spbx2.setValue(values[1])
    def pressedOK(self, event):
        self.done(1)
    def pressedCancel(self, event):
        self.done(0)
    def set_spinbox_ranges(self):
        for spbx1, spbx2 in zip(self.spbx_list1, self.spbx_list2):
            spbx1.setRange(*self.spbx_range1)
            spbx2.setRange(*self.spbx_range2)


class ValueSettingsPopup(QDialog):
    def __init__(self, parent=None, initial_value=gf.value_settings_popups_init, label="enter value", title="", double=True):
        super().__init__()
        self.setWindowTitle(title)
        # スピンボックス
        if double:
            self.spbx_RS = QDoubleSpinBox()
        else:
            self.spbx_RS = QSpinBox()
        self.spbx_RS.setMinimum(0)
        self.spbx_RS.setMaximum(100000)
        # 初期値
        self.spbx_RS.setValue(initial_value)
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

class TextSettingsPopup(QDialog):
    def __init__(self, parent=None, initial_txt="", label="Enter Text", title="text setting"):
        super().__init__()
        self.parent = parent
        self.setWindowTitle(title)
        # 要素
        self.line_edit = QLineEdit(initial_txt)
        self.btnOK = QPushButton("OK")
        self.btnCancel = QPushButton("cancel")
        self.btnOK.clicked.connect(self.pressedOK)
        self.btnCancel.clicked.connect(self.pressedCancel)
        label = QLabel(label)
        label.setOpenExternalLinks(True)
        # レイアウト
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btnOK)
        btn_layout.addWidget(self.btnCancel)
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.line_edit)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    def pressedOK(self, event):
        self.done(1)
    def pressedCancel(self, event):
        self.done(0)
    def text(self):
        return self.line_edit.text()

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

class MessageDialog(QDialog):
    def __init__(self, parent=None, message="", title="", p_type="Normal", enable_event_connect=True):
        super().__init__()
        self.parent = parent
        self.setWindowTitle(title)
        label = QLabel(message)
        label.setOpenExternalLinks(True)
        self.btnOk = QPushButton("OK")
        if p_type == "Normal":
            btn_list = [self.btnOk]
            btn_name_list = ["btnOk"]
        elif p_type == "Cancel":
            self.btnCancel = QPushButton("Cancel")
            btn_list = [self.btnCancel, self.btnOk]
            btn_name_list = ["btnCancel", "btnOk"]
        else:
            raise Exception("unknown p_type: {0}".format(p_type))
        if enable_event_connect:
            for btn_name in btn_name_list:
                btn = getattr(self, btn_name)
                func = getattr(self, "{0}_clicked".format(btn_name))
                btn.clicked.connect(func)
        self.btnOk.setDefault(True)
        # レイアウト
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        for btn in btn_list:
            btn_layout.addWidget(btn)
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    def btnOk_clicked(self, event):
        self.done(1)
    def btnCancel_clicked(self, event):
        self.done(0)

class ProgressBarWidget(QWidget):
    signal = pyqtSignal(int)
    def __init__(self, parent, message="", real_value_max=100, message2="", N_iter=None, segment=97):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        # シグナル
        self.real_value_max = real_value_max
        self.signal.connect(self.on_signal_emit)
        # 実質
        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)
        self.label = QLabel(message)
        self.label2 = QLabel(message2)
        if N_iter is not None:
            self.segment_list = self.get_segment_list(N_iter, segment)
        else:
            self.segment_list = None
        # レイアウト
        label2_layout = QHBoxLayout()
        label2_layout.setAlignment(Qt.AlignRight)
        label2_layout.addWidget(self.label2)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.pbar)
        layout.addLayout(label2_layout)
        layout.addStretch(1)
        self.setLayout(layout)
        self.is_close_allowed = False
    def get_segment_list(self, n, segment):
        if n > segment:
            return np.arange(n)[::int(n/segment)]
        else:
            return np.arange(n)[::1]
    def processSegment(self, idx):
        if idx in self.segment_list:
            self.addValue(1)
    def show(self):
        super().show()
        QCoreApplication.processEvents()
    def setLabel(self, text):
        self.label.setText(text)
    def setLabel2(self, text):
        self.label2.setText(text)
        QCoreApplication.processEvents()
    def setRealValue(self, real_value):
        self.pbar.setValue(100 * real_value / self.real_value_max)
        QCoreApplication.processEvents()
    def addValue(self, value):
        cur_value = self.pbar.value()
        self.pbar.setValue(cur_value + value)
        QCoreApplication.processEvents()
    def master_close(self):
        self.is_close_allowed = True
        self.close()
    def closeEvent(self, event=None):
        if self.is_close_allowed:
            event.accept()
        else:
            event.ignore()
    def on_signal_emit(self, real_value):
        print("{0}/{1}".format(real_value, self.real_value_max))
        self.setRealValue(real_value)










