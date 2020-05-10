# -*- Coding: utf-8 -*-

import os
import glob
import functools
import numpy as np
import re
import traceback
import struct

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
    QMessageBox, 
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
        btnSelectMapImage = my_w.CustomPicButton("added_map1.svg", "added_map2.svg", "added_map3.svg", base_path=gf.icon_path, parent=self)
        btnSelectSpectrum = my_w.CustomPicButton("spectrum1.svg", "spectrum2.svg", "spectrum3.svg", base_path=gf.icon_path, parent=self)
        btnSetMapImageContrast = my_w.CustomPicButton("map_contrast1.svg", "map_contrast2.svg", "map_contrast3.svg", base_path=gf.icon_path, parent=self)
        btnSignalIntensity = my_w.CustomPicButton("sig_int1.svg", "sig_int2.svg", "sig_int3.svg", base_path=gf.icon_path, parent=self)
        btnSignalToBaseline = my_w.CustomPicButton("sig2base1.svg", "sig2base2.svg", "sig2base3.svg", base_path=gf.icon_path, parent=self)
        btnSianglToHorizontalBaseline = my_w.CustomPicButton("sig2h_base1.svg", "sig2h_base2.svg", "sig2h_base3.svg", base_path=gf.icon_path, parent=self)
        btnSignalToAxis = my_w.CustomPicButton("sig2axis1.svg", "sig2axis2.svg", "sig2axis3.svg", base_path=gf.icon_path, parent=self)
        btnAddCurrentSpectrum = my_w.CustomPicButton("add_cur_spec1.svg", "add_cur_spec2.svg", "add_cur_spec3.svg", base_path=gf.icon_path, parent=self)
        btnAddSpectrumFromFile = my_w.CustomPicButton("add_spct1.svg", "add_spct2.svg", "add_spct3.svg", base_path=gf.icon_path, parent=self)
        btnSpectrumSubtraction = my_w.CustomPicButton("spct_calc1.svg", "spct_calc2.svg", "spct_calc3.svg", base_path=gf.icon_path, parent=self)
        btnUMX = my_w.CustomPicButton("unmix1.svg", "unmix2.svg", "unmix3.svg", base_path=gf.icon_path, parent=self)
        # btnExportImages = my_w.CustomPicButton("save_map1.svg", "save_map2.svg", "save_map3.svg", base_path=gf.icon_path, parent=self)
        btnExportSvg = my_w.CustomPicButton("save_spct1.svg", "save_spct2.svg", "save_spct3.svg", base_path=gf.icon_path, parent=self)
        btnSaveTarget = my_w.CustomPicButton("save_target1.svg", "save_target2.svg", "save_target3.svg", base_path=gf.icon_path, parent=self)
        btnCosmicRayRemoval = my_w.CustomPicButton("CRR1.svg", "CRR2.svg", "CRR3.svg", base_path=gf.icon_path, parent=self)
        btnNoiseFilterPCA = my_w.CustomPicButton("NF1.svg", "NF2.svg", "NF3.svg", base_path=gf.icon_path, parent=self)
        btnSetWindowSize = my_w.CustomPicButton("map_size1.svg", "map_size2.svg", "map_size3.svg", base_path=gf.icon_path, parent=self)
        btnExportData = my_w.CustomPicButton("export_spc1.svg", "export_spc2.svg", "export_spc3.svg", base_path=gf.icon_path, parent=self)
        btnImportedPlugins = my_w.CustomPicButton("imported_plgin1.svg", "imported_plgin2.svg", "imported_plgin3.svg", base_path=gf.icon_path, parent=self)
        btnExecuteProcedures = my_w.CustomPicButton("exec_umx1.svg", "exec_umx2.svg", "exec_umx3.svg", base_path=gf.icon_path, parent=self)
        btnHideAllInVb2 = my_w.CustomPicButton("hide_v2_1.svg", "hide_v2_2.svg", "hide_v2_3.svg", base_path=gf.icon_path, parent=self)
        btnHideSelectedItem = my_w.CustomPicButton("hide1.svg", "hide2.svg", "hide3.svg", base_path=gf.icon_path, parent=self)
        btnHideRightAxis = my_w.CustomPicButton("HideShow_R_Ax1.svg", "HideShow_R_Ax2.svg", "HideShow_R_Ax3.svg", base_path=gf.icon_path, parent=self)
        btnPause = my_w.CustomPicButton("pause1.svg", "pause2.svg", "pause3.svg", base_path=gf.icon_path, parent=self)
        btnAddCustomName = my_w.CustomPicButton("name1.svg", "name2.svg", "name3.svg", base_path=gf.icon_path, parent=self)
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
        # tool_layout.addRow(btnExportImages, QLabel(" export images and spectrum viewbox"))
        tool_layout.addRow(btnExportSvg, QLabel(" capture current spectrum"))
        tool_layout.addRow(btnSaveTarget, QLabel(" save target (crosshair)"))
        tool_layout.addRow(btnExportData, QLabel(" export data"))
        tool_layout.addRow(gf.QRichLabel("\n--- Preprocess Actions ---", font=gf.boldFont))
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
        tool_layout.addRow(btnAddSpectrumFromFile, QLabel(" add spectrum from a file"))
        tool_layout.addRow(btnAddCustomName, QLabel(" add custom name to added content"))
        tool_layout.addRow(gf.QRichLabel("\n--- Data Actions 2 ---", font=gf.boldFont))
        tool_layout.addRow(btnSpectrumSubtraction, QLabel(" spectrum subtraction"))
        tool_layout.addRow(btnUMX, QLabel(" spectrum unmixing"))
        tool_layout.addRow(btnImportedPlugins, QLabel(" imported plugins"))
        tool_layout.addRow(btnExecuteProcedures, QLabel(" execute procedures"))
        tool_layout.addRow(btnPause, QLabel("pause"))
        tool_layout.addRow(gf.QRichLabel("\n--- View Actions ---", font=gf.boldFont))
        tool_layout.addRow(btnSelectMapImage, QLabel(" select from added map images"))
        tool_layout.addRow(btnSelectSpectrum, QLabel(" select from added spectra"))
        tool_layout.addRow(btnHideAllInVb2, QLabel(" hide all items in view box 2"))
        tool_layout.addRow(btnHideSelectedItem, QLabel(" hide selected item"))
        tool_layout.addRow(btnShowSpectrumWithMaxInt, QLabel(" show spectrum at max intensity"))
        tool_layout.addRow(btnSetSpcRange, QLabel(" set spectrum range"))
        tool_layout.addRow(btnSetMapImageContrast, QLabel(" set map image contrast"))
        tool_layout.addRow(btnSetWindowSize, QLabel(" set window size"))
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
        btnSelectMapImage.clicked.connect(self.btnSelectMapImage_clicked)
        btnSelectSpectrum.clicked.connect(self.btnSelectSpectrum_clicked)
        btnSetMapImageContrast.clicked.connect(self.btnSetMapImageContrast_clicked)
        btnSignalIntensity.clicked.connect(self.btnSignalIntensity_clicked)
        btnSignalToBaseline.clicked.connect(self.btnSignalToBaseline_clicked)
        btnSianglToHorizontalBaseline.clicked.connect(self.SianglToHorizontalBaseline_clicked)
        btnSignalToAxis.clicked.connect(self.btnSignalToAxis_clicked)
        btnAddCurrentSpectrum.clicked.connect(self.btnAddCurrentSpectrum_clicked)
        btnAddSpectrumFromFile.clicked.connect(self.btnAddSpectrumFromFile_clicked)
        btnAddCustomName.clicked.connect(self.btnAddCustomName_clicked)
        btnSpectrumSubtraction.clicked.connect(self.btnSpectrumSubtraction_clicked)
        btnUMX.clicked.connect(self.btnUMX_clicked)
        # btnExportImages.clicked.connect(self.btnExportImages_clicked)
        btnExportSvg.clicked.connect(self.btnExportSvg_clicked)
        btnSaveTarget.clicked.connect(self.btnSaveTarget_clicked)
        btnCosmicRayRemoval.clicked.connect(self.btnCosmicRayRemoval_clicked)
        btnNoiseFilterPCA.clicked.connect(self.btnNoiseFilterPCA_clicked)
        btnSetWindowSize.clicked.connect(self.btnSetWindowSize_clicked)
        btnExportData.clicked.connect(self.btnExportData_clicked)
        btnImportedPlugins.clicked.connect(self.btnImportedPlugins_clicked)
        btnExecuteProcedures.clicked.connect(self.btnExecuteProcedures_clicked)
        btnHideAllInVb2.clicked.connect(self.btnHideAllInVb2_clicked)
        btnHideSelectedItem.clicked.connect(self.btnHideSelectedItem_clicked)
        btnHideRightAxis.clicked.connect(self.btnHideRightAxis_clicked)
        btnPause.clicked.connect(self.btnPause_clicked)
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
    def btnSelectMapImage_clicked(self, event):
        return SelectMapImage(parent=self.process_layout, main_window=self.parent), "SMI"
    @btn_clicked
    def btnSelectSpectrum_clicked(self, event):
        return SelectSpectrum(parent=self.process_layout, main_window=self.parent), "SSC"
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
    def btnAddSpectrumFromFile_clicked(self, event):
        return AddSpectrumFromFile(parent=self.process_layout, main_window=self.parent), "ASF"
    @btn_clicked
    def btnAddCustomName_clicked(self, event):
        return AddCustomName(parent=self.process_layout, main_window=self.parent), "ACN"
    @btn_clicked
    def btnSpectrumSubtraction_clicked(self, event):
        return SpectrumSubtraction(parent=self.process_layout, main_window=self.parent), "SSB"
    @btn_clicked
    def btnUMX_clicked(self, event):
        return BatchUnmixing(parent=self.process_layout, main_window=self.parent), "UMX"
    # @btn_clicked
    # def btnExportImages_clicked(self, event):
    #     return ExportImages(parent=self.process_layout, main_window=self.parent), "SI"
    @btn_clicked
    def btnExportSvg_clicked(self, event):
        return ExportSvg(parent=self.process_layout, main_window=self.parent), "ESG"
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
    def btnHideSelectedItem_clicked(self, event):
        return HideSelectedItem(parent=self.process_layout, main_window=self.parent), "HSI"
    @btn_clicked
    def btnHideRightAxis_clicked(self, event):
        return HideRightAxis(parent=self.process_layout, main_window=self.parent), "HRA"
    @btn_clicked
    def btnPause_clicked(self, event):
        return Pause(parent=self.process_layout, main_window=self.parent), "PUS"
    # その他のボタン押された場合
    def btnSetPath_clicked(self, event):
        cur_text = self.path_entry.text()
        if os.path.exists(cur_text):
            new_path = cur_text
        else:
            new_path = gf.settings["last opened dir"]
        dir_path = QFileDialog.getExistingDirectory(self, 'select folder', new_path)
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
        # 何もない場合
        if self.process_layout.count() == 1:
            warning_popup = popups.WarningPopup("No action to process.")
            warning_popup.exec_()
            return
        dir_path = self.path_entry.text()
        if not os.path.exists(dir_path):
            warning_popup = popups.WarningPopup("Folder named '{0}' could not be found.".format(dir_path))
            warning_popup.exec_()
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
        self.window_type.addItems(["1 spectrum data", "hyperspectral data", "all '*.spc' data", "size unknown hyperspectral data", "filter by file name: None"])
        self.file_name_filter_idx = 4
        self.window_type.setItemData(self.file_name_filter_idx, "None")
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("open window"))
        self.layout.addStretch(1)
        self.layout.addWidget(self.window_type)
        self.setFixedHeight(gf.process_widget_height)
        # イベントコネクト
        self.window_type.activated.connect(self.item_activated)
    def item_activated(self, event=None):
        if event == self.file_name_filter_idx:
            text_settings_popup = popups.TextSettingsPopup(
                parent=self.parent, 
                initial_txt=self.window_type.itemData(event), 
                label="""
                <p>
                    Enter regular expression (re.search) to filter by file name.
                <\p>
                <p>
                    Visit <a href=\"https://docs.python.org/3/library/re.html\">Regular expression operations</a> for detailed syntaxes.
                    <br>
                <\p>
                """, 
                title="file name filter")
            done = text_settings_popup.exec_()
            if done == 0:
                return
            if text_settings_popup.text() == "":
                warning_popup = popups.WarningPopup("Enter some string!")
                warning_popup.exec_()
                self.item_activated(event=self.file_name_filter_idx)
                return
            self.window_type.setItemData(self.file_name_filter_idx, text_settings_popup.text())
            self.window_type.setItemText(self.file_name_filter_idx, "filter by file name: {0}".format(text_settings_popup.text()))
    def procedure(self, spc_path=None, opened_window=None):
        # バイナリを読む（その方が早い？）
        with open(spc_path, 'rb') as f:
            f.seek(24, 0)
            fnsub = struct.unpack("<i", f.read(4))[0]
            try:
                f.seek(-10000, 2) # 2: 末尾から読む
            except:
                f.seek(0, 0)    # 頭から全て読む（サイズが小さすぎて、10000では足りない場合）
            matchedObject_list = list(re.finditer(b"\[map_size\]\r\nmap_x=[0-9]+\r\nmap_y=[0-9]+\r\nmap_z=[0-9]+\r\n\[map_size\]\r\n", f.read(), flags=0))
        # サイズ未設定の hyper spectrum data のみを開く場合
        if self.window_type.currentText() == "size unknown hyperspectral data":
            # サイズ指定されていない map の場合、開く
            if (len(matchedObject_list) == 0) & (fnsub > 1):
                self.main_window.just_open(spc_path)
                opened_window = self.main_window.child_window_list[-1]
                return opened_window, "continue"
            else:
                return None, "skip"
        # フィルターする場合
        elif self.window_type.currentIndex() == self.file_name_filter_idx:
            # マッチしないものをスキップ
            file_name_matched = re.search(self.window_type.currentData(), os.path.basename(spc_path))
            if file_name_matched is None:
                return None, "skip"
        # それ以外の場合、サイズ未指定であれば、注意喚起
        if (len(matchedObject_list) == 0) & (fnsub > 1):
            warning_popup = popups.WarningPopup("The file '{0}' may be opened for the first time and may require size settings.".format(spc_path), title="WARNING", p_type="Bool")
            done = warning_popup.exec_()
            if done == 16384:   # YES
                pass
            else:   # NO
                return None, "Error in opening '{0}'. It may be opened for the first time and require size settings before any processes.".format(spc_path)
        # マッチするもののみを開く
        if (((fnsub > 1) and (self.window_type.currentText() == "hyperspectral data")) 
        or ((fnsub == 1) and (self.window_type.currentText() == "1 spectrum data")) 
        or (self.window_type.currentText() == "all '*.spc' data")
        or (self.window_type.currentIndex() == self.file_name_filter_idx)):
            self.main_window.just_open(spc_path)
            return self.main_window.child_window_list[-1], "continue"
        # ターゲットの window でない場合は、閉じて次へ
        else:
            return None, "skip"
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
        self.continue_process = None
        self.opened_window = None
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
        if opened_window.window_type != "ms":
            return None, "Invalid window type."
        # イベントループ
        loop = QEventLoop()
        def closeEvent1(self_, event=None):
            bool_popup = popups.WarningPopup("Closing the window will stop the batch.\nDo you really want to close?", title="warning", p_type="Bool")
            done = bool_popup.exec_()
            if done == 0x00004000:      # Yes
                event.accept()
                loop.exit()
                self.continue_process = "Position of interest was not set."
            elif done == 0x00010000:    # No
                event.ignore()
        def cancelEvent():
            bool_popup = popups.WarningPopup("Closing the window will stop the batch.\nDo you really want to close?", title="warning", p_type="Bool")
            done = bool_popup.exec_()
            if done == 0x00004000:      # Yes
                loop.exit()
                self.continue_process = "Position of interest was not set."
            elif done == 0x00010000:    # No
                pass
        def okEvent():
            # 大元のバイナリファイルを上書き（ついでに、現在の spc_file にpoi_xなども追加します）
            poi_key = poi_settings_popup.get_poi_key()
            if poi_key in opened_window.spectrum_widget.spc_file.log_dict[b"point_of_interest_dict"].keys():
                warning_popup = popups.WarningPopup("The name '{0}' is already taken. Do you really want to overwrite?".format(poi_key), title="WARNING", p_type="Bool")
                done = warning_popup.exec_()
                if done == 16384:   # YES
                    poi_idx = opened_window.parent.poi_manager.get_poi_idx(poi_key=poi_key)
                    x, y = opened_window.spectrum_widget.cur_x, opened_window.spectrum_widget.cur_y
                    opened_window.parent.poi_manager.poi_layout.set_focus(idx=poi_idx)
                    opened_window.parent.poi_manager.btn_poi_del_clicked()
                    # focus すると、スペクトルの場所が移動してしまうので。
                    opened_window.toolbar_layout.set_spectrum_and_crosshair(x, y)
                else:   # NO
                    return
            opened_window.parent.poi_manager.btn_poi_add_clicked()
            opened_window.parent.poi_manager.poi_layout.set_focus(idx=-2)
            opened_window.parent.poi_manager.btn_poi_rename_clicked(ask=False, poi_key=poi_key)
            # 脱ループ
            loop.exit()
            self.opened_window = opened_window
            self.continue_process = "continue"        
        def skipEvent():
            loop.exit()
            self.opened_window = opened_window
            self.continue_process = "continue"
        opened_window.closeEvent = closeEvent1.__get__(opened_window, type(opened_window))
        # クロスヘア初期値設定
        poi_key = self.default_name.text()
        x_size = int(opened_window.spectrum_widget.spc_file.log_dict[b"map_x"])
        y_size = int(opened_window.spectrum_widget.spc_file.log_dict[b"map_y"])
        if poi_key in opened_window.spectrum_widget.spc_file.log_dict[b"point_of_interest_dict"].keys():
            initial_values = opened_window.spectrum_widget.spc_file.log_dict[b"point_of_interest_dict"][poi_key]
        else:
            initial_values = (0, 0)
        # クロスヘア、スペクトル、poi_settings_popup を initial_values にあわせる
        opened_window.toolbar_layout.set_spectrum_and_crosshair(*initial_values)
        # ポップアップ
        poi_settings_popup = popups.PoiSettingsPopup(parent=opened_window, initial_values=(0,0), labels=("x position", "y position"), title="set point of interest", poi_key="poi1")
        poi_settings_popup.setWindowFlags(Qt.WindowStaysOnTopHint)
        poi_settings_popup.set_spinbox_range((0, x_size-1), "RS1")
        poi_settings_popup.set_spinbox_range((0, y_size-1), "RS2")
        poi_settings_popup.setValues(initial_values)
        poi_settings_popup.set_poi_key(poi_key)
        opened_window.map_widget.scene().sigMouseClicked.connect(poi_settings_popup.on_map_widget_click)
        # イベントコネクト
        poi_settings_popup.btnCancel.disconnect()
        poi_settings_popup.btnOK.disconnect()
        poi_settings_popup.btnCancel.clicked.connect(cancelEvent)
        poi_settings_popup.btnOK.clicked.connect(okEvent)
        poi_settings_popup.btnSkip.clicked.connect(skipEvent)
        poi_settings_popup.closeEvent = closeEvent1.__get__(poi_settings_popup, type(poi_settings_popup))
        poi_settings_popup.show()
        # 位置調整：親windowの右上に揃える感じで
        pwg = opened_window.geometry()
        pwf = opened_window.frameSize()
        poi_settings_popup.move(pwg.left() + pwf.width(), pwg.top() - pwf.height() + pwg.height())
        # ループ
        loop.exec_()
        # ポップアップ閉じる
        opened_window.closeEvent = closeEvent.__get__(opened_window, type(opened_window))
        poi_settings_popup.closeEvent = closeEvent.__get__(poi_settings_popup, type(poi_settings_popup))
        poi_settings_popup.close()
        ###
        return self.opened_window, self.continue_process
