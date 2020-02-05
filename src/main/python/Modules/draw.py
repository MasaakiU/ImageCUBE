# -*- Coding: utf-8 -*-

import os
import spc
import numpy as np
import re
import functools
import pickle
from scipy.optimize import nnls, curve_fit

from PyQt5.QtWidgets import (
    QVBoxLayout, 
    QFileDialog, 
    )
from PyQt5.QtCore import (
    QSize, 
    QRect, 
    QLineF, 
    Qt, 
    )
from PyQt5.QtGui import (
        QPainter, 
        QGraphicsRectItem, 
    )    
from PyQt5.QtSvg import QSvgGenerator

import pyqtgraph as pg
from pyqtgraph.exporters import SVGExporter
pg.setConfigOptions(antialias=True)

from PIL import Image
import xml.etree.ElementTree as ET

from . import general_functions as gf
from . import my_widgets as my_w
from . import popups
from . import CRR_core as crrc
from . import NF_core as nfc

# added content ant its subclasses
class AddedContent():
    def __init__(self, item, info=None, parent_window=None):
        self.item = item
        self.info = info
        # {content: map/spectrum,
        # type:     original/added/unmixed/subtracted,
        # detail:   file_path/from_data/signal_intensity/signal_to_baseline/representative_cell_free_pos,
        # values:   []
        # idx:      int     (optional)
        # "data":   data    (optional)
        # }
        self.parent_window = parent_window
        self.allowed_btn_list = ["hide_show"]
        self.focused = False
    def content_type(self):
        return " " + self.info["type"] + " " + self.info["content"]
    def detail_values(self):
        detail_values = ""
        if len(self.info["values"]) != 0:
            detail_values += "(" + ",".join(list(map(str, self.info["values"]))) + ") "
        detail_values += self.info["detail"]
        return detail_values
    def summary(self):
        summary = ""
        summary += self.content_type()
        summary += self.detail_values()
        return summary
class AddedContent_Spectrum(AddedContent):
    def __init__(self, item, info=None, parent_window=None):
        super().__init__(item, info, parent_window)
        self.CLASS = "Specttum"
        # オリジナルスペクトルの場合は、消す行為は許されない
        if self.info["type"] != "original":
            self.allowed_btn_list.append("remove")
        self.allowed_btn_list.append("export")
    def focus_unfocus(self, focused):
        self.focused = focused
        if self.focused:
            brush_color = self.item.opts["pen"].color()
            brush_color.setAlpha(gf.brushAlpha)
        else:
            brush_color = None
        self.item.setBrush(brush_color)
    def hide_show_item(self):
        if self.item.isVisible():
            self.item.hide()
        else:
            self.item.show()
    def remove_item(self):
        self.parent_window.spectrum_widget.vb2.removeItem(self.item)
        self.parent_window.toolbar_layout.added_spectrum_info_list.remove(self)
    def export_spectrum(self, save_path=None, ask=True):
        spc_like = gf.SpcLike()
        spc_like.init_fmt(self.parent_window.spectrum_widget.spc_file)
        spc_like.add_xData(self.item.xData)
        # subフィアル作成
        sub_like = gf.SubLike()
        sub_like.init_fmt(self.parent_window.spectrum_widget.spc_file.sub[0])
        sub_like.add_data(self.item.yData, sub_idx=0)
        # 追加
        spc_like.add_subLike(sub_like)
        self.parent_window.spectrum_widget.save_spectrum_as_spc(spc_like, save_path=save_path, ask=ask)
class AddedContent_RepresentativeCFP(AddedContent_Spectrum):
    def __init__(self, item, info=None, parent_window=None):
        super().__init__(item, info, parent_window)
        self.CLASS = "RepresentativeCFP"
        self.allowed_btn_list.remove("export")
    def focus_unfocus(self, focused):
        self.focused = focused
class AddedContent_Map(AddedContent):
    def __init__(self, item, info, parent_window):
        super().__init__(item, info, parent_window)
        self.allowed_btn_list.append("remove")
        self.info["spectrum_hidden"] = False
    def focus_unfocus(self, focused):
        self.focused = focused
        if self.focused:
            self.parent_window.cur_displayed_map_info = self.info
            self.parent_window.map_widget.display_map(self.item)
            self.parent_window.spectrum_widget.display_map_spectrum()
            if self.info["spectrum_hidden"]:
                self.parent_window.spectrum_widget.hide_all_fill_btwn_items()
                self.parent_window.spectrum_widget.hide_all_lines()
        else:
            self.parent_window.map_widget.map_img.hide()
            self.parent_window.cur_displayed_map_info = None
            self.parent_window.spectrum_widget.hide_all_fill_btwn_items()
            self.parent_window.spectrum_widget.hide_all_lines()
            self.info["spectrum_hidden"] = False
    def hide_show_item(self):
        if self.info["detail"] == "signal_intensity":
            isVisible = self.parent_window.spectrum_widget.additional_lines[0].isVisible()
            object_name = "lines"
        elif self.info["detail"] in ("signal_to_baseine", "signal_to_H_baseline", "signal_to_axis"):
            isVisible = self.parent_window.spectrum_widget.additional_fill_btwn_items[0].isVisible()
            object_name = "fill_btwn_items"
        else:
            raise Exception("no attrib")
        if isVisible:
            exe = "hide"
        else:
            exe = "show"
        self.info["spectrum_hidden"] = isVisible
        function = getattr(self.parent_window.spectrum_widget, "%s_all_%s"%(exe, object_name))
        function()
    def remove_item(self):
        self.parent_window.toolbar_layout.added_map_info_list.remove(self)
        self.parent_window.map_widget.map_img.hide()
        self.parent_window.cur_displayed_map_info = None
        self.parent_window.spectrum_widget.set_N_additional_lines(0)
        self.parent_window.spectrum_widget.set_N_additional_fill_btwn_items(0)
        return None
class AddedContent_Unmixed(AddedContent_Map):
    def __init__(self, item, info, parent_window):
        super().__init__(item, info, parent_window)
    def focus_unfocus(self, focused):
        super().focus_unfocus(focused)
        self.focused = focused
        if self.focused:
            if self.info["spectrum_hidden"]:
                self.parent_window.spectrum_widget.additional_lines[self.info["data"].n_th_components[0]].show()
                self.parent_window.spectrum_widget.additional_lines[-2].show()  # baseline
    def hide_show_item(self):
        line_item = self.parent_window.spectrum_widget.additional_lines[self.info["data"].n_th_components[0]]
        fill_btwn_item = self.parent_window.spectrum_widget.additional_fill_btwn_items[0]
        bg_lins_item = self.parent_window.spectrum_widget.additional_lines[-2]  # baseline
        isVisible = fill_btwn_item.isVisible()
        if isVisible:
            self.parent_window.spectrum_widget.hide_all_lines()
            line_item.show()
            bg_lins_item.show()
            fill_btwn_item.hide()
        else:
            fill_btwn_item.show()
            self.parent_window.spectrum_widget.show_all_lines()
        self.info["spectrum_hidden"] = isVisible
    def remove_item(self):
        abs_id = self.parent_window.cur_displayed_map_info["data"].abs_id
        idxes_to_remove = []
        for idx, added_content in enumerate(self.parent_window.toolbar_layout.added_map_info_list):
            if added_content.info["type"] != "unmixed":
                continue
            if added_content.info["data"].abs_id == abs_id:
                idxes_to_remove.append(idx)
        for idx in idxes_to_remove[::-1]:
            del self.parent_window.toolbar_layout.added_map_info_list[idx]
        self.parent_window.map_widget.map_img.hide()
        self.parent_window.cur_displayed_map_info = None
        self.parent_window.spectrum_widget.set_N_additional_lines(0)
        self.parent_window.spectrum_widget.set_N_additional_fill_btwn_items(0)
        return idxes_to_remove
class AddedContent_SubtractedSpectrums(AddedContent_Map):
    def __init__(self, item, info=None, parent_window=None):
        super().__init__(item, info, parent_window)
        self.allowed_btn_list.append("export")
        self.CLASS = "SubtractedSpectrums"
    def hide_show_item(self):
        isVisible = self.parent_window.spectrum_widget.additional_fill_btwn_items[0].isVisible()
        if isVisible:
            exe = "hide"
        else:
            exe = "show"
        self.info["spectrum_hidden"] = isVisible
        function = getattr(self.parent_window.spectrum_widget, "%s_all_fill_btwn_items"%exe)
        function()
    def export_spectrum(self, save_path=None, ask=True):
        spc_like = gf.SpcLike()
        spc_like.init_fmt(self.parent_window.spectrum_widget.spc_file)
        spc_like.add_xData(self.info["data"].master_x_list1)
        added_y_list1 = self.info["data"].added_y_list1
        for sub_idx, umx_h in enumerate(self.info["data"].umx_h_list):
            # subフィアル作成
            sub_like = gf.SubLike()
            sub_like.init_fmt(self.parent_window.spectrum_widget.spc_file.sub[sub_idx])
            sub_like.add_data(self.parent_window.spectrum_widget.spc_file.sub[sub_idx].y + added_y_list1 * umx_h, sub_idx=sub_idx)
            # 追加
            spc_like.add_subLike(sub_like)
        self.parent_window.spectrum_widget.save_spectrum_as_spc(spc_like, save_path=save_path, ask=ask)

# class containing information about spectrum unmixing
class UnmixedData():
    def __init__(self, standard_type, abs_id, n_th_components, umx_x_list, umx_y_matrix, umx_h_matrix):
        self.standard_type = standard_type   # index, bd (baseline drift), ts (total signal)
        self.abs_id = abs_id
        self.n_th_components = n_th_components  # (idx, n_components)
        self.umx_x_list = umx_x_list        # umx_x_lislt.shape = (,n_data_points)
        self.umx_y_matrix = umx_y_matrix    # umx_y_matrix.shape = (n_data_points, n_spectrum)
        self.umx_h_matrix = umx_h_matrix    # umx_h_matrix.shape = (fnsub, n_spectrum)
    def get_sum_data(self, sub_idx):
        return (self.umx_y_matrix * self.umx_h_matrix[sub_idx]).sum(axis=1)
    def get_first_data(self, sub_idx):
        return self.umx_y_matrix[:, 0] * self.umx_h_matrix[sub_idx, 0]
    def get_btm_curves(self, sub_idx):
        if self.standard_type in ("ts", "bd"):
            return pg.PlotDataItem([self.umx_x_list[0], self.umx_x_list[-1]], [0, 0])
        else:
            baseline_drift_left = (self.umx_y_matrix[0, 1:] * self.umx_h_matrix[sub_idx, 1:]).sum()
            baseline_drift_right = (self.umx_y_matrix[-1, 1:] * self.umx_h_matrix[sub_idx, 1:]).sum()
            return pg.PlotDataItem([self.umx_x_list[0], self.umx_x_list[-1]], [baseline_drift_left, baseline_drift_right])
class SubtractionData():
    def __init__(self, abs_id, x_minmax1, master_x_list1, added_y_list1, umx_h_list):
        self.abs_id = abs_id
        self.x_minmax1 = x_minmax1
        self.master_x_list1 = master_x_list1
        self.added_y_list1 = added_y_list1
        self.umx_h_list = umx_h_list        # len: (spc_file.fnxub)  
    def get_data(self, sub_idx, original_spc_file):
        original_x_data, original_y_data = original_spc_file.get_data(self.x_minmax1[0], self.x_minmax1[1], sub_idx=sub_idx)
        subtracted_y_list = original_y_data + self.added_y_list1 * self.umx_h_list[sub_idx]
        return self.master_x_list1, subtracted_y_list
    def get_btm_curves(self):
        return pg.PlotDataItem([self.master_x_list1[0], self.master_x_list1[-1]], [0, 0])
