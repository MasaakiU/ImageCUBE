# -*- Coding: utf-8 -*-

import glob
import functools
import numpy as np
import re
import traceback

from PyQt5.QtWidgets import (
    QFileDialog, 
    QWidget, 
    QPushButton, 
    QVBoxLayout, 
    QHBoxLayout,  
    QSpinBox, 
    QScrollArea, 
    QLabel, 
    QLineEdit, 
    QDialog, 
    QComboBox, 
    QFormLayout, 
    QCheckBox, 
    )
from PyQt5.QtCore import QEventLoop, QCoreApplication, Qt
from Modules import general_functions as gf
from Modules import draw
from Modules import popups
from Modules import my_widgets as my_w

class BatchProcessingWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.window_type = "b"
        # 上部ファイルパス
        self.path_entry = QLineEdit()
        btnSetPath = QPushButton("...")
        # 左部ツールレイアウト
        btnOpenWindow = my_w.CustomPicButton("open1.svg", "open2.svg", "open3.svg", base_path=gf.icon_path, parent=self)
        btnCloseWindow = my_w.CustomPicButton("close_all_1.svg", "close_all_2.svg", "close_all_3.svg", base_path=gf.icon_path, parent=self)
        btnSetPOI = my_w.CustomPicButton("poi1.svg", "poi2.svg", "poi3.svg", base_path=gf.icon_path, parent=self)
        btnGoToPOI = my_w.CustomPicButton("poi1.svg", "poi2.svg", "poi3.svg", base_path=gf.icon_path, parent=self)
        btnSetSpcRange = my_w.CustomPicButton("set_spc_range1.svg", "set_spc_range2.svg", "set_spc_range3.svg", base_path=gf.icon_path, parent=self)
        btnShowSpectrumWithMaxInt = my_w.CustomPicButton("show_max_int_spc1.svg", "show_max_int_spc2.svg", "show_max_int_spc3.svg", base_path=gf.icon_path, parent=self)
        btnSetMapImageContrast = my_w.CustomPicButton("map_contrast1.svg", "map_contrast2.svg", "map_contrast3.svg", base_path=gf.icon_path, parent=self)
        btnSignalIntensity = my_w.CustomPicButton("sig_int1.svg", "sig_int2.svg", "sig_int3.svg", base_path=gf.icon_path, parent=self)
        btnSignalToBaseline = my_w.CustomPicButton("sig2base1.svg", "sig2base2.svg", "sig2base3.svg", base_path=gf.icon_path, parent=self)
        btnSianglToHorizontalBaseline = my_w.CustomPicButton("sig2h_base1.svg", "sig2h_base2.svg", "sig2h_base3.svg", base_path=gf.icon_path, parent=self)
        btnSignalToAxis = my_w.CustomPicButton("sig2axis1.svg", "sig2axis2.svg", "sig2axis3.svg", base_path=gf.icon_path, parent=self)
        btnAddCurrentSpectrum = my_w.CustomPicButton("add_cur_spec1.svg", "add_cur_spec2.svg", "add_cur_spec3.svg", base_path=gf.icon_path, parent=self)
        btnSpectrumSubtraction = my_w.CustomPicButton("spct_calc1.svg", "spct_calc2.svg", "spct_calc3.svg", base_path=gf.icon_path, parent=self)
        btnUMX = my_w.CustomPicButton("unmix1.svg", "unmix2.svg", "unmix3.svg", base_path=gf.icon_path, parent=self)
        btnSaveImages = my_w.CustomPicButton("save_map1.svg", "save_map2.svg", "save_map3.svg", base_path=gf.icon_path, parent=self)
        btnSaveSpectrum = my_w.CustomPicButton("save_spct1.svg", "save_spct2.svg", "save_spct3.svg", base_path=gf.icon_path, parent=self)
        btnSaveTarget = my_w.CustomPicButton("save_target1.svg", "save_target2.svg", "save_target3.svg", base_path=gf.icon_path, parent=self)
        btnCosmicRayRemoval = my_w.CustomPicButton("CRR1.svg", "CRR2.svg", "CRR3.svg", base_path=gf.icon_path, parent=self)
        btnNoiseFilterPCA = my_w.CustomPicButton("NF1.svg", "NF2.svg", "NF3.svg", base_path=gf.icon_path, parent=self)
        btnSetWindowSize = my_w.CustomPicButton("map_size1.svg", "map_size2.svg", "map_size3.svg", base_path=gf.icon_path, parent=self)
        btnExportData = my_w.CustomPicButton("export_spc1.svg", "export_spc2.svg", "export_spc3.svg", base_path=gf.icon_path, parent=self)
        btnImportedPlugins = my_w.CustomPicButton("imported_plgin1.svg", "imported_plgin2.svg", "imported_plgin3.svg", base_path=gf.icon_path, parent=self)
        btnExecuteProcedures = my_w.CustomPicButton("exec_umx1.svg", "exec_umx2.svg", "exec_umx3.svg", base_path=gf.icon_path, parent=self)
        btnHideAllInVb2 = my_w.CustomPicButton("hide1.svg", "hide2.svg", "hide3.svg", base_path=gf.icon_path, parent=self)
        btnHideRightAxis = my_w.CustomPicButton("HideShow_R_Ax1.svg", "HideShow_R_Ax2.svg", "HideShow_R_Ax3.svg", base_path=gf.icon_path, parent=self)
        ##
        size = (75, 35)
        btnRUN = QPushButton("EXECUTE\n▶") # my_w.CustomPicButton("run_action1.svg", "run_action2.svg", "run_action3.svg" ,base_path=gf.icon_path, parent=self)
        btnRUN.setFixedSize(*size)
        btnRUN.setStyleSheet(
            """
            QPushButton{border:1px solid gray; border-radius: 10px; background-color:light gray; color:black}
            QPushButton:hover:!pressed{border:1px solid gray; background-color:gray; color:black}
            QPushButton:hover{border:1px solid gray; background-color:rgb(255,150,150); color:black}
            """
        )
        btnRUN.repaint()
        ##
        btnMoveUp = QPushButton("move up\n⬆") # my_w.CustomPicButton("up1.svg", "up2.svg", "up3.svg" ,base_path=gf.icon_path, parent=self)
        btnMoveUp.setFixedSize(*size)
        btnMoveUp.setStyleSheet(
            """
            QPushButton{border:1px none; background-color:light gray; color:black}
            QPushButton:hover:!pressed{border:1px solid gray; background-color:light gray; color:black}
            QPushButton:hover{border:1px gray; background-color:gray; color:white}
            """
        )
        btnRemove = QPushButton("remove\n✖") # my_w.CustomPicButton("remove_action1.svg", "remove_action2.svg", "remove_action3.svg",base_path=gf.icon_path, parent=self)
        btnRemove.setFixedSize(*size)
        btnRemove.setStyleSheet(
            """
            QPushButton{border:1px none; background-color:light gray; color:black}
            QPushButton:hover:!pressed{border:1px solid gray; background-color:light gray; color:black}
            QPushButton:hover{border:1px gray; background-color:gray; color:white}
            """
        )
        btnMoveDown = QPushButton("move down\n⬇") # my_w.CustomPicButton("down1.svg", "down2.svg", "down3.svg" ,base_path=gf.icon_path, parent=self)
        btnMoveDown.setFixedSize(*size)
        btnMoveDown.setStyleSheet(
            """
            QPushButton{border:1px none; background-color:light gray; color:black}
            QPushButton:hover:!pressed{border:1px solid gray; background-color:light gray; color:black}
            QPushButton:hover{border:1px gray; background-color:gray; color:white}
            """
        )
        # 右部バッチエリア
        self.process_layout = my_w.ClickableLayout(parent=self)
        # 上部ファイルパスレイアウト
        batch_path_selection_layout = QHBoxLayout()
        batch_path_selection_layout.addWidget(QLabel("folder path"))
        batch_path_selection_layout.addWidget(self.path_entry)
        batch_path_selection_layout.addWidget(btnSetPath)
        # 左部ツールレイアウト
        tool_layout = QFormLayout()
        tool_layout.setContentsMargins(5,5,5,5)
        tool_layout.setSpacing(0)
        tool_layout.addRow(gf.QRichLabel("--- File Actions ---", font=gf.boldFont))
        tool_layout.addRow(btnOpenWindow, QLabel(" open window"))
        tool_layout.addRow(btnCloseWindow, QLabel(" close window"))
        tool_layout.addRow(btnSaveImages, QLabel(" save images"))
        tool_layout.addRow(btnSaveSpectrum, QLabel(" save spectrum"))
        tool_layout.addRow(btnSaveTarget, QLabel(" save spectrum"))
        tool_layout.addRow(btnExportData, QLabel(" export data"))
        tool_layout.addRow(gf.QRichLabel("--- Preprocess Actions ---", font=gf.boldFont))
        tool_layout.addRow(btnCosmicRayRemoval, QLabel(" cosmic ray removal"))
        tool_layout.addRow(btnNoiseFilterPCA, QLabel(" PCA based noise filter"))
        tool_layout.addRow(gf.QRichLabel("\n--- Data Actions 1 ---", font=gf.boldFont))
        tool_layout.addRow(btnSetPOI, QLabel(" set position of interest"))
        tool_layout.addRow(btnGoToPOI, QLabel(" go to position of interest"))
        tool_layout.addRow(btnSignalIntensity, QLabel(" signal intensity"))
        tool_layout.addRow(btnSignalToBaseline, QLabel(" signal to baseline"))
        tool_layout.addRow(btnSianglToHorizontalBaseline, QLabel(" signal to horizontal line"))
        tool_layout.addRow(btnSignalToAxis, QLabel(" signal to axis"))
        tool_layout.addRow(btnAddCurrentSpectrum, QLabel(" add current spectrum"))
        tool_layout.addRow(gf.QRichLabel("\n--- Data Actions 2 ---", font=gf.boldFont))
        tool_layout.addRow(btnSpectrumSubtraction, QLabel(" spectrum subtraction"))
        tool_layout.addRow(btnUMX, QLabel(" spectrum unmixing"))
        tool_layout.addRow(btnImportedPlugins, QLabel(" imported plugins"))
        tool_layout.addRow(btnExecuteProcedures, QLabel(" execute procedures"))
        tool_layout.addRow(gf.QRichLabel("\n--- View Actions ---", font=gf.boldFont))
        tool_layout.addRow(btnShowSpectrumWithMaxInt, QLabel(" show spectrum with max intensity"))
        tool_layout.addRow(btnSetSpcRange, QLabel(" set spectrum range"))
        tool_layout.addRow(btnSetMapImageContrast, QLabel(" set map image contrast"))
        tool_layout.addRow(btnSetWindowSize, QLabel(" set window size"))
        tool_layout.addRow(btnHideAllInVb2, QLabel(" hide all items in view box 2"))
        tool_layout.addRow(btnHideRightAxis, QLabel("hide right axis for view box 2"))
        # execute
        execute_layout = QHBoxLayout()
        execute_layout.setContentsMargins(0,0,0,0)
        execute_layout.setSpacing(0)
        execute_layout.addStretch(1)
        execute_layout.addWidget(btnMoveUp)
        execute_layout.addWidget(btnRemove)
        execute_layout.addWidget(btnMoveDown)
        execute_layout.addSpacerItem(my_w.CustomSpacer(width=15))
        execute_layout.addWidget(btnRUN)
        # layout
        tools_inside_widget = QWidget()
        tools_inside_widget.setLayout(tool_layout)
        tools_scroll_area = QScrollArea()
        tools_scroll_area.setWidgetResizable(True)
        tools_scroll_area.setMinimumWidth(200)
        tools_scroll_area.setWidget(tools_inside_widget)
        tools_scroll_area.focusInEvent = self.focusInEvent
        tools_area_layout = QVBoxLayout()
        tools_area_layout.addWidget(gf.QRichLabel("Available Actions (click icon)", font=gf.boldFont))
        tools_area_layout.addWidget(tools_scroll_area)
        # 右部バッチエリア
        inside_widget = QWidget()
        inside_widget.setLayout(self.process_layout)
        inside_widget.setObjectName("inside_widget")
        inside_widget.setStyleSheet("QWidget#inside_widget{background-color: white}")
        batch_scroll_area = QScrollArea()
        batch_scroll_area.setWidgetResizable(True)
        batch_scroll_area.setMinimumWidth(400)
        batch_scroll_area.setWidget(inside_widget)
        batch_scroll_area.focusInEvent = self.focusInEvent
        batch_area_layout = QVBoxLayout()
        # batch_area_layout.setSpacing(5)
        batch_area_layout.addWidget(gf.QRichLabel("Action Flow for every *.spc files", font=gf.boldFont))
        batch_area_layout.addWidget(batch_scroll_area)
        batch_area_layout.addLayout(execute_layout)
        # 全体
        sub_layout = QHBoxLayout()
        sub_layout.addLayout(tools_area_layout)
        sub_layout.addLayout(batch_area_layout)
        layout = QVBoxLayout()
        layout.addLayout(batch_path_selection_layout)
        layout.addLayout(sub_layout)
        # self.setMinimumSize(gf.batch_window_min_width, gf.batch_window_min_height)
        self.setLayout(layout)
        # イベントコネクト
        btnOpenWindow.clicked.connect(self.btnOpenWindow_clicked)
        btnCloseWindow.clicked.connect(self.btnCloseW_clicked)
        btnSetPath.clicked.connect(self.btnSetPath_clicked)
        btnSetPOI.clicked.connect(self.btnSetPOI_clicked)
        btnGoToPOI.clicked.connect(self.btnGoToPOI_clicked)
        btnSetSpcRange.clicked.connect(self.btnSetSpcRange_clicked)
        btnShowSpectrumWithMaxInt.clicked.connect(self.btnShowSpectrumWithMaxInt_clicked)
        btnSetMapImageContrast.clicked.connect(self.btnSetMapImageContrast_clicked)
        btnSignalIntensity.clicked.connect(self.btnSignalIntensity_clicked)
        btnSignalToBaseline.clicked.connect(self.btnSignalToBaseline_clicked)
        btnSianglToHorizontalBaseline.clicked.connect(self.SianglToHorizontalBaseline_clicked)
        btnSignalToAxis.clicked.connect(self.btnSignalToAxis_clicked)
        btnAddCurrentSpectrum.clicked.connect(self.btnAddCurrentSpectrum_clicked)
        btnSpectrumSubtraction.clicked.connect(self.btnSpectrumSubtraction_clicked)
        btnUMX.clicked.connect(self.btnUMX_clicked)
        btnSaveImages.clicked.connect(self.btnSaveImages_clicked)
        btnSaveSpectrum.clicked.connect(self.btnSaveSpectrum_clicked)
        btnSaveTarget.clicked.connect(self.btnSaveTarget_clicked)
        btnCosmicRayRemoval.clicked.connect(self.btnCosmicRayRemoval_clicked)
        btnNoiseFilterPCA.clicked.connect(self.btnNoiseFilterPCA_clicked)
        btnSetWindowSize.clicked.connect(self.btnSetWindowSize_clicked)
        btnExportData.clicked.connect(self.btnExportData_clicked)
        btnImportedPlugins.clicked.connect(self.btnImportedPlugins_clicked)
        btnExecuteProcedures.clicked.connect(self.btnExecuteProcedures_clicked)
        btnHideAllInVb2.clicked.connect(self.btnHideAllInVb2_clicked)
        btnHideRightAxis.clicked.connect(self.btnHideRightAxis_clicked)
        btnRUN.clicked.connect(self.btnRUN_clicked)
        btnRemove.clicked.connect(self.btnRemove_clicked)
        btnMoveUp.clicked.connect(self.btnMoveUp_clicked)
        btnMoveDown.clicked.connect(self.btnMoveDown_clicked)
    def focusInEvent(self, event):
        self.parent.focusChanged(self)
    def focusOutEvent(self, event):
        pass
    # プロセス系ボタン
    def btn_clicked(func):
        def _wrapper(self, *args, **kwargs):
            each_layout, object_name = func(self, *args, **kwargs)
            each_layout.setObjectName(object_name)
            each_layout.setStyleSheet("QWidget#%s{border: 1px solid gray; background-color: lightGray}"%object_name)
            self.process_layout.insertWidget(self.process_layout.count() - 1, each_layout)
        return _wrapper
    @btn_clicked
    def btnOpenWindow_clicked(self, event):
        return OpenWindow(parent=self.process_layout, main_window=self.parent), "OW"
    @btn_clicked
    def btnCloseW_clicked(self, event):
        return CloseWindow(parent=self.process_layout, main_window=self.parent), "CW"
    @btn_clicked
    def btnSetPOI_clicked(self, event):
        return PositionOfInterestSettings(parent=self.process_layout, main_window=self.parent), "CFP"
    @btn_clicked
    def btnGoToPOI_clicked(self, event):
        return GoToPositionOfInterest(parent=self.process_layout, main_window=self.parent), "CFP"
    @btn_clicked
    def btnSetSpcRange_clicked(self, event):
        return SetSpectrumRange(parent=self.process_layout, main_window=self.parent), "SSR"
    @btn_clicked
    def btnShowSpectrumWithMaxInt_clicked(self, event):
        return ShowSpectrumWithMaxInt(parent=self.process_layout, main_window=self.parent), "SMS"
    @btn_clicked
    def btnSetMapImageContrast_clicked(self, event):
        return SetMapImageContrast(parent=self.process_layout, main_window=self.parent), "SIC"
    @btn_clicked
    def btnSignalIntensity_clicked(self, event):
        return SignalIntensity(parent=self.process_layout, main_window=self.parent), "SINT"
    @btn_clicked
    def btnSignalToBaseline_clicked(self, event):
        return SignalToBaseline(parent=self.process_layout, main_window=self.parent), "STB"
    @btn_clicked
    def SianglToHorizontalBaseline_clicked(self, event):
        return SianglToHorizontalBaseline(parent=self.process_layout, main_window=self.parent), "STHB"
    @btn_clicked
    def btnSignalToAxis_clicked(self, event):
        return SignalToAxis(parent=self.process_layout, main_window=self.parent), "STA"
    @btn_clicked
    def btnAddCurrentSpectrum_clicked(self, event):
        return AddCurrentSpectrum(parent=self.process_layout, main_window=self.parent), "ACS"
    @btn_clicked
    def btnSpectrumSubtraction_clicked(self, event):
        return SpectrumSubtraction(parent=self.process_layout, main_window=self.parent), "SSB"
    @btn_clicked
    def btnUMX_clicked(self, event):
        return BatchUnmixing(parent=self.process_layout, main_window=self.parent), "UMX"
    @btn_clicked
    def btnSaveImages_clicked(self, event):
        return SaveImages(parent=self.process_layout, main_window=self.parent), "SI"
    @btn_clicked
    def btnSaveSpectrum_clicked(self, event):
        return SaveSpectrum(parent=self.process_layout, main_window=self.parent), "SS"
    @btn_clicked
    def btnSaveTarget_clicked(self, event):
        return SaveTarget(parent=self.process_layout, main_window=self.parent), "SS"
    @btn_clicked
    def btnCosmicRayRemoval_clicked(self, event):
        return CosmicRayRemoval(parent=self.process_layout, main_window=self.parent), "CRR"
    @btn_clicked
    def btnNoiseFilterPCA_clicked(self, event):
        return NoiseFilterPCA(parent=self.process_layout, main_window=self.parent), "CRR"
    @btn_clicked
    def btnSetWindowSize_clicked(self, event):
        return SetWindowSize(parent=self.process_layout, main_window=self.parent), "SWS"
    @btn_clicked
    def btnExportData_clicked(self, event):
        return ExportData(parent=self.process_layout, main_window=self.parent), "EXD"
    @btn_clicked
    def btnImportedPlugins_clicked(self, event):
        return ImportedPlugins(parent=self.process_layout, main_window=self.parent), "SWS"
    @btn_clicked
    def btnExecuteProcedures_clicked(self, event):
        return ExecuteProcedures(parent=self.process_layout, main_window=self.parent), "EXP"
    @btn_clicked
    def btnHideAllInVb2_clicked(self, event):
        return HideAllInVb2(parent=self.process_layout, main_window=self.parent), "HV2"
    @btn_clicked
    def btnHideRightAxis_clicked(self, event):
        return HideRightAxis(parent=self.process_layout, main_window=self.parent), "HRA"
    # その他のボタン押された場合
    def btnSetPath_clicked(self, event):
        dir_path = QFileDialog.getExistingDirectory(self, 'select folder', gf.settings["last opened dir"])
        if len(dir_path):
            self.path_entry.setText(dir_path)
    def btnRemove_clicked(self, event):
        self.process_layout.remove_current_focused_item(new_focus=True)
    def btnMoveUp_clicked(self, event):
        self.process_layout.moveUp_current_focused_item()
    def btnMoveDown_clicked(self, event):
        self.process_layout.moveDown_current_focused_item()
    def btnRUN_clicked(self, event):
        self.parent.temp_variables = {}
        if self.process_layout.count() == 1:
            warning_popup = popups.WarningPopup("No action to process.")
            warning_popup.exec_()
            return
        dir_path = self.path_entry.text()
        if dir_path == "":
            return
        # ファイルごとに回す
        spc_path_list = glob.glob("%s/**/*.spc"%dir_path, recursive=True)
        for spc_path in spc_path_list:

            # if spc_path.endswith("_FL_2.spc") or spc_path.endswith("_FL.spc"):
            #     pass
            # else:
            #     continue

            # 開いたファイルは、次のプロセスで受け取ることができる
            opened_window = None
            for idx in range(self.process_layout.count() - 1):
                QCoreApplication.processEvents()
                try:
                    opened_window, continue_process = self.process_layout.itemAt(idx).widget().procedure(spc_path, opened_window)
                except:
                    continue_process = traceback.format_exc()
                    break
                if continue_process == "continue":
                    pass    # 次のプロセスへ
                else:
                    break   # 現在のプロセスを中断
            else:
                continue    # ループ正常終了時 -> 次のファイルへ
            # ループ異常終了時
            if continue_process == "skip":
                continue    # 次のファイルへ
            else:
                break       # バッチそのものを終了
        # ループ正常終了時
        else:
            warning_popup = popups.WarningPopup("Successfully completed d(^^)b", icon=0)
            warning_popup.exec_()
            self.parent.temp_variables = {}
            return
        # ループ異常終了時
        warning_popup = popups.WarningPopup(continue_process + "\nProcess was canceled.")
        warning_popup.exec_()
        self.parent.temp_variables = {}
        return