class GoToPositionOfInterest(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "POI"
        self.title = "go to position of interest"
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
        self.title = "show spectrum at max. int."
        self.option = {}
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in '{0}' action. No window is opened.".format(self.title)
        if opened_window.window_type == "ms":
            if opened_window.cur_displayed_map_content is None:
                return None, "Error in '{0}' action.\nImages must be set before showing spectrum with max intensity.".format(self.title)
            cur_image2d = opened_window.cur_displayed_map_content.item.image2d
            max_loc = np.unravel_index(np.argmax(cur_image2d), cur_image2d.shape)
            opened_window.spectrum_widget.replace_spectrum(*max_loc)
            opened_window.map_widget.set_crosshair(*max_loc)
            return opened_window, "continue"
        else:
            # opened_window.close()
            return None, "Invalid window type."
# class SelectMapImage(my_w.ClickableQWidget):
#     def __init__(self, parent=None, main_window=None):
#         super().__init__(parent)
#         self.main_window = main_window
#         self.type = "SMI"
#         self.title = "select from added map images"
#         self.option = {}
#         # コンテンツ
#         self.tgt_label = QLabel("target: ")
#         self.tgt_txt = QLineEdit("")
#         # レイアウト
#         self.layout.setContentsMargins(11,0,11,0)
#         self.layout.addWidget(QLabel("select from added map images"))
#         self.layout.addStretch(1)
#         self.layout.addWidget(self.tgt_label)
#         self.layout.addWidget(self.tgt_txt)
#         self.setFixedHeight(gf.process_widget_height)
#     def procedure(self, spc_path=None, opened_window=None):
#         if opened_window is None:
#             return None, "Error in '{0}' action. No window is opened.".format(self.title)
#         if opened_window.window_type == "ms":
#             if opened_window.cur_displayed_map_content is None:
#                 return None, "Error in '{0}' action.\nImages must be set before selection.".format(self.title)
#             # ターゲットレイアウトの探索
#             if self.tgt_txt.text() != "":
#                 isNotNone_list = [re.search(self.tgt_txt.text(), added_content_map.summary()) is not None for added_content_map in opened_window.toolbar_layout.added_content_map_list]
#                 N_NotNone = sum(isNotNone_list)
#                 if N_NotNone == 0:
#                     return None, "No search result for '{0}'".format(self.tgt_txt.text())
#                 elif N_NotNone > 1:
#                     return None, "Multiple search result for '{0}'".format(self.tgt_txt.text())
#                 # GUI がいじられた場合でも、エラーが出ないようにする
#                 try:
#                     opened_window.cur_displayed_map_content.focus_unfocus(focused=False)
#                 except:
#                     pass
#                 # ターゲットを選択
#                 added_content = opened_window.toolbar_layout.added_content_map_list[isNotNone_list.index(True)]
#                 added_content.focus_unfocus(focused=True)
#                 try:
#                     opened_window.parent.map_spect_table.focus_content(added_content)
#                 except:
#                     pass
#             return opened_window, "continue"
#         else:
#             # opened_window.close()
#             return None, "Invalid window type."
class SelectContent(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None, map_or_spc=None):
        super().__init__(parent)
        self.main_window = main_window
        self.map_or_spc = map_or_spc
        if self.map_or_spc == "spectrum":
            self.type = "SSC"
            self.title = "select from added spectra"
            self.allowed_windows = ("ms", "s")
            self.abbriviation = "spc"
        else:
            self.type = "SMI"
            self.title = "select from added maps"
            self.allowed_windows = ("ms")
            self.abbriviation = "map"
        self.option = {}
        # コンテンツ
        self.tgt_cmb = QComboBox()
        self.tgt_cmb.addItems(["index", "target"])
        self.tgt_txt = QLineEdit("")
        self.tgt_idx = QSpinBox()
        self.tgt_idx.setRange(-1000, 1000)
        self.tgt_idx.setValue(0)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.tgt_cmb)
        self.layout.addWidget(self.tgt_txt)
        self.layout.addWidget(self.tgt_idx)
        self.tgt_txt.hide()
        self.setFixedHeight(gf.process_widget_height)
        # イベントコネクト
        self.tgt_cmb.currentTextChanged.connect(self.tgt_cmb_changed)
    def tgt_cmb_changed(self, event):
        if event == "target":
            self.tgt_txt.show()
            self.tgt_idx.hide()
        elif event == "index":
            self.tgt_txt.hide()
            self.tgt_idx.show()
        else:
            raise Exception("unknown event: {0}".format(event))
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in '{0}' action. No window is opened.".format(self.title)
        if opened_window.window_type not in self.allowed_windows:
            return None, "Invalid window type."
        # spc については、 original spectrum が必ずあるはずなので、不要。
        if self.map_or_spc == "map":
            if opened_window.cur_displayed_map_content is None:
                return None, "Error in '{0}' action.\nImages must be added before selection.".format(self.title)
        # ターゲットレイアウトの取得
        target_added_content_list = getattr(opened_window.toolbar_layout, "added_content_{0}_list".format(self.map_or_spc))
        target_cur_displayed_content = getattr(opened_window, "cur_displayed_{0}_content".format(self.abbriviation))
        # ターゲットレイアウトの探索
        if self.tgt_cmb.currentText() == "target":
            if self.tgt_txt.text() == "":
                return None, "Error in '{0}' action.\nTarget string is empty!".format(self.title)
            isNotNone_list = [re.search(self.tgt_txt.text(), added_content.summary()) is not None for added_content in target_added_content_list]
            N_NotNone = sum(isNotNone_list)
            if N_NotNone == 0:
                return None, "No search result for '{0}'".format(self.tgt_txt.text())
            elif N_NotNone > 1:
                return None, "Multiple search result for '{0}'".format(self.tgt_txt.text())
            idx = isNotNone_list.index(True)
        elif self.tgt_cmb.currentText() == "index":
            idx = self.tgt_idx.value()
            LEN = len(target_added_content_list)
            if (LEN < idx - 1) or (LEN < -idx):
                return None, "Error in '{0}' action.\nThe index is out of range!".format(self.title)
        # GUI がいじられた場合でも、エラーが出ないようにする
        try:
            target_cur_displayed_content.focus_unfocus(focused=False)
        except:
            pass
        # ターゲットを選択
        added_content = target_added_content_list[idx]
        added_content.focus_unfocus(focused=True)
        try:
            opened_window.parent.map_spect_table.focus_content(added_content)
        except:
            pass
        return opened_window, "continue"