# スペクトル操作ツールバー
class ToolbarLayout(QVBoxLayout):
    def __init__(self, window_type, parent=None):
        self.parent = parent
        self.isImageSet = False
        self.current_N_maps = 0
        self.current_N_spectrum = 0
        self.pbar_widget = None
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)
        # # 元のイメージと interactive に作用する GUIを、予め作成しとく
        self.cfp_setting_popup = popups.CfpSettingsPopup(parent=self.parent, initial_values=(0,0), labels=("x position", "y position"), title="set cell free position")
        self.cfp_popup_connected = False    # まだ self.parent.map_widget 存在していないので、cfp_settings_popup を表示する段でコネクトする
        # レイアウト準備
        map_layout = QVBoxLayout()
        spectrum_layout = QVBoxLayout()
        # 追加された画像・スペクトルはここへ
        self.added_map_info_list = []
        self.added_spectrum_info_list = []
        self.added_spectrums_info_list = []
        # マップスペクトルウィンドウのみで表示するもボタンたち
        if window_type == "ms": # map & spectrum
            # シグナル強度
            btnSignalIntensity = my_w.CustomPicButton("sig_int1.svg", "sig_int2.svg", "sig_int3.svg", base_path=gf.icon_path)
            btnSignalIntensity.clicked.connect(self.execute_signal_intensity)
            btnSignalIntensity.setToolTip("signal intensity")
            # シグナル to ベースライン
            btnSignalToBaseline = my_w.CustomPicButton("sig2base1.svg", "sig2base2.svg", "sig2base3.svg", base_path=gf.icon_path)
            btnSignalToBaseline.clicked.connect(self.execute_signal_to_baseline)
            btnSignalToBaseline.setToolTip("signal to baseline")
            # シグナル to Horizontal ベースライン
            btnSignalToHBaseline = my_w.CustomPicButton("sig2h_base1.svg", "sig2h_base2.svg", "sig2h_base3.svg", base_path=gf.icon_path)
            btnSignalToHBaseline.clicked.connect(self.execute_signal_to_H_baseline)
            btnSignalToHBaseline.setToolTip("signal to horizontal baseline")
            # シグナル to Axis
            btnSignalToAxis = my_w.CustomPicButton("sig2axis1.svg", "sig2axis2.svg", "sig2axis3.svg", base_path=gf.icon_path)
            btnSignalToAxis.clicked.connect(self.execute_signal_to_axis)
            btnSignalToAxis.setToolTip("signal to axis")
            # # ガウスフィット
            # btnCurveFitting = my_w.CustomPicButton("gauss_fit1.png", "gauss_fit2.png", "gauss_fit3.png", base_path=gf.icon_path)
            # btnCurveFitting.clicked.connect(self.execute_curve_fitting)
            # btnCurveFitting.setToolTip("gaussian fitting")
            # アンミックスボタン
            btnUnmixing = my_w.CustomPicButton("unmix1.svg", "unmix2.svg", "unmix3.svg", base_path=gf.icon_path)
            btnUnmixing.clicked.connect(self.execute_unmixing)
            btnUnmixing.setToolTip("unmixing using added spectrum")
            # アンミックス右クリックメニュー
            btnUnmixing.setContextMenuPolicy(Qt.CustomContextMenu)
            unmix_action_name_list=["with exported method"]
            unmix_action_func_list=[self.unmix_with_method]
            menu = my_w.CustomContextMenu(parentBtn=btnUnmixing, action_name_list=unmix_action_name_list, action_func_list=unmix_action_func_list)
            btnUnmixing.customContextMenuRequested.connect(functools.partial(my_w.on_context_menu, menu=menu))
            # 宇宙線除去
            btnCosmicRayRemoval = my_w.CustomPicButton("CRR1.svg", "CRR2.svg", "CRR3.svg", base_path=gf.icon_path)
            btnCosmicRayRemoval.setToolTip("cosmic ray removal")
            btnCosmicRayRemoval.clicked.connect(functools.partial(self.cosmic_ray_removal, ask=True))
            # 宇宙線除去右クリックメニュー
            btnCosmicRayRemoval.setContextMenuPolicy(Qt.CustomContextMenu)
            crr_action_name_list=["hide/show Cosmic Rays", "Clear Detected Cosmic Rays"]
            crr_action_func_list=[self.hide_show_cosmic_rays, self.clear_cosmic_rays]
            menu = my_w.CustomContextMenu(parentBtn=btnCosmicRayRemoval, action_name_list=crr_action_name_list, action_func_list=crr_action_func_list)
            btnCosmicRayRemoval.customContextMenuRequested.connect(functools.partial(my_w.on_context_menu, menu=menu))
            # PCAノイズフィルター
            btnNoiseFilterPCA = my_w.CustomPicButton("NF1.svg", "NF2.svg", "NF3.svg", base_path=gf.icon_path)
            btnNoiseFilterPCA.setToolTip("PCA based Noise Filter")
            btnNoiseFilterPCA.clicked.connect(functools.partial(self.apply_noise_filter, ask=True))
            # # 計算
            # btnImageCalculator = my_w.CustomPicButton("calc1.png", "calc2.png", "calc3.png", base_path=gf.icon_path)
            # btnImageCalculator.clicked.connect(self.launch_image_calculator)
            # btnImageCalculator.setToolTip("launch image calculator")
            # 現在のスペクトルを追加
            btnAddCurrent = my_w.CustomPicButton("add_cur_spec1.svg", "add_cur_spec2.svg", "add_cur_spec3.svg", base_path=gf.icon_path)
            btnAddCurrent.clicked.connect(self.add_current_spectrum)
            btnAddCurrent.setToolTip("add current spectrum")
            # 細胞が無いエリアを設定（unmixで使う）
            btnSetCFP = my_w.CustomPicButton("cfp1.svg", "cfp2.svg", "cfp3.svg", base_path=gf.icon_path)
            btnSetCFP.clicked.connect(self.set_CellFreePosition)
            btnSetCFP.setToolTip("set cell free position (x, y) in a map image")
            # 全てのmapの保存
            btnSaveAllMaps = my_w.CustomPicButton("save_map1.svg", "save_map2.svg", "save_map3.svg", base_path=gf.icon_path)
            btnSaveAllMaps.clicked.connect(self.save_all_maps)
            btnSaveAllMaps.setToolTip("save all map images in current contrast\n(for unmixed map images, unmixed spectrums will also be saved)")
            # ターゲット保存
            btnSaveTarget = my_w.CustomPicButton("save_target1.svg", "save_target2.svg", "save_target3.svg", base_path=gf.icon_path)
            btnSaveTarget.clicked.connect(self.save_target)
            btnSaveTarget.setToolTip("save target (crosshair)")
            # レイアウト
            map_layout.addWidget(btnCosmicRayRemoval)
            map_layout.addWidget(btnNoiseFilterPCA)
            map_layout.addWidget(btnSetCFP)
            map_layout.addWidget(btnSignalIntensity)
            map_layout.addWidget(btnSignalToBaseline)
            map_layout.addWidget(btnSignalToHBaseline)
            map_layout.addWidget(btnSignalToAxis)
            # map_layout.addWidget(btnCurveFitting)
            map_layout.addWidget(btnUnmixing)
            # map_layout.addWidget(btnImageCalculator)
            map_layout.addWidget(btnSaveAllMaps)
            map_layout.addWidget(btnSaveTarget)
            map_layout.addItem(my_w.CustomSpacer())
            map_layout.addWidget(my_w.CustomSeparator())  # スペーサー
            map_layout.addItem(my_w.CustomSpacer())       # スペーサー
            spectrum_layout.addWidget(btnAddCurrent)
        # spectrum windowだけで出てくるボタンたち
        elif window_type == "s":
            pass
        # unmix method作成画面ででてくるボタンたち
        if window_type == "u":
            # バックグラウンド追加ボタン
            btnIncludeCellFreePosition = my_w.CustomPicButton("include_cell_free_position1.svg", "include_cell_free_position2.svg", "include_cell_free_position3.svg", base_path=gf.icon_path)
            btnIncludeCellFreePosition.clicked.connect(self.include_CellFreePosition)
            btnIncludeCellFreePosition.setToolTip("include/exclude spectrum from cell free position\n(if set, a cell free position will be required when runnning the method)")
            # レンジ設定ボタン
            btnSetRange = my_w.CustomSmallButton("range")
            btnSetRange.clicked.connect(self.set_range)
            btnSetRange.setToolTip("range setting")
            # レンジdisplay
            self.range_left = my_w.CustomSmallLabel("none")
            self.range_right = my_w.CustomSmallLabel("none")
            # メソッドexportボタン
            btnExportMethod = my_w.CustomPicButton("export_umx1.svg", "export_umx2.svg", "export_umx3.svg", base_path=gf.icon_path)
            btnExportMethod.clicked.connect(self.export_method)
            btnExportMethod.setToolTip("export method")
            # レイアウト
            spectrum_layout.addWidget(btnIncludeCellFreePosition)
            spectrum_layout.addWidget(btnSetRange)
            spectrum_layout.addWidget(self.range_left)
            spectrum_layout.addWidget(self.range_right)
            spectrum_layout.addWidget(btnExportMethod)
        # アンミキシング window 以外で表示される者たち
        else:
            # スペクトルの引き算
            btnSpectrumLinearSubtraction = my_w.CustomPicButton("spct_calc1.svg", "spct_calc2.svg", "spct_calc3.svg", base_path=gf.icon_path)
            btnSpectrumLinearSubtraction.clicked.connect(functools.partial(self.execute_spectrum_linear_subtraction, to_zero=False))
            btnSpectrumLinearSubtraction.setToolTip("linear subtraction of spectrum")
            # スペクトル引き算右クリックメニュー
            btnSpectrumLinearSubtraction.setContextMenuPolicy(Qt.CustomContextMenu)
            subtraction_action_name_list=["to zero"]
            subtraction_action_func_list=[functools.partial(self.execute_spectrum_linear_subtraction, to_zero=True)]
            subt_menu = my_w.CustomContextMenu(parentBtn=btnSpectrumLinearSubtraction, action_name_list=subtraction_action_name_list, action_func_list=subtraction_action_func_list)
            btnSpectrumLinearSubtraction.customContextMenuRequested.connect(functools.partial(my_w.on_context_menu, menu=subt_menu))
            # レイアウト
            spectrum_layout.addWidget(btnSpectrumLinearSubtraction)
        # 右側の軸を隠すかどうか
        btnHideRightAx = my_w.CustomPicButton("HideShow_R_Ax1.svg", "HideShow_R_Ax2.svg", "HideShow_R_Ax3.svg", base_path=gf.icon_path)
        btnHideRightAx.clicked.connect(self.hide_right_axis)
        btnHideRightAx.setToolTip("hide/show right axis")
        spectrum_layout.addWidget(btnHideRightAx)
        # スペクトルオンリーのウィンドウでも表示するものたち
        # スペクトル追加
        btnAddSpectrum = my_w.CustomPicButton("add_spct1.svg", "add_spct2.svg", "add_spct3.svg", base_path=gf.icon_path)
        btnAddSpectrum.clicked.connect(self.add_spectrum_from_file)
        btnAddSpectrum.setToolTip("add spectrum from a file")
        # スペクトルを保存
        btnSaveSpectrum = my_w.CustomPicButton("save_spct1.svg", "save_spct2.svg", "save_spct3.svg", base_path=gf.icon_path)
        btnSaveSpectrum.clicked.connect(self.save_spectrum)
        btnSaveSpectrum.setToolTip("save current spectrum")
        # Map-Spect table 表示
        btnMapSpectTable = my_w.CustomPicButton("spct_map_table1.svg", "spct_map_table2.svg", "spct_map_table3.svg", base_path=gf.icon_path)
        btnMapSpectTable.clicked.connect(self.parent.parent.open_map_spect_table)
        btnMapSpectTable.setToolTip("open map-spectrum table")
        # レイアウト
        spectrum_layout.insertWidget(0, btnAddSpectrum)
        spectrum_layout.addWidget(btnSaveSpectrum)
        self.addItem(my_w.CustomSpacer())       # スペーサー
        self.addLayout(map_layout)
            # ここにスペーサーが入ります（map_layoutに含まれている）
        self.addLayout(spectrum_layout)
        self.addItem(my_w.CustomSpacer())       # スペーサー
        self.addWidget(my_w.CustomSeparator())  # スペーサー
        self.addItem(my_w.CustomSpacer())       # スペーサー
        # テーブル表示ボタン
        self.addWidget(btnMapSpectTable)
        self.addStretch(1)
    # 何かしら追加した時作成されたオブジェクトを格納
    def add_content(self, item, CLASS, info=None, parent_window=None):   # "map" or "spectrum", "added" or unmixed (added は vb2で、unmixed は vb1)
        if CLASS == "Spectrum":
            added_content = AddedContent_Spectrum(item, info, parent_window)
        elif CLASS == "SubtractedSpectrums":
            added_content = AddedContent_SubtractedSpectrums(item, info, parent_window)
            self.added_spectrums_info_list.append(added_content)
        elif CLASS == "RepresentativeCFP":
            added_content = AddedContent_RepresentativeCFP(item, info, parent_window)
        elif CLASS == "Map":
            added_content = AddedContent_Map(item, info, parent_window)
        elif CLASS == "Unmixed":
            added_content = AddedContent_Unmixed(item, info, parent_window)
        getattr(self, "added_%s_info_list"%added_content.info["content"]).append(added_content)
        self.parent.parent.map_spect_table.add_content(added_content)
        # マップの場合、最初から表示
        if added_content.info["content"] == "map":
            self.parent.parent.map_spect_table.focus_map(added_content)
    def focus_unfocus_content(self, item):
        # スペクトルの場合
        self.parent.spectrum_widget.focus(item)
    # スペクトルを追加：ただし、1本のスペクトルであるものに限る
    def add_spectrum_from_file(self):
        file_path_set, file_type = QFileDialog.getOpenFileNames(self.parent, 'Select spctrum file', gf.settings["last opened dir"], filter="spc files (*.spc *.spcl)")
        for file_path in file_path_set:
            # 開く、追加する
            spc_file = gf.open_spc_spcl(file_path)
            # 単一スペクトルの場合
            if spc_file.fnsub == 1:
                plot_data_item = pg.PlotDataItem(spc_file.x, spc_file.sub[0].y, fillLevel=0)
                self.add_plot_data_item(plot_data_item, detail=file_path, values=[], data=spc_file)
            else:
                ppup = popups.WarningPopup("Error in opening '%s'\nThe file contains more than 1 spectrum"%file_path)
                ppup.exec_()
    # 現在のスペクトルを追加
    def add_current_spectrum(self):
        plot_data_item = self.parent.spectrum_widget.get_current_plot_data_item()
        # テーブルに追加
        self.add_plot_data_item(
            plot_data_item, 
            detail="from_data", 
            values=[self.parent.spectrum_widget.cur_x, self.parent.spectrum_widget.cur_y]
            )
    def add_plot_data_item(self, plot_data_item, detail, values, data=None):
        # ボタン追加
        self.parent.spectrum_widget.add_spectrum_to_v2(plot_data_item)
        self.add_content(
            plot_data_item, 
            CLASS = "Spectrum",
            info={"content":"spectrum", "type":"added", "detail":detail, "values":values, "data":data}, 
            parent_window=self.parent, 
        )
    # build unmix method 専用
    def include_CellFreePosition(self):
        added_item_list = self.parent.spectrum_widget.vb2.addedItems
        # CFPが追加されているか
        for added_item in added_item_list:
            if not isinstance(added_item, pg.InfiniteLine):
                continue
            else:
                break
        # ベースラインドリフトが追加されていない場合
        else:
            # viewboxには、horizontal line を赤点線で入れる
            representative_cell_free_pos = pg.InfiniteLine(angle=0, movable=False)
            representative_cell_free_pos.setPen(gf.mk_bg_pen())
            self.parent.spectrum_widget.vb2.addItem(representative_cell_free_pos)
            #ボタン追加
            self.add_content(
                representative_cell_free_pos, 
                CLASS="RepresentativeCFP",
                info={"content":"spectrum", "type":"added", "detail":"cell free position", "values":[]}, 
                parent_window=self.parent
                )
            return
        # ベースラインドリフトが追加されている場合
        for widget in self.parent.parent.map_spect_table.spectrum_layout.all_widgets():
            if widget.optional_item.info["detail"] == "cell free position":
                break
        widget.optional_item.remove_item()
        self.parent.parent.map_spect_table.spectrum_layout.removeWidget(widget)
        widget.deleteLater()
        del widget
        self.parent.parent.map_spect_table.spectrum_focus_changed(event=False)
    def set_range(self):
        # 範囲を決める
        range_settings_popup = popups.RangeSettingsPopup(parent=self.parent, title="unmixing range")
        done = range_settings_popup.exec_()
        if done:
            RS1 = range_settings_popup.spbx_RS1.value()
            RS2 = range_settings_popup.spbx_RS2.value()
            RS1, RS2 = np.sort([RS1, RS2])
            self.range_left.setText(str(RS1))
            self.range_right.setText(str(RS2))
        else:
            return
    def export_method(self, event=None, save_path=None, ask=True):
        # レンジが未設定の場合、エラー
        if self.range_left.text() == "none":
            warning_popup = popups.WarningPopup("ranges are not set")
            warning_popup.exec_()
            return
        # 保存先
        if save_path is None:
            default_path = os.path.join(gf.default_last_opened_dir, "new_unmixing_method.umx")
            save_path, file_type = QFileDialog.getSaveFileName(self.parent, 'save unmixing method file', default_path, filter="unmix method files (*.umx)")
        else:
            if os.path.exists(save_path) and ask:
                warwning_popup = popups.WarningPopup("File '%s' already exists. Do you want to overwrite it?"%save_path, p_type="Bool")
                done = warwning_popup.exec_()
                if 65536:
                    save_path = None
        if save_path:
            # メソッドとして保存
            self.parent.spectrum_widget.save_as_method(save_path=save_path)
    # 右側の軸を隠すかどうか
    def hide_right_axis(self):
        isVisible = self.parent.spectrum_widget.getAxis("right").isVisible()
        self.parent.spectrum_widget.showAxis("right", show=not isVisible)
    # マップ作成
    def execute_signal_intensity(self, event=None, ask=True, RS=None):
        # 範囲を決める
        if ask:
            value_settings_popup = popups.ValueSettingsPopup(parent=self.parent, title="signal intensity", double=True)
            done = value_settings_popup.exec_()
            RS = value_settings_popup.spbx_RS.value()
        else:
            done = 1
        # 計算
        if done == 1:
            image2D = self.parent.spectrum_widget.signal_intensity(RS)
            # ボタン追加
            self.add_content(
                image2D, 
                CLASS="Map", 
                info={"content":"map", "type":"added", "detail":"signal_intensity", "values":[RS]}, 
                parent_window=self.parent
            )
    def execute_signal_to_baseline(self, event=None, ask=True, RS_set=None):
        # 範囲を決める
        if ask:
            range_settings_popup = popups.RangeSettingsPopup(parent=self.parent, title="siganl to baseline")
            done = range_settings_popup.exec_()
            RS1 = range_settings_popup.spbx_RS1.value()
            RS2 = range_settings_popup.spbx_RS2.value()
            RS1, RS2 = np.sort([RS1, RS2])
        else:
            done = 1
            RS1, RS2 = np.sort(RS_set)
        # 計算
        if done == 1:
            image2D = self.parent.spectrum_widget.signal_to_bl(RS1, RS2)
            # ボタン追加
            self.add_content(
                image2D, 
                CLASS="Map", 
                info={"content":"map", "type":"added", "detail":"signal_to_baseline", "values":[RS1, RS2]}, 
                parent_window=self.parent
            )
    def execute_signal_to_H_baseline(self, event=None, ask=True, RS_set=None):
        # 範囲を決める
        if ask:
            range_settings_popup = popups.RangeSettingsPopup(parent=self.parent, title="signal to H baseline")
            done = range_settings_popup.exec_()
            RS1 = range_settings_popup.spbx_RS1.value()
            RS2 = range_settings_popup.spbx_RS2.value()
            RS1, RS2 = np.sort([RS1, RS2])
        else:
            done = 1
            RS1, RS2 = np.sort(RS_set)
        # 計算
        if done == 1:
            image2D = self.parent.spectrum_widget.signal_to_h_bl(RS1, RS2)
            # ボタン追加
            self.add_content(
                image2D, 
                CLASS="Map", 
                info={"content":"map", "type":"added", "detail":"signal_to_H_baseline", "values":[RS1, RS2]}, 
                parent_window=self.parent
            )
    def execute_signal_to_axis(self, event=None, ask=True, RS_set=None):
        # 範囲を決める
        if ask:
            range_settings_popup = popups.RangeSettingsPopup(parent=self.parent, title="signal to axis")
            done = range_settings_popup.exec_()
            RS1 = range_settings_popup.spbx_RS1.value()
            RS2 = range_settings_popup.spbx_RS2.value()
            RS1, RS2 = np.sort([RS1, RS2])
        else:
            done = 1
            RS1, RS2 = np.sort(RS_set)
        # 計算
        if done == 1:
            image2D = self.parent.spectrum_widget.signal_to_axis(RS1, RS2)
            # ボタン追加
            self.add_content(
                image2D, 
                CLASS="Map", 
                info={"content":"map", "type":"added", "detail":"signal_to_axis", "values":[RS1, RS2]}, 
                parent_window=self.parent
            )
    # アンミックス
    def execute_unmixing(self):
        # 範囲を決める
        range_settings_popup = popups.RangeSettingsPopup(parent=self.parent, title="unmixing")
        done = range_settings_popup.exec_()
        if done == 1:
            RS1 = range_settings_popup.spbx_RS1.value()
            RS2 = range_settings_popup.spbx_RS2.value()
            RS1, RS2 = np.sort([RS1, RS2])
            # アンミックス及びスペクトル追加、画像追加
            self.parent.spectrum_widget.unmixing(RS1, RS2)
            # スペクトル更新
            self.parent.spectrum_widget.replace_spectrum(0, 0)
            self.parent.map_widget.set_crosshair(0, 0)
            # アンミックスされたものの最初のものを表示
            abs_id = self.added_map_info_list[-1].info["data"].abs_id
            for added_map_info in self.added_map_info_list:
                if added_map_info.info["type"] == "unmixed":
                    if added_map_info.info["data"].abs_id == abs_id:
                        self.parent.parent.map_spect_table.focus_map(added_map_info)
                        break
    def unmix_with_method(self, btn=None, file_path=None):
        if file_path is None:
            file_path, file_type = QFileDialog.getOpenFileName(self.parent, 'select unmixing method file', gf.settings["method dir"], filter="unmixing method files (*.umx)")
        if file_path:
            with open(file_path, 'rb') as f:
                UMX = pickle.load(f)
            self.parent.spectrum_widget.unmix_with_method(UMX)
            self.parent.spectrum_widget.replace_spectrum(0, 0)
            self.parent.map_widget.set_crosshair(0, 0)
            # アンミックスされたものの最初のものを表示
            abs_id = self.added_map_info_list[-1].info["data"].abs_id
            for added_map_info in self.added_map_info_list:
                if added_map_info.info["type"] == "unmixed":
                    if added_map_info.info["data"].abs_id == abs_id:
                        self.parent.parent.map_spect_table.focus_map(added_map_info)
                        break
            # 次回用に保存
            gf.settings["method dir"] = os.path.dirname(file_path)
            gf.save_settings_file()
    def execute_spectrum_linear_subtraction(self, btn=None, to_zero=False, ask=True, RS_set=None):
        # チェック
        added_content_list = [added_spectrum_info for added_spectrum_info in self.added_spectrum_info_list 
            if added_spectrum_info.item.isVisible() and (added_spectrum_info.info["type"] == "added")]
        if len(added_content_list) > 1 or len(added_content_list) == 0:
            # v2 に表示されてるスペクトルが無ければ無効
            warning_popup = popups.WarningPopup("Exactly 1 added spectrum (blue spectrum) should be displayed!")
            warning_popup.exec_()
            return
        if ask:
            range_settings_popup = popups.RangeSettingsPopup(parent=self.parent, initial_values=(250, 450), title="set reference range")
            done = range_settings_popup.exec_()
            sRS = range_settings_popup.spbx_RS1.value()
            eRS = range_settings_popup.spbx_RS2.value()
        else:
            sRS = RS_set[0]
            eRS = RS_set[1]
            done = 1
        # スペクトルオンリーデータの場合
        if self.parent.spectrum_widget.spc_file.fnsub == done == 1:
            self.parent.spectrum_widget.spectrum_linear_subtraction(sRS, eRS, to_zero)
        # マップイメージの場合
        elif self.parent.spectrum_widget.spc_file.fnsub > 1 and done == 1:
            self.parent.spectrum_widget.multi_spectrum_linear_subtraction(sRS, eRS, to_zero)
            # スペクトル更新
            self.parent.spectrum_widget.replace_spectrum(0, 0)
            self.parent.map_widget.set_crosshair(0, 0)
    # 宇宙線除去
    def cosmic_ray_removal(self, ask=True):
        # 既に一度書かれていたら、一度 CRR を削除
        file_path, log = self.clear_cosmic_rays(ask=ask)
        if log == "CRR clear canceled":
            return
        # プログレスバー処理
        self.pbar_widget = popups.ProgressBarWidget(parent=self, message="Detecting cosmic rays... please wait.", real_value_max=self.parent.spectrum_widget.spc_file.fnpts)
        self.pbar_widget.show()
        segment_list = self.pbar_widget.get_segment_list(self.parent.spectrum_widget.spc_file.fnpts, segment=96)
        # 空間情報も含め、宇宙線を検出・除去する。
        cosmic_ray_locs, CRR_params = crrc.locate_cosmic_ray(self.parent.spectrum_widget.spc_file, pbar=self.pbar_widget, segment_list=segment_list)
        # 書き込むだけ（計算は既に終了している）オブジェクト中の data もアップデートされる（ただし元ファイル情報は保持したままである）
        self.pbar_widget.setLabel("Applying views...")
        self.pbar_widget.addValue(1)
        self.parent.spectrum_widget.spc_file.CRR(file_path, cosmic_ray_locs, CRR_params)
        self.apply_CRR()
        # プログレスバー閉じる
        self.pbar_widget.is_close_allowed = True
        self.pbar_widget.close()
    def apply_CRR(self):
        # マップイメージ
        map_x = int(self.parent.spectrum_widget.spc_file.log_dict[b"map_x"])
        map_y = int(self.parent.spectrum_widget.spc_file.log_dict[b"map_y"])
        image_data3d = np.zeros((map_x, map_y, 4), dtype=int)
        for sub_idx in self.parent.spectrum_widget.spc_file.log_dict[b"cosmic_ray_locs"].keys():
            cur_y, cur_x = divmod(sub_idx, map_x)
            image_data3d[cur_x, cur_y, :] = [255, 0, 0, 255]
        self.parent.map_widget.crr_img.setImage(image_data3d)
    def hide_show_cosmic_rays(self, btn=None):
        try:
            # スペクトル
            spc_item = self.parent.spectrum_widget.added_items_dict["CRR items"]
            spc_item.setVisible(not spc_item.isVisible())
            # マップ
            map_item = self.parent.map_widget.crr_img
            map_item.setVisible(not map_item.isVisible())
        except:
            pass
    def clear_cosmic_rays(self, btn=None, ask=True):
        dir_path = self.parent.dir_path
        file_name = self.parent.file_name
        file_path = os.path.join(dir_path, file_name)
        if b'cosmic_ray_locs' not in self.parent.spectrum_widget.spc_file.log_dict:
            return file_path, "CRR not set"
        if ask:
            warning_popup = popups.WarningPopup("Cosmic rays are already detected.\nAre you really sure to modify them?", title="warning", p_type="Bool")
            done = warning_popup.exec_()
            if done == 65536:
                return None, "CRR clear canceled"
            else:
                pass
        # オリジナルのデータを回復する
        self.parent.spectrum_widget.spc_file.clear_CRR_fm_object()
        gf.clear_CRR_fm_binary(file_path=file_path)
        # マップイメージ
        map_x = int(self.parent.spectrum_widget.spc_file.log_dict[b"map_x"])
        map_y = int(self.parent.spectrum_widget.spc_file.log_dict[b"map_y"])
        self.parent.map_widget.crr_img.setImage(np.zeros((map_x, map_y, 4), dtype=int))
        # スペクトル
        self.parent.spectrum_widget.replace_spectrum(0, 0)
        # クロスヘア
        self.parent.map_widget.set_crosshair(0, 0)
        return file_path, "CRR cleared"
    # ノイズフィルタ
    def apply_noise_filter(self, ask=True, N_components=100):
        if ask:
            noise_filter_popup = popups.ValueSettingsPopup(parent=self, initial_value=N_components, label="Number of\nComponent", double=False)
            done = noise_filter_popup.exec_()
            N_components = noise_filter_popup.spbx_RS.value()
        else:
            done = 1
        if done:
            self.pbar_widget = popups.ProgressBarWidget(parent=self, message="Noise reduction is in progress... please wait.")
            self.pbar_widget.show()
            self.pbar_widget.addValue(10)
            nfc.PCA_based_NF(self.parent.spectrum_widget.spc_file, N_components=N_components)
            self.pbar_widget.addValue(90)
            self.pbar_widget.is_close_allowed = True
            self.pbar_widget.close()

            self.parent.spectrum_widget.replace_spectrum(0, 0)
            self.parent.map_widget.set_crosshair(0, 0)
    def save_all_maps(self):
        if not self.isImageSet:
            warning_popup = popups.WarningPopup("There are no generated images!")
            warning_popup.exec_()
            return
        # vb2を全て隠す（unmix スペクトル用）
        is_shown_vb2 = self.parent.spectrum_widget.getAxis("right").isVisible()
        self.parent.spectrum_widget.showAxis("right", show=False)
        self.parent.spectrum_widget.vb2.hide()
        # 現在のコントラストの条件を取得
        contrast_range = self.parent.map_widget.ContrastConfigurator.getLevels()
        FIX = self.parent.map_widget.ContrastConfigurator.FIX
        BIT = self.parent.map_widget.ContrastConfigurator.BIT
        # image2Dを取得 & コントラスト設定 & 保存
        for added_content in self.parent.toolbar_layout.added_map_info_list:
            image2D = added_content.item
            image2D.save_image(
                base_name=self.parent.file_name_wo_ext, 
                dir_path=self.parent.dir_path, 
                FIX=FIX, 
                BIT=BIT, 
                contrast_range=contrast_range
                )
            if added_content.info["type"] == "unmixed":
                svg_base_path = os.path.join(self.parent.dir_path, "%s_%s "%(self.parent.file_name_wo_ext, image2D.name))
                # 番号付け
                svg_number = 1
                while os.path.exists("%s%s.svg"%(svg_base_path, svg_number)):
                    svg_number += 1
                svg_path = "%s%s.svg"%(svg_base_path, svg_number)
                # unmixにフォーカスして保存
                added_content.focus_unfocus(focused=True)
                added_content.hide_show_item()
                self.parent.spectrum_widget.save_spectrum(save_path=svg_path)
                added_content.hide_show_item()
        # 元の状態に戻す
        self.parent.spectrum_widget.showAxis("right", show=is_shown_vb2)
        self.parent.spectrum_widget.vb2.show()
    def save_target(self):
        # ターゲット
        x_size = int(self.parent.spectrum_widget.spc_file.log_dict[b"map_x"])
        y_size = int(self.parent.spectrum_widget.spc_file.log_dict[b"map_y"])
        cur_x = self.parent.spectrum_widget.cur_x
        cur_y = self.parent.spectrum_widget.cur_y
        # パス
        dir_path = self.parent.dir_path
        file_name_wo_ext = self.parent.file_name_wo_ext
        file_name = "{0}_x{1}y{2}.svg".format(file_name_wo_ext, cur_x, cur_y)
        save_path = os.path.join(dir_path, file_name)
        # svg作成
        svg_gen = QSvgGenerator()
        svg_gen.setFileName(save_path)
        svg_gen.setSize(QSize(x_size, y_size))
        svg_gen.setViewBox(QRect(0, 0, x_size, y_size))
        svg_gen.setTitle("{0} svg".format(file_name_wo_ext))
        svg_gen.setDescription("target svg with x={0}, y={1} in image x{2}y{3}".format(cur_x, cur_y, x_size, y_size))
        # クロスヘア追加
        half_width = gf.t_width / 2
        painter = QPainter()
        painter.begin(svg_gen)
        painter.setPen(gf.mk_target_color())
        painter.drawLine(QLineF(half_width, cur_y+0.5,  x_size-half_width,  cur_y+0.5))
        painter.drawLine(QLineF(cur_x+0.5,  half_width, cur_x+0.5,          y_size-half_width))
        painter.end()
    # unmixなどで使うbackgroundに相当するエリアを設定、spcのバイナリファイルに書き込む
    def set_CellFreePosition(self):
        # popup の range 入力欄の範囲設定
        x_size = int(self.parent.spectrum_widget.spc_file.log_dict[b"map_x"])
        y_size = int(self.parent.spectrum_widget.spc_file.log_dict[b"map_y"])
        # self.cfp_setting_popup.set_spinbox_range((0, x_size-1), "RS1")
        # self.cfp_setting_popup.set_spinbox_range((0, y_size-1), "RS2")
        dir_path = self.parent.dir_path
        file_name = self.parent.file_name
        file_path = os.path.join(dir_path, file_name)
        if b"[cfp]" in self.parent.spectrum_widget.spc_file.log_other:
            initial_values = (int(self.parent.spectrum_widget.spc_file.log_dict[b"cfp_x"]), int(self.parent.spectrum_widget.spc_file.log_dict[b"cfp_y"]))
        else:
            initial_values = (0, 0)
        # クロスヘア、スペクトル、cfp_settings_popup を initial_values にあわせる
        self.parent.map_widget.set_crosshair(*initial_values)
        self.parent.spectrum_widget.replace_spectrum(*initial_values)
        # popup表示
        self.cfp_setting_popup.set_spinbox_range((0, x_size-1), "RS1")
        self.cfp_setting_popup.set_spinbox_range((0, y_size-1), "RS2")
        self.cfp_setting_popup.setValues(initial_values)
        if not self.cfp_popup_connected:
            self.parent.map_widget.scene().sigMouseClicked.connect(self.cfp_setting_popup.on_map_widget_click)
            self.cfp_setting_popup.btnOK.clicked.connect(self.cfp_settings_popup_ok_clicked)
            self.cfp_popup_connected = True
        self.cfp_setting_popup.show()
        # 位置調整：親windowの右上に揃える感じで
        pwg = self.parent.geometry()
        pwf = self.parent.frameSize()
        self.cfp_setting_popup.move(pwg.left() + pwf.width(), pwg.top() - pwf.height() + pwg.height())
        return True
    def cfp_settings_popup_ok_clicked(self):
        # x, y は範囲内であることは、cfp_setting_popup の spbx 内で保証されている。
        cfp_x = self.cfp_setting_popup.spbx_RS1.value()
        cfp_y = self.cfp_setting_popup.spbx_RS2.value()
        dir_path = self.parent.dir_path
        file_name = self.parent.file_name
        file_path = os.path.join(dir_path, file_name)
        # 大元のバイナリファイルを上書き（ついでに、現在の spc_file にcfp_xなども追加します）
        self.parent.spectrum_widget.spc_file.set_cfp(file_path, cfp_x, cfp_y)
    def save_spectrum(self):
        # 保存先の状況をチェック
        dir_path = self.parent.dir_path
        file_name_wo_ext = self.parent.file_name_wo_ext
        svg_number = 1
        file_name = "%s %d.svg"%(file_name_wo_ext, svg_number)
        while os.path.exists(os.path.join(dir_path, file_name)):
            svg_number += 1
            file_name = "%s %d.svg"%(file_name_wo_ext, svg_number)
        save_path = os.path.join(dir_path, file_name)
        # svg変換、保存
        self.parent.spectrum_widget.save_spectrum(save_path=save_path)