def closeEvent(self, event=None):
    event.accept()

class OpenWindow(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type="OW"
        self.option = {}
        # オプション
        self.window_type = QComboBox()
        self.window_type.addItems(["1 spectrum data", "all hyperspectral data", "size unknown data", "all '*.spc' data"])
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("open window"))
        self.layout.addStretch(1)
        self.layout.addWidget(self.window_type)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        # サイズがサイズが未設定の hyper spectrum data のみを開く
        if self.window_type.currentText() == "size unknown data":
            # バイナリを読む（その方が早いから）
            with open(spc_path,'rb') as f:
                f.seek(-1000, 2) # 2: 末尾から読む
                matchedObject_list = list(re.finditer(b"\n\[map_size\]\r\nmap_x=[0-9]+\r\nmap_y=[0-9]+\r\nmap_z=[0-9]+\r\n\[map_size\]\r\n", f.read(), flags=0))
            # サイズ指定されていない場合、開く
            if len(matchedObject_list) == 0:
                self.main_window.just_open(spc_path)
                opened_window = self.main_window.child_window_list[-1]
                # map spectrum data でない場合は開かない
                if opened_window.window_type != "ms":
                    opened_window.close()
                    return None, "skip"
                return opened_window, "continue"
            else:
                return None, "skip"
        # とりあえず開く
        self.main_window.just_open(spc_path)
        opened_window = self.main_window.child_window_list[-1]
        # ターゲットの window でない場合は、閉じて次へ
        if ((opened_window.window_type == "s") and (self.window_type.currentText() == "all hyperspectral data")) or \
            ((opened_window.window_type == "ms") and (self.window_type.currentText() == "1 spectrum data")):
            opened_window.close()
            return None, "skip"
        return opened_window, "continue"
