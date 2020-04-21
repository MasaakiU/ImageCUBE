# -*- Coding: utf-8 -*-

import os
import spc
import numpy as np
import functools
import pickle
import re
from scipy.optimize import nnls, curve_fit

from PyQt5.QtWidgets import (
    QVBoxLayout, 
    QFileDialog, 
    QWidget, 
    QCheckBox, 
    QLabel, 
    QHBoxLayout, 
    QComboBox, 
    QDoubleSpinBox, 
    QPushButton, 
    )
from PyQt5.QtCore import (
    QSize, 
    QRect, 
    QLineF, 
    Qt, 
    QCoreApplication, 
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
        # draw:     v_line/range/func
        # "data":   RS/[RS1, RS2]/[RS1, RS2, func]   (correspond with "draw")
        # }
        self.parent_window = parent_window
        self.focused = False
    def format_data(self):
        if self.info["draw"] == "v_line":
            return "({0[0]})".format(self.info["data"])
        elif self.info["draw"] == "range":
            return "({0[0]}-{0[1]})".format(self.info["data"])
        elif self.info["draw"] == "func":
            return "({0[0]}-{0[1]}, {1})".format(self.info["data"], self.info["data"][2].format_data())
        elif self.info["draw"] == "static":
            return "{0}".format(self.info["data"])
        elif self.info["draw"] == "master":
            return ""
        elif self.info["draw"] == "spc_overlay":
            return ""
        elif self.info["draw"] == "none":
            return ""
        else:
            raise Exception("unknown draw type")
    def content_type(self):
        return "{0} {1}".format(self.info["type"], self.info["content"])
    def info_to_display(self):
        return " {0}\t{1} {2}".format(self.content_type(), self.format_data(), self.info["detail"])
    def get_save_path(self, ext, ask):
        save_path = "{0}_{1}{2}{3}".format(
            os.path.join(self.parent_window.dir_path, self.parent_window.file_name_wo_ext), 
            self.info["type"], self.format_data(), 
            ext
        )
        # 保存先：ボタンについてる名前がデフォルトのファイル名になる
        N = 0
        root, ext = os.path.splitext(save_path)
        while os.path.exists(save_path):
            N += 1
            save_path = "{0}_{1}{2}".format(root, N, ext)
        if ask:
            save_path, file_type = QFileDialog.getSaveFileName(self.parent_window, 'save as {0} file'.format(ext), os.path.splitext(save_path)[0], filter="unmix method files (*{0})".format(ext))
        else:
            pass
        return save_path
    # widgets は作っても消されるので、自作できるようにしとく
    def init_widgets(self):
        return []
    def summary(self):
        return "{0} {1} {2}".format(self.content_type(), self.format_data(), self.info["detail"])
class AddedContent_Spectrum(AddedContent):
    def __init__(self, item, info=None, parent_window=None):
        super().__init__(item, info, parent_window)
        # オリジナルスペクトルの場合は、消す行為は許されない
    def focus_unfocus(self, focused):
        self.focused = focused
        if self.focused:
            brush_color = self.item.opts["pen"].color()
            brush_color.setAlpha(gf.brushAlpha)
        else:
            brush_color = None
        self.item.setBrush(brush_color)
    def hide_show_item(self):
        self.item.setVisible(not self.item.isVisible())
    def remove_item(self):
        self.parent_window.toolbar_layout.added_content_spectrum_list.remove(self)
        self.parent_window.spectrum_widget.vb2.removeItem(self.item)
    def export_spectrum(self, ext, ask=None):
        # パス処理
        save_path = self.get_save_path(ext, ask)
        if save_path == "":
            return
        # spc_like 作成
        spc_like = gf.SpcLike()
        spc_like.init_fmt(self.parent_window.spectrum_widget.spc_file)
        spc_like.add_xData(self.item.xData)
        # sub_like 作成
        sub_like = gf.SubLike()
        sub_like.init_fmt(self.parent_window.spectrum_widget.spc_file.sub[0])
        sub_like.add_data(self.item.yData, sub_idx=0)
        # 追加
        spc_like.add_subLike(sub_like)
        # 保存！
        if ext == ".spc":
            spc_like.save_as_spc(save_path=save_path)
        elif ext == ".txt":
            spc_like.save_as_txt(save_path=save_path)
        else:
            raise Exception("unknown extension")
class AddedContent_POI(AddedContent_Spectrum):
    def __init__(self, item, info=None, parent_window=None):
        super().__init__(item, info, parent_window)
    def focus_unfocus(self, focused):
        self.focused = focused
class AddedContent_Map(AddedContent):
    def __init__(self, item, info, parent_window):
        super().__init__(item, info, parent_window)
        self.info["spectrum_hidden"] = False
    def focus_unfocus(self, focused):
        self.focused = focused
        if self.focused:
            self.parent_window.cur_displayed_map_content = self
            self.parent_window.map_widget.display_map(self.item)
            self.parent_window.spectrum_widget.display_map_spectrum()
            if self.info["spectrum_hidden"]:
                self.parent_window.spectrum_widget.hide_all_fill_btwn_items()
                self.parent_window.spectrum_widget.hide_all_lines()
        else:
            self.parent_window.map_widget.map_img.hide()
            self.parent_window.cur_displayed_map_content = None
            self.parent_window.spectrum_widget.hide_all_fill_btwn_items()
            self.parent_window.spectrum_widget.hide_all_lines()
    def hide_show_item(self):
        if self.info["draw"] == "v_line":
            isVisible = self.parent_window.spectrum_widget.additional_lines[0].isVisible()
            object_name = "lines"
        elif self.info["draw"] == "range":
            isVisible = self.parent_window.spectrum_widget.additional_fill_btwn_items[0].isVisible()
            object_name = "fill_btwn_items"
        else:
            print(self.info["draw"])
            raise Exception("no attrib")
        if isVisible:
            exe = "hide"
            self.info["spectrum_hidden"] = True
        else:
            exe = "show"
            self.info["spectrum_hidden"] = False
        function = getattr(self.parent_window.spectrum_widget, "%s_all_%s"%(exe, object_name))
        function()
    def remove_item(self):
        self.parent_window.toolbar_layout.added_content_map_list.remove(self)
        self.parent_window.map_widget.map_img.hide()
        self.parent_window.cur_displayed_map_content = None
        self.parent_window.spectrum_widget.set_N_additional_lines(0)
        self.parent_window.spectrum_widget.set_N_additional_fill_btwn_items(0)
        return None
class AddedContent_Unmixed(AddedContent_Map):
    def __init__(self, item, info, parent_window):
        super().__init__(item, info, parent_window)
    def hide_show_item(self):
        standard_type = self.info["data"][2].standard_type
        if standard_type == "bd":
            idx = -2
        elif standard_type == "ts":
            idx = -1
        else:
            idx = int(standard_type) - 1
        line_item = self.parent_window.spectrum_widget.additional_lines[idx]
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
        abs_id = self.info["data"][2].abs_id
        idxes_to_remove = []
        for idx, added_content in enumerate(self.parent_window.toolbar_layout.added_content_map_list):
            if added_content.info["type"] != "unmixed":
                continue
            if added_content.info["data"][2].abs_id == abs_id:
                idxes_to_remove.append(idx)
        for idx in idxes_to_remove[::-1]:
            del self.parent_window.toolbar_layout.added_content_map_list[idx]
        self.parent_window.map_widget.map_img.hide()
        self.parent_window.cur_displayed_map_content = None
        self.parent_window.spectrum_widget.set_N_additional_lines(0)
        self.parent_window.spectrum_widget.set_N_additional_fill_btwn_items(0)
        return idxes_to_remove
class AddedContent_Unmixed_s(AddedContent_Spectrum):
    def __init__(self, item, info, parent_window):
        super().__init__(item, info, parent_window)
    def hide_show_item(self):
        # 何故か少しだけ view がズレるので、調整
        view_range = self.parent_window.spectrum_widget.viewRange()
        # 関連スペクトルを、現在のもの以外全て隠す。
        abs_id = self.info["data"][2].abs_id
        isVisible = self.item.opts["fillBrush"].color().getRgbF()[:3] != (0.0, 0.0, 0.0)
        for added_content in self.parent_window.toolbar_layout.added_content_spectrum_list:
            if added_content.info["type"] != "unmixed":
                continue
            if added_content.info["data"][2].abs_id == abs_id:
                added_content.item.setVisible(not isVisible)
            if added_content.info["detail"] == "baseline_drift":
                added_content.item.setVisible(True)
        # fill の設定
        if isVisible:
            brush_color = None
        else:
            brush_color = self.item.opts["pen"].color()
            brush_color.setAlpha(gf.brushAlpha)
        self.item.setBrush(pg.mkBrush(brush_color))
        self.item.setVisible(True)
        self.parent_window.spectrum_widget.setXRange(*view_range[0], padding=0)
        self.parent_window.spectrum_widget.setYRange(*view_range[1], padding=0)
    def remove_item(self):
        abs_id = self.info["data"][2].abs_id
        idxes_to_remove = []
        for idx, added_content in enumerate(self.parent_window.toolbar_layout.added_content_spectrum_list):
            if added_content.info["type"] != "unmixed":
                continue
            if added_content.info["data"][2].abs_id == abs_id:
                idxes_to_remove.append(idx)
        for idx in idxes_to_remove[::-1]:
            added_content = self.parent_window.toolbar_layout.added_content_spectrum_list.pop(idx)
            for item in added_content.item.all_items():
                self.parent_window.spectrum_widget.plotItem.vb.removeItem(item)
            del added_content
        return idxes_to_remove
    def focus_unfocus(self, focused):
        # フォーカスで、関連スペクトルを 全て隠す or 表示する
        abs_id = self.info["data"][2].abs_id
        for added_content in self.parent_window.toolbar_layout.added_content_spectrum_list:
            if added_content.info["type"] != "unmixed":
                continue
            if added_content.info["data"][2].abs_id == abs_id:
                added_content.item.setVisible(focused)
        super().focus_unfocus(focused)
    def export_spectrum(self, ext, ask=None):   # ext: ".spc", ".txt", ".info"
        # パス処理
        save_path = self.get_save_path(ext, ask)
        print(save_path)
        if save_path == "":
            return
        # spc_like 作成
        xData, yData = self.info["data"][2].get_no_bd_data(sub_idx=0, original_spc_file=None)
        spc_like = gf.SpcLike()
        spc_like.init_fmt(self.parent_window.spectrum_widget.spc_file)
        spc_like.add_xData(xData)
        # sub_like 作成
        sub_like = gf.SubLike()
        sub_like.init_fmt(self.parent_window.spectrum_widget.spc_file.sub[0])
        sub_like.add_data(yData, sub_idx=0)
        # 追加
        spc_like.add_subLike(sub_like)
        # 保存！
        if ext == ".spc":
            spc_like.save_as_spc(save_path=save_path)
        elif ext == ".txt":
            spc_like.save_as_txt(save_path=save_path)
        else:
            raise Exception("unknown extension")
    def export_information(self, ext, ask=None, **kwargs):   # ext: ".spc", ".txt", ".info"
        standard_info_list = kwargs["standard_info_list"]
        path_name_func = kwargs["path_name_func"]
        # パス処理
        save_path = self.get_save_path(ext, ask)
        if save_path == "":
            return
        save_path = path_name_func(save_path)
        print(save_path)
        # データ書き込み
        unmixed_data = self.info["data"][2]
        index_list = []
        txt = "# umx_data\n"
        txt += "# standard_type standard_info\n"
        for idx, standard_info in enumerate(standard_info_list):
            txt += "'standard_{0}' '{1}'\n".format(idx, standard_info)
            index_list.append("standard_{0}".format(idx))
        else:
            txt += "'{0}' '{1}'\n".format("intercept(-)", "system_default")
            txt += "'{0}' '{1}'\n".format("baseline_drift_1", "system_default")
            txt += "'{0}' '{1}'\n".format("baseline_drift_2", "system_default")
            index_list.extend(['intercept(-)', 'baseline_drift_1', 'baseline_drift_2'])
        txt_h = "# standard_type height_values\n"
        txt_x = "# x_values\n{0}\n".format(" ".join(map(str, unmixed_data.umx_x_list)))
        txt_y = "# standard_type[1] y_values\n"
        for idx, umx_h_list, umx_y_list in zip(index_list, unmixed_data.umx_h_matrix.T, unmixed_data.umx_y_matrix.T):
            txt_h += "'{0}' {1}\n".format(idx, " ".join(map(str, umx_h_list)))
            txt_y += "'{0}' {1}\n".format(idx, " ".join(map(str, umx_y_list)))
        txt += txt_h + "\n" + txt_x + "\n" + txt_y
        with open(save_path, "w") as f:
            f.write(txt)
class AddedContent_SubtractedSpectrums(AddedContent_Map):
    def __init__(self, item, info=None, parent_window=None):
        super().__init__(item, info, parent_window)
    def hide_show_item(self):
        isVisible = self.parent_window.spectrum_widget.additional_fill_btwn_items[0].isVisible()
        if isVisible:
            exe = "hide"
        else:
            exe = "show"
        self.info["spectrum_hidden"] = isVisible
        function = getattr(self.parent_window.spectrum_widget, "%s_all_fill_btwn_items"%exe)
        function()
    def export_spectrum(self, ext, ask=None):
        # パス処理
        save_path = self.get_save_path(ext, ask)
        if save_path == "":
            return
        # spc_like 作成
        added_y_list1 = self.info["data"][2].added_y_list1
        master_x_list1 = self.info["data"][2].master_x_list1
        ones_x_list = np.ones_like(master_x_list1)
        spc_like = gf.SpcLike()
        spc_like.init_fmt(self.parent_window.spectrum_widget.spc_file)
        spc_like.add_xData(master_x_list1)
        for sub_idx, sub_h_list in enumerate(self.info["data"][2].sub_h_set):
            # subフィアル作成
            sub_like = gf.SubLike()
            sub_like.init_fmt(self.parent_window.spectrum_widget.spc_file.sub[sub_idx])
            sub_like.add_data(
                self.parent_window.spectrum_widget.spc_file.sub[sub_idx].y 
                - (added_y_list1 * sub_h_list[0] + master_x_list1 * sub_h_list[1] + ones_x_list * sub_h_list[2]), 
                sub_idx=sub_idx
            )
            # 追加
            spc_like.add_subLike(sub_like)
        # Size 以外の PreProcesses を除去（既に処理されているものが保存されるため）
        for func_name, kwargs in spc_like.log_dict[b"prep_order"]:
            if func_name == "set_size":
                pass
            elif func_name == "CRR_master":
                spc_like.delete_from_object(master_key="CRR", key_list=["cosmic_ray_locs", "cosmic_ray_removal_params"])
            elif func_name == "NR_master":
                spc_like.delete_from_object(master_key="NR", key_list=["noise_reduction_params"])
            else:
                print(func_name)
                raise Exception("unknown preprocesses")
        spc_like.update_object(master_key="PreP", key_list=["prep_order"], data_list=[[["set_size", {'size':None,'mode':'init'}]]])
        # 保存！
        if ext == ".spc":
            spc_like.save_as_spc(save_path=save_path)
        else:
            raise Exception("unknown extension")
class AddedContent_PreP(AddedContent):
    def __init__(self, item, info=None, parent_window=None):
        super().__init__(item, info, parent_window)
    def focus_unfocus(self, focused):
        pass
    def remove_item(self):
        self.parent_window.toolbar_layout.added_content_preprocess_list.remove(self)
        self.parent_window.map_widget.overlay_img.hide()
        self.parent_window.cur_overlayed_map_content = None
        self.parent_window.spectrum_widget.set_N_overlayed_lines(0)
        self.parent_window.spectrum_widget.set_N_overlayed_fill_btwn_items(0)
        return None
class AddedContent_Size(AddedContent_PreP):
    def __init__(self, item, info=None, parent_window=None):
        super().__init__(item, info, parent_window)
        self.two_products_list = ["{0}(x) x {1}(y)".format(product_x, product_y) for product_x, product_y in zip(*self.info["data"])]
        self.cur_idx = 0
        self.updated_manually = True
        self.init_widgets()
    def init_widgets(self):
        self.cmbox = QComboBox()
        self.cmbox.addItems(self.two_products_list)
        self.cmbox.setCurrentIndex(self.cur_idx)
        self.cmbox.currentIndexChanged.connect(self.cmbox_selection_changed)
        return [self.cmbox]
    def cmbox_selection_changed(self, event):
        if self.updated_manually:
            product_x = self.info["data"][0][event]
            product_y = self.info["data"][1][event]
            self.parent_window.toolbar_layout.set_size(size=[product_x, product_y, 1])
    def set_item_fm_size(self, product_x, product_y):
        self.updated_manually = False
        self.cur_idx = self.cmbox.findText("{0}(x) x {1}(y)".format(product_x, product_y))
        self.cmbox.setCurrentIndex(self.cur_idx)
        self.updated_manually = True
class AddedContent_CRR(AddedContent_PreP):
    def __init__(self, item, info=None, parent_window=None):
        super().__init__(item, info, parent_window)
    def hide_show_item(self, show=None):
        # map
        if show is not None:
            if show:
                self.parent_window.map_widget.overlay_img.setImage(self.item.image())
            isVisible = not show
        else:
            isVisible = self.parent_window.map_widget.overlay_img.isVisible()
        if not isVisible:
            self.parent_window.cur_overlayed_map_content = self
        else:
            pass
        # map, spectrum の表示非表示
        self.parent_window.map_widget.overlay_img.setVisible(not isVisible)
        for line in self.parent_window.spectrum_widget.overlayed_lines:
            line.setVisible(not isVisible)
    def remove_item(self, mode=None):
        log = self.parent_window.toolbar_layout.CRR_master(mode=mode)
        if log == "not executed":
            return log
        self.parent_window.toolbar_layout.added_content_preprocess_list.remove(self)
        if mode == "just revert":
            self.parent_window.map_widget.overlay_img.hide()
            self.parent_window.cur_overlayed_map_content = None
            self.parent_window.spectrum_widget.set_N_overlayed_lines(0)
            self.parent_window.spectrum_widget.set_N_overlayed_fill_btwn_items(0)
class AddedContent_NR(AddedContent_PreP):
    def __init__(self, item, info=None, parent_window=None):
        super().__init__(item, info, parent_window)
    def remove_item(self, mode=None):
        self.parent_window.toolbar_layout.added_content_preprocess_list.remove(self)
        log = self.parent_window.toolbar_layout.NR_master(mode=mode)
        if log == "not executed":
            return log
    def hide_show_item(self, show=None):
        pass
class AddedContent_SCL(AddedContent_PreP):
    def __init__(self, item, info=None, parent_window=None):
        super().__init__(item, info, parent_window)
        self.init_widgets()
    def init_widgets(self):
        # 調整 widget
        self.scl_label = QLabel("   scaling: ")
        self.wid_label = QLabel("   g-width: ")
        self.scl_var = QDoubleSpinBox()
        self.scl_var.setDecimals(4)
        self.scl_var.setSingleStep(0.1)
        self.scl_var.setKeyboardTracking(False) # the spinbox doesn't emit the valueChanged() signal while typing
        self.scl_var.setMinimum(0.5)
        self.scl_var.setMaximum(1.5)
        self.scl_var.setValue(self.parent_window.spectrum_widget.spc_file.scaling)
        self.wid_var = QDoubleSpinBox()
        self.wid_var.setDecimals(1)
        self.wid_var.setSingleStep(1)
        self.wid_var.setKeyboardTracking(False) # the spinbox doesn't emit the valueChanged() signal while typing
        self.wid_var.setMinimum(0.1)
        self.wid_var.setMaximum(100)
        self.wid_var.setValue(self.parent_window.spectrum_widget.spc_file.g_width)
        # イベントコネクト
        self.scl_var.valueChanged.connect(self.scl_var_changed)
        self.wid_var.valueChanged.connect(self.wid_var_changed)
        return [self.scl_label, self.scl_var, self.wid_label, self.wid_var]
    def remove_item(self, mode=None):
        log = self.parent_window.toolbar_layout.SCL_master(ask=True, mode=mode)
        if log == "not executed":
            return log
    def hide_show_item(self, show=None):
        if show is not None:
            isVisible = not show
        else:
            isVisible = self.parent_window.spectrum_widget.overlayed_lines[0].isVisible()
        if not isVisible:
            self.parent_window.cur_overlayed_spc_info = self.info
            self.parent_window.spectrum_widget.display_spectrum()
        # スペクトルの表示
        for line in self.parent_window.spectrum_widget.overlayed_lines:
            line.setVisible(not isVisible)
    def scl_var_changed(self, event):
        self.parent_window.spectrum_widget.spc_file.scl_changed(scl=event, wid=None)
        self.parent_window.spectrum_widget.display_spectrum()   # overlay spectrum の更新
        self.parent_window.spectrum_widget.update_spectrum()    # master spectrum の更新
    def wid_var_changed(self, event):
        self.parent_window.spectrum_widget.spc_file.scl_changed(scl=None, wid=event)
        self.parent_window.spectrum_widget.update_spectrum()
class AddedContent_Range(AddedContent_PreP):
    def __init__(self, item, info=None, parent_window=None):
        super().__init__(item, info, parent_window)
        self.updated_via_spbx = True
        self.updated_via_item = True
        self.init_widgets()
    def init_widgets(self):
        self.range_l = QDoubleSpinBox()
        self.range_l.setMinimum(-65535)
        self.range_l.setMaximum(65535)
        self.range_l.valueChanged.connect(self.spbx_value_changed)
        self.range_l.setValue(self.info["data"][0])
        self.range_r = QDoubleSpinBox()
        self.range_r.setMinimum(-65535)
        self.range_r.setMaximum(65535)
        self.range_r.valueChanged.connect(self.spbx_value_changed)
        self.range_r.setValue(self.info["data"][1])
        self.item.setBounds([-65535, 65535])
        self.item.sigRegionChanged.connect(self.item_region_changed)
        self.btn_unset = QPushButton("unset")
        self.btn_unset.clicked.connect(self.btn_unset_clicked)
        return [QLabel("left:"), self.range_l, QLabel("right:"), self.range_r, QLabel(" "), self.btn_unset]
    def spbx_value_changed(self, event):
        if self.updated_via_spbx:
            self.updated_via_item = False
            values = [self.range_l.value(), self.range_r.value()]
            self.item.setRegion(values)
            self.updated_via_item = True
            self.info["data"][:] = values
            self.set_range_label_in_toolbar(values)
    def item_region_changed(self, item):
        if self.updated_via_item:
            self.updated_via_spbx = False
            values = np.sort([item.lines[i].value() for i in [0, 1]])
            self.range_l.setValue(values[0])
            self.range_r.setValue(values[1])
            self.item.setVisible(True)
            self.updated_via_spbx = True
            # data 更新
            self.info["data"][:] = list(values)
            self.set_range_label_in_toolbar(values)
    def btn_unset_clicked(self, event):
        self.item.setVisible(False)
        self.item.setRegion([0, 0])
    def set_range_label_in_toolbar(self, values):
        self.parent_window.toolbar_layout.range_left.setText(str(values[0]))
        self.parent_window.toolbar_layout.range_right.setText(str(values[1]))
# class containing information about spectrum unmixing
class UnmixedData():
    def __init__(self, abs_id, standard_type, umx_x_list, umx_y_matrix, umx_h_matrix):
        self.abs_id = abs_id
        self.standard_type = standard_type   # std(1スタートのindex), "bd", or "ts" (baseline drift, total signal)
        self.umx_x_list = umx_x_list        # umx_x_list.shape = (,n_data_points)
        self.umx_y_matrix = umx_y_matrix    # umx_y_matrix.shape = (n_data_points, n_spectrum + 1)  ※ bdがプラスマイナスで重複しているため
        self.umx_h_matrix = umx_h_matrix    # umx_h_matrix.shape = (fnsub, n_spectrum + 1)          ※ bdがプラスマイナスで重複しているため
    def N_lines(self):
        return self.umx_y_matrix.shape[1] - 1 # ts, bd
    def N_ranges(self):
        return 1
    def format_data(self):
        return "#{0}".format(self.standard_type)
    def get_y_data_matrix(self, sub_idx):
        y_matrix = self.umx_y_matrix * self.umx_h_matrix[sub_idx]
        bd_matrix = y_matrix[:, -3:].sum(axis=1, keepdims=True)
        y_data_matrix = np.empty((len(self.umx_x_list), self.N_lines()), dtype=float)
        y_data_matrix[:, :-2] = y_matrix[:, :-3] + bd_matrix
        y_data_matrix[:, -2]  = bd_matrix[:, 0]
        y_data_matrix[:, -1]  = y_matrix.sum(axis=1)    # ts
        return y_data_matrix
    def get_line_data_list(self, sub_idx, original_spc_file=None):
        return [(self.umx_x_list, y_data) for y_data in self.get_y_data_matrix(sub_idx).T]
    def get_region_data_list(self, sub_idx, original_spc_file=None):
        y_matrix = self.umx_y_matrix * self.umx_h_matrix[sub_idx]
        if self.standard_type in ("bd", "ts"):
            btm_line = pg.PlotDataItem(self.umx_x_list[[0, -1]], [0, 0], fillLevel=0, pen=gf.mk_u_pen())
        else:
            btm_line = pg.PlotDataItem(self.umx_x_list[[0, -1]], y_matrix[[0, -1], -3:].sum(axis=1), fillLevel=0, pen=gf.mk_u_pen())
        if self.standard_type == "bd":
            top_line = pg.PlotDataItem(self.umx_x_list, y_matrix[:, -3:].sum(axis=1), fillLevel=0, pen=gf.mk_u_pen())
        elif self.standard_type == "ts":
            top_line = pg.PlotDataItem(self.umx_x_list, y_matrix.sum(axis=1), fillLevel=0, pen=gf.mk_u_pen())
        else:
            top_line = pg.PlotDataItem(self.umx_x_list, y_matrix[:, [int(self.standard_type)-1, -3, -2, -1]].sum(axis=1), fillLevel=0, pen=gf.mk_u_pen())
        return [(btm_line, top_line)]
    # baseline_drift を上乗せしない、そのままのデータ
    def get_no_bd_data(self, sub_idx, original_spc_file=None):
        region_data = self.get_region_data_list(sub_idx=0, original_spc_file=None)[0]
        # np.interp(x, xp, fp) must be increasing
        xData_btm = region_data[0].xData
        xData_top = region_data[1].xData
        yData_btm = region_data[0].yData
        if (xData_btm[-1] - xData_btm[0]) < 0:
            xData_btm = xData_btm[::-1]
            yData_btm = yData_btm[::-1]
        yData_sub = region_data[1].yData - np.interp(xData_top, xData_btm, yData_btm)
        return xData_top, yData_sub
class SubtractionData():
    def __init__(self, x_minmax1, master_x_list1, added_y_list1, sub_h_set, to_zero):
        self.x_minmax1 = x_minmax1
        self.master_x_list1 = master_x_list1
        self.added_y_list1 = added_y_list1
        self.sub_h_set = sub_h_set        # shape(spc_file.fnxub, 3)
        self.to_zero = to_zero
    def N_lines(self):
        return 1
    def N_ranges(self):
        return 1
    def format_data(self):
        return "to_horizontal" if self.to_zero else "to_angled"
    def get_line_data_list(self, sub_idx, original_spc_file):
        return [self.get_data(sub_idx, original_spc_file)]
    def get_region_data_list(self, sub_idx, original_spc_file):
        btm_line = pg.PlotDataItem(self.master_x_list1[[0, -1]], [0, 0])
        top_line = pg.PlotDataItem(*self.get_line_data_list(sub_idx, original_spc_file)[0])
        return [(btm_line, top_line)]
    def get_data(self, sub_idx, original_spc_file):
        original_x_data, original_y_data = original_spc_file.get_data(*self.x_minmax1, sub_idx=sub_idx)
        subtracted_y_list = original_y_data - (
            self.added_y_list1 * self.sub_h_set[sub_idx, 0] + 
            original_x_data * self.sub_h_set[sub_idx, 1] + 
            np.ones_like(original_x_data) * self.sub_h_set[sub_idx, 2]
        )
        return self.master_x_list1, subtracted_y_list
class CRR_Data():
    def __init__(self):
        pass
    def N_lines(self, sub_idx):
        return 1
    def N_ranges(self, sub_idx):
        return 0
    def format_data(self):
        return ""
    def get_line_data_list(self, sub_idx, original_spc_file):
        # CRRされたスペクトル
        cosmic_ray_locs = original_spc_file.log_dict.get(b"cosmic_ray_locs", [])
        if sub_idx not in cosmic_ray_locs:
            return [([], [], {"connect":[]})]
        selected_se_idx_set, TopBottomLeftRight_idxes, original_data_set = cosmic_ray_locs[sub_idx]
        crr_x_list = np.empty(0, dtype=float)
        crr_y_list = np.empty(0, dtype=float)
        crr_connection = np.empty(0, dtype=float)
        for (s_idx, e_idx), original_data in zip(selected_se_idx_set, original_data_set):
            # 両サイドに広げる
            if 0 <= s_idx-1:
                try:
                    crr_x_list = np.hstack((crr_x_list, original_spc_file.x[s_idx-1:e_idx+2]))
                    crr_y_list = np.hstack((crr_y_list, original_spc_file.sub[sub_idx].y[s_idx-1], original_data, original_spc_file.sub[sub_idx].y[e_idx+1]))
                    crr_connection = np.hstack((crr_connection, [True]*(e_idx - s_idx + 2) + [False]))
                # end 側が飛び出ている場合をケア
                except:
                    crr_x_list = np.hstack((crr_x_list, original_spc_file.x[s_idx-1:e_idx+1]))
                    crr_y_list = np.hstack((crr_y_list, original_spc_file.sub[sub_idx].y[s_idx-1], original_data))
                    crr_connection = np.hstack((crr_connection, [True]*(e_idx - s_idx + 1) + [False]))
            # start 側が飛びてている場合をケア
            else:
                crr_x_list = np.hstack((crr_x_list, original_spc_file.x[s_idx:e_idx+2]))
                crr_y_list = np.hstack((crr_y_list, original_data, original_spc_file.sub[sub_idx].y[e_idx+1]))
                crr_connection = np.hstack((crr_connection, [True]*(e_idx - s_idx + 1) + [False]))
        return [(crr_x_list, crr_y_list, {"connect":crr_connection})]
    def get_region_data_list(self, sub_idx, original_spc_file):
        return []
class SCL_Data():
    def __init__(self):
        pass
    def N_lines(self, sub_idx):
        return 1
    def N_ranges(self, sub_idx):
        return 0
    def format_data(self):
        return ""
    def get_line_data_list(self, sub_idx, original_spc_file):
        intn_list = original_spc_file.get_sub_activity(sub_idx)
        freq_list = original_spc_file.get_sub_freq_list(sub_idx, scaling=True)
        connect = np.concatenate((np.ones_like(freq_list, dtype=int), np.zeros_like(freq_list, dtype=int))).reshape(2, -1).T.reshape(-1)
        freq_list = np.concatenate((freq_list, freq_list)).reshape(2, -1).T.reshape(-1)
        intn_list = np.concatenate((intn_list, np.zeros_like(intn_list))).reshape(2, -1).T.reshape(-1)
        return [(freq_list, intn_list, {"connect":connect})]
    def get_region_data_list(self, sub_idx, original_spc_file):
        return []
# POI_manager 用
class POI_Info():
    def __init__(self, poi_key, poi_data, parent_window):
        self.poi_key = poi_key
        self.poi_data = poi_data
        self.focused = False
        self.allow_loc_update = True
        self.parent_window = parent_window
    def focus_unfocus(self, focused):
        self.focused = focused
        if focused & self.allow_loc_update:
            # スペクトル更新
            self.parent_window.toolbar_layout.set_spectrum_and_crosshair(*self.poi_data)

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
        # 元のイメージと interactive に作用する GUIを、予め作成しとく
        self.poi_settings_popup = popups.PoiSettingsPopup(parent=self.parent, initial_values=(0,0), labels=("x position", "y position"), title="set point of interest", poi_key="poi1")
        self.poi_popup_connected = False    # まだ self.parent.map_widget 存在していないので、cfp_settings_popup を表示する段でコネクトする
        # レイアウト準備
        map_layout = QVBoxLayout()
        spectrum_layout = QVBoxLayout()
        info_layout = QVBoxLayout()
        # 追加された画像・スペクトルはここへ
        self.added_content_map_list = []
        self.added_content_spectrum_list = []
        self.added_content_preprocess_list = []
        self.added_info_poi_list = []
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
            # 現在のスペクトルを追加
            btnAddCurrent = my_w.CustomPicButton("add_cur_spec1.svg", "add_cur_spec2.svg", "add_cur_spec3.svg", base_path=gf.icon_path)
            btnAddCurrent.clicked.connect(self.add_current_spectrum)
            btnAddCurrent.setToolTip("add current spectrum")
            # # 細胞が無いエリアを設定（unmixで使う）
            # btnSetCFP = my_w.CustomPicButton("cfp1.svg", "cfp2.svg", "cfp3.svg", base_path=gf.icon_path)
            # btnSetCFP.clicked.connect(self.set_CellFreePosition)
            # btnSetCFP.setToolTip("set cell free position (x, y) in a map image")
            # 全てのmapの保存
            btnSaveAllMaps = my_w.CustomPicButton("save_map1.svg", "save_map2.svg", "save_map3.svg", base_path=gf.icon_path)
            btnSaveAllMaps.clicked.connect(self.save_all_maps)
            btnSaveAllMaps.setToolTip("save all map images in current contrast\n(for unmixed map images, unmixed spectrums will also be saved)")
            # ターゲット保存
            btnSaveTarget = my_w.CustomPicButton("save_target1.svg", "save_target2.svg", "save_target3.svg", base_path=gf.icon_path)
            btnSaveTarget.clicked.connect(self.save_target)
            btnSaveTarget.setToolTip("save target (crosshair)")
            # Point of interest 表示
            btnPOI = my_w.CustomPicButton("poi1.svg", "poi2.svg", "poi3.svg", base_path=gf.icon_path)
            btnPOI.clicked.connect(self.parent.parent.open_poi_manager)
            btnPOI.setToolTip("points of interest (POI) manager")
            # レイアウト
            # map_layout.addWidget(btnSetCFP)
            map_layout.addWidget(btnSignalIntensity)
            map_layout.addWidget(btnSignalToBaseline)
            map_layout.addWidget(btnSignalToHBaseline)
            map_layout.addWidget(btnSignalToAxis)
            # map_layout.addWidget(btnCurveFitting)
            # map_layout.addWidget(btnImageCalculator)
            map_layout.addWidget(btnSaveAllMaps)
            map_layout.addWidget(btnSaveTarget)
            map_layout.addItem(my_w.CustomSpacer())
            map_layout.addWidget(my_w.CustomSeparator())  # スペーサー
            map_layout.addItem(my_w.CustomSpacer())       # スペーサー
            spectrum_layout.addWidget(btnAddCurrent)
            info_layout.addWidget(btnPOI)
        # spectrum windowだけで出てくるボタンたち
        elif window_type == "s":
            pass
        # unmix method作成画面ででてくるボタンたち
        if window_type == "u":
            # バックグラウンド追加ボタン
            btnIncludePOI = my_w.CustomPicButton("poi1.svg", "poi2.svg", "poi3.svg", base_path=gf.icon_path)
            btnIncludePOI.clicked.connect(self.include_POI)
            btnIncludePOI.setToolTip("include/exclude spectra from stored Position Of Interest")
            # # レンジ設定ボタン
            btnSetRange = my_w.CustomSmallButton("range")
            btnSetRange.clicked.connect(functools.partial(self.set_range, mode="fmToolB"))
            btnSetRange.setToolTip("range setting")
            # レンジdisplay
            self.range_left = my_w.CustomSmallLabel("none")
            self.range_right = my_w.CustomSmallLabel("none")
            # メソッドexportボタン
            btnExportMethod = my_w.CustomPicButton("export_umx1.svg", "export_umx2.svg", "export_umx3.svg", base_path=gf.icon_path)
            btnExportMethod.clicked.connect(self.export_procedures)
            btnExportMethod.setToolTip("export method")
            # レイアウト
            spectrum_layout.addWidget(btnIncludePOI)
            spectrum_layout.addWidget(btnSetRange)
            spectrum_layout.addWidget(self.range_left)
            spectrum_layout.addWidget(self.range_right)
            spectrum_layout.addWidget(btnExportMethod)
        # アンミキシング window 以外で表示される者たち
        else:
            # スペクトルの引き算
            btnSpectrumLinearSubtraction = my_w.CustomPicButton("spct_calc1.svg", "spct_calc2.svg", "spct_calc3.svg", base_path=gf.icon_path)
            btnSpectrumLinearSubtraction.clicked.connect(self.execute_spectrum_linear_subtraction)
            btnSpectrumLinearSubtraction.setToolTip("linear subtraction of spectrum")
            # アンミックスボタン
            btnUnmixing = my_w.CustomPicButton("unmix1.svg", "unmix2.svg", "unmix3.svg", base_path=gf.icon_path)
            btnUnmixing.clicked.connect(self.execute_unmixing)
            btnUnmixing.setToolTip("unmixing using added spectrum")
            # メソッドexecute
            btnExecuteProcedures = my_w.CustomPicButton("exec_umx1.svg", "exec_umx2.svg", "exec_umx3.svg", base_path=gf.icon_path)
            btnExecuteProcedures.clicked.connect(self.execute_saved_procedures)
            btnExecuteProcedures.setToolTip("load and execute saved procedures ('umx' file)")
            # レイアウト
            spectrum_layout.addWidget(btnSpectrumLinearSubtraction)
            info_layout.addWidget(btnUnmixing)
            info_layout.addWidget(btnExecuteProcedures)
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
        info_layout.addWidget(btnMapSpectTable)
        info_layout.addStretch(1)
        self.addItem(my_w.CustomSpacer())       # スペーサー
        self.addLayout(map_layout)
            # ここにスペーサーが入ります（map_layoutに含まれている）
        self.addLayout(spectrum_layout)
        self.addItem(my_w.CustomSpacer())       # スペーサー
        self.addWidget(my_w.CustomSeparator())  # スペーサー
        self.addItem(my_w.CustomSpacer())       # スペーサー
        # テーブル表示ボタン
        self.addLayout(info_layout)
    def is_file_exists(self):
        # ファイルの有無でまずカット
        if not os.path.exists(self.parent.file_path):
            warning_popup = popups.WarningPopup("The original file was moved or deleted.\nMap size was not changed.", title="warning", p_type="Normal")
            warning_popup.exec_()
            return False
        else:
            return True
    def execute_preprocess(self, mode=None):
        if mode != "newWin":
            if not self.is_file_exists():
                return "not executed"
        for func_name, kwargs in self.parent.spectrum_widget.spc_file.log_dict[b"prep_order"]:
            self.pbar_widget = popups.ProgressBarWidget(parent=self, message="{0} is in progress...".format(func_name))
            self.pbar_widget.addValue(100)
            self.pbar_widget.show()
            QCoreApplication.processEvents()
            #####
            func = getattr(self, func_name)
            func(**kwargs)
            #####
            self.pbar_widget.is_close_allowed = True
            self.pbar_widget.close()
            QCoreApplication.processEvents()
    def execute_poi(self, mode=None):
        if b"point_of_interest_dict" in self.parent.spectrum_widget.spc_file.log_dict.keys():
            self.added_info_poi_list = [
                POI_Info(poi_key=poi_key, poi_data=poi_data, parent_window=self.parent) 
                for poi_key, poi_data in self.parent.spectrum_widget.spc_file.log_dict[b"point_of_interest_dict"].items()
            ]
            self.parent.parent.poi_manager.window_focus_changed(window=self.parent)
    # 基本、PrePが作られてから呼ばれる前提。
    def add_preprocess(self, key):
        if not self.is_file_exists():
            return "not executed"
        self.parent.spectrum_widget.spc_file.add_to_prep_ordred(key)
    def set_spectrum_and_crosshair(self, x, y):
        self.parent.spectrum_widget.replace_spectrum(x, y)
        self.parent.map_widget.set_crosshair(x, y)
    def get_poi_info_from_POI_manager(self, poi_key):
        return self.parent.parent.poi_manager.get_poi_info(poi_key)
    # PreProcesses
    def set_size(self, size=None, mode=None):
        if not self.is_file_exists():
            return "not executed"
        if mode == "init":
            product_x_list, product_y_list = gf.into_2_products(self.parent.spectrum_widget.spc_file.fnsub)
            added_content = AddedContent_Size(
                item=None,
                info={"content":"preprocess", "type":"SIZE", "detail":"", "draw":"none", "data":[product_x_list, product_y_list]}, 
                parent_window=self.parent
            )
            added_content.set_item_fm_size(*self.parent.spectrum_widget.spc_file.get_shape()[::-1])
            self.add_content(added_content)
        # アップデート用
        else:
            # log_dict に必ずあるはずなので、一旦消し、log_dict と バイナリに書き込む
            self.parent.spectrum_widget.spc_file.update_binary(self.parent.file_path, master_key="map_size", key_list=["map_x", "map_y", "map_z"], data_list=size, log_dict=True)
        self.parent.map_widget.map_size_changed()
    # 何かしら追加した時作成されたオブジェクトを格納
    def add_content(self, added_content):
        getattr(self, "added_content_%s_list"%added_content.info["content"]).append(added_content)
        self.parent.parent.map_spect_table.add_content(added_content)
        # マップの場合、最初から表示
        if added_content.info["content"] == "map":
            self.parent.parent.map_spect_table.focus_content(added_content)
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
                self.add_plot_data_item(plot_data_item, detail=file_path, data="")
            else:
                ppup = popups.WarningPopup("Error in opening '%s'\nThe file contains more than 1 spectrum"%file_path)
                ppup.exec_()
    def add_spectra_from_obj(self, **kwargs):
        # テーブルに追加
        plot_data_item = pg.PlotDataItem(kwargs["xData"], kwargs["yData"], fillLevel=0)
        self.add_plot_data_item(plot_data_item, detail=kwargs["info"]["detail"], data="")
    def add_spectra_from_POI(self, **kwargs):
        poi_key = kwargs["info"]["detail"]
        poi_info = self.get_poi_info_from_POI_manager(poi_key=poi_key)
        if poi_info is None:
            return "not executed: Position Of Interest named '{0}' was not found.".format(poi_key)
        self.set_spectrum_and_crosshair(*poi_info.poi_data)
        self.add_current_spectrum()
    def add_current_spectrum(self):
        plot_data_item = self.parent.spectrum_widget.get_current_plot_data_item()
        # テーブルに追加
        self.add_plot_data_item(plot_data_item, detail="from_data", data=[self.parent.spectrum_widget.cur_x, self.parent.spectrum_widget.cur_y])
    def add_plot_data_item(self, plot_data_item, detail, data):
        # ボタン追加
        self.parent.spectrum_widget.add_spectrum_to_v2(plot_data_item)
        self.add_content(
            AddedContent_Spectrum(
                plot_data_item,
                info={"content":"spectrum", "type":"added", "detail":detail, "draw":"static", "data":data}, 
                parent_window=self.parent
            )
        )
    # 右側の軸を隠すかどうか
    def hide_right_axis(self):
        isVisible = self.parent.spectrum_widget.getAxis("right").isVisible()
        self.parent.spectrum_widget.showAxis("right", show=not isVisible)
    def hide_all_in_v2(self, **kwargs):
        v2_settings = self.parent.spectrum_widget.hide_all_in_v2(**kwargs)
        setattr(self, kwargs["var_name"], v2_settings)
    def restore_v2_view(self, **kwargs):
        v2_settings = getattr(self, kwargs["var_name"])
        self.parent.spectrum_widget.restore_v2_view(*v2_settings)
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
                AddedContent_Map(
                    image2D, 
                    info={"content":"map", "type":"added", "detail":"signal_intensity", "draw":"v_line", "data":[RS, "0", "master"]}, 
                    parent_window=self.parent
                )                
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
                AddedContent_Map(
                    image2D, 
                    info={"content":"map", "type":"added", "detail":"signal_to_baseline", "draw":"range", "data":[RS1, RS2, "end2end", "master"]}, 
                    parent_window=self.parent
                )
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
                AddedContent_Map(
                    image2D, 
                    info={"content":"map", "type":"added", "detail":"signal_to_H_baseline", "draw":"range", "data":[RS1, RS2, "minimum", "master"]}, 
                    parent_window=self.parent
                )
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
                AddedContent_Map(
                    image2D, 
                    info={"content":"map", "type":"added", "detail":"signal_to_axis", "draw":"range", "data":[RS1, RS2, "0", "master"]}, 
                    parent_window=self.parent
                )
            )
    # アンミックス
    def execute_unmixing(self, event=None, ask=True, **kwargs):
        if ask:
            # 範囲を決める
            range_settings_popup = popups.RangeSettingsPopup(parent=self.parent, title="unmixing")
            done = range_settings_popup.exec_()
            RS1 = range_settings_popup.spbx_RS1.value()
            RS2 = range_settings_popup.spbx_RS2.value()
        else:
            RS1, RS2 = kwargs["umx_range"]
            done = 1
        if done == 1:
            RS1, RS2 = np.sort([RS1, RS2])
            # アンミックス及びスペクトル追加、画像追加
            self.parent.spectrum_widget.unmixing(RS1, RS2)
            # mapの場合
            if self.parent.spectrum_widget.spc_file.fnsub > 1:
                TYPE = "map"
                self.set_spectrum_and_crosshair(0, 0)
            # 単一スペクトルの場合
            else:
                TYPE = "spectrum"
            # アンミックスされたもののうち、最後のもの（total_signal）を表示 
            # -> 最後のものは、どちらにしろ map_spect_table に追加される時点でフォーカスされてるので、どちらかというと、 abs_id のものを half_focus にするために行う
            self.parent.parent.map_spect_table.focus_content(added_content=getattr(self, "added_content_{0}_list".format(TYPE))[-1])
    def execute_spectrum_linear_subtraction(self, event=None, mode="norm", **kwargs):
        # チェック
        added_content_list = [added_content_spectrum for added_content_spectrum in self.added_content_spectrum_list 
            if added_content_spectrum.item.isVisible() and (added_content_spectrum.info["type"] == "added")]
        if len(added_content_list) > 1 or len(added_content_list) == 0:
            # v2 に表示されてるスペクトルが無ければ無効
            warning_popup = popups.WarningPopup("Exactly 1 added spectrum (blue spectrum) should be displayed!")
            warning_popup.exec_()
            return "not executed"
        if mode == "norm":
            range_settings_popup = popups.RangeSettingsPopupWithCmb(parent=self.parent, initial_values=(250, 450), title="set reference range", cmb_messages=["fit to the horizontal line", "fit to the angled line"])
            done = range_settings_popup.exec_()
            sRS = range_settings_popup.spbx_RS1.value()
            eRS = range_settings_popup.spbx_RS2.value()
            to_zero = range_settings_popup.cmb.currentText() == "fit to the horizontal line"
        elif mode == "macro":
            done = 1
            sRS, eRS = kwargs["range"]
            to_zero = kwargs["to_zero"]
        else:
            print(mode)
            raise Exception("unknwon mode")
        # スペクトルオンリーデータの場合
        if self.parent.spectrum_widget.spc_file.fnsub == done == 1:
            self.parent.spectrum_widget.spectrum_linear_subtraction(sRS, eRS, to_zero)
        # マップイメージの場合
        elif self.parent.spectrum_widget.spc_file.fnsub > 1 and done == 1:
            self.parent.spectrum_widget.multi_spectrum_linear_subtraction(sRS, eRS, to_zero)
            # スペクトル更新
            cur_x = self.parent.spectrum_widget.cur_x
            cur_y = self.parent.spectrum_widget.cur_y
            self.set_spectrum_and_crosshair(cur_x, cur_y)
        else:
            return "not executed"
        return "executed"
    # Saved Procedures
    def export_procedures(self, event=None, save_path=None, ask=True):
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
            self.save_as_method(save_path=save_path)
    def save_as_method(self, save_path):
        # 入れ物づくり
        procedures = [["hide_all_in_v2", {"var_name":"v2_settings"}]]
        for added_content in self.added_content_spectrum_list:
            if added_content.content_type() == " added spectrum":
                procedures.append([
                    "add_spectra_from_obj", 
                    {
                        "xData":list(added_content.item.xData), 
                        "yData":list(added_content.item.yData), 
                        "info":added_content.info
                    }
                ])
            elif added_content.content_type() == " POI spectrum":
                procedures.append([
                    "add_spectra_from_POI", 
                    {
                        "info":added_content.info
                    }
                ])
            else:
                print(added_content.content_type())
                raise Exception("error")
        umx_range = [float(self.range_left.text()), float(self.range_right.text())]
        procedures.append(["execute_unmixing", {"ask":False, "umx_range":umx_range}])
        procedures.append(["restore_v2_view", {"var_name":"v2_settings"}])
        UMX = gf.UnmixingMethod(procedures=procedures, convert2nparray=False)
        UMX.save(save_path)
    def execute_saved_procedures(self, event=None, file_path=None):
        if file_path is None:
            file_path, file_type = QFileDialog.getOpenFileName(self.parent, 'select a procedure method file', gf.settings["method dir"], filter="procedure method files (*.umx)")
        if file_path:
            UMX = gf.load_umx(file_path)
            for procedure, kwargs in UMX.procedures:
                func = getattr(self, procedure)
                log = func(**kwargs)
                try:
                    if log.startswith("not executed"):
                        warning_popup = popups.WarningPopup(log)
                        warning_popup.exec_()
                        break
                except:
                    pass
            # 次回用に保存
            gf.settings["method dir"] = os.path.dirname(file_path)
            gf.save_settings_file()
    # 宇宙線除去
    def CRR_master(self, mode="init", params={}):  # mode = "just revert", or "update"...
        if not self.is_file_exists():
            return "not executed"
        # log_dict と バイナリから削除
        if mode == "just revert":
            if b'[CRR]' in self.parent.spectrum_widget.spc_file.log_other:
                warning_popup = popups.WarningPopup("Do you really want to modify Removed Cosmic Rays?", title="warning", p_type="Bool")
                done = warning_popup.exec_()
                if done == 65536:   # No
                    return "not executed"
                else:
                    self.revert_CRR()
                    return "executed"
            else:
                warning_popup = popups.WarningPopup("No history of CRR.\nCannot be reverted.", title="warning", p_type="Normal")
                warning_popup.exec_()
                return "not executed"
        # log_dict と バイナリを刷新
        elif mode == "update":
            # log_dict と バイナリを削除してよいか確認
            if b'[CRR]' in self.parent.spectrum_widget.spc_file.log_other:
                warning_popup = popups.WarningPopup("Do you really want to modify Removed Cosmic Rays?", title="warning", p_type="Bool")
                done = warning_popup.exec_()
                if done == 65536:   # No
                    return "not executed"
                else:
                    self.revert_CRR()
            # log_dict と バイナリを登録
            self.apply_CRR()
            # master_spectrum を更新
            crrc.replace_cosmic_ray(self.parent.spectrum_widget.spc_file)
        elif mode == "init":
            # master_spectrum を更新
            crrc.replace_cosmic_ray(self.parent.spectrum_widget.spc_file)
        elif mode == "macro":
            # log_dict と バイナリを削除してよいかは確認しない。
            if b'[CRR]' in self.parent.spectrum_widget.spc_file.log_other:
                self.revert_CRR()
            # log_dict とバイナリへ登録
            self.apply_CRR()
            # master_spectrum を更新
            crrc.replace_cosmic_ray(self.parent.spectrum_widget.spc_file)
        # マップイメージ処理
        map_x = int(self.parent.spectrum_widget.spc_file.log_dict[b"map_x"])
        map_y = int(self.parent.spectrum_widget.spc_file.log_dict[b"map_y"])
        image2d_color = np.zeros((map_x, map_y, 4), dtype=int)
        for sub_idx in self.parent.spectrum_widget.spc_file.log_dict[b"cosmic_ray_locs"].keys():
            cur_y, cur_x = divmod(sub_idx, map_x)
            image2d_color[cur_x, cur_y, :] = [255, 0, 0, 255]
        image2D_color = Image2D_color(image2d_color, name="CRR")
        # ボタン用意
        added_content = AddedContent_CRR(
            item=image2D_color, 
            info={"content":"preprocess", "type":"CRR", "detail":"defaut settings", "draw":"spc_overlay", "data":[None, None, CRR_Data()]}, 
            parent_window=self.parent
        )
        self.add_content(added_content)
        # focus/unfocus で表示される map とは違って、hide/show で表示されるかが切り替わる。最初は hide されてるので、表示する。
        added_content.hide_show_item(show=True)
    def apply_CRR(self):
        # プログレスバー処理
        self.pbar_widget = popups.ProgressBarWidget(parent=self, message="Detecting cosmic rays... please wait.", real_value_max=self.parent.spectrum_widget.spc_file.fnpts)
        self.pbar_widget.show()
        segment_list = self.pbar_widget.get_segment_list(self.parent.spectrum_widget.spc_file.fnpts, segment=96)
        # 空間情報も含め、宇宙線を検出・除去する。
        cosmic_ray_locs, CRR_params = crrc.locate_cosmic_ray(self.parent.spectrum_widget.spc_file, pbar=self.pbar_widget, segment_list=segment_list)
        # 書き込む（計算は既に終了している）オブジェクト中の data もアップデートされる
        self.pbar_widget.setLabel("Applying views...")
        self.pbar_widget.addValue(1)
        self.parent.spectrum_widget.spc_file.write_to_binary(
            self.parent.file_path, 
            master_key="CRR", 
            key_list=["cosmic_ray_locs", "cosmic_ray_removal_params"], 
            data_list=[cosmic_ray_locs, CRR_params],
            log_dict=True
        )
        # PreProcess にも追加
        self.parent.spectrum_widget.spc_file.modify_prep_order(
            self.parent.file_path, 
            mode="append", 
            key="CRR_master", 
            kwargs={"mode":"init"}, 
            log_dict=True
        )
        # プログレスバー閉じる
        self.pbar_widget.is_close_allowed = True
        self.pbar_widget.close()
    def revert_CRR(self):
        # オリジナルのデータを回復する
        crrc.restore_cosmic_ray(self.parent.spectrum_widget.spc_file)
        # バイナリから削除
        self.parent.spectrum_widget.spc_file.delete_from_binary(
            self.parent.file_path, 
            master_key="CRR", 
            key_list=["cosmic_ray_locs", "cosmic_ray_removal_params"], 
            log_dict=True
        )
        # PreProcess からも削除
        self.parent.spectrum_widget.spc_file.modify_prep_order(
            self.parent.file_path, 
            mode="remove", 
            key="CRR_master", 
            kwargs=None, 
            log_dict=True
        )
        # マップイメージを初期化
        map_x = int(self.parent.spectrum_widget.spc_file.log_dict[b"map_x"])
        map_y = int(self.parent.spectrum_widget.spc_file.log_dict[b"map_y"])
        self.parent.map_widget.overlay_img.setImage(np.zeros((map_x, map_y, 4), dtype=int))
        self.parent.spectrum_widget.hide_all_lines_overlayed()
        # スペクトル、クロスヘア
        self.set_spectrum_and_crosshair(0, 0)
    # ノイズフィルタ
    def NR_master(self, mode=None, params={}): # mode = "init", "just revert", or "update"...
        if not self.is_file_exists():
            return "not executed"
        # log_dict とバイナリから削除
        if mode == "just revert":
            if b'[NR]' in self.parent.spectrum_widget.spc_file.log_other:
                warning_popup = popups.WarningPopup("Do you really want to modify Noise Reduction?", title="warning", p_type="Bool")
                done = warning_popup.exec_()
                if done == 65536:   # No
                    return "not executed"
                else:
                    self.revert_NR()
                    return "executed"
            else:
                warning_popup = popups.WarningPopup("No history of Noise Reduction.\nCannot be reverted.", title="warning", p_type="Normal")
                warning_popup.exec_()
                return "not executed"
        # log_dict と バイナリを刷新
        elif mode == "update":
            # log_dict と バイナリを削除してよいか確認
            if b'[NR]' in self.parent.spectrum_widget.spc_file.log_other:
                warning_popup = popups.WarningPopup("Do you really want to modify Noise Reduction?", title="warning", p_type="Bool")
                done = warning_popup.exec_()
                if done == 65536:   # No
                    return "not executed"
                else:
                    self.revert_NR()
            # パラメータ設定
            noise_filter_popup = popups.ValueSettingsPopup(parent=self, initial_value=self.parent.spectrum_widget.spc_file.log_dict.get(b"noise_reduction_params", 100), label="Number of\nComponent", double=False)
            done = noise_filter_popup.exec_()
            if done == 0:   # Cancel
                return "not executed"
            # log_dict とバイナリへ登録
            self.apply_NR(noise_filter_popup.spbx_RS.value())
            # master_spectrum を更新
            N_components = nfc.PCA_based_NR(self.parent.spectrum_widget.spc_file)
        elif mode == "init":
            # master_spectrum を更新
            N_components = nfc.PCA_based_NR(self.parent.spectrum_widget.spc_file)
        elif mode == "macro":
            # log_dict と バイナリを削除してよいかは確認しない。
            if b'[NR]' in self.parent.spectrum_widget.spc_file.log_other:
                self.revert_NR()
            N_components = params["N_components"]
            # log_dict とバイナリへ登録
            self.apply_NR(N_components)
            # master_spectrum を更新
            nfc.PCA_based_NR(self.parent.spectrum_widget.spc_file)
        # ボタン追加
        self.add_content(
            AddedContent_NR(
                item=None, 
                info={"content":"preprocess", "type":"NR", "detail":"PCA-based", "draw":"none", "data":N_components}, 
                parent_window=self.parent
            )
        )
        # 表示
        self.set_spectrum_and_crosshair(0, 0)
    def apply_NR(self, N_components):
        self.pbar_widget = popups.ProgressBarWidget(parent=self, message="Noise reduction is in progress... please wait.")
        self.pbar_widget.show()
        self.pbar_widget.addValue(10)
        self.pbar_widget.addValue(90)
        # バイナリに追加
        self.parent.spectrum_widget.spc_file.write_to_binary(
            self.parent.file_path, 
            master_key="NR", 
            key_list=["noise_reduction_params"], 
            data_list=[{"N_components":N_components}],
            log_dict=True
        )
        # PreProcess にも追加
        self.parent.spectrum_widget.spc_file.modify_prep_order(
            self.parent.file_path, 
            mode="append", 
            key="NR_master", 
            kwargs={"mode":"init"}, 
            log_dict=True
        )
        # プログレスバー
        self.pbar_widget.is_close_allowed = True
        self.pbar_widget.close()
    def revert_NR(self):
        # オリジnfcナルのデータを回復する
        gf.spc_transplant(self.parent.spectrum_widget.spc_file, donor_spc=gf.open_spc_spcl(self.parent.file_path))
        # バイナリから削除
        self.parent.spectrum_widget.spc_file.delete_from_binary(
            self.parent.file_path, 
            master_key="NR", 
            key_list=["noise_reduction_params"], 
            log_dict=True
        )
        # PreProcess からも削除
        self.parent.spectrum_widget.spc_file.modify_prep_order(
            self.parent.file_path, 
            mode="remove", 
            key="NR_master", 
            kwargs=None, 
            log_dict=True
        )
        # スペクトル、クロスヘア
        self.set_spectrum_and_crosshair(0, 0)
    def SCL_master(self, mode=None, params={}):
        # ボタン追加
        self.parent.spectrum_widget.set_N_overlayed_lines(1)
        added_content = AddedContent_SCL(
            item=None, 
            info={"content":"preprocess", "type":"SCL", "detail":"", "draw":"spc_overlay", "data":[None, None, SCL_Data()]}, 
            parent_window=self.parent
        )
        self.add_content(added_content)
        # スペクトルの表示
        added_content.hide_show_item(show=True)
    # Point of Interest
    def POI_master(self, mode=None, params={}):
        poi_dict = self.parent.spectrum_widget.spc_file.log_dict[b"point_of_interest_dict"]
        # 大元のバイナリファイルを上書き
        if mode == "add":
            idx = 1
            while "poi{0}".format(idx) in poi_dict.keys():
                idx += 1
            poi_key = "poi{0}".format(idx)
            poi_dict[poi_key] = [self.parent.spectrum_widget.cur_x, self.parent.spectrum_widget.cur_y]
            # info処理
            poi_info = POI_Info(poi_key=poi_key, poi_data=poi_dict[poi_key], parent_window=self.parent)
            self.added_info_poi_list.append(poi_info)
        elif mode == "del":
            poi_info = params["poi_info"]
            del poi_dict[poi_info.poi_key]
            # info処理
            self.added_info_poi_list.remove(poi_info)
        elif mode == "mod_name":
            poi_info = params["poi_info"]
            poi_dict[poi_info.poi_key] = poi_dict.pop(params["old_poi_key"])
            # info処理は、POI_manager にて済
        elif mode == "mod_data":
            poi_info = params["poi_info"]
            poi_dict[poi_info.poi_key] = poi_info.poi_data
            # info処理は、POI_manager にて済
        # バイナリを更新
        self.parent.spectrum_widget.spc_file.update_binary(
            self.parent.file_path, 
            master_key="POI", 
            key_list=["point_of_interest_dict"], 
            data_list=[poi_dict], 
            log_dict=True
        )
        return poi_info
    def set_POI_fm_macro(self, poi_key):
        # popup の range 入力欄の範囲設定
        x_size = int(self.parent.spectrum_widget.spc_file.log_dict[b"map_x"])
        y_size = int(self.parent.spectrum_widget.spc_file.log_dict[b"map_y"])
        if poi_key in self.parent.spectrum_widget.spc_file.log_dict[b"point_of_interest_dict"].keys():
            initial_values = self.parent.spectrum_widget.spc_file.log_dict[b"point_of_interest_dict"][poi_key]
        else:
            initial_values = (0, 0)
        # クロスヘア、スペクトル、poi_settings_popup を initial_values にあわせる
        self.set_spectrum_and_crosshair(*initial_values)
        # popup表示
        self.poi_settings_popup.set_spinbox_range((0, x_size-1), "RS1")
        self.poi_settings_popup.set_spinbox_range((0, y_size-1), "RS2")
        self.poi_settings_popup.setValues(initial_values)
        self.poi_settings_popup.set_poi_key(poi_key)
        if not self.poi_popup_connected:
            self.parent.map_widget.scene().sigMouseClicked.connect(self.poi_settings_popup.on_map_widget_click)
            self.poi_popup_connected = True
        self.poi_settings_popup.show()        # 位置調整：親windowの右上に揃える感じで
        pwg = self.parent.geometry()
        pwf = self.parent.frameSize()
        self.poi_settings_popup.move(pwg.left() + pwf.width(), pwg.top() - pwf.height() + pwg.height())
        return True
    def poi_settings_popup_ok_clicked(self):
        # 大元のバイナリファイルを上書き（ついでに、現在の spc_file にpoi_xなども追加します）
        poi_key = self.poi_settings_popup.get_poi_key()
        if poi_key in self.parent.spectrum_widget.spc_file.log_dict[b"point_of_interest_dict"].keys():
            warning_popup = popups.WarningPopup("The name {0} is already taken. Do you really want to overwrite?".format(poi_key), title="WARNING", p_type="Bool")
            done = warning_popup.exec_()
            if done == 16384:   # YES
                poi_idx = self.parent.parent.poi_manager.get_poi_idx(poi_key=poi_key)
                x, y = self.parent.spectrum_widget.cur_x, self.parent.spectrum_widget.cur_y
                self.parent.parent.poi_manager.poi_layout.set_focus(idx=poi_idx)
                self.parent.parent.poi_manager.btn_poi_del_clicked()
                # focus すると、スペクトルの場所が移動してしまうので。
                self.set_spectrum_and_crosshair(x, y)
            else:   # NO
                self.set_POI_fm_macro(poi_key)
                return False
        self.parent.parent.poi_manager.btn_poi_add_clicked()
        self.parent.parent.poi_manager.poi_layout.set_focus(idx=-2)
        self.parent.parent.poi_manager.btn_poi_rename_clicked(ask=False, poi_key=poi_key)
        return True
    # 構築画像保存
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
        for added_content in self.parent.toolbar_layout.added_content_map_list:
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
        # 図のサイズ変更（pixel指定にする）<svg width="65.9694mm" height="44.0972mm" ...> の部分。
        with open(save_path, mode="rb") as f:
            matched_object = re.sub(b'<svg width="[0-9\.]+mm" height="[0-9\.]+mm"\\n viewBox="0 0 ([0-9\.]+) ([0-9\.]+)"', 
                            b'<svg width="\\1px" height="\\2px"\\n viewBox="0 0 \\1 \\2"', f.read()
                            )
            if matched_object is None:
                raise Exception("error in exporting svg file")
        with open(save_path, mode="wb") as f:
            f.write(matched_object)
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
    # build unmix method 専用関数
    def include_POI(self, event=None, ask=True, **kwargs):
        if ask:
            poi_name_popup = popups.TextSettingsPopup(parent=self.parent, initial_txt="target_poi", label="POI name", title="set POI name")
            poi_key = poi_name_popup.text()
            done = poi_name_popup.exec_()
        else:
            poi_key = kwargs["poi_key"]
            done = True
        if done:
            if " " in poi_key:
                warning_popup = popups.WarningPopup("Spaces are not allowed in the name.")
                warning_popup.exec_()
                self.include_POI()
                return
            if poi_key == "":
                warning_popup = popups.WarningPopup("Empty name is not allowed.")
                warning_popup.exec_()
                self.include_POI()
                return
        else:
            return
        # viewbox は、text_item を変更する
        self.parent.add_poi()
        #ボタン追加
        self.add_content(
            AddedContent_POI(
                item=pg.PlotDataItem(), # pseudo
                info={"content":"spectrum", "type":"POI", "detail":poi_key, "draw":"none", "data":""}, 
                parent_window=self.parent
            )
        )
        return
    def set_range(self, mode, **kwargs):
        if mode in ("newWin", "init"):
            brush_color = gf.mk_u_pen().color()
            brush_color.setAlpha(gf.brushAlpha)
            region_item = pg.LinearRegionItem(values=[0, 0], brush=brush_color, movable=True, bounds=None)
            region_item.hide()
            self.parent.spectrum_widget.vb2.addItem(region_item)
            added_content = AddedContent_Range(
                item=region_item,
                info={"content":"preprocess", "type":"range-setting", "detail":"", "draw":"none", "data":[0, 0]}, 
                parent_window=self.parent
            )
            self.add_content(added_content)
            if mode == "init":
                RS1, RS2 = kwargs["umx_range"]
                self.range_left.setText(str(RS1))
                self.range_right.setText(str(RS2))
                added_content.item.setRegion([RS1, RS2])
            return
        for added_content in self.added_content_preprocess_list:
            if added_content.info["type"] == "range_setting":
                break
        else:
            raise Exception ("no added_content")
        if mode == "fmToolB":
            range_settings_popup = popups.RangeSettingsPopup(parent=self.parent, initial_values=added_content.info["data"], title="unmixing range")
            done = range_settings_popup.exec_()
            RS1 = range_settings_popup.spbx_RS1.value()
            RS2 = range_settings_popup.spbx_RS2.value()
            if done:
                RS1, RS2 = np.sort([RS1, RS2])
                self.range_left.setText(str(RS1))
                self.range_right.setText(str(RS2))
                added_content.item.setRegion([RS1, RS2])
            else:
                return
        else:
            print(mode)
            raise Exception("unknown mode")


