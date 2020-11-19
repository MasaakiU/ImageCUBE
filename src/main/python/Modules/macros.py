# -*- Coding: utf-8 -*-

import os
import glob
import functools
import numpy as np
import re
import traceback
import struct
import json
import shutil
from urllib import parse

from PyQt5.QtWidgets import (
    QFileDialog, 
    QWidget, 
    QPushButton, 
    QVBoxLayout, 
    QHBoxLayout,  
    QSpinBox, 
    QDoubleSpinBox, 
    QScrollArea, 
    QLabel, 
    QLineEdit, 
    QDialog, 
    QComboBox, 
    QFormLayout, 
    QCheckBox, 
    QMessageBox, 
    QSplitter, 
    QGridLayout, 
    QMainWindow, 
    )
from PyQt5.QtCore import QEventLoop, QCoreApplication, Qt
from Modules import general_functions as gf
from Modules import draw
from Modules import popups
from Modules import my_widgets as my_w

class BatchProcessingWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.window_type = "b"
        self.setWindowTitle("untitled_action_flow.umx")
        # ドラッグ・アンド・ドロップ
        self.setAcceptDrops(True)
        # 上部ファイルパス
        self.path_entry = QLineEdit()
        self.cmbExt = my_w.CheckableComboBox()
        self.cmbExt.addItems([".spc", ".cspc", ".spcl", ".out"], datalist=["*.spc", "*.cspc", "*.spcl", "*.out"])
        self.cmbExt.setCheckState(0, 2) # idx = 0 (.spc), checkstate = 2 (checked)
        btnSetPath = QPushButton("...")
        # 左部ツールレイアウト
        btnOpenWindow = my_w.CustomPicButton("open1.svg", "open2.svg", "open3.svg", base_path=gf.icon_path, parent=self)
        btnCloseWindow = my_w.CustomPicButton("close_all_1.svg", "close_all_2.svg", "close_all_3.svg", base_path=gf.icon_path, parent=self)
        btnPOISettings = my_w.CustomPicButton("poi1.svg", "poi2.svg", "poi3.svg", base_path=gf.icon_path, parent=self)
        btnTrashFiles = my_w.CustomPicButton("trash1.svg", "trash2.svg", "trash3.svg", base_path=gf.icon_path, parent=self)
        btnGoToPositionOfInterest = my_w.CustomPicButton("poi1.svg", "poi2.svg", "poi3.svg", base_path=gf.icon_path, parent=self)
        btnSetSpectrumRange = my_w.CustomPicButton("set_spc_range1.svg", "set_spc_range2.svg", "set_spc_range3.svg", base_path=gf.icon_path, parent=self)
        btnShowSpectrumWithMaxInt = my_w.CustomPicButton("show_max_int_spc1.svg", "show_max_int_spc2.svg", "show_max_int_spc3.svg", base_path=gf.icon_path, parent=self)
        btnSelectAddedItem = my_w.CustomPicButton("added_item1.svg", "added_item2.svg", "added_item3.svg", base_path=gf.icon_path, parent=self)
        btnSetMapImageContrast = my_w.CustomPicButton("map_contrast1.svg", "map_contrast2.svg", "map_contrast3.svg", base_path=gf.icon_path, parent=self)
        btnExecuteSignalIntensity = my_w.CustomPicButton("sig_int1.svg", "sig_int2.svg", "sig_int3.svg", base_path=gf.icon_path, parent=self)
        btnExecuteSignalToBaseline = my_w.CustomPicButton("sig2base1.svg", "sig2base2.svg", "sig2base3.svg", base_path=gf.icon_path, parent=self)
        btnExecuteSianglToHBaseline = my_w.CustomPicButton("sig2h_base1.svg", "sig2h_base2.svg", "sig2h_base3.svg", base_path=gf.icon_path, parent=self)
        btnExecuteSignalToAxis = my_w.CustomPicButton("sig2axis1.svg", "sig2axis2.svg", "sig2axis3.svg", base_path=gf.icon_path, parent=self)
        btnAddCurrentSpectrum = my_w.CustomPicButton("add_cur_spec1.svg", "add_cur_spec2.svg", "add_cur_spec3.svg", base_path=gf.icon_path, parent=self)
        btnAddSpectrumFromFile = my_w.CustomPicButton("add_spct1.svg", "add_spct2.svg", "add_spct3.svg", base_path=gf.icon_path, parent=self)
        btnAddSpectraFromObj = my_w.CustomPicButton("add_spct1.svg", "add_spct2.svg", "add_spct3.svg", base_path=gf.icon_path, parent=self)
        btnExecuteSpectrumLinearSubtraction = my_w.CustomPicButton("spct_calc1.svg", "spct_calc2.svg", "spct_calc3.svg", base_path=gf.icon_path, parent=self)
        btnExecuteUnmixing = my_w.CustomPicButton("unmix1.svg", "unmix2.svg", "unmix3.svg", base_path=gf.icon_path, parent=self)
        # btnExportImages = my_w.CustomPicButton("save_map1.svg", "save_map2.svg", "save_map3.svg", base_path=gf.icon_path, parent=self)
        btnExportSvg = my_w.CustomPicButton("save_spct1.svg", "save_spct2.svg", "save_spct3.svg", base_path=gf.icon_path, parent=self)
        btnSaveTarget = my_w.CustomPicButton("save_target1.svg", "save_target2.svg", "save_target3.svg", base_path=gf.icon_path, parent=self)
        btnCRRMaster = my_w.CustomPicButton("CRR1.svg", "CRR2.svg", "CRR3.svg", base_path=gf.icon_path, parent=self)
        btnNRMaster = my_w.CustomPicButton("NF1.svg", "NF2.svg", "NF3.svg", base_path=gf.icon_path, parent=self)
        btnSetWindowSize = my_w.CustomPicButton("map_size1.svg", "map_size2.svg", "map_size3.svg", base_path=gf.icon_path, parent=self)
        btnExportData = my_w.CustomPicButton("export_spc1.svg", "export_spc2.svg", "export_spc3.svg", base_path=gf.icon_path, parent=self)
        btnExecutePlugins = my_w.CustomPicButton("imported_plgin1.svg", "imported_plgin2.svg", "imported_plgin3.svg", base_path=gf.icon_path, parent=self)
        btnExecuteSavedActionFlows = my_w.CustomPicButton("exec_umx1.svg", "exec_umx2.svg", "exec_umx3.svg", base_path=gf.icon_path, parent=self)
        btnHideAllInV2 = my_w.CustomPicButton("hide_v2_1.svg", "hide_v2_2.svg", "hide_v2_3.svg", base_path=gf.icon_path, parent=self)
        btnHideSelectedItem = my_w.CustomPicButton("hide1.svg", "hide2.svg", "hide3.svg", base_path=gf.icon_path, parent=self)
        btnHideRightAxis = my_w.CustomPicButton("HideShow_R_Ax1.svg", "HideShow_R_Ax2.svg", "HideShow_R_Ax3.svg", base_path=gf.icon_path, parent=self)
        btnPause = my_w.CustomPicButton("pause1.svg", "pause2.svg", "pause3.svg", base_path=gf.icon_path, parent=self)
        btnUpdateCustomName = my_w.CustomPicButton("name1.svg", "name2.svg", "name3.svg", base_path=gf.icon_path, parent=self)
        btnSelectWindow = my_w.CustomPicButton("window1.svg", "window2.svg", "window3.svg", base_path=gf.icon_path, parent=self)
        # 特殊ボタン
        btnImportProcedures = my_w.CustomPicButton("exec_umx1.svg", "exec_umx2.svg", "exec_umx3.svg", base_path=gf.icon_path, parent=self)
        btnImportProcedures.setToolTip("import Action Flow")
        btnExportProcedures = my_w.CustomPicButton("export_umx1.svg", "export_umx2.svg", "export_umx3.svg", base_path=gf.icon_path, parent=self)
        btnExportProcedures.setToolTip("export Action Flow")
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

        # batch_path_selection_layout = QHBoxLayout()
        # batch_path_selection_layout.addWidget(QLabel("folder path"))
        # batch_path_selection_layout.addWidget(self.path_entry)
        # batch_path_selection_layout.addWidget(self.cmbExt)
        # batch_path_selection_layout.addWidget(btnSetPath)

        cmb_ext_layout = QHBoxLayout()
        cmb_ext_layout.setContentsMargins(0,0,0,0)
        cmb_ext_layout.setSpacing(0)
        cmb_ext_layout.addWidget(self.cmbExt)
        cmb_ext_layout.addStretch(1)
        batch_path_selection_layout = QGridLayout()
        batch_path_selection_layout.setSpacing(5)
        batch_path_selection_layout.addWidget(QLabel("folder path"), 0, 0)
        batch_path_selection_layout.addWidget(self.path_entry, 0, 1)
        batch_path_selection_layout.addWidget(btnSetPath, 0, 2)
        batch_path_selection_layout.addWidget(QLabel("extension(s)"), 1, 0)
        batch_path_selection_layout.addLayout(cmb_ext_layout, 1, 1)

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
        tool_layout.addRow(btnTrashFiles, QLabel(" trash files"))
        tool_layout.addRow(gf.QRichLabel("\n--- Preprocess Actions ---", font=gf.boldFont))
        tool_layout.addRow(btnCRRMaster, QLabel(" cosmic ray removal"))
        tool_layout.addRow(btnNRMaster, QLabel(" PCA based noise filter"))
        tool_layout.addRow(gf.QRichLabel("\n--- Data Actions 1 ---", font=gf.boldFont))
        tool_layout.addRow(btnPOISettings, QLabel(" set position of interest"))
        tool_layout.addRow(btnGoToPositionOfInterest, QLabel(" go to position of interest"))
        tool_layout.addRow(btnExecuteSignalIntensity, QLabel(" signal intensity"))
        tool_layout.addRow(btnExecuteSignalToBaseline, QLabel(" signal to baseline"))
        tool_layout.addRow(btnExecuteSianglToHBaseline, QLabel(" signal to horizontal line"))
        tool_layout.addRow(btnExecuteSignalToAxis, QLabel(" signal to axis"))
        tool_layout.addRow(btnAddCurrentSpectrum, QLabel(" add current spectrum"))
        tool_layout.addRow(btnAddSpectrumFromFile, QLabel(" add spectrum from a file (dynamic)"))
        tool_layout.addRow(btnAddSpectraFromObj, QLabel(" add spectrum from a file (static)"))
        tool_layout.addRow(btnUpdateCustomName, QLabel(" set custom name to added content"))
        tool_layout.addRow(gf.QRichLabel("\n--- Data Actions 2 ---", font=gf.boldFont))
        tool_layout.addRow(btnExecuteSpectrumLinearSubtraction, QLabel(" spectrum subtraction"))
        tool_layout.addRow(btnExecuteUnmixing, QLabel(" spectrum unmixing"))
        tool_layout.addRow(btnExecutePlugins, QLabel(" imported plugins"))
        tool_layout.addRow(btnExecuteSavedActionFlows, QLabel(" execute Action Flow"))
        tool_layout.addRow(btnPause, QLabel("pause"))
        tool_layout.addRow(gf.QRichLabel("\n--- View Actions ---", font=gf.boldFont))
        tool_layout.addRow(btnSelectAddedItem, QLabel(" select from added items"))
        tool_layout.addRow(btnHideSelectedItem, QLabel(" hide selected item"))
        tool_layout.addRow(btnHideAllInV2, QLabel(" hide all items in view box 2"))
        tool_layout.addRow(btnHideRightAxis, QLabel("hide right axis for view box 2"))
        tool_layout.addRow(btnShowSpectrumWithMaxInt, QLabel(" show spectrum at max intensity"))
        tool_layout.addRow(btnSetSpectrumRange, QLabel(" set spectrum range"))
        tool_layout.addRow(btnSetMapImageContrast, QLabel(" set map image contrast"))
        tool_layout.addRow(btnSetWindowSize, QLabel(" set window size"))
        tool_layout.addRow(btnSelectWindow, QLabel(" select window"))
        # execute
        execute_layout = QHBoxLayout()
        execute_layout.setContentsMargins(0,0,0,0)
        execute_layout.setSpacing(0)
        execute_layout.addWidget(btnImportProcedures)
        execute_layout.addWidget(btnExportProcedures)
        execute_layout.addStretch(1)
        execute_layout.addWidget(btnMoveUp)
        execute_layout.addWidget(btnRemove)
        execute_layout.addWidget(btnMoveDown)
        execute_layout.addSpacerItem(my_w.CustomSpacer(width=5))
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
        tools_area_layout.setContentsMargins(0,0,0,0)
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
        batch_area_layout.setContentsMargins(0,0,0,0)
        batch_area_layout.addWidget(gf.QRichLabel("Action Flow for every *.spc files", font=gf.boldFont))
        batch_area_layout.addWidget(batch_scroll_area)
        batch_area_layout.addLayout(execute_layout)
        # スプリッター
        tools_area_widget = QWidget()
        tools_area_widget.setLayout(tools_area_layout)
        batch_area_widget = QWidget()
        batch_area_widget.setLayout(batch_area_layout)
        sub_area = QSplitter(Qt.Horizontal)
        policy = sub_area.sizePolicy()
        policy.setVerticalStretch(10)
        sub_area.setSizePolicy(policy)
        sub_area.addWidget(tools_area_widget)
        sub_area.addWidget(batch_area_widget)
        # 全体
        sub_layout = QHBoxLayout()
        sub_layout.setSpacing(0)
        sub_layout.addWidget(sub_area)
        layout = QVBoxLayout()
        layout.addLayout(batch_path_selection_layout)
        layout.addLayout(sub_layout)
        # self.setMinimumSize(gf.batch_window_min_width, gf.batch_window_min_height)
        # self.setLayout(layout)
        # tab barが現れるのを防ぐため、QWidget ではなく QMainWindow で window を作成し、TabBarを消去した。
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.setUnifiedTitleAndToolBarOnMac(True)
        # イベントコネクト
        btnOpenWindow.clicked.connect(self.btnOpenWindow_clicked)
        btnCloseWindow.clicked.connect(self.btnCloseWindow_clicked)
        btnSetPath.clicked.connect(self.btnSetPath_clicked)
        btnPOISettings.clicked.connect(self.btnPOISettings_clicked)
        btnGoToPositionOfInterest.clicked.connect(self.btnGoToPositionOfInterest_clicked)
        btnSetSpectrumRange.clicked.connect(self.btnSetSpectrumRange_clicked)
        btnShowSpectrumWithMaxInt.clicked.connect(self.btnShowSpectrumWithMaxInt_clicked)
        btnSelectAddedItem.clicked.connect(self.btnSelectAddedItem_clicked)
        btnSetMapImageContrast.clicked.connect(self.btnSetMapImageContrast_clicked)
        btnExecuteSignalIntensity.clicked.connect(self.btnExecuteSignalIntensity_clicked)
        btnExecuteSignalToBaseline.clicked.connect(self.btnExecuteSignalToBaseline_clicked)
        btnExecuteSianglToHBaseline.clicked.connect(self.btnExecuteSianglToHBaseline_clicked)
        btnExecuteSignalToAxis.clicked.connect(self.btnExecuteSignalToAxis_clicked)
        btnAddCurrentSpectrum.clicked.connect(self.btnAddCurrentSpectrum_clicked)
        btnAddSpectrumFromFile.clicked.connect(self.btnAddSpectrumFromFile_clicked)
        btnAddSpectraFromObj.clicked.connect(self.btnAddSpectraFromObj_clicked)
        btnUpdateCustomName.clicked.connect(self.btnUpdateCustomName_clicked)
        btnExecuteSpectrumLinearSubtraction.clicked.connect(self.btnExecuteSpectrumLinearSubtraction_clicked)
        btnExecuteUnmixing.clicked.connect(self.btnExecuteUnmixing_clicked)
        # btnExportImages.clicked.connect(self.btnExportImages_clicked)
        btnExportSvg.clicked.connect(self.btnExportSvg_clicked)
        btnSaveTarget.clicked.connect(self.btnSaveTarget_clicked)
        btnCRRMaster.clicked.connect(self.btnCRRMaster_clicked)
        btnNRMaster.clicked.connect(self.btnNRMaster_clicked)
        btnSetWindowSize.clicked.connect(self.btnSetWindowSize_clicked)
        btnSelectWindow.clicked.connect(self.btnSelectWindow_clicked)
        btnExportData.clicked.connect(self.btnExportData_clicked)
        btnTrashFiles.clicked.connect(self.btnTrashFiles_clicked)
        btnExecutePlugins.clicked.connect(self.btnExecutePlugins_clicked)
        btnExecuteSavedActionFlows.clicked.connect(self.btnExecuteSavedActionFlows_clicked)
        btnHideAllInV2.clicked.connect(self.btnHideAllInV2_clicked)
        btnHideSelectedItem.clicked.connect(self.btnHideSelectedItem_clicked)
        btnHideRightAxis.clicked.connect(self.btnHideRightAxis_clicked)
        btnPause.clicked.connect(self.btnPause_clicked)
        # 特殊ボタン
        btnExportProcedures.clicked.connect(self.btnExportProcedures_clicked)
        btnImportProcedures.clicked.connect(self.btnImportProcedures_clicked)
        btnRUN.clicked.connect(self.btnRUN_clicked)
        btnRemove.clicked.connect(self.btnRemove_clicked)
        btnMoveUp.clicked.connect(self.btnMoveUp_clicked)
        btnMoveDown.clicked.connect(self.btnMoveDown_clicked)
    def focusInEvent(self, event):
        self.parent.focusChanged(self)
    def focusOutEvent(self, event):
        pass
    def dragEnterEvent(self, event):
        event.accept()
    def dropEvent(self, event):
        mimeData = event.mimeData()
        for mimetype in mimeData.formats():
            if mimetype == "text/uri-list":
                url_byte = mimeData.data(mimetype).data()
                file_path_list = parse.unquote(url_byte.decode()).replace('file://', '').replace('\r', '').strip().split("\n")
                if len(file_path_list) > 1:
                    warning_popup = popups.WarningPopup("Multiple items cannot be loaded.")
                    warning_popup.exec_()
                    return
                file_path = file_path_list[0]
                if file_path.endswith(".umx"):
                    self.btnImportProcedures_clicked(event=None, mode="DragAndDrop", file_path=file_path)
                else:
                    warning_popup = popups.WarningPopup("Only '.umx' file is supported.")
                    warning_popup.exec_()
                    return
    # プロセス系ボタン
    def btn_clicked(func):
        def _wrapper(self, event, **kwargs):
            each_layout, object_name = func(self)
            each_layout.setObjectName(object_name)
            each_layout.setStyleSheet("QWidget#%s{border: 1px solid gray; background-color: lightGray}"%object_name)
            self.process_layout.insertWidget(self.process_layout.count() - 1, each_layout)
            if event is None:
                each_layout.import_AF(**kwargs)
        return _wrapper
    @btn_clicked
    def btnOpenWindow_clicked(self):
        return OpenWindow(parent=self.process_layout, main_window=self.parent), "OW"
    @btn_clicked
    def btnCloseWindow_clicked(self):
        return CloseWindow(parent=self.process_layout, main_window=self.parent), "CW"
    @btn_clicked
    def btnTrashFiles_clicked(self):
        return TrashFiles(parent=self.process_layout, main_window=self.parent), "TF"
    @btn_clicked
    def btnPOISettings_clicked(self):
        return POISettings(parent=self.process_layout, main_window=self.parent), "POI"
    @btn_clicked
    def btnGoToPositionOfInterest_clicked(self):
        return GoToPositionOfInterest(parent=self.process_layout, main_window=self.parent), "GPI"
    @btn_clicked
    def btnSetSpectrumRange_clicked(self):
        return SetSpectrumRange(parent=self.process_layout, main_window=self.parent), "SSR"
    @btn_clicked
    def btnShowSpectrumWithMaxInt_clicked(self):
        return ShowSpectrumWithMaxInt(parent=self.process_layout, main_window=self.parent), "SMS"
    @btn_clicked
    def btnSelectAddedItem_clicked(self):
        return SelectAddedItem(parent=self.process_layout, main_window=self.parent), "SSC"
    @btn_clicked
    def btnSetMapImageContrast_clicked(self):
        return SetMapImageContrast(parent=self.process_layout, main_window=self.parent), "SIC"
    @btn_clicked
    def btnExecuteSignalIntensity_clicked(self):
        return ExecuteSignalIntensity(parent=self.process_layout, main_window=self.parent), "SINT"
    @btn_clicked
    def btnExecuteSignalToBaseline_clicked(self):
        return ExecuteSignalToBaseline(parent=self.process_layout, main_window=self.parent), "STB"
    @btn_clicked
    def btnExecuteSianglToHBaseline_clicked(self):
        return ExecuteSianglToHBaseline(parent=self.process_layout, main_window=self.parent), "STHB"
    @btn_clicked
    def btnExecuteSignalToAxis_clicked(self):
        return ExecuteSignalToAxis(parent=self.process_layout, main_window=self.parent), "STA"
    @btn_clicked
    def btnAddCurrentSpectrum_clicked(self):
        return AddCurrentSpectrum(parent=self.process_layout, main_window=self.parent), "ACS"
    @btn_clicked
    def btnAddSpectrumFromFile_clicked(self):
        return AddSpectrumFromFile(parent=self.process_layout, main_window=self.parent), "ASF"
    @btn_clicked
    def btnAddSpectraFromObj_clicked(self):
        return AddSpectraFromObj(parent=self.process_layout, main_window=self.parent), "ASF"
    @btn_clicked
    def btnUpdateCustomName_clicked(self):
        return UpdateCustomName(parent=self.process_layout, main_window=self.parent), "ACN"
    @btn_clicked
    def btnExecuteSpectrumLinearSubtraction_clicked(self):
        return ExecuteSpectrumLinearSubtraction(parent=self.process_layout, main_window=self.parent), "SSB"
    @btn_clicked
    def btnExecuteUnmixing_clicked(self):
        return ExecuteUnmixing(parent=self.process_layout, main_window=self.parent), "UMX"
    # @btn_clicked
    # def btnExportImages_clicked(self):
    #     return ExportImages(parent=self.process_layout, main_window=self.parent), "SI"
    @btn_clicked
    def btnExportSvg_clicked(self):
        return ExportSvg(parent=self.process_layout, main_window=self.parent), "ESG"
    @btn_clicked
    def btnSaveTarget_clicked(self):
        return SaveTarget(parent=self.process_layout, main_window=self.parent), "SS"
    @btn_clicked
    def btnCRRMaster_clicked(self):
        return CRRMaster(parent=self.process_layout, main_window=self.parent), "CRR"
    @btn_clicked
    def btnNRMaster_clicked(self):
        return NRMaster(parent=self.process_layout, main_window=self.parent), "CRR"
    @btn_clicked
    def btnSetWindowSize_clicked(self):
        return SetWindowSize(parent=self.process_layout, main_window=self.parent), "SWS"
    @btn_clicked
    def btnSelectWindow_clicked(self):
        return SelectWindow(parent=self.process_layout, main_window=self.parent), "SLW"
    @btn_clicked
    def btnExportData_clicked(self):
        return ExportData(parent=self.process_layout, main_window=self.parent), "EXD"
    @btn_clicked
    def btnExecutePlugins_clicked(self):
        return ExecutePlugins(parent=self.process_layout, main_window=self.parent), "SWS"
    @btn_clicked
    def btnExecuteSavedActionFlows_clicked(self):
        return ExecuteSavedActionFlows(parent=self.process_layout, main_window=self.parent), "EXP"
    @btn_clicked
    def btnHideAllInV2_clicked(self):
        return HideAllInV2(parent=self.process_layout, main_window=self.parent), "HV2"
    @btn_clicked
    def btnHideSelectedItem_clicked(self):
        return HideSelectedItem(parent=self.process_layout, main_window=self.parent), "HSI"
    @btn_clicked
    def btnHideRightAxis_clicked(self):
        return HideRightAxis(parent=self.process_layout, main_window=self.parent), "HRA"
    @btn_clicked
    def btnPause_clicked(self):
        return Pause(parent=self.process_layout, main_window=self.parent), "PUS"
    # 特殊ボタンアクション
    def btnSetPath_clicked(self, event):
        cur_text = self.path_entry.text()
        if os.path.exists(cur_text):
            new_path = cur_text
        else:
            new_path = gf.settings["last opened dir"]
        dir_path = QFileDialog.getExistingDirectory(self, 'select folder', new_path)
        if len(dir_path):
            self.path_entry.setText(dir_path)
    def btnExportProcedures_clicked(self, event):
        if self.process_layout.count() == 1:
            warning_popup = popups.WarningPopup("No action is added.")
            warning_popup.exec_()
            return
        # 保存場所   # デフォルトでは上書き保存する想定でのファイル名。
        # save_path, N = gf.get_save_path(os.path.join(gf.settings["method dir"], self.windowTitle()))
        save_path = os.path.join(gf.settings["method dir"], self.windowTitle())
        save_path, file_type = QFileDialog.getSaveFileName(self.parent, 'save as .umx file', save_path, filter="action flow files (*.umx)")
        if not save_path:
            return
        # 保存！
        procedures = []
        for process in self.process_layout.get_all_items():
            # ToolbarLayout の関数として、吐き出される。
            exported_process = process.export_AF()
            if exported_process[0] is None:
                warning_popup = popups.WarningPopup(exported_process[1])
                warning_popup.exec_()
                break
            procedures.append(exported_process)
        # 中断されなかった場合
        else:
            with open(save_path, 'w') as f:
                json.dump(procedures, f, indent=4)
            self.setWindowTitle(os.path.basename(save_path))
        # 中断された場合
    def btnImportProcedures_clicked(self, event=None, mode=None, **kwargs):
        if mode is None:
            file_path, file_type = QFileDialog.getOpenFileName(self, 'Select spctrum file', gf.settings["method dir"], filter="action flow file (*.umx)")
        elif mode == "DragAndDrop":
            file_path = kwargs["file_path"]
        if not file_path:
            return
        # 読み込み
        with open(file_path, 'r') as f:
            procedures = json.loads(f.read())
        # self.process_layout に追加
        for func_name, kwargs in procedures:
            func = getattr(self, "btn{0}_clicked".format(gf.snake2camel(func_name)))
            func(event=None, **kwargs)
        gf.settings["method dir"] = os.path.os.path.dirname(file_path)
        gf.save_settings_file()
        self.setWindowTitle(os.path.basename(file_path))
    def btnRemove_clicked(self, event):
        self.process_layout.remove_current_focused_item(new_focus=True)
    def btnMoveUp_clicked(self, event):
        self.process_layout.moveUp_current_focused_item()
    def btnMoveDown_clicked(self, event):
        self.process_layout.moveDown_current_focused_item()
    def btnRUN_clicked(self, event):
        self.parent.temp_variables = {}
        # action がない場合
        if self.process_layout.count() == 1:
            warning_popup = popups.WarningPopup("No action is added.")
            warning_popup.exec_()
            return
        # dir_path がない場合
        dir_path = self.path_entry.text()
        if not os.path.exists(dir_path):
            warning_popup = popups.WarningPopup("Folder named '{0}' could not be found.".format(dir_path))
            warning_popup.exec_()
            return
        # ext がない場合
        if len(self.cmbExt.currentData()) == 0:
            warning_popup = popups.WarningPopup("Extensions are not set.")
            warning_popup.exec_()
            return
        # ファイルごとに回す
        spc_path_list = []
        for ext in self.cmbExt.currentData():
            spc_path_list.extend(glob.glob("{0}/**/{1}".format(dir_path, ext), recursive=True))
        for spc_path in spc_path_list:
            # フォルダはスキップ？
            if os.path.isdir(spc_path):
                continue
            # 開いたファイルは、次のプロセスで受け取ることができる
            opened_window = None
            for process in self.process_layout.get_all_items():
                QCoreApplication.processEvents()
                try:
                    opened_window, continue_process = process.procedure(spc_path, opened_window)
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
        warning_popup = popups.WarningPopup("Error in '{0}' action.\n{1}\n\n{2}\n\nProcess was canceled.".format(process.title, spc_path, continue_process))
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
        self.title = "open window"
        # オプション
        self.window_type = QComboBox()
        self.window_type.addItems(["1 spectrum data", "hyperspectral data", "all '*.spc' data", "size unknown hyperspectral data", "filter by file name: None"])
        self.file_name_filter_idx = 4
        self.window_type.setItemData(self.file_name_filter_idx, "None")
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.window_type)
        self.setFixedHeight(gf.process_widget_height)
        # イベントコネクト
        self.window_type.activated.connect(self.item_activated)
    def item_activated(self, event=None):
        if event != self.file_name_filter_idx:
            return
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
        # プレサーチ（単一スペクトルチェック）
        fnsub, matchedObject_list = gf.pre_open_search(spc_path)
        # 通常ファイルが開かれた場合
        if matchedObject_list is not None:
            pass
        # 特殊ファイルが開かれた場合
        else:
            spc_file, traceback = gf.open_spc_spcl(spc_path)
            if spc_file is None:
                return None, traceback
            fnsub = spc_file.fnsub
            matchedObject_list = []
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
        main_window = self.parent.parent.parent
        do_not_show_again = main_window.temp_variables.setdefault("DNSA_open_window", False)
        if (len(matchedObject_list) == 0) & (fnsub > 1) & (not do_not_show_again):
            warning_popup = popups.WarningPopup("The file '{0}' may be opened for the first time and may require size settings. Do you want to continue?".format(spc_path), title="WARNING", p_type="YesToAll")
            done = warning_popup.exec_()
            if done == 16384:   # YES
                pass
            elif done == 32768: # YES to ALL
                main_window.temp_variables["DNSA_open_window"] = True
            else:   # NO
                return None, "The process to open '{0}' was canceled. It may be opened for the first time and require size settings before any processes.".format(spc_path)
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
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {"window_type":self.window_type.currentText()}
        if self.window_type.currentIndex() == self.file_name_filter_idx:
            kwargs["itemData"] = self.window_type.currentData()
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        window_type = kwargs.get("window_type", self.window_type.currentText())
        if window_type.startswith("filter by file name:"):
            filter_name = kwargs.get("itemData", "None")
            self.window_type.setCurrentIndex(self.file_name_filter_idx)
            self.window_type.setItemData(self.file_name_filter_idx, filter_name)
            self.window_type.setItemText(self.file_name_filter_idx, "filter by file name: {0}".format(filter_name))
        else:
            self.window_type.setCurrentText(window_type)
