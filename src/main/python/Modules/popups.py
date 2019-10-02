# -*- Coding: utf-8 -*-
import functools
from PyQt5.QtCore import Qt
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

from . import draw
from . import general_functions as gf

# map画像を最初に開くときにサイズを決めなくてはならない
class SizeSettingsPopup(QDialog):
    def __init__(self, spc_file=None, parent=None):
        self.spc_file = spc_file
        self.cur_RS = 2950
        self.size_x = None
        self.size_y = None
        self.product_x_list, self.product_y_list = gf.into_2_products(self.spc_file.fnsub)
        two_products_list = ["%dx%d"%(product_x, product_y) for product_x, product_y in zip(self.product_x_list, self.product_y_list)]
        super().__init__()
        self.setWindowTitle("determine x-y size")
        # コンボボックス
        self.cmbox_size = QComboBox()
        self.cmbox_size.addItems(two_products_list)
        self.cmbox_size.currentIndexChanged.connect(self.cmbox_selection_changed)
        # ボタン
        btnOK = QPushButton("OK")
        btnCancel = QPushButton("cancel")
        btnOK.clicked.connect(self.pressedOK)
        btnCancel.clicked.connect(self.pressedCancel)
        # イメージ
        self.simple_map_widget = draw.SimpleMapWidget(spc_file=self.spc_file, parent=self)
        self.toolbar_layout = draw.SimpleToolbarLayout(parent=self)
        # レイアウト1
        mini_layout1 = QHBoxLayout()
        mini_layout1.addWidget(QLabel("   %d [pixels]="%self.spc_file.fnsub))
        mini_layout1.addWidget(self.cmbox_size)
        mini_layout1.addWidget(QLabel(" (x by y)"))
        mini_layout1.addStretch(1)
        mini_layout1.addWidget(btnOK)
        mini_layout1.addWidget(btnCancel)
        # レイアウト2
        mini_layout2 = QVBoxLayout()
        mini_layout2.addLayout(mini_layout1)
        mini_layout2.addWidget(self.simple_map_widget)
        # レイアウト
        layout = QHBoxLayout()
        layout.addLayout(self.toolbar_layout)
        layout.addLayout(mini_layout2)
        layout.setContentsMargins(gf.dcm, gf.dcm, gf.dcm, gf.dcm)
        layout.setSpacing(gf.dsp)
        self.setLayout(layout)
        # self.setGeometry(QtCore.QRect(100, 100, 200, 100))
        self.setWindowTitle("Size Settings")
        # 設定
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(p)
        # 初期描画
        self.cmbox_size.setCurrentIndex(int(len(two_products_list) / 2))
    # 描画
    def cmbox_selection_changed(self, event):
        product_x = self.product_x_list[event]
        product_y = self.product_y_list[event]
        point_intensity_list = self.spc_file.get_total_intensity_list()
        image2D = draw.Image2D(point_intensity_list.reshape(product_y, product_x).T)
        self.simple_map_widget.display_map(image2D)
    def pressedOK(self):
        current_idx = self.cmbox_size.currentIndex()
        self.size_x = self.product_x_list[current_idx]
        self.size_y = self.product_y_list[current_idx]
        self.done(1)
    def pressedCancel(self):
        self.done(0)

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
    def __init__(self, parent=None, initial_values=(1900, 2400), labels=("left", "right"), title="range setting", double=True, ckbx_message=""):
        super().__init__(parent, initial_values, labels, title, double)
        self.ckbx = QCheckBox()
        self.spbx_layout.addRow(self.ckbx, QLabel(ckbx_message))
        self.ckbx.stateChanged.connect(self.ckbx_state_changed)
    def ckbx_state_changed(self, event):
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
    def __init__(self, parent, message=""):
        super().__init__()
        self.pbar = QProgressBar(self)
        self.pbar.setGeometry(30, 40, 200, 25)
        self.pbar.setValue(0)
        self.label = QLabel()
        self.setLabel(message)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(QLabel(" "))
        layout.addStretch(1)
        self.setLayout(layout)
        self.is_close_allowed = False
    def setLabel(self, text):
        self.label.setText(text)
    def addValue(self, value):
        cur_value = self.pbar.value()
        self.pbar.setValue(cur_value + value)
    def closeEvent(self, event=None):
        if self.is_close_allowed:
            event.accept()
        else:
            event.ignore()
            

# class BoolMessagePopup(QMessageBox):
#     def __init__(self, message, title=None)
#         super().__init__()
#         self.setWindowTitle(title)
#         self.setText(message)

#         btnOK = QPushButton("OK")
#         btnCancel = QPushButton("cancel")
#         btnOK.clicked.connect(self.pressedOK)
#         btnCancel.clicked.connect(self.pressedCancel)