# スペクトル描画
class SpectrumWidget(pg.PlotWidget):
    def __init__(self, spc_file=None, parent=None):
        self.spc_file = spc_file
        self.parent = parent
        # 現在地情報
        self.cur_x = 0
        self.cur_y = 0
        # used for displaying multiple spectrum set in vb2
        self.abs_id = 0
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
        self.overlayed_lines = []
        self.overlayed_fill_btwn_items = []
        # master spectrum 用のボタンを追加
        self.parent.toolbar_layout.add_content(
            AddedContent_Spectrum(
                self.master_spectrum, 
                info={"content":"spectrum", "type":"original", "detail":"", "draw":"master", "data":""}, 
                parent_window=self.parent
            )
        )
        # unmix window の場合は spc_file = None
        if self.spc_file is not None:
            self.master_spectrum.setData(self.spc_file.x, self.spc_file.sub[0].y)
            # mapの場合テキスト追加（どこの位置のスペクトルかということ）
            if self.spc_file.fnsub > 1:
                self.text_item = pg.TextItem(text="   x=0, y=0")
                self.text_item.setParentItem(self.getPlotItem().vb)
        # unmix window の場合、pseudoデータを追加
        else:
            self.spc_file = gf.SpcLike()
            self.text_item = pg.TextItem(text="")
            self.text_item.setParentItem(self.getPlotItem().vb)
    # グラフがある場合、親 widget が focus を get できない。
    def focusInEvent(self, event):
        self.parent.focusInEvent(event)
    def focusOutEvent(self, event):
        self.parent.focusOutEvent(event)
    def get_current_plot_data_item(self):
        current_plot = self.getPlotItem().vb.addedItems[0]
        plot_data_item = pg.PlotDataItem(current_plot.xData, current_plot.yData, fillLevel=0)
        return plot_data_item
    def update_spectrum(self):
        # spc_file のデータが更新された時。
        sub_idx = self.spc_file.get_sub_idx(self.cur_x, self.cur_y)
        self.master_spectrum.setData(self.spc_file.x, self.spc_file.sub[sub_idx].y)
    # 現在表示されているスペクトルを(vb2に)追加
    def add_spectrum_to_v2(self, plot_data_item):
        # vb2への追加がはじめての場合のみ、右軸を表示する（それ以外の場合は設定をそのまま引継ぐ）
        if len(self.vb2.addedItems):
            self.showAxis("right")
        # 追加
        plot_data_item.setPen(gf.mk_a_pen())
        self.vb2.addItem(plot_data_item)
        return plot_data_item
    def hide_all_in_v2(self, **kwargs):
        already_in_vb2 = len(self.vb2.addedItems)
        if already_in_vb2:
            v2_xy_range = self.vb2.viewRange()
        else:
            v2_xy_range = None
        isVisible_dict = {}
        for added_item in self.vb2.addedItems:
            isVisible_dict[added_item] = added_item.isVisible()
            added_item.hide()
        return isVisible_dict, v2_xy_range
    def restore_v2_view(self, isVisible_dict, v2_xy_range):
        for added_item, isVisible in isVisible_dict.items():
            added_item.setVisible(isVisible)
        if v2_xy_range is not None:
            self.vb2.setXRange(*v2_xy_range[0])
            self.vb2.setYRange(*v2_xy_range[1])
    # mapデータ用。別の位置のspectrumを表示する
    def replace_spectrum(self, map_x, map_y):
        # 場所情報の更新
        self.cur_x = map_x
        self.cur_y = map_y
        self.text_item.setText("  x=%d, y=%d"%(self.cur_x, self.cur_y))
        # オリジナルのスペクトル
        sub_idx = self.spc_file.get_sub_idx(self.cur_x, self.cur_y)
        self.master_spectrum.setData(self.spc_file.x, self.spc_file.sub[sub_idx].y)
        self.display_map_spectrum()
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
    def set_N_overlayed_lines(self, N):
        N_overlayed_lines = len(self.overlayed_lines)
        if N_overlayed_lines < N:
            for idx in range(N - N_overlayed_lines):
                overlayed_lines = pg.PlotCurveItem(pen=gf.mk_u_pen())
                self.overlayed_lines.append(overlayed_lines)
                self.addItem(overlayed_lines)
        elif N_overlayed_lines > N:
            for idx in range(N_overlayed_lines - N):
                deleted_item = self.overlayed_lines.pop(0)
                self.removeItem(deleted_item)
        for content in self.overlayed_lines:
            content.show()
    def set_N_overlayed_fill_btwn_items(self, N):
        N_overlayed_fill_btwn_items = len(self.overlayed_fill_btwn_items)
        if N_overlayed_fill_btwn_items < N:
            for idx in range(N - N_overlayed_fill_btwn_items):
                overlayed_fill_btwn_item = pg.FillBetweenItem(brush=gf.mk_u_brush())
                self.overlayed_fill_btwn_items.append(overlayed_fill_btwn_item)
                self.addItem(overlayed_fill_btwn_item)
        elif N_overlayed_fill_btwn_items > N:
            for idx in range(N_overlayed_fill_btwn_items - N):
                deleted_item = self.overlayed_fill_btwn_items.pop(0)
                self.removeItem(deleted_item)
        for content in self.overlayed_fill_btwn_items:
            content.show()
    def hide_all_fill_btwn_items(self):
        for content in self.additional_fill_btwn_items:
            content.hide()
    def hide_all_lines(self):
        for content in self.additional_lines:
            content.hide()
    def hide_all_points(self):
        self.additional_points.hide()
    def hide_all_fill_btwn_items_overlayed(self):
        for content in self.overlayed_fill_btwn_items:
            content.hide()
    def hide_all_lines_overlayed(self):
        for content in self.overlayed_lines:
            content.hide()
    def show_all_fill_btwn_items(self):
        for content in self.additional_fill_btwn_items:
            content.show()
    def show_all_lines(self):
        for content in self.additional_lines:
            content.show()
    def show_all_points(self):
        self.additional_points.show()
    def show_all_fill_btwn_items_overlayed(self):
        for content in self.overlayed_fill_btwn_items:
            content.show()
    def show_all_lines_overlayed(self):
        for content in self.overlayed_lines:
            content.show()
    # Process items to display in vb1
    def display_map_spectrum(self):
        sub_idx = self.spc_file.get_sub_idx(self.cur_x, self.cur_y)
        if self.parent.cur_displayed_map_content is None:
            print("necessary1")
            # umx_methodから呼ばれたときは、background を設定する際、mapを指定せずにreplace_spectrumするので、これが呼ばれてしまう。
        else:
            data = self.parent.cur_displayed_map_content.info["data"]
            draw = self.parent.cur_displayed_map_content.info["draw"]
            if draw == "v_line":    # data = [RS1, btm, top]
                self.set_N_additional_lines(1)
                self.hide_all_fill_btwn_items()
                RS_idx1 = self.spc_file.get_idx(data[0])
                x_value1 = self.spc_file.x[RS_idx1]
                if data[1] == "0":
                    btm_value = 0
                if data[2] == "master":
                    top_value = self.spc_file.sub[sub_idx].y[RS_idx1]
                self.additional_lines[0].setData([x_value1, x_value1], [btm_value, top_value])
            elif draw == "range":   # data = [RS1, RS2, btm, top]
                self.set_N_additional_fill_btwn_items(1)
                self.hide_all_lines()
                RS_idx1 = self.spc_file.get_idx(data[0])
                RS_idx2 = self.spc_file.get_idx(data[1])
                RS_idx1, RS_idx2 = np.sort([RS_idx1, RS_idx2])
                x_value1 = self.spc_file.x[RS_idx1]
                x_value2 = self.spc_file.x[RS_idx2]
                y_value_list = self.spc_file.sub[sub_idx].y[RS_idx1:RS_idx2 + 1]
                if data[2] == "0":
                    fill_btm = pg.PlotDataItem([x_value1, x_value2], [0, 0])
                elif data[2] == "end2end":
                    y_value1 = y_value_list[0]
                    y_value2 = y_value_list[-1]
                    fill_btm = pg.PlotDataItem([x_value1, x_value2], [y_value1, y_value2])
                elif data[2] == "minimum":
                    min_y_value = np.min(y_value_list)
                    fill_btm = pg.PlotDataItem([x_value1, x_value2], [min_y_value, min_y_value])
                if data[3] == "master":
                    fill_top = pg.PlotDataItem(self.spc_file.x[RS_idx1:RS_idx2 + 1], y_value_list)
                self.additional_fill_btwn_items[0].setCurves(fill_btm, fill_top)
            elif draw == "func": # data = [RS1, RS2, multi_data]
                self.set_N_additional_lines(data[2].N_lines())
                self.set_N_additional_fill_btwn_items(data[2].N_ranges())
                for idx, (line_data_x, line_data_y) in enumerate(data[2].get_line_data_list(sub_idx=sub_idx, original_spc_file=self.spc_file)):
                    self.additional_lines[idx].setData(line_data_x, line_data_y)
                for idx, (btm_line, top_line) in enumerate(data[2].get_region_data_list(sub_idx=sub_idx, original_spc_file=self.spc_file)):
                    self.additional_fill_btwn_items[idx].setCurves(btm_line, top_line)
            else:
                raise Exception("unsuitable args")
        # overlayed map info
        if self.parent.cur_overlayed_map_content is None:
            print("necessary2")
        else:
            data = self.parent.cur_overlayed_map_content.info["data"]
            draw = self.parent.cur_overlayed_map_content.info["draw"]
            if draw == "spc_overlay":   # [param1, param2, spc_data]
                self.set_N_overlayed_lines(data[2].N_lines(sub_idx))
                self.set_N_overlayed_fill_btwn_items(data[2].N_ranges(sub_idx))
                for idx, (line_data_x, line_data_y, kwargs) in enumerate(data[2].get_line_data_list(sub_idx=sub_idx, original_spc_file=self.spc_file)):
                    self.overlayed_lines[idx].setData(line_data_x, line_data_y, **kwargs)
                for idx, (btm_line, top_line, kwargs) in enumerate(data[2].get_region_data_list(sub_idx=sub_idx, original_spc_file=self.spc_file)):
                    self.additional_fill_btwn_items[idx].setCurves(btm_line, top_line, **kwargs)
            else:
                raise Exception("unknow kwargs")
    def display_spectrum(self):
        if self.parent.cur_overlayed_spc_info is None:
            print("necessary3")
        else:
            data = self.parent.cur_overlayed_spc_info["data"]
            draw = self.parent.cur_overlayed_spc_info["draw"]
            sub_idx = 0
            if draw == "spc_overlay":   # [param1, param2, spc_data]
                self.set_N_overlayed_lines(data[2].N_lines(sub_idx))
                self.set_N_overlayed_fill_btwn_items(data[2].N_ranges(sub_idx))
                for idx, (line_data_x, line_data_y, kwargs) in enumerate(data[2].get_line_data_list(sub_idx=sub_idx, original_spc_file=self.spc_file)):
                    self.overlayed_lines[idx].setData(line_data_x, line_data_y, **kwargs)
                for idx, (btm_line, top_line, kwargs) in enumerate(data[2].get_region_data_list(sub_idx=sub_idx, original_spc_file=self.spc_file)):
                    self.additional_fill_btwn_items[idx].setCurves(btm_line, top_line, **kwargs)
            else:
                raise Exception("unknow kwargs")
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
        optional_name_list = added_summary_list + ["baseline_drift", "total_signal"]
        optional_id_list = list(map(lambda x: str(x+1), range(n_spectrum - 3))) + ["bd", "ts"]
        # データ準備
        unmixed_data_list = [
            UnmixedData(
                abs_id = self.abs_id, 
                standard_type = optional_id, 
                umx_x_list = umx_x_list, 
                umx_y_matrix = regional_y_matrix, 
                umx_h_matrix = umx_height_matrix
            ) for optional_id in optional_id_list]
        # map画像作成
        if self.spc_file.fnsub > 1:
            # image2d_list = [np.reshape(area_list, self.spc_file.get_shape()).T for area_list in area_list_set.T]
            item_list = [
                Image2D(
                    np.reshape(area_list, self.spc_file.get_shape()).T, 
                    name="unmixed_{0}-{1}_{2}".format(sRS, eRS, optional_id)
                ) for area_list, optional_id in zip(area_list_set.T, optional_id_list)]
            content = "map"
            umx_class = AddedContent_Unmixed
        # スペクトル 1 本のみのデータの場合
        else:
            item_list = []
            for unmixed_data in unmixed_data_list:
                item = my_w.CustomFillBetweenItems(
                    *unmixed_data.get_region_data_list(sub_idx=0, original_spc_file=None)[0], 
                    brush = pg.mkBrush(0.0, 0.0, 0.0, 1.0), 
                    pen = gf.mk_u_pen()
                )
                item_list.append(item)
                for i in item.all_items():
                    self.plotItem.addItem(i)
                # ボトムラインは除く
                if unmixed_data.standard_type in ("bd", "ts"):
                    self.plotItem.removeItem(item.curve1)
            content = "spectrum"
            umx_class = AddedContent_Unmixed_s
        # 作られたmapたちをmap_widgeteに渡す
        for idx, (item, optional_name, unmixed_data) in enumerate(zip(item_list, optional_name_list, unmixed_data_list)):
            # ボタン追加
            self.parent.toolbar_layout.add_content(
                umx_class(
                    item=item, 
                    info={"content":content, "type":"unmixed", "detail":optional_name, "draw":"func", "data":[sRS, eRS, unmixed_data]}, 
                    parent_window=self.parent
                )
            )
        # プログレスバー閉じる
        self.abs_id += 1
        self.pbar_widget.is_close_allowed = True
        self.pbar_widget.close()
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
    def get_spectrum_linear_subtraction_basic_info(self, sRS, eRS):
        # # (sRS, eRS)と(sRS-idx, eRS-idx)は必ずしも一致しない（RSは降順にもなりうるがidxはあくまで昇順に並ぶ）
        # sRS_idx, eRS_idx = np.sort([self.spc_file.get_idx(sRS), self.spc_file.get_idx(eRS)])
        # 使用する追加スペクトル（事前チェックは済ませといてね）
        added_content_list = [added_content_spectrum for added_content_spectrum in self.parent.toolbar_layout.added_content_spectrum_list 
            if added_content_spectrum.item.isVisible() and (added_content_spectrum.info["type"] == "added")]
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
        # master_x_list2, master_y_list2 = self.spc_file.get_data(x_minmax2[0], x_minmax2[1], sub_idx=0)
        sub_h_set = np.empty((self.spc_file.fnsub, 3), dtype=float)
        # イメージ格納庫（全スペクトルの総和としてイメージを作成）
        area_values_list = np.empty(self.spc_file.fnsub, dtype=float)
        selected_RS_diff_list_half = np.absolute(np.diff(self.spc_file.x[x_min1_idx:x_max1_idx + 1])) / 2
        to_subtract_base_values = np.array([
            ((added_y_list1[1:] + added_y_list1[:-1]) * selected_RS_diff_list_half).sum(), 
            ((self.spc_file.x[x_min1_idx:x_max1_idx] + self.spc_file.x[x_min1_idx + 1:x_max1_idx + 1]) * selected_RS_diff_list_half).sum(), 
            selected_RS_diff_list_half.sum() * 1
        ])
        for idx in range(self.spc_file.fnsub):
            master_x_list2, master_y_list2 = self.spc_file.get_data(x_minmax2[0], x_minmax2[1], sub_idx=idx)
            # 最小二乗
            h_values = gf.spectrum_linear_subtraction_core(master_x_list2, master_y_list2, added_y_list2, to_zero)
            sub_h_set[idx, :] = h_values
            area_values_list[idx] = ((self.spc_file.sub[idx].y[x_min1_idx + 1:x_max1_idx + 1] + self.spc_file.sub[idx].y[x_min1_idx:x_max1_idx]) \
                                         * selected_RS_diff_list_half).sum() - (to_subtract_base_values * h_values).sum()
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
            x_minmax1 = x_minmax1, 
            master_x_list1 = master_x_list1, 
            added_y_list1 = added_y_list1, 
            sub_h_set = sub_h_set, 
            to_zero = to_zero
            )
        self.parent.toolbar_layout.add_content(
            AddedContent_SubtractedSpectrums(
                image2D, 
                info={"content":"map", "type":"subtracted", "detail":added_content.summary(), "draw":"func", "data":[sRS, eRS, subtraction_data]}, 
                parent_window=self.parent
            )
        )
        # プログレスバー閉じる
        self.pbar_widget.is_close_allowed = True
        self.pbar_widget.close()
    # 追加スペクトルが1本のみの場合に適用。指定された波数範囲において元スペクトルから、n倍した追加スペクトルを引き算し、なるべく直線に近づくような引き算をする。
    def spectrum_linear_subtraction(self, sRS, eRS, to_zero):
        # 追加スペクトルの補間版（1はオリジナルと追加の共通部分、2はそれにsRS, eRSの共通部分も含めたもの）
        x_minmax1, x_minmax2, added_y_list1, added_y_list2, added_content = self.get_spectrum_linear_subtraction_basic_info(sRS, eRS)
        # 元データ
        master_x_list1, master_y_list1 = self.spc_file.get_data(x_minmax1[0], x_minmax1[1], sub_idx=0)
        master_x_list2, master_y_list2 = self.spc_file.get_data(x_minmax2[0], x_minmax2[1], sub_idx=0)
        # 最小二乗  [n, a, b] in master_y_list - (n * added_regional_y_list + a * master_x_list + b)
        h_values = gf.spectrum_linear_subtraction_core(master_x_list2, master_y_list2, added_y_list2, to_zero)
        # 追加
        y_list = master_y_list1 - (added_y_list1 * h_values[0] + master_x_list1 * h_values[1] + np.ones_like(master_x_list1) * h_values[2])
        plot_data_item = pg.PlotDataItem(master_x_list1, y_list, fillLevel=0, pen=gf.mk_u_pen())
        self.plotItem.vb.addItem(plot_data_item)
        self.parent.toolbar_layout.add_content(
            AddedContent_Spectrum(
                plot_data_item, 
                info={"content":"spectrum", "type":"subtracted", "detail":added_content.summary(), "draw":"static", "data":[sRS, eRS]}, 
                parent_window=self.parent
            )
        )

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
        self.overlay_img = pg.ImageItem()
        self.img_view_box.addItem(self.overlay_img)
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
        # イベントコネクト
        self.scene().sigMouseClicked.connect(self.on_click)
        self.scene().sigMouseMoved.connect(self.on_move)
    # グラフがある場合、親 widget が focus を get できない。
    def focusInEvent(self, event):
        self.parent.focusInEvent(event)
    def focusOutEvent(self, event):
        self.parent.focusOutEvent(event)
    # 初期処理
    def map_size_changed(self):
        self.parent.set_window_title()
        self.set_crosshair(0, 0)
        # 枠のサイズアップデート
        w, h = self.parent.spectrum_widget.spc_file.get_shape()
        self.frame.setRect(0, 0, h, w)
        # imgのサイズアップデート
        if self.map_img.image is not None:
            self.map_img.setImage(np.reshape(self.map_img.image.T, (w, h)).T)
        else:
            pseudo_image2d = np.zeros((w, h), dtype=float).T
            self.map_img.setImage(pseudo_image2d)
            self.map_img.hide()
        self.img_view_box.autoRange()
        # 既に追加された map がある場合は、それをアップデート
        for added_content in self.parent.toolbar_layout.added_content_map_list:
            added_content.item.image2d = added_content.item.image2d.T.reshape(w, h).T
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
    # # 現在の画像を、新たな画像で割る
    # def Divide(self, image2D):
    #     new_name = "div_%s_by_%s"%(self.name, image2D.name)
    #     new_image2d = self.image2d / image2D.image2d
    #     return Image2D(new_image2d, name=new_name)
    # infは無視するよ
    def image(self):
        return self.image2d
    def getLevels(self):
        finite_array = self.image2d[np.isfinite(self.image2d)]
        return np.min(finite_array), np.max(finite_array)
class Image2D_color():
    def __init__(self, image2d_color, name="none-type"):
        self.image2d_color = image2d_color
        self.x, self.y, self.c = image2d_color.shape
        self.name = name
    def image(self):
        return self.image2d_color

# popup用の簡易版
class SimpleMapWidget(MapWidget):
    def __init__(self, spc_file=None, parent=None):
        super().__init__(spc_file=spc_file, parent=parent)

class SimpleToolbarLayout(QVBoxLayout):
    def __init__(self, parent=None):
        super().__init__()
        self.isImageSet = False



