# -*- Coding: utf-8 -*-

# On Terminal Perform the follwoing ################
# cd /Users/masaaki/Google Drive/8_miniconda/_env_base/ImageCUBE/ImageCUBE_021
# fbs run
# fbs freeze
# fbs installer
# https://build-system.fman.io/manual/#get_resource
####################################################

import os, sys
import spc
import re
import numpy as np
from urllib import parse
import functools
import pickle
import glob
import traceback
import io

from PyQt5.QtWidgets import (
    QMainWindow, 
    QFileDialog, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout,  
    QSizePolicy, 
    QMenuBar, 
    QAction, 
    )
from PyQt5.QtCore import Qt, QEvent, pyqtSignal, QCoreApplication
from PyQt5.QtGui import QIcon
import pyqtgraph as pg

from Modules import my_widgets as my_w
from Modules import popups
from Modules import general_functions as gf
from Modules import draw
from Modules import macros
from Modules import MapSpectTable as mst
from Modules import SavedPointsTable as spt
# インスタンスメソッドを追加
spc.File.get_shape = gf.get_shape
spc.File.get_size = gf.get_size
spc.File.get_sub_idx = gf.get_sub_idx
spc.File.get_idx = gf.get_idx
spc.File.get_data = gf.get_data
spc.File.get_point_intensity_list = gf.get_point_intensity_list
spc.File.get_total_intensity_list = gf.get_total_intensity_list
spc.File.write_to_binary = gf.write_to_binary
spc.File.write_to_object = gf.write_to_object
spc.File.delete_from_binary = gf.delete_from_binary
spc.File.delete_from_object = gf.delete_from_object
spc.File.update_binary = gf.update_binary
spc.File.update_object = gf.update_object
spc.File.modify_prep_order = gf.modify_prep_order
spc.File.toNumPy_2dArray = gf.toNumPy_2dArray
spc.File.fmNumPy_2dArray = gf.fmNumPy_2dArray
spc.File.remove_all_prep = gf.remove_all_prep
spc.File.get_skipped_data = gf.get_skipped_data