class CloseWindow(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "CW"
        self.option = {}
        self.title = "close window"
        # オプション
        self.cmb = QComboBox()
        self.cmb.addItems(["current focused", "all window"])
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(QLabel("target: "))
        self.layout.addWidget(self.cmb)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        opened_window.toolbar_layout.close_window(mode="macro", target=self.cmb.currentText())
        return None, "continue"
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {"target":self.cmb.currentText()}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        target = kwargs.get("target", "current focused")
        self.cmb.setCurrentText(target)
class TrashFiles(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "TF"
        self.option = {}
        self.title = "trash files"
        # オプション
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["files to keep", "files to trash"])
        self.target = QLineEdit()
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.cmb_type)
        self.layout.addWidget(self.target)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        # 同じフォルダに２つ以上 spc ファイルがあり、既に削除されている場合はスキップ
        if not os.path.exists(spc_path):
            return None, "skip"
        main_window = self.parent.parent.parent
        dir_path, file_name, file_name_wo_ext = gf.file_name_processor(spc_path)
        # 次のループでも使い情報を格納
        processed_dir = main_window.temp_variables.setdefault("PD_trash_files", [])
        do_not_show_again = main_window.temp_variables.setdefault("DNSA_trash_files", False)
        trash_dir = main_window.temp_variables.setdefault("TD_trash_files", None)
        if dir_path not in processed_dir:
            processed_dir.append(dir_path)
        else:
            return None, "skip"
        # 同じフォルダ内のファイルを探索
        is_files_to_trash_selected = self.cmb_type.currentText() == "files to trash"
        all_path_list = glob.glob("{0}/*".format(dir_path), recursive=False)
        all_file_names = []
        is_remove_target = []
        for path_name in all_path_list:
            # フォルダはスキップ
            if os.path.isdir(path_name):
                continue
            file_name = os.path.basename(path_name)
            matched_object = re.search(self.target.text(), file_name)
            all_file_names.append(file_name)
            if (matched_object is not None) == is_files_to_trash_selected:
                is_remove_target.append(True)
            else:
                is_remove_target.append(False)
        # ポップアップ
        if not do_not_show_again:
            def btnOK_DNSA_clicked(self_, event):
                main_window.temp_variables["DNSA_trash_files"] = True
                self_.done(1)
            message_popup = popups.MessageDialogWithCkbxes(
                message="Checked files will be moved to newly created 'trash' folder.", 
                p_type="Custom", 
                ckbx_names=all_file_names, 
                is_checked_list=is_remove_target, 
                btn_names=["btnCancel", "btnOK_DNSA"], 
                btn_funcs=[None, btnOK_DNSA_clicked], 
                btn_labels = ["Cancel", "OK (do not show again)"]
                )
            done = message_popup.exec_()
            all_file_names = []
            is_remove_target = []
            for ckbx in message_popup.ckbx_list:
                all_file_names.append(ckbx.text())
                is_remove_target.append(ckbx.isChecked())
        else:
            done = 1
        if done == 0:
            return None, "Aborted by user."
        # 削除フォルダ作製
        if trash_dir is None:
            master_dir = self.parent.parent.path_entry.text()
            trash_dir, N = gf.get_save_dir(os.path.join(master_dir, "trash"))
            os.mkdir(trash_dir)
            main_window.temp_variables["TD_trash_files"] = trash_dir
        # 削除（移動）
        for file_name, remove in zip(all_file_names, is_remove_target):
            if remove:
                # 同盟ファイル・フォルダがある場合、rename しながら移動
                file_name_in_trash, N = gf.get_save_path(os.path.join(trash_dir, file_name))
                shutil.move(os.path.join(dir_path, file_name), file_name_in_trash)
        return None, "continue"
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {"target_type":self.cmb_type.currentText(), "target":self.target.text()}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        self.cmb_type.setCurrentText(kwargs["target_type"])
        self.target.setText(kwargs["target"])