class CloseWindow(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "CW"
        self.option = {}
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("close window"))
        self.layout.addStretch(1)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'close window' action. No window is opened."
        opened_window.close()
        return None, "continue"
class PositionOfInterestSettings(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "POI"
        self.title = "set position of interest"
        # コンテンツ
        self.default_name = QLineEdit("default_name")
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.default_name)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'set position of interest' action. No window is opened."
        if opened_window.window_type == "ms":
            # poi 設定（イベントループ）
            continue_process = ["continue"]   # closeEvent関数内で、参照渡しできるように、リストにしておく。
            loop = QEventLoop()
            def closeEvent1(self, event=None):
                bool_popup = popups.WarningPopup("Closing the window will stop the batch.\nDo you really want to close?", title="warning", p_type="Bool")
                done = bool_popup.exec_()
                if done == 0x00004000:      # Yes
                    continue_process[0] = "Position of interest was not set."
                    self.toolbar_layout.poi_settings_popup.close()
                    event.accept()
                    loop.exit()
                elif done == 0x00010000:    # No
                    event.ignore()
            def closeEvent2(self, event=None):
                close_or_not = opened_window.close()
                if close_or_not:
                    event.accept()
                else:
                    event.ignore()
            def cancelEvent():
                close_or_not = opened_window.close()
                if close_or_not:
                    loop.exit()
                else:
                    opened_window.toolbar_layout.set_POI_fm_macro(poi_key=self.default_name.text())
            def okEvent():
                is_exit = opened_window.toolbar_layout.poi_settings_popup_ok_clicked()
                if is_exit:
                    loop.exit()
            opened_window.closeEvent = closeEvent1.__get__(opened_window, type(opened_window))
            result = opened_window.toolbar_layout.set_POI_fm_macro(poi_key=self.default_name.text())
            # position of interest が指定された時
            if result:
                pass
            # cell free position の window で cancel された時
            else:
                opened_window.closeEvent = closeEvent.__get__(opened_window, type(opened_window))
                loop.exit(0)
                return None, "Position of interest was not set."
            opened_window.toolbar_layout.poi_settings_popup.closeEvent = closeEvent2.__get__(opened_window.toolbar_layout.poi_settings_popup, type(opened_window.toolbar_layout.poi_settings_popup))
            # opened_window.toolbar_layout.poi_settings_popup.btnOK.clicked.connect(lambda future: loop.exit())
            opened_window.toolbar_layout.poi_settings_popup.btnCancel.clicked.connect(cancelEvent)
            opened_window.toolbar_layout.poi_settings_popup.btnOK.clicked.connect(okEvent)
            loop.exec_()
            opened_window.closeEvent = closeEvent.__get__(opened_window, type(opened_window))
            return opened_window, continue_process[0]
        else:
            # opened_window.close()
            return None, "Invalid window type."