# スペクトル描画
class SpectrumWidget(pg.PlotWidget):
    def __init__(self, spc_file=None, parent=None):
        self.spc_file = spc_file
        self.parent = parent
        # 現在地情報
        self.cur_x = None
        self.cur_y = None
        # used for displaying multiple spectrum set in vb2
        self.abs_id = 0
        # 計算済みスペクトル格納庫（追加は、self.add_spectrum にて）
        self.added_items_dict = {"CRR items": pg.PlotCurveItem(pen=gf.mk_crr_pen())}
        # カーブフィット用情報
        self.gaussian_func_coeff_set = None # shape: (self.spc_file.fnsub, 5)
        # レイアウト
        super().__init__()
        self.getAxis("left").setWidth(w=gf.axis_width)
        self.getAxis("right").setWidth(w=gf.axis_width)
        self.showAxis("right", show=False)
        vb1 = self.plotItem.vb
        vb1.setMouseMode(pg.ViewBox.RectMode)
        # 追加するスペクトル用のviewbox（軸は右側）
        self.vb2 = pg.ViewBox()
        self.scene().addItem(self.vb2)
        self.getAxis("right").linkToView(self.vb2)
        self.vb2.setXLink(self.plotItem)
        # vbのサイズを同じにする
        gf.updateViews(vb1, self.vb2)
        vb1.sigResized.connect(functools.partial(gf.updateViews, vb1=vb1, vb2=self.vb2))
        # all spectrum items in vb1
        self.master_spectrum = pg.PlotDataItem(pen=gf.mk_o_pen(), fillLevel=0)
        self.addItem(self.master_spectrum)  # original
        self.additional_lines = []
        self.additional_fill_btwn_items = []
        self.additional_points = pg.ScatterPlotItem(size=3, pen=pg.mkPen(255, 0, 0, 255), brush=pg.mkBrush(255, 0, 0, 255))
        self.addItem(self.additional_points)
    # グラフがある場合、親 widget が focus を get できない。
    def focusInEvent(self, event):
        self.parent.focusInEvent(event)
    def focusOutEvent(self, event):
        self.parent.focusOutEvent(event)
    # 最初に何もないところへの追加
    def open_initial(self):
        # 初回開いたときにも追加可能
        # 複数のスペクトルがある場合でも、最初のものが表示される
        self.cur_x = 0
        self.cur_y = 0
        self.master_spectrum.setData(self.spc_file.x, self.spc_file.sub[0].y)
        # 宇宙線追加
        self.addItem(self.added_items_dict["CRR items"])
        # mapの場合テキスト追加（どこの位置のスペクトルかということ）
        if self.spc_file.fnsub > 1:
            self.text_item = pg.TextItem(text="   x=0, y=0")
            self.text_item.setParentItem(self.getPlotItem().vb)
        # Toolbarからの追加ではないので、ボタンを追加する必要がある
        self.parent.toolbar_layout.add_content(
            self.master_spectrum, 
            CLASS="Spectrum",
            info={"content":"spectrum", "type":"original", "detail":"", "values":[]}, 
            parent_window=self.parent
        )
    def get_current_plot_data_item(self):
        current_plot = self.getPlotItem().vb.addedItems[0]
        plot_data_item = pg.PlotDataItem(current_plot.xData, current_plot.yData, fillLevel=0)
        return plot_data_item
    # 現在表示されているスペクトルを(vb2に)追加
    def add_spectrum_to_v2(self, plot_data_item):
        # vb2への追加がはじめての場合のみ、右軸を表示する（それ以外の場合は設定をそのまま引継ぐ）
        if len(self.vb2.addedItems):
            self.showAxis("right")
        # 追加
        plot_data_item.setPen(gf.mk_a_pen())
        self.vb2.addItem(plot_data_item)
        return plot_data_item
    # def add_calculated_spectrum(self):
    #     # スペクトル描画用のplot_data_item作成：background引き算したいときとかは、係数（self.height_list_set）の方で調節してください
    #     spectrum = pg.PlotDataItem()
    #     spectrum.setData(self.umx_x_list, (self.umx_y_matrix * self.umx_height_matrix).sum(axis=1))
    #     spectrum.setPen(gf.mk_u_pen())
    #     self.addItem(spectrum)
    #     self.added_items_dict.setdefault("calculated spectrum items", [])
    #     self.added_items_dict["calculated spectrum items"].append(spectrum)
    #     return spectrum

    # mapデータ用。別の位置のspectrumを表示する
    def replace_spectrum(self, map_x, map_y):
        # 場所情報の更新
        self.cur_x = map_x
        self.cur_y = map_y
        self.text_item.setText("  x=%d, y=%d"%(self.cur_x, self.cur_y))
        # オリジナルのスペクトル
        sub_idx = self.spc_file.get_sub_idx(self.cur_x, self.cur_y)
        y_list = self.spc_file.sub[sub_idx].y
        self.master_spectrum.setData(self.spc_file.x, y_list)
        self.display_map_spectrum()
        self.display_additional_spectrum(sub_idx)
    def set_N_additional_lines(self, N):
        N_additional_lines = len(self.additional_lines)
        if N_additional_lines < N:
            for idx in range(N - N_additional_lines):
                additional_line = pg.PlotCurveItem(pen=gf.mk_u_pen())
                self.additional_lines.append(additional_line)
                self.addItem(additional_line)
        elif N_additional_lines > N:
            for idx in range(N_additional_lines - N):
                deleted_item = self.additional_lines.pop(0)
                self.removeItem(deleted_item)
        for content in self.additional_lines:
            content.show()
    def set_N_additional_fill_btwn_items(self, N):
        N_additional_fill_btwn_items = len(self.additional_fill_btwn_items)
        if N_additional_fill_btwn_items < N:
            for idx in range(N - N_additional_fill_btwn_items):
                additional_fill_btwn_item = pg.FillBetweenItem(brush=gf.mk_u_brush())
                self.additional_fill_btwn_items.append(additional_fill_btwn_item)
                self.addItem(additional_fill_btwn_item)
        elif N_additional_fill_btwn_items > N:
            for idx in range(N_additional_fill_btwn_items - N):
                deleted_item = self.additional_fill_btwn_items.pop(0)
                self.removeItem(deleted_item)
        for content in self.additional_fill_btwn_items:
            content.show()
    def hide_all_fill_btwn_items(self):
        for content in self.additional_fill_btwn_items:
            content.hide()
    def hide_all_lines(self):
        for content in self.additional_lines:
            content.hide()
    def hide_all_points(self):
        self.additional_points.hide()
    def show_all_fill_btwn_items(self):
        for content in self.additional_fill_btwn_items:
            content.show()
    def show_all_lines(self):
        for content in self.additional_lines:
            content.show()
    def show_all_points(self):
        self.additional_points.show()
    # Process items to display in vb1
    def display_map_spectrum(self):
        # map info
        if self.parent.cur_displayed_map_info is None:
            # umx_methodから呼ばれたときは、background を設定する際、mapを指定せずにreplace_spectrumするので、これが呼ばれてしまう。
            return
        values = self.parent.cur_displayed_map_info["values"]
        sub_idx = self.spc_file.get_sub_idx(self.cur_x, self.cur_y)
        if self.parent.cur_displayed_map_info["type"] == "unmixed":
            # ここから登録作業開始
            umx_data = self.parent.cur_displayed_map_info["data"]
            # draw all unmixed lines
            self.set_N_additional_lines(umx_data.n_th_components[1])
            total_y_list = np.zeros_like(umx_data.umx_x_list)
            for added_content in self.parent.toolbar_layout.added_map_info_list:
                if added_content.info["type"] != "unmixed":
                    continue
                if added_content.info["data"].abs_id != umx_data.abs_id:
                    continue
                # when it is not total signal
                if added_content.info["data"].standard_type != "ts":
                    idx = added_content.info["data"].n_th_components[0]
                    self.additional_lines[idx].setData(
                        added_content.info["data"].umx_x_list, 
                        added_content.info["data"].get_sum_data(sub_idx)
                        )
                    self.additional_lines[idx].show()
                    total_y_list += added_content.info["data"].get_first_data(sub_idx)
                # when it is the total signal
                else:
                    umx_data_total = added_content.info["data"]
            # calc total signal # total signal が未設定の場合でも、added_map_info_list に追加された時点で display_map_specrum が走っちゃうので、例外処理
            try:
                idx = umx_data_total.n_th_components[0]
                self.additional_lines[idx].setData(
                    umx_data_total.umx_x_list, 
                    umx_data_total.get_sum_data(sub_idx) + total_y_list
                    )
                self.additional_lines[idx].show()
                # draw fill between item
                self.set_N_additional_fill_btwn_items(1)
                self.additional_fill_btwn_items[0].setCurves(umx_data.get_btm_curves(sub_idx), self.additional_lines[umx_data.n_th_components[0]])
                self.additional_fill_btwn_items[0].show()
            except:
                pass
        elif self.parent.cur_displayed_map_info["type"] == "subtracted":
            # ここから登録作業開始
            subtraction_data = self.parent.cur_displayed_map_info["data"]
            master_x_list1, subtracted_y_list = subtraction_data.get_data(sub_idx, self.spc_file)
            # draw a subtracted line
            self.set_N_additional_lines(1)
            self.additional_lines[0].setData(
                master_x_list1, 
                subtracted_y_list
            )
            self.additional_lines[0].show()            
            # fill between item
            self.set_N_additional_fill_btwn_items(1)
            self.additional_fill_btwn_items[0].setCurves(subtraction_data.get_btm_curves(), self.additional_lines[0])
            self.additional_fill_btwn_items[0].show()
        elif self.parent.cur_displayed_map_info["type"] == "added":
            RS_idx1 = self.spc_file.get_idx(values[0])
            if len(values) == 1:
                self.set_N_additional_lines(1)
                self.hide_all_fill_btwn_items()
                RS_idx2 = None
                x_value2 = None
                y_value_list = None
                fill_top = None
            elif len(values) == 2:
                self.set_N_additional_fill_btwn_items(1)
                self.hide_all_lines()
                RS_idx2 = self.spc_file.get_idx(values[1])
                RS_idx1, RS_idx2 = np.sort([RS_idx1, RS_idx2])
                x_value2 = self.spc_file.x[RS_idx2]
                y_value_list = self.spc_file.sub[sub_idx].y[RS_idx1:RS_idx2 + 1]
                fill_top = pg.PlotDataItem(self.spc_file.x[RS_idx1:RS_idx2 + 1], y_value_list)
            x_value1 = self.spc_file.x[RS_idx1]
            # set graph
            if self.parent.cur_displayed_map_info["detail"] == "signal_intensity":
                y_value1 = self.spc_file.sub[sub_idx].y[RS_idx1]
                self.additional_lines[0].setData([x_value1, x_value1], [0, y_value1])
            elif self.parent.cur_displayed_map_info["detail"] == "signal_to_baseline":
                y_value1 = y_value_list[0]
                y_value2 = y_value_list[-1]
                fill_btm = pg.PlotDataItem([x_value1, x_value2], [y_value1, y_value2])
                # set values
                self.additional_fill_btwn_items[0].setCurves(fill_btm, fill_top)
            elif self.parent.cur_displayed_map_info["detail"] == "signal_to_H_baseline":
                min_y_value = np.min(y_value_list)
                fill_btm = pg.PlotDataItem([x_value1, x_value2], [min_y_value, min_y_value])
                # set values
                self.additional_fill_btwn_items[0].setCurves(fill_btm, fill_top)
            elif self.parent.cur_displayed_map_info["detail"] == "signal_to_axis":
                fill_btm = pg.PlotDataItem([x_value1, x_value2], [0, 0])
                # set values
                self.additional_fill_btwn_items[0].setCurves(fill_btm, fill_top)
            else:
                raise Exception("attr error")
        elif self.parent.cur_displayed_map_info["type"] == "custom":
            if "range" in self.parent.cur_displayed_map_info["data"].keys():
                self.set_N_additional_fill_btwn_items(1)
                RS_val1, RS_val2 = self.parent.cur_displayed_map_info["data"]["range"]
                RS_idx1 = self.spc_file.get_idx(RS_val1)
                RS_idx2 = self.spc_file.get_idx(RS_val2)
                RS_idx1, RS_idx2 = np.sort([RS_idx1, RS_idx2])
                y_value_list = self.spc_file.sub[sub_idx].y[RS_idx1:RS_idx2 + 1]
                x_value1 = self.spc_file.x[RS_idx1]
                x_value2 = self.spc_file.x[RS_idx2]
                # set values
                fill_btm = pg.PlotDataItem([x_value1, x_value2], [0, 0])
                fill_top = pg.PlotDataItem(self.spc_file.x[RS_idx1:RS_idx2 + 1], y_value_list)
                self.additional_fill_btwn_items[0].setCurves(fill_btm, fill_top)
            else:
                self.hide_all_fill_btwn_items()
            if "points" in self.parent.cur_displayed_map_info["data"].keys():
                self.additional_points.setData(
                    x=self.parent.cur_displayed_map_info["data"]["points"][sub_idx][0],
                    y=self.parent.cur_displayed_map_info["data"]["points"][sub_idx][1]
                    )
                self.show_all_points()
            else:
                self.hide_all_points()
            if "lines" in self.parent.cur_displayed_map_info["data"].keys():
                self.set_N_additional_lines(len(self.parent.cur_displayed_map_info["data"]["lines"][0]))
                for line, value in zip(self.additional_lines, self.parent.cur_displayed_map_info["data"]["lines"][sub_idx]):
                    line.setData([value, value], [0, 10000])
                self.show_all_lines()
            else:
                self.hide_all_lines()

    def display_additional_spectrum(self, sub_idx):
        # CRRされたスペクトル
        cosmic_ray_locs = self.spc_file.log_dict.get(b"cosmic_ray_locs", [])
        if sub_idx in cosmic_ray_locs:
            selected_se_idx_set, TopBottomLeftRight_idxes, original_data_set = cosmic_ray_locs[sub_idx]
            crr_x_list = np.empty(0, dtype=float)
            crr_y_list = np.empty(0, dtype=float)
            crr_connection = np.empty(0, dtype=float)
            for (s_idx, e_idx), original_data in zip(selected_se_idx_set, original_data_set):
                # 両サイドに広げる
                if 0 <= s_idx-1:
                    try:
                        crr_x_list = np.hstack((crr_x_list, self.spc_file.x[s_idx-1:e_idx+2]))
                        crr_y_list = np.hstack((crr_y_list, self.spc_file.sub[sub_idx].y[s_idx-1], original_data, self.spc_file.sub[sub_idx].y[e_idx+1]))
                        crr_connection = np.hstack((crr_connection, [True]*(e_idx - s_idx + 2) + [False]))
                    # end 側が飛び出ている場合をケア
                    except:
                        crr_x_list = np.hstack((crr_x_list, self.spc_file.x[s_idx-1:e_idx+1]))
                        crr_y_list = np.hstack((crr_y_list, self.spc_file.sub[sub_idx].y[s_idx-1], original_data))
                        crr_connection = np.hstack((crr_connection, [True]*(e_idx - s_idx + 1) + [False]))
                # start 側が飛びてている場合をケア
                else:
                    crr_x_list = np.hstack((crr_x_list, self.spc_file.x[s_idx:e_idx+2]))
                    crr_y_list = np.hstack((crr_y_list, original_data, self.spc_file.sub[sub_idx].y[e_idx+1]))
                    crr_connection = np.hstack((crr_connection, [True]*(e_idx - s_idx + 1) + [False]))
            self.added_items_dict["CRR items"].setData(x=crr_x_list, y=crr_y_list, connect=crr_connection)
        else:
            self.added_items_dict["CRR items"].setData()
    # map画像作成
    def signal_intensity(self, RS):
        RS_idx = self.spc_file.get_idx(RS)
        values_list = [self.spc_file.sub[sub_idx].y[RS_idx] for sub_idx in range(self.spc_file.fnsub)]
        image2d = np.reshape(values_list, self.spc_file.get_shape()).T
        image2D = Image2D(image2d, name="signal_intensity_%d"%RS)
        return image2D
    def signal_to_bl(self, sRS, eRS):
        # (sRS, eRS)と(sRS-idx, eRS-idx)は必ずしも一致しない（RSは降順にもなりうるがidxはあくまで昇順に並ぶ）
        sRS_idx, eRS_idx = np.sort([self.spc_file.get_idx(sRS), self.spc_file.get_idx(eRS)])
        half_RS_width = np.absolute(self.spc_file.x[eRS_idx] - self.spc_file.x[sRS_idx]) / 2
        selected_RS_diff_list_half = np.absolute(np.diff(self.spc_file.x[sRS_idx:eRS_idx + 1])) / 2
        area_values_list = np.empty(self.spc_file.fnsub, dtype=float)
        for sub_idx in range(self.spc_file.fnsub):
            selected_data = self.spc_file.sub[sub_idx].y[sRS_idx:eRS_idx + 1]
            raw_area = ((selected_data[1:] + selected_data[:-1]) * selected_RS_diff_list_half).sum()
            bg_area = np.absolute(selected_data[0] + selected_data[-1]) * half_RS_width
            area_values_list[sub_idx] = raw_area - bg_area
        image2d = area_values_list.reshape(self.spc_file.get_shape()).T
        image2D = Image2D(image2d, name="signal_to_baseline_%d-%d"%(sRS, eRS))
        return image2D
    def signal_to_h_bl(self, sRS, eRS):
        # (sRS, eRS)と(sRS-idx, eRS-idx)は必ずしも一致しない（RSは降順にもなりうるがidxはあくまで昇順に並ぶ）
        sRS_idx, eRS_idx = np.sort([self.spc_file.get_idx(sRS), self.spc_file.get_idx(eRS)])
        RS_width = np.absolute(self.spc_file.x[eRS_idx] - self.spc_file.x[sRS_idx])
        selected_RS_diff_list_half = np.absolute(np.diff(self.spc_file.x[sRS_idx:eRS_idx + 1])) / 2
        area_values_list = np.empty(self.spc_file.fnsub, dtype=float)
        for sub_idx in range(self.spc_file.fnsub):
            selected_data = self.spc_file.sub[sub_idx].y[sRS_idx:eRS_idx + 1]
            raw_area = ((selected_data[1:] + selected_data[:-1]) * selected_RS_diff_list_half).sum()
            bg_area = np.min(selected_data) * RS_width
            area_values_list[sub_idx] = raw_area - bg_area
        image2d = area_values_list.reshape(self.spc_file.get_shape()).T
        image2D = Image2D(image2d, name="signal_to_H_baseline_%d-%d"%(sRS, eRS))
        return image2D
    def signal_to_axis(self, sRS, eRS):
        # (sRS, eRS)と(sRS-idx, eRS-idx)は必ずしも一致しない（RSは降順にもなりうるがidxはあくまで昇順に並ぶ）
        sRS_idx, eRS_idx = np.sort([self.spc_file.get_idx(sRS), self.spc_file.get_idx(eRS)])
        # RS_width = np.absolute(self.spc_file.x[eRS_idx] - self.spc_file.x[sRS_idx])
        selected_RS_diff_list_half = np.absolute(np.diff(self.spc_file.x[sRS_idx:eRS_idx + 1])) / 2
        area_values_list = np.empty(self.spc_file.fnsub, dtype=float)
        for sub_idx in range(self.spc_file.fnsub):
            selected_data = self.spc_file.sub[sub_idx].y[sRS_idx:eRS_idx + 1]
            area_values_list[sub_idx] = ((selected_data[1:] + selected_data[:-1]) * selected_RS_diff_list_half).sum()
        image2d = area_values_list.reshape(self.spc_file.get_shape()).T
        image2D = Image2D(image2d, name="signal_to_axis_%d-%d"%(sRS, eRS))
        return image2D
    # def curve_fitting(self, sRS, eRS):
    #     # (sRS, eRS)と(sRS-idx, eRS-idx)は必ずしも一致しない（RSは降順にもなりうるがidxはあくまで昇順に並ぶ）
    #     sRS_idx, eRS_idx = np.sort([self.spc_file.get_idx(sRS), self.spc_file.get_idx(eRS)])
    #     # 大元（fittingされる前のもの）は、spc_fileから情報を取得しよう（そのほうが楽だし…）
    #     self.umx_x_list, master_y_list = self.spc_file.get_data(sRS, eRS, sub_idx=0)
    #     initial_s = (eRS - sRS) / 6
    #     # 格納庫
    #     self.gaussian_func_coeff_set = np.empty((self.spc_file.fnsub, 5), dtype=float)   # shape: (self.spc_file.fnsub, n_spectrum)
    #     # ピクセルごとに回す
    #     for idx, sub in enumerate(self.spc_file.sub):
    #         y_data = sub.y[sRS_idx:eRS_idx + 1]
    #         y_max = y_data.max()
    #         y_min = y_data.min()
    #         parameter_initial = [self.umx_x_list[np.argmax(y_data)], initial_s, y_max - y_min, -18, y_min]
    #         # カーブフィット
    #         try:
    #             parameter_optimal, covariance = curve_fit(gf.gaussian_fitting_function, self.umx_x_list, y_data, p0=parameter_initial, ftol=0.001, xtol=0.001)
    #         except:
    #             parameter_optimal = np.zeros(len(parameter_initial))
    #         self.gaussian_func_coeff_set[idx] = parameter_optimal
    #     # Image2Dへ変換
    #     int_list = np.empty((self.spc_file.fnsub, len(self.umx_x_list)), dtype=float)
    #     for idx, coeffs in enumerate(self.gaussian_func_coeff_set[:, :3]):
    #         int_list[idx] = gf.gaussian_function(self.umx_x_list, *coeffs)
    #     image2d = np.reshape(((int_list[:, 1:] + int_list[:, :-1]) * np.absolute(np.diff(self.umx_x_list) / 2)).sum(axis=1), self.spc_file.get_shape()).T
    #     image2D = Image2D(image2d, name="gaussian_fitting_%d-%d"%(sRS, eRS))
    #     return image2D
    # 追加されているスペクトルを元に、レンジの範囲内で、background (from cell or quartz), signal(s), （これ以降追加スペクトル非依存）base, slope1, slope2 にアンミックス
    def unmixing(self, sRS, eRS, no_baseline_for_added=False):
        # プログレスバー処理
        self.pbar_widget = popups.ProgressBarWidget(parent=self, message="Executing spectrum unmising... please wait.")
        self.pbar_widget.show()
        segment_list = self.pbar_widget.get_segment_list(self.spc_file.fnsub, 97)
        # (sRS, eRS)と(sRS-idx, eRS-idx)は必ずしも一致しない（RSは降順にもなりうるがidxはあくまで昇順に並ぶ）
        sRS_idx, eRS_idx = np.sort([self.spc_file.get_idx(sRS), self.spc_file.get_idx(eRS)])
        # 大元（unmixされる前のもの）は、spc_fileから情報を取得しよう（そのほうが楽だし…）
        umx_x_list, master_y_list = self.spc_file.get_data(sRS, eRS, 0)
        # デコンボするための素材：全て master_x に合うようにinterpolateするので、regional_x_listの方は不要、さらにhideされてるものは standard に含まないようにする
        added_content_list = [widget.optional_item for widget in self.parent.parent.map_spect_table.spectrum_layout.all_widgets() 
            if (widget.optional_item.info["type"] == "added") and widget.optional_item.item.isVisible()]
        added_summary_list = [added_content.summary() for added_content in added_content_list]
        n_data_points = len(umx_x_list)
        n_spectrum = len(added_content_list) + 3   # "+3" は base, slope1, slope2 の分
        regional_y_matrix = np.empty((n_data_points, n_spectrum), dtype=float, order="F")
        # base, slopeを追加
        regional_y_matrix[:, -3] = -1                       # base: 正方向の下駄は、slopeの和で表現可能
        slope_list1 = umx_x_list - umx_x_list.min()   # slopeは常に正の値
        slope_list2 = umx_x_list.max() - umx_x_list   # 増減が逆のsloopeも常に正
        regional_y_matrix[:, -2] = slope_list1              # slope1: 直角二等辺三角形とした
        regional_y_matrix[:, -1] = slope_list2              # slope2: 直角二等辺三角形とした
        x_range = np.ptp(umx_x_list)
        # 面積格納庫：これに高さを掛けた値が、エリア値となるわけよ。
        basic_area_values = np.empty(n_spectrum, dtype=float)
        basic_area_values[-3] = -x_range                 # base
        basic_area_values[[-2, -1]] = x_range ** 2 / 2    # slope
        x_diff_list_half = np.absolute(np.diff(umx_x_list)) / 2   # 追加スペクトル依存的な基本面積を求めるのに必要
        # signalsを加えていく（全て追加されたスペクトルをベースに追加する）
        for idx, added_content in enumerate(added_content_list):
            x_list = added_content.item.xData
            y_list = added_content.item.yData
            # interpする場合は元のデータのxは昇順である必要がある
            order = np.argsort(x_list)
            x_list = x_list[order]
            y_list = y_list[order]
            # 補完して取り出す（x_listがmaste_x_listと同じ時は、interpolateする必要無いけど、x_listがが降順の場合もあるのでちとややこしい）
            regional_y_list = np.interp(umx_x_list, x_list, y_list)  # この場合は勝手にmasete_x_listの順になってくれる
            # signal to baselineと同じ手法ででbgを除く（今後消す方針で：BGは事前に除いておくイメージ）
            if not no_baseline_for_added:
                regional_y_list -= np.linspace(regional_y_list[0], regional_y_list[-1], num=n_data_points)
            regional_y_matrix[:, idx] = regional_y_list
            # 面積計算する際の基本面積を求めておく
            basic_area_values[idx] = ((regional_y_list[1:] + regional_y_list[:-1]) * x_diff_list_half).sum()
        # non-negative least-square
        umx_height_matrix = np.empty((self.spc_file.fnsub, n_spectrum), dtype=float)
        rnorm_list = np.empty((self.spc_file.fnsub, 1), dtype=float)
        for idx, sub in enumerate(self.spc_file.sub):
            master_y_list = sub.y[sRS_idx:eRS_idx + 1]
            x, rnorm = nnls(regional_y_matrix, master_y_list)
            umx_height_matrix[idx] = x
            rnorm_list[idx] = rnorm
            # プログレスバー処理
            if idx in segment_list:
                self.pbar_widget.addValue(1)
        # 基本面積を乗じて面積を求める：最後の3つはまとめてベースラインとなっている➙和を取る：トータルのシグナルを最後に追加：rnorm_listも追加➙とりあえずしません！
        area_list_set = umx_height_matrix * basic_area_values[np.newaxis, :]
        area_list_set = np.concatenate((
            area_list_set[:, :-3],                             # 各々のシグナル
            area_list_set[:, -3:].sum(axis=1)[:, np.newaxis],  # baselineシグナル
            area_list_set.sum(axis=1)[:, np.newaxis],          # total シグナル（baselineのシグナルも含む）
            # rnorm_list * 1000
            ), axis=1)
        # map画像作成
        image2d_list = [np.reshape(area_list, self.spc_file.get_shape()).T for area_list in area_list_set.T]
        optional_name_list = added_summary_list + ["baseline_drift", "total_signal"]
        optional_id_list = list(map(lambda x: str(x+1), range(n_spectrum - 3))) + ["bd", "ts"]
        # 作られたmapたちをmap_widgeteに渡す
        for idx, (image2d, optional_name, optional_id) in enumerate(zip(image2d_list, optional_name_list, optional_id_list)):
            image2D = Image2D(image2d, name="unmixed_%d-%d_%s"%(sRS, eRS, optional_id))
            # ボタン追加
            if idx < n_spectrum - 3:
                umx_y_matrix = regional_y_matrix[:, [idx,-3,-2,-1]]   # regional_y_matrix.shape = (n_data_points, n_spectrum)
                umx_h_matrix = umx_height_matrix[:, [idx,-3,-2,-1]]   # umx_height_matrix.shape = (fnsub, n_spectrum)
            # baseline drift
            elif idx == n_spectrum - 3:
                umx_y_matrix = regional_y_matrix[:, -3:]   # regional_y_matrix.shape = (n_data_points, n_spectrum)
                umx_h_matrix = umx_height_matrix[:, -3:]   # umx_height_matrix.shape = (fnsub, n_spectrum)
            # total_signal（total以外の1列目だけの和に、加えることで真の total signal になる）
            elif idx == n_spectrum - 2:
                umx_y_matrix = regional_y_matrix[:, -2:]   # regional_y_matrix.shape = (n_data_points, n_spectrum)
                umx_h_matrix = umx_height_matrix[:, -2:]   # umx_height_matrix.shape = (fnsub, n_spectrum)
            unmixed_data = UnmixedData(
                standard_type = optional_id, 
                abs_id = self.abs_id, 
                n_th_components = (idx, n_spectrum - 1),    # 表示するための曲線の数。n_spectrum - 3 + 2 (baseline drift, total signal の 2)
                umx_x_list = umx_x_list, 
                umx_y_matrix = umx_y_matrix, 
                umx_h_matrix = umx_h_matrix
                )
            self.parent.toolbar_layout.add_content(
                image2D, 
                CLASS="Unmixed",
                info={
                    "content":"map", 
                    "type":"unmixed", 
                    "detail":optional_name, 
                    "values":[sRS, eRS, "#"+optional_id], 
                    "idx":idx, 
                    "data":unmixed_data, 
                    }, 
                parent_window=self.parent
            )
        # プログレスバー閉じる
        self.abs_id += 1
        self.pbar_widget.is_close_allowed = True
        self.pbar_widget.close()
    def unmix_with_method(self, UMX):
        # vb2 情報を事前確保
        already_in_vb2 = len(self.vb2.addedItems)
        if already_in_vb2:
            v2_x_range, v2_y_range = self.vb2.viewRange()
        is_displayed_list = []
        for added_item in self.vb2.addedItems:
            is_displayed_list.append(added_item.isVisible())
            added_item.hide()
        # procedures順に処理いていく
        for procedure in UMX.procedures:
            # とりあえず、登録されてるスペクトル全部を使ってunmixしてくパターン
            if procedure == "unmix":
                # バックグラウンドの場所を選択する
                if UMX.isBackgroundSet:
                    if b"[cfp]" in self.spc_file.log_other:
                        cfp_x = int(self.spc_file.log_dict[b"cfp_x"])
                        cfp_y = int(self.spc_file.log_dict[b"cfp_y"])
                    else:
                        bg_loc_settings_popup = popups.RangeSettingsPopup(parent=self, initial_values=(1, 1), labels=("x (pixels from left)", "y (pixels from top)"), title="background location")
                        bg_loc_settings_popup.spbx_RS1.setMaximum(0)    # 最後に転置して表示するので、xとyが逆になってる
                        bg_loc_settings_popup.spbx_RS2.setMaximum(0)    # 最後に転置して表示するので、xとyが逆になってる
                        bg_loc_settings_popup.spbx_RS1.setMaximum(int(self.spc_file.log_dict[b"map_y"]) - 1)    # 最後に転置して表示するので、xとyが逆になってる
                        bg_loc_settings_popup.spbx_RS2.setMaximum(int(self.spc_file.log_dict[b"map_x"]) - 1)    # 最後に転置して表示するので、xとyが逆になってる
                        done = bg_loc_settings_popup.exec_()
                        if done:
                            cfp_x = bg_loc_settings_popup.spbx_RS1.value()
                            cfp_y = bg_loc_settings_popup.spbx_RS2.value()
                            file_path = os.path.join(self.parent.dir_path, self.parent.file_name)
                            self.spc_file.set_cfp(file_path, cfp_x, cfp_y)
                        else:
                            return
                # スペクトル追加
                for spc_like, file_path in zip(UMX.spc_like_list, UMX.file_path_list):
                    plot_data_item = pg.PlotDataItem(spc_like.x, spc_like.sub[0].y, fillLevel=0)
                    self.parent.toolbar_layout.add_plot_data_item(plot_data_item, detail=file_path, values=[])
                # bg追加
                if UMX.isBackgroundSet:
                    self.replace_spectrum(map_x=cfp_x, map_y=cfp_y)
                    self.parent.toolbar_layout.add_current_spectrum()
                # アンミックス
                self.unmixing(UMX.target_range[0], UMX.target_range[1])
        # 追加スペクトルを隠す
        for added_item in self.parent.spectrum_widget.vb2.addedItems:
            added_item.hide()
        # 元のv2を復帰
        for idx, is_displayed in enumerate(is_displayed_list):
            if is_displayed:
                self.parent.spectrum_widget.vb2.addedItems[idx].show()
        if already_in_vb2:
            self.vb2.setYRange(*v2_y_range)
    # svgにて保存
    def save_spectrum(self, save_path):
        svg_data = SVGExporter(self.scene())
        svg_data.export(fileName=save_path)
        # デフォルトではサイズ指定されておらず、パワポに貼り付ける際に正方形になってしまう
        q_size = self.frameSize()
        x, y = q_size.width(), q_size.height()
        # svg_dataはxml形式なので、それに基づいて編集する
        tree = ET.parse(save_path)
        root = tree.getroot()
        # データにする範囲、および表示サイズを指定する
        root.set("viewBox", "0 0 %d %d"%(x, y))
        root.set("width", str(x))
        root.set("height", str(y))
        # 上書き保存
        tree = ET.ElementTree(element=root)
        tree.write(save_path, encoding='utf-8', xml_declaration=True)
    # spc形式でスペクトルを保存
    def save_spectrum_as_spc(self, spc_like, save_path=None, ask=True):
        # 保存先：ボタンについてる名前がデフォルトのファイル名になる
        if save_path is None:
            name_overlapped = True
            N = 1
            while name_overlapped:
                default_path = "{0}_sub{1}.spc".format(os.path.join(self.parent.dir_path, self.parent.file_name_wo_ext), N)
                if os.path.exists(default_path):
                    N += 1
                else:
                    name_overlapped = False
            if ask:
                save_path, file_type = QFileDialog.getSaveFileName(self.parent, 'save as spc file', default_path, filter="unmix method files (*.spc)")
            else:
                save_path = default_path
        else:
            if os.path.exists(save_path) and ask:
                warwning_popup = popups.WarningPopup("File '%s' already exists. Do you want to overwrite it?"%save_path, p_type="Bool")
                done = warwning_popup.exec_()
                if 65536:
                    save_path = None
        if save_path:
            spc_like.save_as_spc(save_path=save_path)
    # メソッドとして保存する。vb2の中身を保存するようになっているが、UnmixingMethodWindow内にしかこれを呼び出すボタンが無い（今の所）。
    def save_as_method(self, save_path):
        # 入れ物づくり
        UMX = gf.UnmixingMethod(procedures=["unmix"])
        for added_content in self.parent.toolbar_layout.added_spectrum_info_list:
            addedItem = added_content.item
            if isinstance(addedItem, pg.PlotDataItem):
                UMX.spc_like_list.append(added_content.info["data"])
                UMX.file_path_list.append(added_content.info["detail"])
            elif isinstance(addedItem, pg.InfiniteLine):
                UMX.isBackgroundSet = True
        # レンジ
        UMX.target_range = [float(self.parent.toolbar_layout.range_left.text()), float(self.parent.toolbar_layout.range_right.text())]
        # 保存
        with open(save_path, 'wb') as f:
            pickle.dump(UMX, f)
    def get_spectrum_linear_subtraction_basic_info(self, sRS, eRS):
        # # (sRS, eRS)と(sRS-idx, eRS-idx)は必ずしも一致しない（RSは降順にもなりうるがidxはあくまで昇順に並ぶ）
        # sRS_idx, eRS_idx = np.sort([self.spc_file.get_idx(sRS), self.spc_file.get_idx(eRS)])
        # 使用する追加スペクトル（事前チェックは済ませといてね）
        added_content_list = [added_spectrum_info for added_spectrum_info in self.parent.toolbar_layout.added_spectrum_info_list 
            if added_spectrum_info.item.isVisible() and (added_spectrum_info.info["type"] == "added")]
        added_content = added_content_list[0]
        # データ整序
        added_x_list = added_content.item.xData
        added_y_list = added_content.item.yData
        order = np.argsort(added_x_list)
        added_x_list = added_x_list[order]
        added_y_list = added_y_list[order]
        # 元々のスペクトルとadded_spectrumと[sRS, eRS]の共通範囲を取得する
        x_min1 = max([self.spc_file.x.min(), min(added_x_list)])
        x_max1 = min([self.spc_file.x.max(), max(added_x_list)])
        x_min2 = max([self.spc_file.x.min(), min(added_x_list), min(sRS, eRS)])
        x_max2 = min([self.spc_file.x.max(), max(added_x_list), max(sRS, eRS)])
        # 補間して揃える
        master_x_list1, master_y_list1 = self.spc_file.get_data(x_min1, x_max1)
        added_y_list1 = np.interp(master_x_list1, added_x_list, added_y_list)
        master_x_list2, master_y_list2 = self.spc_file.get_data(x_min2, x_max2)
        added_y_list2 = np.interp(master_x_list2, added_x_list, added_y_list)
        return (x_min1, x_max1), (x_min2, x_max2), added_y_list1, added_y_list2, added_content
    # self.spectrum_linear_subtraction の map 用 version.
    def multi_spectrum_linear_subtraction(self, sRS, eRS, to_zero):
        # プログレスバー処理
        self.pbar_widget = popups.ProgressBarWidget(parent=self, message="Subtracting spectrum... please wait.")
        self.pbar_widget.show()
        segment_list = self.pbar_widget.get_segment_list(self.spc_file.fnsub, segment=97)
        # 基本的情報
        x_minmax1, x_minmax2, added_y_list1, added_y_list2, added_content = self.get_spectrum_linear_subtraction_basic_info(sRS, eRS)
        x_min1_idx, x_max1_idx = np.sort([self.spc_file.get_idx(x_minmax1[0]), self.spc_file.get_idx(x_minmax1[1])])
        master_x_list1, master_y_list1 = self.spc_file.get_data(x_minmax1[0], x_minmax1[1], sub_idx=0)
        umx_h_list = np.empty(self.spc_file.fnsub, dtype=float)
        # イメージ格納庫（全スペクトルの総和としてイメージを作成）
        area_values_list = np.empty(self.spc_file.fnsub, dtype=float)
        selected_RS_diff_list_half = np.absolute(np.diff(self.spc_file.x[x_min1_idx:x_max1_idx + 1])) / 2
        to_subtract_base_value = ((added_y_list1[1:] + added_y_list1[:-1]) * selected_RS_diff_list_half).sum()
        for idx in range(self.spc_file.fnsub):
            master_x_list2, master_y_list2 = self.spc_file.get_data(x_minmax2[0], x_minmax2[1], sub_idx=idx)
            # 最小二乗
            umx_h_value = gf.spectrum_linear_subtraction_core(master_x_list2, master_y_list2, added_y_list2, to_zero)
            umx_h_list[idx] = umx_h_value
            area_values_list[idx] = ((self.spc_file.sub[idx].y[x_min1_idx + 1:x_max1_idx + 1] + self.spc_file.sub[idx].y[x_min1_idx:x_max1_idx]) \
                                        * selected_RS_diff_list_half).sum() + to_subtract_base_value * umx_h_value
            # プログレスバー処理
            if idx in segment_list:
                self.pbar_widget.addValue(1)
        # 追加
        image2d = area_values_list.reshape(self.spc_file.get_shape()).T
        image2D = Image2D(image2d, name="subtracted_%d-%d"%(x_minmax2[0], x_minmax2[1]))
        plot_data_item = pg.PlotDataItem(fillLevel=0, pen=gf.mk_u_pen())
        self.plotItem.vb.addItem(plot_data_item)
        # 描画用データ
        subtraction_data = SubtractionData(
            abs_id = self.abs_id, 
            x_minmax1 = x_minmax1, 
            master_x_list1 = master_x_list1, 
            added_y_list1 = added_y_list1, 
            umx_h_list = umx_h_list
            )
        self.parent.toolbar_layout.add_content(
            image2D, 
            CLASS = "SubtractedSpectrums",
            info={
                "content":"map", 
                "type":"subtracted", 
                "detail":added_content.summary(), 
                "values":[sRS, eRS], 
                "data":subtraction_data
                }, 
            parent_window=self.parent
        )
        # プログレスバー閉じる
        self.abs_id += 1
        self.pbar_widget.is_close_allowed = True
        self.pbar_widget.close()
    # 追加スペクトルが1本のみの場合に適用。指定された波数範囲において元スペクトルから、n倍した追加スペクトルを引き算し、なるべく直線に近づくような引き算をする。
    def spectrum_linear_subtraction(self, sRS, eRS, to_zero):
        # 追加スペクトルの補間版（1はオリジナルと追加の共通部分、2はそれにsRS, eRSの共通部分も含めたもの）
        x_minmax1, x_minmax2, added_y_list1, added_y_list2, added_content = self.get_spectrum_linear_subtraction_basic_info(sRS, eRS)
        # 元データ
        master_x_list1, master_y_list1 = self.spc_file.get_data(x_minmax1[0], x_minmax1[1], sub_idx=0)
        master_x_list2, master_y_list2 = self.spc_file.get_data(x_minmax2[0], x_minmax2[1], sub_idx=0)
        # 最小二乗
        umx_h_value = gf.spectrum_linear_subtraction_core(master_x_list2, master_y_list2, added_y_list2, to_zero)
        # 追加
        plot_data_item = pg.PlotDataItem(master_x_list1, (added_y_list1 * umx_h_value + master_y_list1), fillLevel=0, pen=gf.mk_u_pen())
        self.plotItem.vb.addItem(plot_data_item)
        self.parent.toolbar_layout.add_content(
            plot_data_item, 
            CLASS = "Spectrum",
            info={
                "content":"spectrum", 
                "type":"subtracted", 
                "detail":added_content.summary(), 
                "values":[sRS, eRS], 
                "data":added_content.info["data"]
                }, 
            parent_window=self.parent
        )

        # 以下は、added_spectrumも、x軸方向に平行移動するときのパターン。しかし、誤差は0.002%程度なので、大丈夫かと。
        # # 引き算したあとの関数を直線近似した際の、二乗誤差を求める関数：y軸方向n倍、x軸方向a平行移動
        # def rnorm(params):
        #     n = params[0]
        #     a = params[1]
        #     diff_y_list = master_y_list - n * np.interp(master_x_list, added_x_list + a, added_y_list)
        #     # 直線近似
        #     params, residuals, rank, s = np.linalg.lstsq(np.vstack([(master_x_list), np.ones(len(master_x_list))]).T, diff_y_list, rcond=None)
        #     return(residuals[0])
        # optimized_results = minimize(rnorm, np.array([1, 0]), bounds=((0, None), (None, None)))     # (1, 0): initial guess
        # self.umx_height_matrix = np.array([np.append(-optimized_results.x[0], [1])]) # 係数リスト + オリジナル
        # # 元々のスペクトルとadded_spectrumの共通範囲を取得する
        # x_list = self.vb2.addedItems[0].xData
        # x_min = self.spc_file.x.min()
        # x_max = self.spc_file.x.max()
        # x_min = max([x_min, min(x_list)])
        # x_max = min([x_max, max(x_list)])
        # common_x_region = (x_min <= self.spc_file.x) & (self.spc_file.x <= x_max)
        # self.umx_x_list = self.spc_file.x[common_x_region]
        # # [:, 0]は追加スペクトル、[:, 1]はオリジナル
        # self.umx_y_matrix = np.empty((len(self.umx_x_list), 2), dtype=float, order="F")
        # self.umx_y_matrix[:, 0] = np.interp(self.umx_x_list, added_x_list + optimized_results.x[1], added_y_list)
        # self.umx_y_matrix[:, 1] = self.spc_file.sub[0].y[common_x_region]
        # print(self.umx_height_matrix)
        # print(self.umx_y_matrix)