class MainWindow(QMainWindow):
    # child_window_list_changed = pyqtSignal(QWidget)
    def __init__(self, base_path):
        #　情報
        gf.set_base_path(base_path)
        gf.load_settings_file()
        # 全体設定
        super().__init__()
        self.setAcceptDrops(True)
        self.setWindowTitle('ImageCUBE ver. %s'%gf.ver)
        self.setWindowIcon(QIcon(os.path.join(gf.icon_path, 'app_icon.svg')))
        self.window_type = "main"
        self.child_window_list = []
        self.current_focused_window = self
        # QCoreApplication.setAttribute(Qt.AA_DontUseNativeMenuBar)
        self.setUnifiedTitleAndToolBarOnMac(True) # サイズ固定すると、そもそも tab bar は現れないので、ほんとは必要ない。
        # for Plugins
        self.plugin_func_list = []
        self.temp_variables = {}
        # 予め持っておく window
        self.map_spect_table = mst.MapSpectTable(parent=self)
        self.poi_manager = spt.PointsOfInterestManager(parent=self)
        self.batch_processing_window_list = []
        # 左列ボタンウィジェット
        self.ButtonField = QWidget()
        # ボタン達（廃止の方向？）
        btnOpen = my_w.CustomPicButton("open1.svg", "open2.svg", "open3.svg", base_path=gf.icon_path)
        btnOpen.setToolTip("open *.spc files")
        btnOpen.clicked.connect(self.open_files_clicked)
        btnOpenRecursively = my_w.CustomPicButton("open_s_1.svg", "open_s_2.svg", "open_s_3.svg", base_path=gf.icon_path)
        btnOpenRecursively.setToolTip("open *.spc files recursively")
        btnOpenRecursively.clicked.connect(self.open_recursively_clicked)
        # btnChangeMapSize = my_w.CustomPicButton("resize1.svg", "resize2.svg", "resize3.svg", base_path=gf.icon_path)
        # btnChangeMapSize.setToolTip("resize map and open")
        # btnChangeMapSize.clicked.connect(functools.partial(self.open_files_clicked, resize=True))
        btnMapSpctTable = my_w.CustomPicButton("spct_map_table1.svg", "spct_map_table2.svg", "spct_map_table3.svg", base_path=gf.icon_path)
        btnMapSpctTable.setToolTip("open spectrum-map table")
        btnMapSpctTable.clicked.connect(self.open_map_spect_table)
        btnPoiManager = my_w.CustomPicButton("poi1.svg", "poi2.svg", "poi3.svg", base_path=gf.icon_path)
        btnPoiManager.setToolTip("open poi manager")
        btnPoiManager.clicked.connect(self.open_poi_manager)
        btnNewUnmixingMehod = my_w.CustomPicButton("unmix1.svg", "unmix2.svg", "unmix3.svg", base_path=gf.icon_path)
        btnNewUnmixingMehod.setToolTip("new unmixing method")
        btnNewUnmixingMehod.clicked.connect(self.build_new_unmixing_method)
        btnBatchProcessing = my_w.CustomPicButton("batch_1.svg", "batch_2.svg", "batch_3.svg", base_path=gf.icon_path)
        btnBatchProcessing.setToolTip("batch processing")
        btnBatchProcessing.clicked.connect(self.batch_processing_clicked)
        btnCloseAll = my_w.CustomPicButton("close_all_1.svg", "close_all_2.svg", "close_all_3.svg", base_path=gf.icon_path)
        btnCloseAll.setToolTip("close all")
        btnCloseAll.clicked.connect(self.close_all_clicked)
        btnSettings = my_w.CustomPicButton("Config1.svg", "Config2.svg", "Config3.svg", base_path=gf.icon_path)
        btnSettings.setToolTip("preferences")
        btnSettings.clicked.connect(self.settings_clicked)
        # File Actions
        openAction = my_w.CustomAction(gf.icon_path, "open1.svg", 'Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(self.open_files_clicked)
        openSeqAction = my_w.CustomAction(gf.icon_path, "open_s_1.svg", 'Open Recursively', self)
        openSeqAction.setShortcut('Ctrl+Shift+O')
        openSeqAction.triggered.connect(self.open_recursively_clicked)
        # changeMapSizeAction = my_w.CustomAction(gf.icon_path, "resize1.svg", "Resize and Open", self)
        # changeMapSizeAction.setShortcut("Ctrl+Alt+O")
        # changeMapSizeAction.triggered.connect(functools.partial(self.open_files_clicked, resize=True))
        captureCurrentSpectrum = my_w.CustomAction(gf.icon_path, "save_spct1.svg", "capture current spectrum", self)
        captureCurrentSpectrum.triggered.connect(functools.partial(self.capture_current_spectrum, compatible_window_types=["ms", "s", "u"]))
        exportAllMapsAction = my_w.CustomAction(gf.icon_path, "save_map1.svg", "Save All Map Images", self)
        exportAllMapsAction.triggered.connect(functools.partial(self.export_all_maps, compatible_window_types=["ms"]))
        closeAction = my_w.CustomAction(gf.icon_path, "close.svg", "Close", self)
        closeAction.setShortcut("Ctrl+W")
        closeAction.triggered.connect(self.menu_close_window)
        closeAllAction = my_w.CustomAction(gf.icon_path, "close_all.svg", "Close All", self)
        closeAllAction.setShortcut("Ctrl+Shift+W")
        closeAllAction.triggered.connect(self.close_all_clicked)
        settingsAction = my_w.CustomAction(gf.icon_path, "Config1.svg", "Preferences", self)
        settingsAction.triggered.connect(self.settings_clicked)
        quitAction = QAction("Quit", self)
        quitAction.setShortcut("Ctrl+Q")
        quitAction.triggered.connect(self.closeEvent)
        # open_unmixing_scoreAction = QAction("unmixing score viewer", self)
        # open_unmixing_scoreAction.triggered.connect(self.open_unmixing_score_window)
        # View Actions
        hs_rightAxisAction = my_w.CustomAction(gf.icon_path, "HideShow_R_Ax1.svg", "Hide/Show Right Axis", self)
        hs_rightAxisAction.setShortcut("Ctrl+Shift+H")
        hs_rightAxisAction.triggered.connect(functools.partial(self.menu_hs_rightAxis, compatible_window_types=["ms","s","u"]))
        ms_tableAction = my_w.CustomAction(gf.icon_path, "spct_map_table1.svg", "Spctrum-Map Table", self)
        ms_tableAction.setShortcut("Ctrl+T")
        ms_tableAction.triggered.connect(self.open_map_spect_table)
        poi_managerAction = my_w.CustomAction(gf.icon_path, "poi1.svg", "POI manager", self)
        poi_managerAction.setShortcut("Meta+T")
        poi_managerAction.triggered.connect(self.open_poi_manager)
        window_sizeAction = my_w.CustomAction(gf.icon_path, "map_size1.svg", "change window size", self)
        window_sizeAction.triggered.connect(functools.partial(self.change_window_size, compatible_window_types=["ms","s","u","t"]))
        spectrum_x_Action = QAction("set spectrum x range", self)
        spectrum_x_Action.triggered.connect(functools.partial(self.set_spectrum_range, compatible_window_types=["ms","s","u"], x_or_y="x"))
        spectrum_y_Action = QAction("set spectrum y range", self)
        spectrum_y_Action.triggered.connect(functools.partial(self.set_spectrum_range, compatible_window_types=["ms","s","u"], x_or_y="y"))
        reset_map_viewAction = QAction("reset map view", self)
        reset_map_viewAction.triggered.connect(functools.partial(self.reset_map_view, compatible_window_types=["ms"]))
        jump_to_map_locAction = QAction("jump to (x, y) on the map image", self)
        jump_to_map_locAction.setShortcut('Ctrl+G')
        jump_to_map_locAction.triggered.connect(functools.partial(self.jump_to_map_loc, compatible_window_types=["ms"]))
        # PreProcess Actions
        crrAction = my_w.CustomAction(gf.icon_path, "CRR1.svg", "Cosmic Ray Removal", self)
        crrAction.triggered.connect(functools.partial(self.menu_crr, compatible_window_types=["ms"]))
        hsCrrAction = my_w.CustomAction(gf.icon_path, "CRR1.svg", "Hide/Show Cosmic Rays", self)
        hsCrrAction.triggered.connect(functools.partial(self.menu_hs_crr, compatible_window_types=["ms"]))
        clearCrrAction = my_w.CustomAction(gf.icon_path, "CRR1.svg", "Clear Detected Cosmic Rays", self)
        clearCrrAction.triggered.connect(functools.partial(self.menu_clear_crr, compatible_window_types=["ms"]))
        pcaNrAction = my_w.CustomAction(gf.icon_path, "NF1.svg", "PCA based Noise Filter", self)
        pcaNrAction.triggered.connect(functools.partial(self.menu_pcaNr, compatible_window_types=["ms"]))
        # Spectrum Actions
        addSpectrumAction = my_w.CustomAction(gf.icon_path, "add_spct1.svg", "Add Spectrum from a File", self)
        addSpectrumAction.triggered.connect(functools.partial(self.menu_addSpectrumFmFile, compatible_window_types=["ms", "s", "u"]))
        addSpectrumAction.setShortcut("Ctrl+A")
        addCurSpectrumAction = my_w.CustomAction(gf.icon_path, "add_cur_spec1.svg", "Add Current Spectrum", self)
        addCurSpectrumAction.triggered.connect(functools.partial(self.menu_addCurSpectrum, compatible_window_types=["ms"]))
        linearSubtractSpectrumAction = my_w.CustomAction(gf.icon_path, "spct_calc1.svg", "Gaussian Fitted Subtract Spectrum", self)
        linearSubtractSpectrumAction.triggered.connect(functools.partial(self.menu_linearSubtractSpectrum, compatible_window_types=["ms", "s"]))
        # # Map Actions
        # setCfpAction = my_w.CustomAction(gf.icon_path, "cfp1.svg", "Set Cell Free Position", self)
        # setCfpAction.triggered.connect(functools.partial(self.menu_setCfp, compatible_window_types=["ms"]))
        # Basic Image Reconstruction Actions
        signalIntensityAction = my_w.CustomAction(gf.icon_path, "sig_int1.svg", "Signal Intensity", self)
        signalIntensityAction.triggered.connect(functools.partial(self.menu_sigInt, compatible_window_types=["ms"]))
        signal2Baseline = my_w.CustomAction(gf.icon_path, "sig2base1.svg", "Signal to Baseline", self)
        signal2Baseline.triggered.connect(functools.partial(self.menu_sig2base, compatible_window_types=["ms"]))
        signal2HBaseline = my_w.CustomAction(gf.icon_path, "sig2h_base1.svg", "Signal to Horizontal Baseline", self)
        signal2HBaseline.triggered.connect(functools.partial(self.menu_sig2Hbase, compatible_window_types=["ms"]))
        signal2Axis = my_w.CustomAction(gf.icon_path, "sig2axis1.svg", "Signal to Axis", self)
        signal2Axis.triggered.connect(functools.partial(self.menu_sig2axis, compatible_window_types=["ms"]))
        # Unmixing Actions
        umxAction = my_w.CustomAction(gf.icon_path, "unmix1.svg", "Unmixing", self)
        umxAction.setShortcut("Ctrl+U")
        umxAction.triggered.connect(functools.partial(self.menu_umx, compatible_window_types=["ms", "s"]))
        umxWithMethodAction = my_w.CustomAction(gf.icon_path, "unmix1.svg", "Unmixing with Method", self)
        umxWithMethodAction.setShortcut("Ctrl+Shift+U")
        umxWithMethodAction.triggered.connect(functools.partial(self.menu_umxWithMethod, compatible_window_types=["ms", "s"]))
        mkUmxMethodAction = my_w.CustomAction(gf.icon_path, "unmix1.svg", "Make New Unmixing Method", self)
        mkUmxMethodAction.setShortcut("Ctrl+Alt+U")
        mkUmxMethodAction.triggered.connect(self.build_new_unmixing_method)
        includeCellFreePositionAction = my_w.CustomAction(gf.icon_path, "include_cell_free_position1.svg", "Set/Unset Baseline Drift", self)
        includeCellFreePositionAction.triggered.connect(functools.partial(self.menu_includeCFP, compatible_window_types=["u"]))
        expUmxMethodAction = my_w.CustomAction(gf.icon_path, "export_umx1.svg", "Export Unmixing Method", self)
        expUmxMethodAction.triggered.connect(functools.partial(self.menu_expUmxMethod, compatible_window_types=["u"]))
        # Plugin Actions
        openBatchWindAction = my_w.CustomAction(gf.icon_path, "batch_1.svg", "Open Action Flow Window", self)
        openBatchWindAction.setShortcut("Ctrl+B")
        openBatchWindAction.triggered.connect(self.batch_processing_clicked)
        syncPluginFolderAction = my_w.CustomAction(gf.icon_path, "sync_plugin1.svg", "Sync with plugin folder", self)
        syncPluginFolderAction.triggered.connect(self.import_plugin)
        syncPluginFolderAction.setShortcut("Ctrl+R")
        # メニューバー
        self.menu_bar = QMenuBar(self)
        # ファイル
        fileMenu = self.menu_bar.addMenu(' &File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(openSeqAction)
        # fileMenu.addAction(changeMapSizeAction)
        fileMenu.addAction(captureCurrentSpectrum)
        fileMenu.addAction(exportAllMapsAction)
        fileMenu.addAction(closeAction)
        fileMenu.addAction(closeAllAction)
        fileMenu.addAction(settingsAction)
        fileMenu.addAction(quitAction)
        # fileMenu.addSeparator()
        # optionMenu = fileMenu.addMenu(" &Option")
        # optionMenu.addAction(open_unmixing_scoreAction)
        # ビュー
        viewMenu = self.menu_bar.addMenu(' &View')
        viewMenu.addAction(hs_rightAxisAction)
        viewMenu.addAction(ms_tableAction)
        viewMenu.addAction(poi_managerAction)
        viewMenu.addAction(window_sizeAction)
        viewMenu.addAction(spectrum_x_Action)
        viewMenu.addAction(spectrum_y_Action)
        viewMenu.addAction(reset_map_viewAction)
        viewMenu.addAction(jump_to_map_locAction)
        # プロセス
        processMenu = self.menu_bar.addMenu(' &Process')
        # プレ
        pre_processingMenu = processMenu.addMenu(" &Pre Process")
        pre_processingMenu.addAction(crrAction)
        pre_processingMenu.addAction(hsCrrAction)
        pre_processingMenu.addAction(clearCrrAction)
        pre_processingMenu.addAction(pcaNrAction)
        # スペクトル
        spectrum_processingMenu = processMenu.addMenu(" &Spectrum Processing")
        spectrum_processingMenu.addAction(addSpectrumAction)
        spectrum_processingMenu.addAction(addCurSpectrumAction)
        spectrum_processingMenu.addAction(linearSubtractSpectrumAction)
        # マップ
        map_processingMenu = processMenu.addMenu(" &Map Processing")
        # map_processingMenu.addAction(setCfpAction)
        # ベーシック
        basic_image_reconstructionMenus = processMenu.addMenu(" &Basic Image Reconstruction")
        basic_image_reconstructionMenus.addAction(signalIntensityAction)
        basic_image_reconstructionMenus.addAction(signal2Baseline)
        basic_image_reconstructionMenus.addAction(signal2HBaseline)
        basic_image_reconstructionMenus.addAction(signal2Axis)
        # アンミックス
        unmixingMenu = processMenu.addMenu(" &Unmixing")
        unmixingMenu.addAction(umxAction)
        unmixingMenu.addAction(umxWithMethodAction)
        unmixingMenu.addAction(mkUmxMethodAction)
        unmixingMenu.addAction(includeCellFreePositionAction)
        unmixingMenu.addAction(expUmxMethodAction)
        self.setMenuBar(self.menu_bar)
        # マクロ
        pluginMenu = self.menu_bar.addMenu(" &Plugins")
        pluginMenu.addAction(openBatchWindAction)
        pluginMenu.addAction(syncPluginFolderAction)
        self.imported_plugins = pluginMenu.addMenu(" &Imported Plugins")
        # 背景
        self.setObjectName("MainWindow")   # childWidgetに影響を与えないためのID付け
        self.setStyleSheet('QWidget#MainWindow{background-color: %s}'%gf.dbg_color)
        # レイアウト
        btnLayout = QHBoxLayout()
        btnLayout.addWidget(btnOpen)
        btnLayout.addWidget(btnOpenRecursively)
        # btnLayout.addWidget(btnChangeMapSize)
        btnLayout.addWidget(btnMapSpctTable)
        btnLayout.addWidget(btnPoiManager)
        btnLayout.addWidget(btnNewUnmixingMehod)
        btnLayout.addWidget(btnBatchProcessing)
        btnLayout.addWidget(btnCloseAll)
        btnLayout.addStretch(1)
        btnLayout.addWidget(btnSettings)
        btnLayout.setContentsMargins(gf.dcm, gf.dcm, gf.dcm, gf.dcm)
        btnLayout.setSpacing(gf.dsp)
        layout = QVBoxLayout()
        layout.addLayout(btnLayout)
        layout.setContentsMargins(gf.dcm, gf.dcm, gf.dcm, gf.dcm)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setFixedSize(gf.mainwindow_width, gf.mainwindow_height)
        # central widget
        self.setCentralWidget(central_widget)
        self.setFocusPolicy(Qt.StrongFocus)
        # マクロ
        self.import_plugin()
    # 開く
    def open_files(func):
        def _wrapper(self, *args, **kwargs):
            file_path_list, file_type = func(self, *args, **kwargs)
            if file_type.startswith("Spectrum files"):
                for file_path in file_path_list:
                    print(file_path)
                    gf.settings["last opened dir"] = os.path.dirname(file_path)
                    gf.save_settings_file()
                    # unmix method file
                    if file_path.endswith(".umx"):
                        self.open_unmixing_window(file_path)
                    # normal spectrum file
                    elif file_path.endswith(".spc") | file_path.endswith(".spcl") | file_path.endswith(".cspc") | file_path.endswith(".out"):
                        spc_file, traceback = gf.open_spc_spcl(file_path)
                        if spc_file is None:
                            warning_popup = popups.WarningPopup("File '{0}' could not be opened.\nERROR: {1}".format(file_path, traceback))
                            warning_popup.exec_()
                            continue
                        # 初期処理（変数のバイナリからの変換など）：特殊ファイル（.cspc, .out）は初期処理しない。
                        if spc_file.length is not None:
                            spc_file = gf.spc_init(spc_file, file_path)
                        # 単一スペクトルの場合
                        if spc_file.fnsub == 1:
                            self.open_spectrum_window(spc_file, file_path)
                        # map画像以上の場合
                        else:
                            self.open_map_spect_window(spc_file, file_path)
                        print(gf.int2datetime(spc_file.fdate))
                    else:
                        raise Exception("unknown file type: {0}".format(file_path))
                    # GUI update
                    QCoreApplication.processEvents()
            elif file_type.startswith("Image files"):
                if file_path_list:
                    gf.settings["last opened dir"] = os.path.dirname(file_path_list[0])
                    gf.save_settings_file()
                    set_order_popup = popups.SetOrderPopup(list(map(lambda x: os.path.basename(x), file_path_list)), optional_items=file_path_list, optional_range_dict={"left":2000, "right":2300})
                    done = set_order_popup.exec_()
                    if done:
                        xData = np.linspace(*set_order_popup.get_spinbox_values(), num=set_order_popup.get_N())
                        spc_file, traceback = gf.open_fm_imgs(set_order_popup.get_optional_items(), xData)
                        if spc_file is None:
                            warning_popup = popups.WarningPopup("Files could not be opened.\nERROR: {0}".format(traceback))
                            warning_popup.exec_()
                        else:
                            # 初期処理（変数のバイナリからの変換など）
                            dirname = os.path.basename(gf.settings["last opened dir"])
                            file_path = os.path.join(format(gf.settings["last opened dir"]), dirname)
                            spc_file = gf.spc_init(spc_file, file_path)
                            self.open_map_spect_window(spc_file, file_path=file_path, mode="newWin")
        return _wrapper
    # 通常の開く
    @open_files
    def open_files_clicked(self, event=None):
        file_path_list, file_type = QFileDialog.getOpenFileNames(self, 'Select spctrum file', gf.settings["last opened dir"], 
            filter="Spectrum files (*.spc *.spcl *.umx *.out *.cspc);;Image files (*.tif *.tiff)")
        return file_path_list, file_type
    # ダブルクリックにより開く
    @open_files
    def open_a_file(self, file_path, file_type):
        return [file_path], file_type
    # 再帰的に開く
    @open_files
    def open_recursively_clicked(self, event=None):
        # ファイルを見つけていく
        dir_path = QFileDialog.getExistingDirectory(self, 'select folder', gf.settings["last opened dir"])
        if len(dir_path):
            spc_path_list = glob.glob("%s/**/*.spc"%dir_path, recursive=True)
            return spc_path_list, "Spectrum files (*.spc)"
        else:
            return []
    # パスから開く
    @open_files
    def just_open(self, spc_path):
        return [spc_path], "Spectrum files (*.spc)"
    # windowで開く
    def open_spectrum_window(self, spc_file, file_path):
        spectrum_window = SpectrumWindow(spc_file, file_path, parent=self)
        spectrum_window.show()
        self.child_window_list.append(spectrum_window)
    def open_map_spect_window(self, spc_file, file_path, mode="init"):
        map_spect_window = MapSpectWindow(spc_file, file_path, parent=self, mode=mode)
        map_spect_window.show()
        self.child_window_list.append(map_spect_window)
    def open_unmixing_window(self, file_path):
        unmix_method_window = UnmixingMethodWindow(file_path=file_path, parent=self)
        unmix_method_window.show()
        self.child_window_list.append(unmix_method_window)
    # アンミックスメソッドを作る（スペクトルwindowで作る）
    def build_new_unmixing_method(self, event=None):
        unmix_method_window = UnmixingMethodWindow(parent=self)
        unmix_method_window.show()
        self.child_window_list.append(unmix_method_window)
    # Spectrum-Map table
    def open_map_spect_table(self, event=None):
        self.map_spect_table.bring_to_front()
        self.map_spect_table.grab_focus()
    # Points Of Interest 表示
    def open_poi_manager(self, event=None):
        self.poi_manager.bring_to_front()
        self.poi_manager.grab_focus()
    # バッチ処理
    def batch_processing_clicked(self, event=None):
        batch_processing_window = macros.BatchProcessingWindow(parent=self)
        batch_processing_window.show()
        self.batch_processing_window_list.append(batch_processing_window)
    # 閉じる系
    def close_all_clicked(self, event=None):
        # 最終的に close_data_window が呼ばれるので、self.child_window_list = [] とする必要はない
        child_window_list = np.copy(self.child_window_list)
        for window in child_window_list:
            window.close()
    def close_data_window(self, closing_window):
        for idx, window in enumerate(self.child_window_list):
            if window == closing_window:
                del self.child_window_list[idx]
                break
        self.map_spect_table.data_window_closed()
        self.poi_manager.data_window_closed()
    # メニューバーからの、window ごとの処理
    def process_opened_window(func):
        def _wrapper(self, compatible_window_types, *args, **kwargs):
            if self.current_focused_window.window_type in compatible_window_types:
                func(self, *args, **kwargs)
            else:
                warning_popup = popups.WarningPopup("No window is opened or the window type is invalid!")
                warning_popup.exec_()
        return _wrapper
    # Files
    @ process_opened_window
    def export_all_maps(self):
        self.current_focused_window.toolbar_layout.export_all_maps(ext=".tiff .svg")
    @ process_opened_window
    def capture_current_spectrum(self):
        self.current_focused_window.toolbar_layout.export_svg()
    def menu_close_window(self):
        if self.current_focused_window.window_type == "main":
            return
        else:
            self.current_focused_window.close()
    # View
    @ process_opened_window
    def menu_hs_rightAxis(self):
        self.current_focused_window.toolbar_layout.hide_right_axis()
    @ process_opened_window
    def change_window_size(self):
        window_size_settings_popup = popups.RangeSettingsPopup(parent=self, initial_values=(0,0), labels=("width", "height"), double=False)
        done = window_size_settings_popup.exec_()
        if not done:
            return
        width = window_size_settings_popup.spbx_RS1.value()
        height = window_size_settings_popup.spbx_RS2.value()
        if width == 0:
            width = self.current_focused_window.frameGeometry().width()
        if height == 0:
            height = self.current_focused_window.frameGeometry().height()
        self.current_focused_window.resize(width, height)
    @ process_opened_window
    def set_spectrum_range(self, x_or_y=None):
        if x_or_y == "x":
            idx = 0
            labels = ("left", "right")
            ckbx_messages = [" FULL", " propagate to all"]
            func_name = "setXRange"
            auto_func_name = "get_auto_xRange"
        else:
            idx = 1
            labels = ("top", "bottom")
            ckbx_messages = [" AUTO", " propagate to all"]
            func_name = "setYRange"
            auto_func_name = "get_auto_yRange"
        cur_ranges = self.current_focused_window.spectrum_widget.viewRange()
        main_range = cur_ranges[idx]
        sub_ranage = cur_ranges[1 - idx]
        size_setting_popup = popups.RangeSettingsPopupWithCkbx(
            initial_values=main_range, 
            labels=labels, 
            title="set spectrum {0} range".format(x_or_y), 
            ckbx_messages=ckbx_messages)
        done = size_setting_popup.exec_()
        if not done:
            return
        if size_setting_popup.ckbxes[1].isChecked():
            window_list = self.get_windows(window_types=["u", "s", "ms"])
        else:
            window_list = [self.current_focused_window]
        for window in window_list:
            if not size_setting_popup.ckbxes[0].isChecked():
                range_1 = size_setting_popup.spbx_RS1.value()
                range_2 = size_setting_popup.spbx_RS2.value()
                padding = 0
            # オート
            else:
                auto_func = getattr(window.spectrum_widget, auto_func_name)
                range_1, range_2 = auto_func(sub_ranage)
                padding = None
            func = getattr(window.spectrum_widget, func_name)
            func(range_1, range_2, padding=padding)
    @ process_opened_window
    def reset_map_view(self):
        self.current_focused_window.map_widget.img_view_box.autoRange()
    @ process_opened_window
    def jump_to_map_loc(self):
        cur_x = self.current_focused_window.spectrum_widget.cur_x
        cur_y = self.current_focused_window.spectrum_widget.cur_y
        size_setting_popup = popups.RangeSettingsPopupWithCkbx(
            parent=self.current_focused_window, 
            initial_values=[cur_x, cur_y], 
            labels=("x", "y"), 
            title="set position", 
            double=False, 
            ckbx_messages=[" MAX INTENSITY", " propagate to all"]
            )
        size_setting_popup.set_spinbox_ranges_fm_parent()
        done = size_setting_popup.exec_()
        if not done:
            return
        if size_setting_popup.ckbxes[1].isChecked():
            window_list = self.get_windows(window_types=["ms"])
        else:
            window_list = [self.current_focused_window]
        for window in window_list:
            cur_image2d = window.map_widget.get_cur_image2d()
            if size_setting_popup.ckbxes[0].isChecked() == False:
                x = size_setting_popup.spbx_RS1.value()
                y = size_setting_popup.spbx_RS2.value()
                if (cur_image2d.shape[0] <= y) or (cur_image2d.shape[1] <= x):
                    warning_popup = popups.WarningPopup("The value exceeds the image size.")
                    warning_popup.exec_()
                    self.jump_to_map_loc(compatible_window_types=["ms"])
                    return
            # オート
            else:
                y, x = np.unravel_index(np.argmax(cur_image2d), cur_image2d.shape)
            window.spectrum_widget.replace_spectrum(x, y)
            window.map_widget.set_crosshair(x, y)
    # PreProcess
    @ process_opened_window
    def menu_crr(self):
        self.current_focused_window.toolbar_layout.cosmic_ray_removal(ask=True)
    @ process_opened_window
    def menu_hs_crr(self):
        self.current_focused_window.toolbar_layout.hide_show_cosmic_rays()
    @ process_opened_window
    def menu_clear_crr(self):
        self.current_focused_window.toolbar_layout.clear_cosmic_rays(ask=True)
    @ process_opened_window
    def menu_pcaNr(self):
        self.current_focused_window.toolbar_layout.apply_noise_filter(ask=True)
    # Image Reconstruction
    @ process_opened_window
    def menu_sigInt(self):
        self.current_focused_window.toolbar_layout.execute_signal_intensity()
    @ process_opened_window
    def menu_sig2base(self):
        self.current_focused_window.toolbar_layout.execute_signal_to_baseline()
    @ process_opened_window
    def menu_sig2Hbase(self):
        self.current_focused_window.toolbar_layout.execute_signal_to_H_baseline()
    @ process_opened_window
    def menu_sig2axis(self):
        self.current_focused_window.toolbar_layout.execute_signal_to_axis()
    # Spectrum Process
    @ process_opened_window
    def menu_addSpectrumFmFile(self):
        self.current_focused_window.toolbar_layout.add_spectrum_from_file()
    @ process_opened_window
    def menu_addCurSpectrum(self):
        self.current_focused_window.toolbar_layout.add_current_spectrum()
    @ process_opened_window
    def menu_linearSubtractSpectrum(self):
        self.current_focused_window.toolbar_layout.execute_spectrum_linear_subtraction()
    # Map
    # @ process_opened_window
    # def menu_setCfp(self):
    #     self.current_focused_window.toolbar_layout.set_CellFreePosition()
    # Unmixing
    @ process_opened_window
    def menu_umx(self):
        self.current_focused_window.toolbar_layout.execute_unmixing(ask=True)
    @ process_opened_window
    def menu_umxWithMethod(self):
        self.current_focused_window.toolbar_layout.unmix_with_method()
    @ process_opened_window
    def menu_includeCFP(self):
        self.current_focused_window.toolbar_layout.include_CellFreePosition()
    @ process_opened_window
    def menu_expUmxMethod(self):
        self.current_focused_window.toolbar_layout.export_method()
    # 設定
    def settings_clicked(self, event=None):
        settings_popup = gf.SettingsPopup(gf.settings)
        done = settings_popup.exec_()
        if done:
            gf.settings = settings_popup.settings
    def import_plugin(self):
        # 先にあるものを消去
        self.plugin_func_list = []
        self.imported_plugins.clear()
        plugin_path_list = glob.glob("%s/**/*.icm"%gf.settings["plugin dir"], recursive=True)
        for idx, plugin_path in enumerate(plugin_path_list):
            file_name = os.path.basename(plugin_path)
            file_name_wo_ext = os.path.splitext(file_name)[0]
            with open(plugin_path, "rb") as f:   # なぜバイナリで読み込み？でもそれでok
                script = f.read()
                self.plugin_func_list.append(script)
            pluginAction = QAction(file_name_wo_ext, self)
            pluginAction.triggered.connect(functools.partial(self.plugin_func, idx))
            self.imported_plugins.addAction(pluginAction)
    def plugin_func(self, idx):
        newdict = dict(globals())
        newdict.update(locals())
        try:
            exec(self.plugin_func_list[idx], newdict, newdict)
        except:
            self.temp_variables = {}
            error_log = traceback.format_exc()
            warning_popup = popups.WarningPopup(error_log)
            warning_popup.exec_()
        if self.temp_variables.get("clear temp_variables", True):
            self.temp_variables = {}
    # window取得
    def get_windows(self, window_types):
        windows = []
        for window in self.child_window_list:
            if window.window_type in window_types:
                windows.append(window)
        return windows
    def select_window(self, mode=None, **kwargs):
        idx = kwargs["idx"]
        try:
            focused_window = self.child_window_list[idx]
        except:
            return None, "window index {0} is out of range ({1})".format(idx, len(self.child_window_list))
        self.focusChanged(focused_window)
        return focused_window, "continue"
    # フォーカスイベント処理
    def focusInEvent(self, event):
        print("main focused")
        self.current_focused_window = self
        self.map_spect_table.window_focus_changed(self.current_focused_window)
        self.poi_manager.window_focus_changed(self.current_focused_window)
    def focusOutEvent(self, event):
        pass
    def focusChanged(self, focused_window):
        if self.current_focused_window != focused_window:
            self.current_focused_window = focused_window
            self.map_spect_table.window_focus_changed(self.current_focused_window)
            self.poi_manager.window_focus_changed(self.current_focused_window)
    def dragEnterEvent(self, event):
        event.accept()
    def dropEvent(self, event):
        event.accept()
        mimeData = event.mimeData()
        for mimetype in mimeData.formats():
            if mimetype == "text/uri-list":
                url_byte = mimeData.data(mimetype).data()
                file_path_list = parse.unquote(url_byte.decode()).replace('file://', '').replace('\r', '').strip().split("\n")
                for file_path in file_path_list:
                    ext = os.path.splitext(file_path)[1]
                    if ext in (".spc", ".spcl", ".umx", ".out", ".cspc"):
                        self.open_a_file(file_path, "Spectrum files (*{0})".format(ext))
                    else:
                        warning_popup = popups.WarningPopup("Extension {0} is not supported for drug and drop event or unreadable file.".format(ext))
                        warning_popup.exex_()
    def closeEvent(self, event=None):
        print("closing...")
        sys.exit()

class SpectrumWindow(QMainWindow):
    def __init__(self, spc_file, file_path, parent=None, mode="init"):
        # 情報
        self.parent = parent
        self.window_type = "s"
        self.file_path = file_path
        self.dir_path, self.file_name, self.file_name_wo_ext = gf.file_name_processor(self.file_path)
        self.cur_displayed_spc_content = None
        self.cur_overlayed_spc_content = None
        # 全体設定
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setWindowTitle("%s (%d points)"%(self.file_name, spc_file.fnpts))
        # 操作パネルとグラフ
        self.toolbar_layout = draw.ToolbarLayout(self.window_type, parent=self)  # spectrum
        self.spectrum_widget = draw.SpectrumWidget(spc_file, parent=self)
        # レイアウト
        layout = QHBoxLayout()
        layout.addLayout(self.toolbar_layout)
        layout.addWidget(self.spectrum_widget)
        layout.setContentsMargins(gf.dcm, gf.dcm, gf.dcm, gf.dcm)
        layout.setSpacing(gf.dsp)
        # self.setLayout(layout)
        # 初期処理
        self.execute_preprocess(mode=mode)
        self.setAttribute(Qt.WA_DeleteOnClose)
        # tab barが現れるのを防ぐため、QWidget ではなく QMainWindow で window を作成し、TabBarを消去した。
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.setUnifiedTitleAndToolBarOnMac(True)
    # スペクトルオンリーのデータは、今のところ preprocess なし
    def execute_preprocess(self, mode=None):
        if b"prep_order" in self.spectrum_widget.spc_file.log_dict.keys():
            self.toolbar_layout.execute_preprocess(mode=mode)
    def focusInEvent(self, event):
        self.parent.focusChanged(self)
    def focusOutEvent(self, event):
        pass
    # 親 window 経由で閉じる
    def closeEvent(self, event=None):
        self.parent.close_data_window(closing_window=self)
        self.deleteLater()
        event.accept()

class MapSpectWindow(QMainWindow):
    def __init__(self, spc_file, file_path, parent=None, mode="init"):
        # 情報
        self.parent = parent
        self.window_type = "ms"
        self.file_path = file_path
        self.dir_path, self.file_name, self.file_name_wo_ext = gf.file_name_processor(self.file_path)
        self.cur_displayed_spc_content = None
        self.cur_displayed_map_content = None
        self.cur_overlayed_map_content = None
        # 全体設定
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.toolbar_layout = draw.ToolbarLayout(self.window_type, parent=self) # map & spectrum
        self.map_widget = draw.MapWidget(spc_file, parent=self)
        self.spectrum_widget = draw.SpectrumWidget(spc_file, parent=self)
        # 背景
        # self.setObjectName("MapSpectWindow")   # childWidgetに影響を与えないためのID付け
        # self.setStyleSheet('QWidget#MapSpectWindow{background-color: %s}'%gf.dbg_color)
        # レイアウト
        sub_layout = QVBoxLayout()
        sub_layout.addWidget(self.map_widget)
        sub_layout.addWidget(self.spectrum_widget)
        layout = QHBoxLayout()
        layout.addLayout(self.toolbar_layout)
        layout.addLayout(sub_layout)
        layout.setContentsMargins(gf.dcm, gf.dcm, gf.dcm, gf.dcm)
        layout.setSpacing(gf.dsp)
        # self.setLayout(layout)
        # 初期処理
        self.execute_preprocess(mode=mode)
        self.setAttribute(Qt.WA_DeleteOnClose)
        # tab barが現れるのを防ぐため、QWidget ではなく QMainWindow で window を作成し、TabBarを消去した。
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.setUnifiedTitleAndToolBarOnMac(True)
    def set_window_title(self):
        self.setWindowTitle(
            "{0} ({1}(x) x {2}(y) x {3}(spec.))".format(
                self.file_name, 
                *self.spectrum_widget.spc_file.get_shape()[::-1], 
                self.spectrum_widget.spc_file.fnpts
            )
        )
    def execute_preprocess(self, mode=None):
        self.toolbar_layout.execute_preprocess(mode=mode)
        self.toolbar_layout.execute_poi(mode=mode)
    def focusInEvent(self, event):
        self.parent.focusChanged(self)
    def focusOutEvent(self, event):
        pass
    # 親 window 経由で閉じる
    def closeEvent(self, event=None):
        self.parent.close_data_window(closing_window=self)
        self.deleteLater()
        event.accept()

class UnmixingMethodWindow(QWidget):
    def __init__(self, file_path=None, parent=None):
        # 情報
        self.parent = parent
        self.window_type = "u"
        self.file_path = file_path
        self.dir_path, self.file_name, self.file_name_wo_ext = None, None, None
        # 全体設定
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        # 操作パネルとグラフ
        self.toolbar_layout = draw.ToolbarLayout(self.window_type, parent=self)  # spectrum
        self.spectrum_widget = draw.SpectrumWidget(spc_file=None, parent=self)
        del self.toolbar_layout.added_content_spectrum_list[0]                  # master_spectrum を消す
        self.set_text(N_poi=0)
        # vb1は、オリジナルスペクトル追加用なので使わないです、それに伴っての諸々の設定
        self.spectrum_widget.vb2.setMouseMode(pg.ViewBox.RectMode)
        self.spectrum_widget.vb2.setYLink(self.spectrum_widget.plotItem.vb) # XLinkは常にしてる
        self.spectrum_widget.vb2.addItem = self.wrapper_for_addItem(self.spectrum_widget.vb2.addItem)
        # 左下の 'A' を押して全体表示しようとした場合、そのままだと vb1 をターゲットにしてしまうので、それを修正
        def autoBtnClicked_w(btn_item):
            if btn_item.mode == 'auto':
                self.spectrum_widget.vb2.enableAutoRange()
                btn_item.hide()
            else:
                self.spectrum_widget.vb2.disableAutoRange()
        self.spectrum_widget.plotItem.autoBtn.clicked.disconnect()
        self.spectrum_widget.plotItem.autoBtn.clicked.connect(autoBtnClicked_w)
        # レイアウト
        layout = QHBoxLayout()
        layout.addLayout(self.toolbar_layout)
        layout.addWidget(self.spectrum_widget)
        layout.setContentsMargins(gf.dcm, gf.dcm, gf.dcm, gf.dcm)
        layout.setSpacing(gf.dsp)
        self.setLayout(layout)
        # 初期処理
        self.execute_preprocess(mode="newWin")
        if file_path is None:
            self.dir_path = gf.settings["method dir"]
            self.file_name = "new_unmixing_method.umx"
            self.file_name_wo_ext = "new_unmixing_method"
        else:
            self.dir_path, self.file_name, self.file_name_wo_ext = gf.file_name_processor(file_path)
            UMX = gf.load_umx(self.file_path)
            self.display_method(UMX)
            self.spectrum_widget.vb2.autoRange()
        self.setWindowTitle(self.file_name)
        self.setAttribute(Qt.WA_DeleteOnClose)
    def execute_preprocess(self, mode=None):
        # set prep_order to pseudo data
        new_prep_order = [["set_range", {"mode":mode, "left":None, "right":None}]]
        self.spectrum_widget.spc_file.write_to_object(master_key="PreP", key_list=["prep_order"], data_list=[new_prep_order])
        # preprocess
        self.toolbar_layout.execute_preprocess(mode=mode)
    def focusInEvent(self, event):
        self.parent.focusChanged(self)
    def focusOutEvent(self, event):
        pass
    # 親 window 経由で閉じる
    def closeEvent(self, event=None):
        self.parent.close_data_window(closing_window=self)
        self.deleteLater()
        event.accept()
    # 実際の処理の前後に処理を付け加えるラッパー関数
    def wrapper_for_addItem(self, function):
        @functools.wraps(function)
        def new_function(*argv, **keywords):
            result = function(*argv, **keywords)
            # オートrange
            self.spectrum_widget.vb2.autoRange()
            return result
        return new_function
    def display_method(self, UMX):
        for procedure, kwargs in UMX.procedures:
            if procedure == "execute_unmixing":
                self.toolbar_layout.set_range(mode="init", **kwargs)
                continue
            elif procedure == "add_spectra_from_POI":
                self.toolbar_layout.include_POI(ask=False, poi_key=kwargs["info"]["data"])
            func = getattr(self.toolbar_layout, procedure)
            log = func(**kwargs)
        # 右軸閉じる
        self.spectrum_widget.showAxis("right", show=False)
    def set_text(self, N_poi):
        self.spectrum_widget.text_item.setText("   Number of POI: {0}".format(N_poi))
    def add_poi(self):
        N_poi = re.fullmatch("   Number of POI: ([0-9]+)", self.spectrum_widget.text_item.textItem.document().toPlainText())[1]
        self.set_text(str(int(N_poi) + 1))
    def sbt_poi(self):
        N_poi = re.fullmatch("   Number of POI: ([0-9]+)", self.spectrum_widget.text_item.textItem.document().toPlainText())[1]
        self.set_text(str(int(N_poi) - 1))

###########
###########
###########

from fbs_runtime.application_context import cached_property
from fbs_runtime.application_context.PyQt5 import ApplicationContext

# https://blog.aaronhktan.com/posts/2018/06/16/open-with-in-macos-windows-ubuntu
from PyQt5.QtWidgets import QApplication
class MainApp(QApplication):
    def __init__(self, argv, base_path):
        super(MainApp, self).__init__(argv)
        self._window = MainWindow(base_path)
        self._window.show()
    def event(self, event):
        if event.type() == QEvent.FileOpen:
            file_path = event.url().toString().replace('file://', '')
            ext = os.path.splitext(file_path)[1]
            self._window.open_a_file(file_path, "Spectrum files (*{0})".format(ext))
        else:
            super().event(event)
        return True

class AppContext(ApplicationContext):
    # ApplicationContext.app property の overwrite
    @cached_property
    def app(self):
        base_path = os.path.split(self.get_resource("base_path.png"))[0]
        return MainApp(sys.argv, base_path)
    # @cached_property
    # def window(self):
    #     base_path = os.path.split(self.get_resource("base_path.png"))[0]
    #     window = MainWindow(base_path)
    #     window.resize(250, 150)
    #     return window
    def run(self):
        # self.window.show()
        return sys.exit(self.app.exec_())

if __name__ == '__main__':
    appctxt = AppContext()       # 1. Instantiate ApplicationContext
    # base_path = os.path.split(appctxt.get_resource("base_path.png"))[0]
    # window = MainWindow(base_path)
    # window.resize(250, 150)
    # window.show()
    # exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    # sys.exit(exit_code)
    appctxt.run()