class GoToPositionOfInterest(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "POI"
        self.title = "set position of interest"
        # コンテンツ
        self.poi_key = QLineEdit("poi_name")
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.poi_key)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'set position of interest' action. No window is opened."
        if opened_window.window_type == "ms":
            poi_key = self.poi_key.text()
            poi_info = opened_window.toolbar_layout.get_poi_info_from_POI_manager(poi_key=poi_key)
            if poi_info is None:
                return None, "Position Of Interest named '{0}' was not found.".format(poi_key)
            opened_window.toolbar_layout.set_spectrum_and_crosshair(*poi_info.poi_data)
            return opened_window, "continue"
        else:
            # opened_window.close()
            return None, "Invalid window type."
class ShowSpectrumWithMaxInt(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "SMS"
        self.title = "show spectrum with max. int."
        self.option = {}
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("show spectrum with max. int."))
        self.layout.addStretch(1)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'show spectrum with max intensity' action. No window is opened."
        if opened_window.window_type == "ms":
            if opened_window.cur_displayed_map_content is None:
                return None, "Error in 'show spectrum with max intensity' action.\nImages must be set before showing spectrum with max intensity."
            cur_image2d = opened_window.cur_displayed_map_content.item.image2d
            max_loc = np.unravel_index(np.argmax(cur_image2d), cur_image2d.shape)
            opened_window.spectrum_widget.replace_spectrum(*max_loc)
            opened_window.map_widget.set_crosshair(*max_loc)
            return opened_window, "continue"
        else:
            # opened_window.close()
            return None, "Invalid window type."