class SelectMapImage(SelectContent):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent, main_window, "map")
class SelectSpectrum(SelectContent):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent, main_window, "spectrum")
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
            # xData = opened_window.spectrum_widget.master_spectrum.xData
            # yData = opened_window.spectrum_widget.master_spectrum.yData
            # local_y_min, local_y_max = gf.get_local_minmax(xData, yData, x_range)

            local_y_min, local_y_max = opened_window.spectrum_widget.get_auto_yRange(x_range)
            if local_y_min is None:
                return opened_window, "continue"
            if self.y_btm.currentText() == "0":
                btm_value = 0
                top_value = local_y_max + local_y_min
            elif self.y_btm.currentText() == "AUTO":
                btm_value = local_y_min
                top_value = local_y_max
            else:
                raise Exception("unkwon selection")
            # calc padding
            pad = opened_window.spectrum_widget.plotItem.vb.suggestPadding(1) # 1 means height
            p = (top_value - btm_value) * pad
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
        if opened_window.window_type != "ms":
            return None, "Invalid window type."
        opened_window.toolbar_layout.add_current_spectrum()
        return opened_window, "continue"
class AddSpectrumFromFile(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "ASF"
        self.title = "add spectrum from a file"
        # コンテンツ
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["from a file", "target", "target path"])
        self.cmb_type.setItemData(0, "")
        self.cmb_type.setItemData(1, "")
        self.cmb_type.setItemData(2, "directory_path/regular expression to specify file name(s)")
        self.path_entry = QLineEdit()
        btnSetPath = QPushButton("...")
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.cmb_type)
        self.layout.addWidget(self.path_entry)
        self.layout.addWidget(btnSetPath)
        self.setFixedHeight(gf.process_widget_height)
        # イベントコネクト
        self.cmb_type.currentIndexChanged.connect(self.cmb_type_changed)
        btnSetPath.clicked.connect(self.btnSetPath_clicked)
    def btnSetPath_clicked(self, event):
        if self.cmb_type.currentText() == "target":
            explanation_popup = popups.MessageDialog(parent=self, message="""
                <p>
                    Search spc files in the directory that the current opened spc file was loaded from.
                    <br>
                    Enter the regular expression (re.search) to specify file(s).
                <\p>
                <p>
                    Visit <a href=\"https://docs.python.org/3/library/re.html\">Regular expression operations</a> for detailed syntaxes.
                    <br>
                <\p>
            """, p_type="Normal")
            explanation_popup.exec_()
        elif self.cmb_type.currentText() == "target path":
            explanation_popup = popups.MessageDialog(parent=self, message="""
                <p>
                    Search spc files in the specified directory.
                    <br>
                    Enter the directory path and the regular expression (re.search) to specify file(s) as follows.
                    <br>
                    (Only the charactor '/' on the far right is recognized as the separator.)
                <\p>
                <p>
                    <span style='font-family:Courier'>
                        <span style="color:transparent">123</span>directory_path/regular expression to specify file name(s)
                    </span>
                <\p>
                <p>
                    Visit <a href=\"https://docs.python.org/3/library/re.html\">Regular expression operations</a> for detailed syntaxes.
                    <br>
                <\p>
            """, p_type="Normal")
            explanation_popup.exec_()
        elif self.cmb_type.currentText() == "from a file":
            cur_path = self.path_entry.text()
            if not os.path.exists(cur_path):
                cur_path = gf.settings["last opened dir"]
            file_path, file_type = QFileDialog.getOpenFileName(self, 'select procedure file', cur_path, filter="procedure file (*.spc *.out *.cspc *.spcl)")
            if len(file_path):
                self.path_entry.setText(file_path)
        else:
            raise Exception("unknown selection: {0}".format(self.cmb_type.currentText()))
    def cmb_type_changed(self, event):
        self.path_entry.setText(self.cmb_type.itemData(event))
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'add current spectrum' action. No window is opened."
        # ファイルパス取得
        if self.cmb_type.currentText() == "target":
            pattern = self.path_entry.text()
            file_path_candidates = glob.glob("{0}/*".format(opened_window.dir_path), recursive=False)
            file_path_list = [file_path for file_path in file_path_candidates if re.search(pattern, file_path) is not None]
        elif self.cmb_type.currentText() == "target path":
            dir_path_pattern_list = self.path_entry.text().strip().split("/")
            dir_path = "/".join(dir_path_pattern_list[:-1])
            pattern = dir_path_pattern_list[-1]
            file_path_candidates = glob.glob("{0}/*".format(opened_window.dir_path), recursive=False)
            file_path_list = [file_path for file_path in file_path_candidates if re.search(pattern, file_path) is not None]
        elif self.cmb_type.currentText() == "from a file":
            file_path_list = [self.path_entry.text()]
        opened_window.toolbar_layout.add_spectrum_from_file(file_path_list=file_path_list)
        return opened_window, "continue"