class POISettings(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "POI"
        self.title = "set position of interest"
        self.continue_process = None
        self.opened_window = None
        # コンテンツ
        self.ckbx_ask = QCheckBox("pause")
        self.ckbx_ask.setChecked(True)
        self.default_name = QLineEdit("default_name")
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.default_name)
        self.layout.addWidget(QLabel("  "))
        self.layout.addWidget(self.ckbx_ask)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        if opened_window.window_type != "ms":
            return None, "Invalid window type."
        if not self.ckbx_ask.isChecked():
            poi_key = self.default_name.text()
            x, y = opened_window.spectrum_widget.cur_x, opened_window.spectrum_widget.cur_y
            # 名前が重複する場合は削除
            if poi_key in opened_window.spectrum_widget.spc_file.log_dict[b"point_of_interest_dict"].keys():
                poi_idx = opened_window.parent.poi_manager.get_poi_idx(poi_key=poi_key)
                opened_window.parent.poi_manager.poi_layout.set_focus(idx=poi_idx)
                opened_window.parent.poi_manager.btn_poi_del_clicked()
                # focus すると、スペクトルの場所が移動してしまうので。
                opened_window.toolbar_layout.set_spectrum_and_crosshair(x, y)
            log = opened_window.parent.poi_manager.execute_poi_add_fm_macro(poi_key=poi_key, poi_data=(x, y))
            return opened_window, log
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
            x, y = opened_window.spectrum_widget.cur_x, opened_window.spectrum_widget.cur_y
            if poi_key in opened_window.spectrum_widget.spc_file.log_dict[b"point_of_interest_dict"].keys():
                warning_popup = popups.WarningPopup("The name '{0}' is already taken. Do you really want to overwrite?".format(poi_key), title="WARNING", p_type="Bool")
                done = warning_popup.exec_()
                if done == 16384:   # YES
                    poi_idx = opened_window.parent.poi_manager.get_poi_idx(poi_key=poi_key)
                    opened_window.parent.poi_manager.poi_layout.set_focus(idx=poi_idx)
                    opened_window.parent.poi_manager.btn_poi_del_clicked()
                    # focus すると、スペクトルの場所が移動してしまうので。
                    opened_window.toolbar_layout.set_spectrum_and_crosshair(x, y)
                else:   # NO
                    return
            log = opened_window.parent.poi_manager.execute_poi_add_fm_macro(poi_key=poi_key, poi_data=(x, y))
            # 脱ループ
            loop.exit()
            self.opened_window = opened_window
            self.continue_process = log
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
        poi_settings_popup = popups.PoiSettingsPopup(parent=opened_window, initial_values=(0,0), labels=("x position", "y position"), title="set point of interest", poi_key="poi1", skip=True)
        poi_settings_popup.setWindowFlags(Qt.WindowStaysOnTopHint)
        poi_settings_popup.set_spinbox_range((0, x_size-1), "RS1")
        poi_settings_popup.set_spinbox_range((0, y_size-1), "RS2")
        poi_settings_popup.setValues(initial_values)
        poi_settings_popup.set_poi_key(poi_key)
        # イベントコネクト
        opened_window.map_widget.scene().sigMouseClicked.connect(poi_settings_popup.on_map_widget_click)
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
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {
            "default_name":self.default_name.text(), 
            "pause":self.ckbx_ask.isChecked()
        }
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        self.default_name.setText(kwargs["default_name"])
        self.ckbx_ask.setChecked(kwargs.get("pause", True))