class SetSpectrumRange(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "SSR"
        self.option = {}
        # コンテンツ
        self.cmb = QComboBox()
        self.cmb.addItems(["x", "y"])
        self.RS_left = QSpinBox()
        self.RS_right = QSpinBox()
        self.RS_left.setMaximum(65535)
        self.RS_left.setMinimum(-65535)
        self.RS_right.setMaximum(65535)
        self.RS_right.setMinimum(-65535)
        self.RS_left.setValue(1800)
        self.RS_right.setValue(2500)
        self.y_btm = QComboBox()
        self.y_btm.addItems(["AUTO", "0"])
        self.y_top = QComboBox()
        self.y_top.addItems(["AUTO"])
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("set spectrum range"))
        self.layout.addStretch(1)
        self.layout.addWidget(self.cmb)
        self.layout.addWidget(self.RS_left)
        self.layout.addWidget(self.RS_right)
        self.layout.addWidget(self.y_btm)
        self.layout.addWidget(self.y_top)
        self.cmb_changed(event="x")
        self.setFixedHeight(gf.process_widget_height)
        # イベントコネクト
        self.cmb.currentTextChanged.connect(self.cmb_changed)
    def hide_all(self):
        self.RS_left.hide()
        self.RS_right.hide()
        self.y_btm.hide()
        self.y_top.hide()
    def cmb_changed(self, event):
        self.hide_all()
        if event == "x":
            self.RS_left.show()
            self.RS_right.show()
        elif event == "y":
            self.y_btm.show()
            self.y_top.show()
        else:
            raise Exception("unknown kwargs")
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'set spectrum range' action. No window is opened."
        RS_left = self.RS_left.value()
        RS_right = self.RS_right.value()
        x_range, y_range = opened_window.spectrum_widget.plotItem.vb.viewRange()
        # XRange：なぜか 1 回だけではちゃんと範囲設定されない…
        if self.cmb.currentText() == "x":
            while opened_window.spectrum_widget.plotItem.vb.viewRange()[0] != [RS_left, RS_right]:
                opened_window.spectrum_widget.plotItem.vb.setXRange(min=RS_left, max=RS_right, padding=0)
        # YRange：なぜか 1 回だけではちゃんと範囲設定されない…
        elif self.cmb.currentText() == "y":
            xData = opened_window.spectrum_widget.master_spectrum.xData
            yData = opened_window.spectrum_widget.master_spectrum.yData
            local_y_min, local_y_max = gf.get_local_minmax(xData, yData, x_range)
            print(self.y_btm.currentText())
            if self.y_btm.currentText() == "0":
                btm_value = 0
                top_value = local_y_max + local_y_min
            elif self.y_btm.currentText() == "AUTO":
                btm_value = local_y_min
                top_value = local_y_max
            else:
                raise Exception("unkwon selection")
            # calc padding
            xpad = opened_window.spectrum_widget.plotItem.vb.suggestPadding(1) # 1 means height
            p = (top_value - btm_value) * xpad
            btm_padded = btm_value - p
            top_padded = top_value + p
            while opened_window.spectrum_widget.plotItem.vb.viewRange()[1] != [btm_padded, top_padded]:
                opened_window.spectrum_widget.plotItem.vb.setYRange(min=btm_value, max=top_value)
        return opened_window, "continue"