class MapWidget(pg.GraphicsLayoutWidget):
    def __init__(self, spc_file=None, parent=None):
        self.parent = parent
        self.ContrastConfigurator = my_w.CustomHistogramLUTWidget(grad_rect_size=gf.grad_rect_size)
        super().__init__()
        self.ci.layout.setContentsMargins(gf.map_widget_margin, gf.map_widget_margin, gf.map_widget_margin, gf.map_widget_margin)
        # アスペクト比をあわせる
        self.img_view_box = self.addViewBox(invertY=True)
        self.img_view_box.setBackgroundColor([80, 80, 100])
        self.img_view_box.setAspectLocked(lock=True, ratio=1)
        # 枠
        self.frame = QGraphicsRectItem(0, 0, 1, 1)
        self.frame.setPen(pg.mkPen((50,50,50), width=0))
        self.frame.setBrush(pg.mkBrush(100,100,100,100))
        self.img_view_box.addItem(self.frame)
        # イメージ追加（オブジェクトのみ）
        self.map_img = pg.ImageItem()
        self.img_view_box.addItem(self.map_img)
        # CRR用
        self.crr_img = pg.ImageItem()
        self.img_view_box.addItem(self.crr_img)
        # クロスヘア
        self.h_crosshair = pg.InfiniteLine(pen=gf.mk_c_pen(), angle=0)
        self.v_crosshair = pg.InfiniteLine(pen=gf.mk_c_pen())
        self.h_crosshair.hide()
        self.v_crosshair.hide()
        self.img_view_box.addItem(self.h_crosshair)
        self.img_view_box.addItem(self.v_crosshair)
        # テキスト追加（画像の輝度など）
        self.text_item = pg.TextItem(text="x=0, y=0, value=0")
        self.text_item.setParentItem(self.img_view_box)
        # 初期処理
        if spc_file is not None:
            self.initiate_map_spectrum(spc_file)
        self.scene().sigMouseClicked.connect(self.on_click)
        self.scene().sigMouseMoved.connect(self.on_move)
    # グラフがある場合、親 widget が focus を get できない。
    def focusInEvent(self, event):
        self.parent.focusInEvent(event)
    def focusOutEvent(self, event):
        self.parent.focusOutEvent(event)
    # spc_fileを渡された場合（最初だけ？）
    def initiate_map_spectrum(self, spc_file):
        self.set_crosshair(0, 0)
        if b"map_x" in spc_file.log_dict.keys():
            # 枠追加
            w, h = spc_file.get_shape()
            self.frame.setRect(0, 0, h, w)
            # img 追加（クリックするのに必要）
            pseudo_image2d = np.zeros((h, w))
            self.map_img.setImage(pseudo_image2d)
            self.map_img.hide()
            self.img_view_box.autoRange()
    # Image2D インスタンスを渡された場合
    def display_map(self, image2D):
        # そもそもイメージがまだ無ければ、イメージを追加する
        if not self.parent.toolbar_layout.isImageSet:
            # グラジエント
            self.ContrastConfigurator.setImageItem(self.map_img)
            self.parent.toolbar_layout.insertWidget(0, self.ContrastConfigurator)
            # グラジエント追加しましたよ宣言
            self.parent.toolbar_layout.isImageSet = True
        # 既に追加されているImageItemを変更する形で、画像を表示
        self.map_img.setImage(image2D.image2d)
        # 現在の画像のmax, min
        im_min_val, im_max_val = image2D.getLevels()
        # コントラストFIXであれば、グラジエントはそのまま、mapの方を変更。
        if self.ContrastConfigurator.FIX:
            set_min_val, set_max_val = self.ContrastConfigurator.getLevels()
            # gradientを変更できる範囲は、imのmin, set_minの小さい方から、imのmax, set_maxの大きい方
            self.ContrastConfigurator.item.region.setBounds([min(im_min_val, set_min_val), max(im_max_val, set_max_val)])
            self.map_img.setLevels([set_min_val, set_max_val])
        # unFIXであれば、グラジエントの方の表示をオートスケールで変更
        else:
            # gradientを変更できる範囲は、単純に画像輝度のmax, minに。
            self.ContrastConfigurator.item.region.setBounds([im_min_val, im_max_val])
            self.ContrastConfigurator.setLevels(im_min_val, im_max_val)
        self.map_img.show() # hideされている場合もありえる
        return image2D
    def all_images_were_removed(self):
        self.parent.toolbar_layout.isImageSet = False
        self.parent.toolbar_layout.removeWidget(self.ContrastConfigurator)
        self.ContrastConfigurator.setParent(None)
    def on_click(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()
            # クリックしたときのview boxを取得
            loc_of_QPointF = self.img_view_box.mapSceneToView(event.scenePos())
            map_x, map_y, value = self.get_map_xy_fm_QpointF(loc_of_QPointF)
            if value is not None:
                try:
                    self.parent.spectrum_widget.replace_spectrum(map_x, map_y)
                    self.set_crosshair(map_x, map_y)
                except: pass
    def on_move(self, event):
        loc_of_QPointF = self.img_view_box.mapSceneToView(event)
        map_x, map_y, value = self.get_map_xy_fm_QpointF(loc_of_QPointF)
        # 範囲内にある場合のみ、輝度を取得
        if value is not None:
            self.text_item.setText("x=%d, y=%d, value=%s"%(map_x, map_y, str(value)))
    def get_map_xy_fm_QpointF(self, loc_of_QPointF):
        map_x = int(loc_of_QPointF.x())
        map_y = int(loc_of_QPointF.y())
        cur_image2d = self.get_cur_image2d()
        if (0 <= map_x < cur_image2d.shape[1]) and (0 <= map_y < cur_image2d.shape[0]):
            value = np.round(cur_image2d[map_y, map_x], 3)
            return map_x, map_y, value
        else:
            return None, None, None
    def set_crosshair(self, map_x, map_y):
        self.h_crosshair.setValue(map_y + 0.5)
        self.v_crosshair.setValue(map_x + 0.5)
        self.h_crosshair.show()
        self.v_crosshair.show()
    def get_cur_image2d(self):
        return self.map_img.image.T

class Image2D():
    def __init__(self, image2d, name="none-type"):
        self.image2d = image2d
        self.x, self.y = self.image2d.shape
        self.name = name
    # 指定された範囲を、16 bit画像に変換して保存する
    def save_image(self, base_name="map_image", dir_path=gf.default_last_opened_dir, FIX=False, BIT=None, contrast_range=None): # FIXは、オートスケールのこと
        # 浮動小数点数：ratioを取ることが多いだろうから、補正は何もしない
        if BIT == 32:
            saving_data = Image.fromarray(self.image2d.T.astype(np.float32))
            min_value = 0
            max_value = 0
        else:
            if FIX:
                min_value = contrast_range[0]
                max_value = contrast_range[1]
                Numpy_data = np.copy(self.image2d)
                Numpy_data[Numpy_data < min_value] = min_value
                Numpy_data[Numpy_data > max_value] = max_value
                Numpy_data -= min_value
                Numpy_data *= ((2**BIT - 1) / (max_value - min_value))
            else:
                min_value = self.image2d.min()
                max_value = self.image2d.max()
                Numpy_data = (self.image2d - min_value) / (max_value - min_value) * (2**BIT - 1)
            # 8-bit の場合はそのまま処理してOK, 16-bit の場合は処理が必要
            if BIT == 16:
                saving_data = gf.save_u16_to_tiff(Numpy_data.T.astype(np.uint16))
            elif BIT == 8:
                saving_data = Image.fromarray(Numpy_data.T.astype(np.uint8))
        image_name_wo_ext = "%s_%s_%d-%d"%(base_name, self.name, min_value, max_value)
        saving_data.save(os.path.join(dir_path, "%s.tif"%image_name_wo_ext))
    # 現在の画像を、新たな画像で割る
    def Divide(self, image2D):
        new_name = "div_%s_by_%s"%(self.name, image2D.name)
        new_image2d = self.image2d / image2D.image2d
        return Image2D(new_image2d, name=new_name)

    # infは無視するよ
    def getLevels(self):
        finite_array = self.image2d[np.isfinite(self.image2d)]
        return np.min(finite_array), np.max(finite_array)

# popup用の簡易版
class SimpleMapWidget(MapWidget):
    def __init__(self, spc_file=None, parent=None):
        super().__init__(spc_file=spc_file, parent=parent)

class SimpleToolbarLayout(QVBoxLayout):
    def __init__(self, parent=None):
        super().__init__()
        self.isImageSet = False





# objects = self.findChildren(QtCore.QObject)