class GoToPositionOfInterest(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "GPI"
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
            return None, "No window is opened."
        log = opened_window.toolbar_layout.go_to_position_of_interest(poi_key=self.poi_key.text())
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {"poi_key":self.poi_key.text()}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        self.poi_key.setText(kwargs["poi_key"])
class ShowSpectrumWithMaxInt(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "SMS"
        self.title = "show spectrum at max. int."
        self.option = {}
        # コンテンツ
        # self.cmb_type = QComboBox()
        # self.cmb_type.addItems(["all area", "around center"])
        self.spbx_value = QDoubleSpinBox()
        self.spbx_value.setMinimum(0)
        self.spbx_value.setMaximum(1)
        self.spbx_value.setValue(1)
        self.spbx_value.setSingleStep(0.1)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        # self.layout.addWidget(QLabel("target: "))
        # self.layout.addWidget(self.cmb_type)
        self.layout.addWidget(self.spbx_value)
        self.layout.addWidget(QLabel("(set 1 to target all area)"))
        self.setFixedHeight(gf.process_widget_height)
        # イベントコネクト
        # self.spbx_value.hide()
        # self.cmb_type.currentTextChanged.connect(self.cmb_changed)
    # def cmb_changed(self, event):
    #     if event == "all area":
    #         self.spbx_value.hide()
    #     elif event == "around center":
    #         self.spbx_value.show()
    #     else:
    #         raise Exception("unknown type: {0}".format(event))
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        # log = opened_window.toolbar_layout.show_spectrum_with_max_int(target=self.cmb_type.currentText(), value=self.spbx_value.value())
        log = opened_window.toolbar_layout.show_spectrum_with_max_int(value=self.spbx_value.value())
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        # kwargs = {"target":self.cmb_type.currentText(), "value":self.spbx_value.value()}
        kwargs = {"value":self.spbx_value.value()}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        target = kwargs.get("target", "all area")
        value = kwargs.get("value", 1)
        # self.cmb_type.setCurrentText(target)
        self.spbx_value.setValue(value)
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
#             return None, "No window is opened.".format(self.title)
#         if opened_window.window_type == "ms":
#             if opened_window.cur_displayed_map_content is None:
#                 return None, "Images must be set before selection.".format(self.title)
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
class SelectAddedItem(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "SAI"
        self.title = "select from added items"
        self.option = {}
        # コンテンツ
        self.map_or_spectrum = QComboBox()
        self.map_or_spectrum.addItems(["map", "spectrum", "preprocess"])
        self.tgt_cmb = QComboBox()
        self.tgt_cmb.addItems(["index", "target"])
        self.tgt_txt = QLineEdit("")
        self.tgt_idx = QSpinBox()
        self.tgt_idx.setRange(-999, 999)
        self.tgt_idx.setValue(0)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.map_or_spectrum)
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
            return None, "No window is opened."
        log = opened_window.toolbar_layout.select_added_item(
            mode="macro", 
            map_or_spectrum=self.map_or_spectrum.currentText(), 
            target_type=self.tgt_cmb.currentText(), 
            target_text=self.tgt_txt.text(), 
            target_idx=self.tgt_idx.value()
            )
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {
            "map_or_spectrum":self.map_or_spectrum.currentText(), 
            "target_type":self.tgt_cmb.currentText(), 
            "target_text":self.tgt_txt.text(), 
            "target_idx":self.tgt_idx.value(), 
            }
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        self.map_or_spectrum.setCurrentText(kwargs["map_or_spectrum"])
        self.tgt_cmb.setCurrentText(kwargs["target_type"])
        self.tgt_txt.setText(kwargs["target_text"])
        self.tgt_idx.setValue(int(kwargs["target_idx"]))
class SetSpectrumRange(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "SSR"
        self.option = {}
        self.title = "set spectrum range"
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
        self.layout.addWidget(QLabel(self.title))
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
            return None, "No window is opened."
        log = opened_window.toolbar_layout.set_spectrum_range(
            mode="macro", 
            xy=self.cmb.currentText(), 
            range_x=[self.RS_left.value(), self.RS_right.value()], 
            range_y=[self.y_btm.currentText(), self.y_top.currentText()]
            )
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {
            "xy":self.cmb.currentText(), 
            "range_x":[self.RS_left.value(), self.RS_right.value()], 
            "range_y":[self.y_btm.currentText(), self.y_top.currentText()]
            }
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        xy = kwargs["xy"]
        range_x = kwargs["range_x"]
        range_y = kwargs["range_y"]
        self.cmb.setCurrentText(xy)
        self.RS_left.setValue(range_x[0])
        self.RS_right.setValue(range_x[1])
        self.y_btm.setCurrentText(range_y[0])
        self.y_top.setCurrentText(range_y[1])
class SetMapImageContrast(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "SIC"
        self.option = {}
        self.title = "set map image contrast"
        # オプション
        self.range_bottom =  QSpinBox()
        self.range_top =  QSpinBox()
        self.range_bottom.setMinimum(0)
        self.range_top.setMinimum(0)
        self.range_bottom.setMaximum(65535)
        self.range_top.setMaximum(65535)
        self.range_bottom.setValue(0)
        self.range_top.setValue(65535)
        self.cmb_bit = QComboBox()
        self.cmb_bit.addItems(["8bit", "16bit", "32bit"])
        self.cmb_32bit_idx = 2
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.range_bottom)
        self.layout.addWidget(self.range_top)
        self.layout.addWidget(self.cmb_bit)
        self.setFixedHeight(gf.process_widget_height)
        # イベントコネクト
        self.cmb_bit.currentIndexChanged.connect(self.cmb_bit_changed)
    def cmb_bit_changed(self, event):
        if event == self.cmb_32bit_idx:
            self.range_top.hide()
            self.range_bottom.hide()
        else:
            self.range_top.show()
            self.range_bottom.show()
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        if opened_window.window_type != "ms":
            return opened_window, "Invalid window type."
        log = opened_window.toolbar_layout.set_map_image_contrast(contrast_range=(self.range_bottom.value(), self.range_top.value()), bit=self.cmb_bit.currentText())
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {
            "contrast_range":[self.range_bottom.value(), self.range_top.value()], 
            "bit":self.cmb_bit.currentText()
            }
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        contrast_range = kwargs["contrast_range"]
        bit = kwargs.get("bit", "16bit")
        self.range_bottom.setValue(contrast_range[0])
        self.range_top.setValue(contrast_range[1])
        self.cmb_bit.setCurrentText(bit)
class ExecuteSignalIntensity(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "STB"
        self.option = {}
        self.title = "signal intensity"
        # オプション
        self.RS_val =  QSpinBox()
        self.RS_val.setMinimum(0)
        self.RS_val.setMaximum(65535)
        self.RS_val.setValue(2950)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.RS_val)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        log = opened_window.toolbar_layout.execute_signal_intensity(mode="macro", RS=self.RS_val.value())
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {"mode":"macro", "RS":self.RS_val.value()}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        self.RS_val.setValue(kwargs["RS"])
class ExecuteSignalToBaseline(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "STB"
        self.option = {}
        self.title = "signal to baseline"
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
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.range_bottom)
        self.layout.addWidget(self.range_top)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        log = opened_window.toolbar_layout.execute_signal_to_baseline(mode="macro", RS_set=[self.range_bottom.value(), self.range_top.value()])
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {"mode":"macro", "RS_set":[self.range_bottom.value(), self.range_top.value()]}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        bottom_value, top_value = kwargs["RS_set"]
        self.range_bottom.setValue(bottom_value)
        self.range_top.setValue(top_value)
class ExecuteSianglToHBaseline(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "STHB"
        self.option = {}
        self.title = "signal to horizontal baseline"
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
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.range_bottom)
        self.layout.addWidget(self.range_top)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        log = opened_window.toolbar_layout.execute_signal_to_H_baseline(mode="macro", RS_set=[self.range_bottom.value(), self.range_top.value()])
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {"mode":"macro", "RS_set":[self.range_bottom.value(), self.range_top.value()]}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        bottom_value, top_value = kwargs["RS_set"]
        self.range_bottom.setValue(bottom_value)
        self.range_top.setValue(top_value)
class ExecuteSignalToAxis(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "STA"
        self.option = {}
        self.title = "signal to axis"
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
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.range_bottom)
        self.layout.addWidget(self.range_top)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        log = opened_window.toolbar_layout.execute_signal_to_axis(mode="macro", RS_set=[self.range_bottom.value(), self.range_top.value()])
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {"mode":"macro", "RS_set":[self.range_bottom.value(), self.range_top.value()]}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        bottom_value, top_value = kwargs["RS_set"]
        self.range_bottom.setValue(bottom_value)
        self.range_top.setValue(top_value)
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
            return None, "No window is opened."
        log = opened_window.toolbar_layout.add_current_spectrum()
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        pass
class AddSpectrumFromFile(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "ASF"
        self.title = "add spectrum from a file (d)"
        # コンテンツ
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["from a file", "target", "target path"])
        self.cmb_type.setItemData(0, "")
        self.cmb_type.setItemData(1, "")
        self.cmb_type.setItemData(2, "")
        self.cmb_type.setItemData(3, "directory_path/regular expression to specify file name(s)")
        self.path_entry = QLineEdit()
        btnSetPath = QPushButton("...")
        btnSetPath.setFixedWidth(40)
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
        self.path_entry.textChanged.connect(self.path_entry_changed)
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
                    Enter the directory path and the regular expression (re.search) to specify file(s).
                    <br>
                    All files contained in the folder specified by characters leading up to the left of the last appeared file separator.
                    \nwill be recursively collected and searched.
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
    def path_entry_changed(self, event):
        self.cmb_type.setItemData(self.cmb_type.currentIndex(), event)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        log = opened_window.toolbar_layout.add_spectrum_from_file(mode="macro", selection_type=self.cmb_type.currentText(), pattern=self.path_entry.text())
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        selection_type = self.cmb_type.currentText()
        pattern = self.path_entry.text()
        # REGISTER
        kwargs = {
            "selection_type":selection_type, 
            "pattern":pattern, 
            }
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        self.cmb_type.setCurrentText(kwargs["selection_type"])
        self.path_entry.setText(kwargs["pattern"])
class AddSpectraFromObj(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "ASO"
        self.title = "add spectrum from a file (s)"
        # コンテンツ
        self.data = None
        self.path_entry = QLineEdit()
        self.path_entry.setReadOnly(True)
        self.path_entry.setStyleSheet("QLineEdit{background-color:rgba(0,0,0,0)}")
        btnSetPath = QPushButton("...")
        btnSetPath.setFixedWidth(40)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.path_entry)
        self.layout.addWidget(QLabel(" "))
        self.layout.addWidget(btnSetPath)
        self.setFixedHeight(gf.process_widget_height)
        # イベントコネクト
        btnSetPath.clicked.connect(self.btnSetPath_clicked)
    def btnSetPath_clicked(self, event):
        cur_path = self.path_entry.text()
        if not os.path.exists(cur_path):
            cur_path = gf.settings["last opened dir"]
        file_path, file_type = QFileDialog.getOpenFileName(self, 'select procedure file', cur_path, filter="procedure file (*.spc)")# *.out *.cspc *.spcl)")
        if len(file_path):
            data, log = self.get_data_from_file_path(file_path)
            if data is None:
                warning_popup = popups.WarningPopup(log)
                warning_popup.exec_()
                return
            else:
                self.data = data
                self.path_entry.setText(file_path)
    def get_data_from_file_path(self, file_path):
        # REGISTER
        if not os.path.exists(file_path):
            return [None, "\n\nfile_path\n{0}\n\nFile does not exisit.".format(file_path)]
        fnsub, matchedObject_list = gf.pre_open_search(file_path)
        if fnsub > 1:
            return [None, "\n\nfile_path\n{0}\n\nThe file contains more than 1 spectra.".format(file_path)]
        spc_file, traceback = gf.open_spc_spcl(file_path)
        if spc_file is None:
            return [None, "\n\nfile_path\n{0}\n\n{1}".format(file_path, traceback)]
        xData = list(spc_file.x)
        yData = list(spc_file.sub[0].y)
        info = {
                "content":"spectrum",
                "type":"added",
                "detail":file_path,
                "draw":"static",
                "data":""
            }
        return {"xData":xData, "yData":yData, "info":info}, None
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        if self.data is None:
            return None, "Data is not set."
        log = opened_window.toolbar_layout.add_spectra_from_obj(mode="macro", xData=self.data["xData"], yData=self.data["yData"], info=self.data["info"])
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        if self.data is None:
            return [None, "Error in exporting '{0}' action.\n\nData is not set.".format(self.title)]
        pattern = self.path_entry.text()
        kwargs = {
            "pattern":pattern, 
            "data":self.data
            }
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        self.path_entry.setText(kwargs["pattern"])
        self.data = kwargs["data"]
class UpdateCustomName(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "ACN"
        self.title = "set custom name to added content"
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
            return None, "No window is opened."
        log = opened_window.toolbar_layout.update_custom_name(mode="macro", map_or_spc=self.map_or_spc_cmb.currentData(), custom_name=self.custom_name.text())
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {
            "map_or_spc":self.map_or_spc_cmb.currentData(), 
            "custom_name":self.custom_name.text()
            }
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        map_or_spc = "map"
        if kwargs["map_or_spc"] == "spc":
            map_or_spc = "spectrum"
        self.map_or_spc_cmb.setCurrentText(map_or_spc)
        self.custom_name.setText(kwargs["custom_name"])
class ExecuteSpectrumLinearSubtraction(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "SSB"
        self.option = {}
        self.title = "subtract spectrum"
        # オプション
        self.cmb = QComboBox()
        self.cmb.addItems(["to hori. axis", "to hori. line", "to angl. line", "'n' as 1", "advanced"])
        self.n1_idx = 3
        self.advanced_idx = 4
        self.cmb.setItemData(self.advanced_idx, {"cmb":"fit 'result' to the horizontal axis", "seRS_set":[(1900, 2500)]})
        self.range_bottom =  QSpinBox()
        self.range_top =  QSpinBox()
        self.range_bottom.setMinimum(0)
        self.range_top.setMinimum(0)
        self.range_bottom.setMaximum(65535)
        self.range_top.setMaximum(65535)
        self.range_bottom.setValue(1900)
        self.range_top.setValue(2500)
        self.advanced_label = QLabel("N range: 1")
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.cmb)
        self.layout.addWidget(self.range_bottom)
        self.layout.addWidget(self.range_top)
        self.layout.addWidget(self.advanced_label)
        self.setFixedHeight(gf.process_widget_height)
        # イベントコネクト
        self.cmb.activated.connect(self.item_activated)
        self.advanced_label.hide()
    def item_activated(self, event):
        if event == self.n1_idx:
            self.range_bottom.hide()
            self.range_top.hide()
            self.advanced_label.hide()
            return
        elif event != self.advanced_idx:
            self.range_bottom.show()
            self.range_top.show()
            self.advanced_label.hide()
            return
        self.range_bottom.hide()
        self.range_top.hide()
        self.advanced_label.show()
        advanced_popup = popups.MultipleRangeSettingsPopup(
            parent=self.parent, 
            cmb_messages=[
                "fit 'result' to the horizontal axis", 
                "fit 'result' to the horizontal line", 
                "fit 'result' to the angled line", 
                "set 'n' as 1"]
            )
        advanced_popup.set_from_data(self.cmb.currentData())
        done = advanced_popup.exec_()
        if done:
            self.cmb.setItemData(self.advanced_idx, advanced_popup.get_data())
            self.advanced_label.setText("N range: {0}".format(advanced_popup.N_valid_row))
        else:
            self.cmb.setCurrentIndex(0)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        seRS_set, method = self.get_range_method()
        # 実行
        log = opened_window.toolbar_layout.execute_spectrum_linear_subtraction(event=None, mode="macro", range=seRS_set, method=method)
        return opened_window, log
    def get_range_method(self):
        if self.cmb.currentIndex() == self.advanced_idx:
            data = self.cmb.itemData(self.advanced_idx)
            seRS_set = data["seRS_set"]
            method = data["cmb"]
        else:
            seRS_set = [(self.range_bottom.value(), self.range_top.value())]
            method = self.cmb.currentText()
        return seRS_set, method
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        seRS_set, method = self.get_range_method()
        kwargs = {
            "range":seRS_set, 
            "method":method
            }
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        seRS_set = kwargs["range"]
        method = kwargs["method"]
        # 設定
        if len(seRS_set) == 1:
            self.cmb.setCurrentText(method)
            self.range_bottom.setValue(seRS_set[0][0])
            self.range_top.setValue(seRS_set[0][1])
            if self.cmb.currentIndex() == self.n1_idx:
                self.range_bottom.hide()
                self.range_top.hide()
        # advanced settings
        else:
            self.range_bottom.hide()
            self.range_top.hide()
            self.cmb.setItemData(self.advanced_idx, {"seRS_set":seRS_set, "cmb":method})
            self.cmb.setCurrentIndex(self.advanced_idx)
            self.advanced_label.setText("N range: {0}".format(len(seRS_set)))
            self.advanced_label.show()
class ExecuteUnmixing(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "UMX"
        self.option = {}
        self.title = "unmixing"
        # コンテンツ
        self.range_left = QSpinBox()
        self.range_left.setMinimum(-65535)
        self.range_left.setMaximum(65535)
        self.range_left.setValue(1900)
        self.range_right = QSpinBox()
        self.range_right.setMinimum(-65535)
        self.range_right.setMaximum(65535)
        self.range_right.setValue(2500)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.range_left)
        self.layout.addWidget(self.range_right)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        log = opened_window.toolbar_layout.execute_unmixing(mode="macro", umx_range=(self.range_left.value(), self.range_right.value()))
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {"umx_range":(self.range_left.value(), self.range_right.value())}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        seRS = kwargs["umx_range"]
        self.range_left.setValue(seRS[0])
        self.range_right.setValue(seRS[1])
class ExportSvg(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "ESG"
        self.option = {}
        self.title = "capture current spectrum"
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        opened_window.toolbar_layout.export_svg()
        return opened_window, "continue"
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        pass
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
            return None, "action. No window is opened."
        opened_window.toolbar_layout.save_target()
        return opened_window, "continue"
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        pass
class CRRMaster(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "CRR"
        self.option = {}
        self.title = "cosmic ray removal"
        # オプション
        self.crr_target_files = QComboBox()
        self.crr_target_files.addItems(["skip action when possible", "skip files with CRR data", "execute for all", "revert"])
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.crr_target_files)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        if opened_window.window_type != "ms":
            return opened_window, "Invalid window type."
        log = opened_window.toolbar_layout.CRR_master(mode="macro", target_files=self.crr_target_files.currentText())
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {"mode":"macro", "target_files":self.crr_target_files.currentText()}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        self.crr_target_files.setCurrentText(kwargs["target_files"])
class NRMaster(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "NF"
        self.option = {}
        self.title = "PCA based noise filter"
        # オプション
        self.nr_target_files = QComboBox()
        self.nr_target_files.addItems(["skip action when possible", "skip files with NR data", "execute for all", "revert"])
        self.N_components = QSpinBox()
        self.N_components.setMinimum(0)
        self.N_components.setMaximum(9999)
        self.N_components.setValue(100)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.N_components)
        self.layout.addWidget(self.nr_target_files)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        if opened_window.window_type != "ms":
            return opened_window, "Invalid window type."
        log = opened_window.toolbar_layout.NR_master(mode="macro", target_files=self.nr_target_files.currentText(), N_components=self.N_components.value())
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {
            "mode":"macro", 
            "target_files":self.nr_target_files.currentText(), 
            "N_components":self.N_components.value()
            }
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        self.nr_target_files.setCurrentText(kwargs["target_files"])
        self.N_components.setValue(kwargs["N_components"])
class SetWindowSize(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "SWS"
        self.option = {}
        self.title = "set window size"
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
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(QLabel(" w:"))
        self.layout.addWidget(self.w)
        self.layout.addWidget(QLabel(" h:"))
        self.layout.addWidget(self.h)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        log = opened_window.toolbar_layout.set_window_size(width_height=(self.w.value(), self.h.value()))
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {"width_height":[self.w.value(), self.h.value()]}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        width_height = kwargs["width_height"]
        self.w.setValue(width_height[0])
        self.h.setValue(width_height[1])
class SelectWindow(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "SWS"
        self.option = {}
        self.title = "select window"
        # オプション
        self.spbx_idx = QSpinBox()
        self.spbx_idx.setMinimum(-65535)
        self.spbx_idx.setMaximum(65535)
        self.spbx_idx.setValue(0)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(QLabel(" target:"))
        self.layout.addWidget(self.spbx_idx)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            print(self.parent)
            target_window, log = self.parent.parent.parent.select_window(mode="macro", idx=self.spbx_idx.value())
        else:
            target_window, log = opened_window.toolbar_layout.select_window(mode="macro", idx=self.spbx_idx.value())
        return target_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {"idx":self.spbx_idx.value()}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        self.spbx_idx.setValue(kwargs["idx"])
class ExportData(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "EXD"
        self.option = {}
        self.title = "export data"
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
        self.layout.addWidget(QLabel(self.title))
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
            return None, "No window is opened."
        log = opened_window.toolbar_layout.export_data(
            map_or_spectrum=self.cmb_content.currentText(), 
            ext_ask=getattr(self, "cmb_export_{0}".format(self.cmb_content.currentText()[0])).currentData()
            )
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {
            "map_or_spectrum":self.cmb_content.currentText(), 
            "ext_ask":getattr(self, "cmb_export_{0}".format(self.cmb_content.currentText()[0])).currentData()
            }
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        map_or_spectrum = kwargs["map_or_spectrum"]
        self.cmb_content.setCurrentText(map_or_spectrum)
        target_cmb = getattr(self, "cmb_export_{0}".format(map_or_spectrum[0]))
        for i in range(target_cmb.count()):
            if target_cmb.itemData(i) == kwargs["ext_ask"]:
                target_cmb.setCurrentIndex(i)
                break
class ExecutePlugins(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "IP"
        self.option = {}
        self.title = "imported plugins"
        # オプション
        self.action_type = QComboBox()
        for action in self.main_window.imported_plugins.actions():
            action_name = action.iconText()
            self.action_type.addItem(action_name, action)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.action_type)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        self.parent.parent.parent.temp_variables["clear temp_variables"] = False
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
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        action_name = self.action_type.currentText()
        if action_name not in [action.iconText() for action in self.main_window.imported_plugins.actions()]:
            return [None, "Error in exporting '{0}' action.\nCould not load:\n\n{1}".format(self.title, action_name)]
        kwargs = {"action_name":action_name}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        action_name = kwargs["action_name"]
        if action_name not in [action.iconText() for action in self.main_window.imported_plugins.actions()]:
            warning_popups = popups.WarningPopup("No plugin named\n'{0}'\nfound in '{1}' action.\nSelect new plugin before executing the action flow.".format(action_name, self.title))
            warning_popups.exec_()
            action_name = "unknown plugin: '{0}'".format(action_name)
            self.action_type.addItem(action_name)
        self.action_type.setCurrentText(action_name)
class ExecuteSavedActionFlows(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "EXP"
        self.title = "exported Action Flow"
        self.option = {}
        # オプション中身
        self.path_entry = QLineEdit()
        self.path_entry.setText("method ('*.umx') path")
        btnSetPath = QPushButton("...")
        btnSetPath.clicked.connect(self.btnSetPath_clicked)
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
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
            return None, "No window is opened."
        log = opened_window.toolbar_layout.execute_saved_action_flows(mode="macro", file_path=self.path_entry.text())
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        file_path = self.path_entry.text()
        try:
            with open(file_path, 'r') as f:
                procedures = json.loads(f.read())
        except:
            return [None, "Error in exporting '{0}' action.\nCould not load:\n\n{1}".format(self.title, file_path)]
        kwargs = {
            "file_path":file_path, 
            "procedures":procedures
            }
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        self.path_entry.setText(kwargs["file_path"])
class HideSelectedItem(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "HSI"
        self.option = {}
        self.title = "hide selected item"
        # コンテンツ
        self.map_or_spectrum = QComboBox()
        self.map_or_spectrum.addItems(["map", "spectrum", "preprocess"])
        self.hide_show = QComboBox()
        self.hide_show.addItems(["hide", "show"])
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(QLabel("target: "))
        self.layout.addWidget(self.map_or_spectrum)
        self.layout.addWidget(self.hide_show)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        log = opened_window.toolbar_layout.hide_selected_item(mode="macro", map_or_spectrum=self.map_or_spectrum.currentText(), hide_show=self.hide_show.currentText())
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {"map_or_spectrum":self.map_or_spectrum.currentText(), "hide_show":self.hide_show.currentText()}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        self.map_or_spectrum.setCurrentText(kwargs["map_or_spectrum"])
        self.hide_show.setCurrentText(kwargs["hide_show"])
class HideAllInV2(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "HV2"
        self.option = {}
        self.title = "hide all items in view box 2"
        # コンテンツ
        self.cmb_hide_show = QComboBox()
        self.cmb_hide_show.addItems(["hide", "show"])
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.cmb_hide_show)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        opened_window.toolbar_layout.hide_all_in_v2(mode="macro", var_name="pseudo", hide_show=self.cmb_hide_show.currentText())
        return opened_window, "continue"
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {"hide_show":self.cmb_hide_show.currentText()}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        self.cmb_hide_show.setCurrentText(kwargs["hide_show"])
class HideRightAxis(my_w.ClickableQWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.type = "HRA"
        self.option = {}
        self.title = "hide right axis for view box 2"
        # オプション
        self.cmb_hide_show = QComboBox()
        self.cmb_hide_show.addItems(["hide", "show"])
        # レイアウト
        self.layout.setContentsMargins(11,0,11,0)
        self.layout.addWidget(QLabel(self.title))
        self.layout.addStretch(1)
        self.layout.addWidget(self.cmb_hide_show)
        self.setFixedHeight(gf.process_widget_height)
    def procedure(self, spc_path=None, opened_window=None):
        if opened_window is None:
            return None, "No window is opened."
        QCoreApplication.processEvents()
        log = opened_window.toolbar_layout.hide_right_axis(mode="macro", hide_show=self.cmb_hide_show.currentText())
        return opened_window, log
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {"hide_show":self.cmb_hide_show.currentText()}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        self.cmb_hide_show.setCurrentText(kwargs["hide_show"])
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
            return None, "No window is opened."
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
    def export_AF(self):
        func_name = gf.camel2snake(self.__class__.__name__)
        kwargs = {}
        return [func_name, kwargs]
    def import_AF(self, **kwargs):
        pass