class SetMapImageContrast(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "SIC"
        self.option = {}
        # オプション
        self.range_bottom =  QSpinBox()
        self.range_top =  QSpinBox()
        self.range_bottom.setMinimum(0)
        self.range_top.setMinimum(0)
        self.range_bottom.setMaximum(65535)
        self.range_top.setMaximum(65535)
        self.range_bottom.setValue(0)
        self.range_top.setValue(65535)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("set map image contrast"))
        self.layout.addStretch(1)
        self.layout.addWidget(self.range_bottom)
        self.layout.addWidget(self.range_top)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'set map image contrast' action. No window is opened."
        if opened_window.window_type == "ms":
            if opened_window.map_widget.ContrastConfigurator is None:
                return None, "Error in 'set map image contrast' action.\nImages must be created before setting contrast."
            if not opened_window.map_widget.ContrastConfigurator.FIX:
                opened_window.map_widget.ContrastConfigurator.btn_fix_pressed()
            opened_window.map_widget.ContrastConfigurator.setRange(self.range_bottom.value(), self.range_top.value())
            return opened_window, "continue"
        else:
            # opened_window.close()
            return opened_window, "Invalid window type."
class SignalIntensity(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "STB"
        self.option = {}
        # オプション
        self.RS_val =  QSpinBox()
        self.RS_val.setMinimum(0)
        self.RS_val.setMaximum(65535)
        self.RS_val.setValue(2950)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("signal intensity"))
        self.layout.addStretch(1)
        self.layout.addWidget(self.RS_val)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'signal intensity' action. No window is opened."
        if opened_window.window_type == "ms":
            opened_window.toolbar_layout.execute_signal_intensity(ask=False, RS=self.RS_val.value())
            return opened_window, "continue"
        else:
            # opened_window.close()
            return opened_window, "Invalid window type."
class SignalToBaseline(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "STB"
        self.option = {}
        # オプション
        self.range_bottom =  QSpinBox()
        self.range_top =  QSpinBox()
        self.range_bottom.setMinimum(0)
        self.range_top.setMinimum(0)
        self.range_bottom.setMaximum(65535)
        self.range_top.setMaximum(65535)
        self.range_bottom.setValue(1900)
        self.range_top.setValue(2500)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("signal to baseline"))
        self.layout.addStretch(1)
        self.layout.addWidget(self.range_bottom)
        self.layout.addWidget(self.range_top)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'signal to baseline' action. No window is opened."
        if opened_window.window_type == "ms":
            opened_window.toolbar_layout.execute_signal_to_baseline(ask=False, RS_set=[self.range_bottom.value(), self.range_top.value()])
            return opened_window, "continue"
        else:
            # opened_window.close()
            return opened_window, "Invalid window type."
class SianglToHorizontalBaseline(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "STHB"
        self.option = {}
        # オプション
        self.range_bottom =  QSpinBox()
        self.range_top =  QSpinBox()
        self.range_bottom.setMinimum(0)
        self.range_top.setMinimum(0)
        self.range_bottom.setMaximum(65535)
        self.range_top.setMaximum(65535)
        self.range_bottom.setValue(1900)
        self.range_top.setValue(2500)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("signal to horizontal baseline"))
        self.layout.addStretch(1)
        self.layout.addWidget(self.range_bottom)
        self.layout.addWidget(self.range_top)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'signal to horizontal baseline' action. No window is opened."
        if opened_window.window_type == "ms":
            opened_window.toolbar_layout.execute_signal_to_H_baseline(ask=False, RS_set=[self.range_bottom.value(), self.range_top.value()])
            return opened_window, "continue"
        else:
            # opened_window.close()
            return opened_window, "Invalid window type."
class SignalToAxis(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "STA"
        self.option = {}
        # オプション
        self.range_bottom =  QSpinBox()
        self.range_top =  QSpinBox()
        self.range_bottom.setMinimum(0)
        self.range_top.setMinimum(0)
        self.range_bottom.setMaximum(65535)
        self.range_top.setMaximum(65535)
        self.range_bottom.setValue(1900)
        self.range_top.setValue(2500)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("signal to axis"))
        self.layout.addStretch(1)
        self.layout.addWidget(self.range_bottom)
        self.layout.addWidget(self.range_top)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'signal to axis' action. No window is opened."
        if opened_window.window_type == "ms":
            opened_window.toolbar_layout.execute_signal_to_axis(ask=False, RS_set=[self.range_bottom.value(), self.range_top.value()])
            return opened_window, "continue"
        else:
            # opened_window.close()
            return opened_window, "Invalid window type."