class AddCustomName(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "ACN"
        self.title = "add custom name to added content"
        # コンテンツ
        self.map_or_spc_cmb = QComboBox()
        self.map_or_spc_cmb.addItems(["map", "spectrum"])
        self.map_or_spc_cmb.setItemData(0, "map")
        self.map_or_spc_cmb.setItemData(1, "spc")
        self.custom_name = QLineEdit("")
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.map_or_spc_cmb)
        self.layout.addWidget(self.custom_name)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'add current spectrum' action. No window is opened."
        target_content = getattr(opened_window, "cur_displayed_{0}_content".format(self.map_or_spc_cmb.currentData()))
        if target_content is None:
            return None, "No window is added to the menu."
        target_content.update_custom_name(self.custom_name.text())
        return opened_window, "continue"
class SpectrumSubtraction(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "SSB"
        self.option = {}
        self.title = "subtract spectrum"
        # オプション
        self.cmb = QComboBox()
        self.cmb.addItems(["to hori. axis", "to hori. line", "to angl. line", "'n' as 1"])
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
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.cmb)
        self.layout.addWidget(self.range_bottom)
        self.layout.addWidget(self.range_top)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in '{0}' action. No window is opened.".fomat(self.title)
        if opened_window.window_type not in ["ms", "s"]:
            return opened_window, "Invalid window type."
        if opened_window.cur_displayed_spc_content is None:
            return None, "Error in '{0}' action. Exactly 1 added spectrum should be selected.".format(self.title)
        log = opened_window.toolbar_layout.execute_spectrum_linear_subtraction(
            event=None, 
            mode="macro", 
            range=[self.range_bottom.value(), self.range_top.value()], 
            method=self.cmb.currentText()
            )
        if log == "executed":
            return opened_window, "continue"
        else:
            return opened_window, "Not executed."
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
class ExportSvg(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "ESG"
        self.option = {}
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("capture current spectrum"))
        self.layout.addStretch(1)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'capture current spectrum' action. No window is opened."
        opened_window.toolbar_layout.export_svg()
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
        self.cmb_content = QComboBox()
        self.cmb_content.addItems(["spectrum", "map"])
        self.cmb_export_s = QComboBox()
        self.cmb_export_s.addItems(["as spc", "as txt", "as info"])
        self.cmb_export_s.setItemData(0, {"ext":".spc", "ask":False})
        self.cmb_export_s.setItemData(1, {"ext":".txt", "ask":False})
        self.cmb_export_s.setItemData(2, {"ext":".info", "ask":False})
        self.cmb_export_m = QComboBox()
        self.cmb_export_m.addItems(["as tiff & svg", "as spc"])
        self.cmb_export_m.setItemData(0, {"ext":".tiff .svg", "ask":False})
        self.cmb_export_m.setItemData(1, {"ext":".spc", "ask":False})
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel("export data"))
        self.layout.addStretch(1)
        # self.layout.addWidget(self.cmb_target)
        self.layout.addWidget(self.cmb_content)
        self.layout.addWidget(self.cmb_export_s)
        self.layout.addWidget(self.cmb_export_m)
        self.cmb_export_m.hide()
        self.setFixedHeight(gf.process_widget_height)
        # イベントコネクト
        self.cmb_content.currentTextChanged.connect(self.cmb_content_changed)
    def cmb_content_changed(self, event):
        if event == "map":
            self.cmb_export_m.show()
            self.cmb_export_s.hide()
        else:
            self.cmb_export_m.hide()
            self.cmb_export_s.show()
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'export data' action. No window is opened."
        # スペクトル選択時に、マップエクスポートが選択させると、エラー
        if (opened_window.window_type == "s") & (self.cmb_content.currentText() == "map"):
            return None, "Tried to export map data, but the data contains only one spectrum."
        # 何も選択されてないと、エラー
        if (self.cmb_content.currentText() == "spectrum") & (opened_window.cur_displayed_spc_content is None):
            return None, "No item is selected in the {} table.".format(self.cmb_content.currentText())
        if self.cmb_content.currentText() == "map":
            if opened_window.cur_displayed_map_content is None:
                return None, "No item is selected in the {} table.".format(self.cmb_content.currentText())
        func_content = self.cmb_content.currentText()
        if func_content == "spectrum":
            func_args = self.cmb_export_s.currentData()
        elif func_content == "map":
            func_args = self.cmb_export_m.currentData()
        else:
            raise Exception("unkwon func_content: {0}".format(func_content))
        func = getattr(opened_window.toolbar_layout, "export_{0}".format(func_content))
        func(**func_args)
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
        cur_path = self.path_entry.text()
        if not os.path.exists(cur_path):
            cur_path = gf.settings["method dir"]
        file_path, file_type = QFileDialog.getOpenFileName(self, 'select procedure file', cur_path, filter="procedure file (*.umx)")
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
class HideSelectedItem(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "HSI"
        self.option = {}
        self.title = "hide selected item"
        # コンテンツ
        self.map_or_spc = QComboBox()
        self.map_or_spc.addItems(["map", "spc"])
        self.hide_show = QComboBox()
        self.hide_show.addItems(["hide", "show"])
        self.hide_show.setItemData(0, False)
        self.hide_show.setItemData(1, True)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(QLabel("target: "))
        self.layout.addWidget(self.map_or_spc)
        self.layout.addWidget(self.hide_show)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in '{0}' action. No window is opened.".format(self.title)
        if (opened_window.window_type == "s") & (self.map_or_spc.currentText() == "map"):
            return None, "Error in '{0}' action. Target 'map' cannot be applied to 1 spectrum data.".format(self.title)
        target_content = getattr(opened_window, "cur_displayed_{0}_content".format(self.map_or_spc.currentText()))
        if target_content is None:
            return None, "Error in '{0}' action. No {1} item is selected.".format(self.title, self.map_or_spc.currentText())
        target_content.hide_show_item(show=self.hide_show.currentData())
        return opened_window, "continue"
class HideAllInVb2(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "HV2"
        self.option = {}
        self.title = "hide all items in view box 2"
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in '{0}' action. No window is opened.".format(self.title)
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
        if opened_window.spectrum_widget.getAxis("right").isVisible() != self.cmb_hide_show.currentData():
            opened_window.toolbar_layout.hide_right_axis()
        return opened_window, "continue"
class Pause(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "PUS"
        self.title = "pause"
        self.continue_process = None
        self.opened_window = None
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "Error in 'pause' action. No window is opened."
        # イベントループ
        loop = QEventLoop()
        # ポップアップ準備
        def closeEvent1(self_, event=None):
            bool_popup = popups.WarningPopup("Closing the window will stop the batch.\nDo you really want to close?", title="warning", p_type="Bool")
            done = bool_popup.exec_()
            if done == 0x00004000:      # Yes
                event.accept()
                loop.exit()
                self.continue_process = "Batch processes were canceled."
            elif done == 0x00010000:    # No
                event.ignore()
        def cancelEvent():
            bool_popup = popups.WarningPopup("Closing the window will stop the batch.\nDo you really want to close?", title="warning", p_type="Bool")
            done = bool_popup.exec_()
            if done == 0x00004000:      # Yes
                loop.exit()
                self.continue_process = "Batch processes were canceled."
            elif done == 0x00010000:    # No
                pass
        def okEvent():
            loop.exit()
            self.opened_window = opened_window
            self.continue_process = "continue"
        opened_window.closeEvent = closeEvent1.__get__(opened_window, type(opened_window))
        # ポップアップ
        pause_popup = popups.MessageDialog(parent=self.parent, message="Press ok to continue.", p_type="Cancel", enable_event_connect=False)
        pause_popup.setWindowFlags(Qt.WindowStaysOnTopHint)
        # イベントコネクト
        pause_popup.btnOk.clicked.connect(okEvent)
        pause_popup.btnCancel.clicked.connect(cancelEvent)
        pause_popup.closeEvent = closeEvent1.__get__(pause_popup, type(pause_popup))
        pause_popup.show()
        # ループ
        loop.exec_()
        # ポップアップ閉じる
        opened_window.closeEvent = closeEvent.__get__(opened_window, type(opened_window))
        pause_popup.closeEvent = closeEvent.__get__(pause_popup, type(pause_popup))
        pause_popup.close()
        ###
        return self.opened_window, self.continue_process