class AddCurrentSpectrum(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "ACS"
        self.title = "add current spectrum"
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'add current spectrum' action. No window is opened."
        if opened_window.window_type == "ms":
            opened_window.toolbar_layout.add_current_spectrum()
            return opened_window, "continue"
        else:
            return opened_window, "Invalid window type."
class SpectrumSubtraction(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "SSB"
        self.option = {}
        # オプション
        self.ckbx = QCheckBox("to zero   ")
        self.range_bottom =  QSpinBox()
        self.range_top =  QSpinBox()
        self.range_bottom.setMinimum(0)
        self.range_top.setMinimum(0)
        self.range_bottom.setMaximum(65535)
        self.range_top.setMaximum(65535)
        self.range_bottom.setValue(1900)
        self.range_top.setValue(2500)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("subtract spectrum"))
        self.layout.addStretch(1)
        self.layout.addWidget(self.ckbx)
        self.layout.addWidget(self.range_bottom)
        self.layout.addWidget(self.range_top)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'subtract spectrum' action. No window is opened."
        if opened_window.window_type in ["ms", "s"]:
            log = opened_window.toolbar_layout.execute_spectrum_linear_subtraction(
                event=None, 
                mode="macro", 
                range=[self.range_bottom.value(), self.range_top.value()], 
                to_zero=self.ckbx.isChecked()
                )
            if log == "executed":
                return opened_window, "continue"
            else:
                return opened_window, "Not executed."
        else:
            return opened_window, "Invalid window type."
class BatchUnmixing(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "UMX"
        self.title = "unmixing"
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("unmixing"))
        self.layout.addStretch(1)
        self.setFixedHeight(gf.process_widget_height)
class SaveImages(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "SI"
        self.option = {}
        # オプション
        self.image_type = QComboBox()
        bit_list = [8, 16, 32]
        appendix_list = ["int", "int", "float"]
        for bit, appendix in zip(bit_list, appendix_list):
            self.image_type.addItem("{0}-bit ({1})".format(str(bit), appendix), bit)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("save images (and unmixed spctrum)"))
        self.layout.addStretch(1)
        self.addWidget(self.image_type)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'save images' action. No window is opened."
        if opened_window.window_type == "ms":
            bit = self.image_type.itemData(self.image_type.currentIndex(), role=Qt.UserRole)
            opened_window.map_widget.ContrastConfigurator.BIT = bit
            opened_window.toolbar_layout.save_all_maps()
            return opened_window, "continue"
        else:
            # opened_window.close()
            return opened_window, "Invalid window type."
class SaveSpectrum(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "SS"
        self.option = {}
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("save spectrum"))
        self.layout.addStretch(1)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'save spectrum' action. No window is opened."
        opened_window.toolbar_layout.save_spectrum()
        return opened_window, "continue"
class SaveTarget(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "ST"
        self.option = {}
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("save target"))
        self.layout.addStretch(1)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'save spectrum' action. No window is opened."
        opened_window.toolbar_layout.save_target()
        return opened_window, "continue"
class CosmicRayRemoval(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "CRR"
        self.option = {}
        # オプション
        self.crr_target_files = QComboBox()
        self.crr_target_files.addItems(["skip action when possible", "skip files with CRR data", "execute for all"])
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("cosmic ray removal"))
        self.layout.addStretch(1)
        self.layout.addWidget(self.crr_target_files)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'cosmic ray removal' action. No window is opened."
        if opened_window.window_type == "ms":
            if b'[CRR]' in opened_window.spectrum_widget.spc_file.log_other:
                if self.crr_target_files.currentText() == "skip files with CRR data":
                    opened_window.close()
                    return None, "skip"
                if self.crr_target_files.currentText() == "skip action when possible":
                    return opened_window, "continue"
            # PreProcess はお尻からしか消せないので、消していく。そうでない場合は消す必要なし。
            if b'[CRR]' in opened_window.spectrum_widget.spc_file.log_other:
                for func_name, kwargs in opened_window.spectrum_widget.spc_file.log_dict[b"prep_order"][::-1]:
                    if func_name == "CRR_master":
                        del opened_window.toolbar_layout.added_content_preprocess_list[-1]
                        break
                    elif func_name == "NR_master":
                        opened_window.toolbar_layout.revert_NR()
                        del opened_window.toolbar_layout.added_content_preprocess_list[-1]
                    else:
                        print(func_name)
                        raise Exception("unknown preprocesses")
            opened_window.parent.map_spect_table.window_focus_changed(opened_window)
            QCoreApplication.processEvents()
            opened_window.toolbar_layout.CRR_master(mode="macro", params={})
            return opened_window, "continue"
        else:
            # opened_window.close()
            return opened_window, "Invalid window type."
class NoiseFilterPCA(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "NF"
        self.option = {}
        # オプション
        self.nr_target_files = QComboBox()
        self.nr_target_files.addItems(["skip action when possible", "skip files with NR data", "execute for all"])
        self.N_components = QSpinBox()
        self.N_components.setMinimum(0)
        self.N_components.setMaximum(65535)
        self.N_components.setValue(100)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("PCA based noise filter"))
        self.layout.addStretch(1)
        self.layout.addWidget(self.N_components)
        self.layout.addWidget(self.nr_target_files)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'PCA based noise filter' action. No window is opened."
        if opened_window.window_type == "ms":
            if b'[NR]' in opened_window.spectrum_widget.spc_file.log_other:
                if self.nr_target_files.currentText() == "skip files with NR data":
                    opened_window.close()
                    return None, "skip"
                if self.nr_target_files.currentText() == "skip action when possible":
                    return opened_window, "continue"
            # PreProcess はお尻からしか消せないので、消していく。そうでない場合は消す必要なし。
            if b'[NR]' in opened_window.spectrum_widget.spc_file.log_other:
                for func_name, kwargs in opened_window.spectrum_widget.spc_file.log_dict[b"prep_order"][::-1]:
                    if func_name == "NR_master":
                        del opened_window.toolbar_layout.added_content_preprocess_list[-1]
                        break
                    elif func_name == "CRR_master":
                        opened_window.toolbar_layout.revert_CRR()
                        del opened_window.toolbar_layout.added_content_preprocess_list[-1]
                    else:
                        print(func_name)
                        raise Exception("unknown preprocesses")
            opened_window.parent.map_spect_table.window_focus_changed(opened_window)
            QCoreApplication.processEvents()
            opened_window.toolbar_layout.NR_master(mode="macro", params={"N_components":self.N_components.value()})
            return opened_window, "continue"
        else:
            # opened_window.close()
            return opened_window, "Invalid window type."
class SetWindowSize(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "SWS"
        self.option = {}
        # オプション
        self.w = QSpinBox()
        self.w.setMinimum(0)
        self.w.setMaximum(65535)
        self.w.setValue(0)
        self.h = QSpinBox()
        self.h.setMinimum(0)
        self.h.setMaximum(65535)
        self.h.setValue(0)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("set window size"))
        self.layout.addStretch(1)
        self.layout.addWidget(QLabel("width:"))
        self.layout.addWidget(self.w)
        self.layout.addWidget(QLabel("height:"))
        self.layout.addWidget(self.h)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'set window size' action. No window is opened."
        width = self.w.value()
        height = self.h.value()
        if width == 0:
            width = opened_window.frameGeometry().width()
        if height == 0:
            height = opened_window.frameGeometry().height()
        opened_window.resize(width, height)
        return opened_window, "continue"
class ExportData(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "EXD"
        self.option = {}
        # オプション
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["added", "unmixed", "subtracted", "original"])
        self.cmb_type.setItemData
        self.cmb_content = QComboBox()
        self.cmb_content.addItems(["spectrum", "map"])
        self.cmb_content = QComboBox()
        self.cmb_content.addItems(["spectrum", "map"])
        self.cmb_export = QComboBox()
        self.cmb_export.addItems(["as spc", "as txt", "as info"])
        self.cmb_export.setItemData(0, ["export_spectrum", {"ext":".spc", "ask":False}])
        self.cmb_export.setItemData(1, ["export_spectrum", {"ext":".txt", "ask":False}])
        self.cmb_export.setItemData(2, ["export_information", {"ext":".info", "ask":False}])
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("export data"))
        self.layout.addStretch(1)
        self.layout.addWidget(self.cmb_type)
        self.layout.addWidget(self.cmb_content)
        self.layout.addWidget(self.cmb_export)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'export data' action. No window is opened."
        command = "{0} {1}".format(self.cmb_type.currentText(), self.cmb_content.currentText())
        target_content_list = getattr(opened_window.toolbar_layout, "added_content_{0}_list".format(self.cmb_content.currentText()))
        idx = self.cmb_export.currentIndex()
        # spc, txt の場合
        if self.cmb_export.itemData(idx)[0] == "export_spectrum":
            for added_content in target_content_list:
                print(command,  added_content.content_type())
                if command != added_content.content_type():
                    continue
                func = getattr(added_content, self.cmb_export.itemData(idx)[0])
                func(**self.cmb_export.itemData(idx)[1])
        # information の場合
        elif self.cmb_export.itemData(idx)[0] == "export_information":
            processed_abs_idxes = []
            # spectrum
            for added_content in target_content_list:
                if command != added_content.content_type():
                    continue
                abs_id = added_content.info["data"][2].abs_id
                if abs_id in processed_abs_idxes:
                    continue
                processed_abs_idxes.append(abs_id)
                func = getattr(added_content, self.cmb_export.itemData(idx)[0])
                func(**self.cmb_export.itemData(idx)[1], **opened_window.parent.map_spect_table.get_standard_info_list_s(abs_id))
        else:
            print(command)
            raise Exception("unknown command")
        return opened_window, "continue"
class ImportedPlugins(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "IP"
        self.option = {}
        # オプション
        self.action_type = QComboBox()
        action_list = self.main_window.imported_plugins.actions()
        for action in action_list:
            action_name = action.iconText()
            self.action_type.addItem(action_name, action)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("imported plugins"))
        self.layout.addStretch(1)
        self.layout.addWidget(self.action_type)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'imported plugins' action. No window is opened."
        action_idx = self.action_type.currentIndex()
        cur_action = self.action_type.itemData(action_idx, role=Qt.UserRole)
        cur_action.trigger()
        QCoreApplication.processEvents()
        # window が閉じられていた場合、skipと判断、そうでない場合は continue
        try:
            opened_window.isVisible()
            return opened_window, "continue"
        except RuntimeError:
            return None, "skip"
class ExecuteProcedures(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "EXP"
        self.title = "execute procedures"
        self.option = {}
        # オプション中身
        self.path_entry = QLineEdit()
        self.path_entry.setText("method ('*.umx') path")
        btnSetPath = QPushButton("...")
        btnSetPath.clicked.connect(self.btnSetPath_clicked)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("execute procedures"))
        self.layout.addStretch(1)
        self.layout.addWidget(self.path_entry)
        self.layout.addWidget(btnSetPath)
        self.setFixedHeight(gf.process_widget_height)
    def btnSetPath_clicked(self, event):
        file_path, file_type = QFileDialog.getOpenFileName(self, 'select procedure file', gf.settings["last opened dir"], filter="procedure file (*.umx)")
        if len(file_path):
            self.path_entry.setText(file_path)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'execute procedures' action. No window is opened."
        if opened_window.window_type in ("ms", "s"):
            opened_window.toolbar_layout.execute_saved_procedures(event=None, file_path=self.path_entry.text())
            return opened_window, "continue"
        else:
            # opened_window.close()
            return None, "Invalid window type."
class HideAllInVb2(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "HV2"
        self.option = {}
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("hide all items in view box 2"))
        self.layout.addStretch(1)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'hide all items in view box 2' action. No window is opened."
        opened_window.toolbar_layout.hide_all_in_v2(var_name="pseudo")
        return opened_window, "continue"
class HideRightAxis(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "HRA"
        self.option = {}
        # オプション
        self.cmb_hide_show = QComboBox()
        self.cmb_hide_show.addItems(["hide", "show"])
        self.cmb_hide_show.setItemData(0, False)
        self.cmb_hide_show.setItemData(1, True)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("hide right axis for view box 2"))
        self.layout.addStretch(1)
        self.layout.addWidget(self.cmb_hide_show)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'hide right axis for view box 2' action. No window is opened."
        QCoreApplication.processEvents()
        if opened_window.spectrum_widget.getAxis("right").isVisible() != self.cmb_hide_show.itemData(self.cmb_hide_show.currentIndex()):
            opened_window.toolbar_layout.hide_right_axis()
        return opened_window, "continue"




