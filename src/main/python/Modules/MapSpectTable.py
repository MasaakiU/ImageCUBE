# -*- Coding: utf-8 -*-

import os
import functools
import re

from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout,  
    QFileDialog, 
    QSizePolicy, 
    QSpacerItem, 
    QDesktopWidget, 
    QMenu, 
    QScrollArea, 
    QLabel, 
    QPushButton, 
    QSplitter, 
    )
from PyQt5.QtCore import (
    Qt, 
    QVariant, 
    )

from . import general_functions as gf
from . import my_widgets as my_w
from . import popups

class MapSpectTable(QWidget):
    def __init__(self, parent=None):
        self.parent = parent
        self.window_type = "t"
        self.allow_closing = False
        super().__init__()
        self.setWindowTitle("Map-Spectrum Table")
        self.current_focused_table = None
        # 前処理
        self.preprocess_layout = my_w.ClickableLayout(parent=self)
        pre_inside_widget = QWidget()
        pre_inside_widget.setLayout(self.preprocess_layout)
        pre_inside_widget.setObjectName("map_inside_widget")
        pre_inside_widget.setStyleSheet("QWidget#map_inside_widget{background-color: white}")
        pre_scroll_area = QScrollArea()
        pre_scroll_area.setWidgetResizable(True)
        pre_scroll_area.setWidget(pre_inside_widget)
        pre_area_layout = QVBoxLayout()
        pre_area_layout.setContentsMargins(0,0,0,0)
        pre_area_layout.setSpacing(0)
        pre_area_layout.addWidget(gf.QRichLabel("pre-processing", font=gf.boldFont))
        pre_area_layout.addWidget(pre_scroll_area)
        # マップエリア
        self.map_layout = my_w.ClickableLayout(parent=self)
        map_inside_widget = QWidget()
        map_inside_widget.setLayout(self.map_layout)
        map_inside_widget.setObjectName("map_inside_widget")
        map_inside_widget.setStyleSheet("QWidget#map_inside_widget{background-color: white}")
        map_scroll_area = QScrollArea()
        map_scroll_area.setWidgetResizable(True)
        map_scroll_area.setWidget(map_inside_widget)
        map_area_layout = QVBoxLayout()
        map_area_layout.setContentsMargins(0,0,0,0)
        map_area_layout.setSpacing(0)
        map_area_layout.addWidget(gf.QRichLabel("Added Hyperspectral Data", font=gf.boldFont))
        map_area_layout.addWidget(map_scroll_area)
        # スペクトルエリア
        self.spectrum_layout = my_w.ClickableLayout(parent=self)
        spectrum_inside_widget = QWidget()
        spectrum_inside_widget.setLayout(self.spectrum_layout)
        spectrum_inside_widget.setObjectName("spectrum_inside_widget")
        spectrum_inside_widget.setStyleSheet("QWidget#spectrum_inside_widget{background-color: white}")
        spectrum_scroll_area = QScrollArea()
        spectrum_scroll_area.setWidgetResizable(True)
        spectrum_scroll_area.setWidget(spectrum_inside_widget)
        spectrum_area_layout = QVBoxLayout()
        spectrum_area_layout.setContentsMargins(0,0,0,0)
        spectrum_area_layout.setSpacing(0)
        spectrum_area_layout.addWidget(gf.QRichLabel("Added Spectrum Data", font=gf.boldFont))
        spectrum_area_layout.addWidget(spectrum_scroll_area)
        # 前処理ボタンエリア
        self.btn_p_CRR = QPushButton("CRR")
        self.btn_p_CRR.setToolTip("Cosmic Ray Removal")
        self.btn_p_CRR.setFixedWidth(50)
        self.btn_p_CRR.setEnabled(False)
        self.btn_p_NR = QPushButton("NR")
        self.btn_p_NR.setToolTip("PCA-based noise reduction")
        self.btn_p_NR.setFixedWidth(50)
        self.btn_p_NR.setEnabled(False)
        self.btn_p_revert = QPushButton("revert")
        self.btn_p_revert.setFixedWidth(100)
        self.btn_p_revert.setEnabled(False)
        self.btn_p_hide_show = QPushButton("hide/show")
        self.btn_p_hide_show.setFixedWidth(100)
        self.btn_p_hide_show.setEnabled(False)
        btnLayout_p = QHBoxLayout()
        btnLayout_p.setContentsMargins(0,0,0,0)
        btnLayout_p.addWidget(self.btn_p_CRR)
        btnLayout_p.addWidget(self.btn_p_NR)
        btnLayout_p.addStretch(1)
        btnLayout_p.addWidget(self.btn_p_hide_show)
        btnLayout_p.addWidget(self.btn_p_revert)
        # マップボタンエリア
        self.btn_m_export = QPushButton("export")
        self.btn_m_export.setFixedWidth(100)
        self.btn_m_export.setEnabled(False)
        self.btn_m_remove = QPushButton("remove")
        self.btn_m_remove.setFixedWidth(100)
        self.btn_m_remove.setEnabled(False)
        self.btn_m_hide_show = QPushButton("hide/show")
        self.btn_m_hide_show.setFixedWidth(100)
        self.btn_m_hide_show.setEnabled(False)
        btnLayout_m = QHBoxLayout()
        btnLayout_m.setContentsMargins(0,0,0,0)
        btnLayout_m.addStretch(1)
        btnLayout_m.addWidget(self.btn_m_export)
        btnLayout_m.addWidget(self.btn_m_remove)
        btnLayout_m.addWidget(self.btn_m_hide_show)
        # スペクトルボタンエリア
        self.btn_s_export = QPushButton("export")
        self.btn_s_export.setFixedWidth(100)
        self.btn_s_export.setEnabled(False)
        self.btn_s_remove = QPushButton("remove")
        self.btn_s_remove.setFixedWidth(100)
        self.btn_s_remove.setEnabled(False)
        self.btn_s_hide_show = QPushButton("hide/show")
        self.btn_s_hide_show.setFixedWidth(100)
        self.btn_s_hide_show.setEnabled(False)
        btnLayout_s = QHBoxLayout()
        btnLayout_s.setContentsMargins(0,0,0,0)
        btnLayout_s.addStretch(1)
        btnLayout_s.addWidget(self.btn_s_export)
        btnLayout_s.addWidget(self.btn_s_remove)
        btnLayout_s.addWidget(self.btn_s_hide_show)
        # レイアウト
        pre_area_layout.addLayout(btnLayout_p)
        map_area_layout.addLayout(btnLayout_m)
        spectrum_area_layout.addLayout(btnLayout_s)
        pre_area_widget = QWidget()
        policy = pre_area_widget.sizePolicy()
        policy.setVerticalStretch(4)
        pre_area_widget.setSizePolicy(policy)
        pre_area_widget.setLayout(pre_area_layout)
        map_area_widget = QWidget()
        map_area_widget.setLayout(map_area_layout)
        spectrum_area_widget = QWidget()
        spectrum_area_widget.setLayout(spectrum_area_layout)
        sub_area = QSplitter(Qt.Horizontal)
        policy = sub_area.sizePolicy()
        policy.setVerticalStretch(10)
        sub_area.setSizePolicy(policy)
        sub_area.addWidget(map_area_widget)
        sub_area.addWidget(spectrum_area_widget)
        main_area = QSplitter(Qt.Vertical)
        main_area.addWidget(pre_area_widget)
        main_area.addWidget(sub_area)
        self.resize(self.width(), 600)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.addWidget(main_area)
        # その他
        self.setFocusPolicy(Qt.StrongFocus)
        self.setLayout(self.layout)
        # イベントコネクト
        self.btn_p_CRR.clicked.connect(self.btn_CRR_clicked_p)
        self.btn_p_NR.clicked.connect(self.btn_NR_clicked_p)
        self.btn_p_revert.clicked.connect(self.btn_revert_clicked_p)
        self.btn_p_hide_show.clicked.connect(self.btn_hide_show_clicked_p)
        s_export_menu = QMenu()
        self.s_e_action_dict = {}
        self.s_e_action_dict["as spc"] = s_export_menu.addAction('as spc', functools.partial(self.btn_export_clicked_s, ext=".spc"))
        self.s_e_action_dict["as text"] = s_export_menu.addAction('as text', functools.partial(self.btn_export_clicked_s, ext=".txt"))
        self.s_e_action_dict["as info"] = s_export_menu.addAction('as info', functools.partial(self.btn_export_clicked_s, ext=".info"))
        self.btn_s_export.setMenu(s_export_menu)
        self.btn_s_remove.clicked.connect(self.btn_remove_clicked_s)
        self.btn_s_hide_show.clicked.connect(self.btn_hide_show_clicked_s)
        self.btn_m_export.clicked.connect(functools.partial(self.btn_export_clicked_m, ext=".spc"))
        self.btn_m_remove.clicked.connect(self.btn_remove_clicked_m)
        self.btn_m_hide_show.clicked.connect(self.btn_hide_show_clicked_m)
        self.setFocusPolicy(Qt.StrongFocus)
    def add_content(self, added_content):
        # レイアウト
        target_layout = getattr(self, "%s_layout"%added_content.info["content"])
        content_widget = my_w.ClickableQWidget(parent=target_layout, optional_item=added_content)
        content_widget.setFixedHeight(30)
        content_widget.addWidget(QLabel(added_content.info_to_display()))
        content_widget.addStretch(1)
        for widget in added_content.init_widgets():
            content_widget.addWidget(widget)
        content_widget.focuse_changed.connect(added_content.focus_unfocus)
        content_widget.focuse_changed.connect(functools.partial(self.half_focus_process, added_content=added_content))
        content_widget.focuse_changed.connect(functools.partial(getattr(self, "%s_focus_changed"%added_content.info["content"]), window_type=added_content.info["type"]))
        target_layout.insertWidget(target_layout.count()-1, content_widget)
        return content_widget
    def btnSetEnabled(self, enable=None, target_layout=None, key_list=None):
        for key in key_list:
            cur_btn = getattr(self, "btn_{0}_{1}".format(target_layout, key))
            cur_btn.setEnabled(enable)
            cur_btn.repaint()
    def preprocess_focus_changed(self, event=None, window_type=None):
        # とりあえず全て disable
        self.btnSetEnabled(enable=False, target_layout="p", key_list=["revert", "hide_show"])
        # フォーカスされなかった場合
        if not event:
            return
        # フォーカスされた場合
        if window_type == "POI":
            self.btnSetEnabled(enable=True, target_layout="p", key_list=["revert", "hide_show"])
        elif window_type in ("NR", "CRR", "range-setting"):
            pass
        else:
            raise Exception("unknown button type")
    def spectrum_focus_changed(self, event=None, window_type=None):
        # とりあえず全て disable
        self.btnSetEnabled(enable=False, target_layout="s", key_list=["export", "remove", "hide_show"])
        # フォーカスされなかったた場合
        if not event:
            return
        # フォーカスされた場合
        if window_type == "original":
            self.btnSetEnabled(enable=True, target_layout="s", key_list=["export", "hide_show"])
            self.s_e_action_dict["as info"].setEnabled(False)
        elif window_type in ("added", "subtracted"):
            self.btnSetEnabled(enable=True, target_layout="s", key_list=["export", "remove", "hide_show"])
            self.s_e_action_dict["as info"].setEnabled(False)
        elif window_type == "unmixed":
            self.btnSetEnabled(enable=True, target_layout="s", key_list=["export", "remove", "hide_show"])
            self.s_e_action_dict["as info"].setEnabled(True)
        elif window_type == "POI":
            self.btnSetEnabled(enable=True, target_layout="s", key_list=["remove"])
            self.s_e_action_dict["as info"].setEnabled(False)
        else:
            print(window_type)
            raise Exception("unknown button type")
    def map_focus_changed(self, event=None, window_type=None):
        # とりあえず全て disable
        self.btnSetEnabled(enable=False, target_layout="m", key_list=["export", "remove", "hide_show"])
        # フォーカスされなかったた場合
        if not event:
            return
        # フォーカスされた場合
        if window_type == "added":
            self.btnSetEnabled(enable=True, target_layout="m", key_list=["remove", "hide_show"])
        elif window_type == "unmixed":
            self.btnSetEnabled(enable=True, target_layout="m", key_list=["export", "remove", "hide_show"])
        elif window_type == "subtracted":
            self.btnSetEnabled(enable=True, target_layout="m", key_list=["export", "remove", "hide_show"])
        else:
            raise Exception("unknown button type")
    def focus_content(self, added_content):
        target_layout = getattr(self, "{0}_layout".format(added_content.info["content"]))
        for w in target_layout.get_all_items():
            if w.optional_item == added_content:
                w.focus()        
    def half_focus_process(self, added_content):
        target_layout = getattr(self, "{0}_layout".format(added_content.info["content"]))
        try:
            abs_id = added_content.info["data"][2].abs_id
        except:
            abs_id = None
        for w in target_layout.get_all_items():
            # half focus を使う場合
            if abs_id is not None:
                try:
                    # abs_id が同じものを
                    if w.optional_item.info["data"][2].abs_id == abs_id:
                        # 自分自身でなければ、half focuesed にする or しない
                        if w.optional_item != added_content:
                            w.half_focus(added_content.focused)
                        continue
                except:
                    pass
            # half focus を使わない場合
            if w.half_focus:
                w.half_focus(False)
    # ボタン系
    def get_parent_window(self):
        # original spectrum から元 window をたどる。
        return self.spectrum_layout.itemAt(0).widget().optional_item.parent_window
    def btn_CRR_clicked_p(self, event=None):
        # CRRが既に登録済みである場合、削除
        for w in self.preprocess_layout.get_all_items():
            if w.optional_item.info["type"] == "CRR":
                self.btn_revert_clicked_p(mode="update")
                break
        # 登録がなかった場合、original spectrum から元 window をたどる。
        else:
            self.get_parent_window().toolbar_layout.CRR_master(mode="update")
    def btn_NR_clicked_p(self, event=None):
        # NRが既にある場合は、データを開き直すよう要求
        for w in self.preprocess_layout.get_all_items():
            if w.optional_item.info["type"] == "NR":
                self.btn_revert_clicked_p(mode="update")
                break
        else:
            self.get_parent_window().toolbar_layout.NR_master(mode="update")
    def btn_revert_clicked_p(self, event=None, mode="just revert"):
        if self.preprocess_layout.current_focused_idx is not None:
            # お尻からしか消させない！
            if self.preprocess_layout.current_focused_idx != self.preprocess_layout.count() - 2:
                warning_popup = popups.WarningPopup("Pre-processes can ony be reverted from the end.")
                warning_popup.exec_()
                return
            cur_content_widget = self.preprocess_layout.get_current_item()
            log = cur_content_widget.optional_item.remove_item(mode=mode)
            if log == "not executed":
                return log
            # tableからの削除
            self.preprocess_layout.remove_current_focused_item()
            # ボタンをdisable
            self.preprocess_focus_changed(event=False)
    def btn_hide_show_clicked_p(self, event=None):
        if self.preprocess_layout.current_focused_idx is not None:
            self.preprocess_layout.get_current_item().optional_item.hide_show_item()
    def btn_export_clicked_s(self, event=None, ext=None):
        cur_item = self.spectrum_layout.get_current_item().optional_item
        if self.spectrum_layout.current_focused_idx is not None:
            # abs_id がある場合は、それ関連のものを全て export する
            isUnmixed = cur_item.info["type"] == "unmixed"
            if isUnmixed:
                abs_id = cur_item.info["data"][2].abs_id
                iter_list = []
                for w in self.spectrum_layout.get_all_items():
                    if w.optional_item.info["type"] == "unmixed":
                        if w.optional_item.info["data"][2].abs_id == abs_id:
                            iter_list.append(w.optional_item)
            else:
                iter_list = [cur_item]
            if ext in (".spc", ".txt"):
                for idx, i in enumerate(iter_list):
                    ask = (idx == 0)
                    i.export_spectrum(ext, ask=ask)
            elif ext == ".info":
                if cur_item.info["type"] != "unmixed":
                    raise Exception("unknown type")
                cur_item.export_information(ext, ask=True, **self.get_standard_info_list_s(abs_id=abs_id))
    def get_standard_info_list_s(self, abs_id):
        standard_info_list = []
        for w in self.spectrum_layout.get_all_items():
            try:
                cur_unmixed_data = w.optional_item.info["data"][2]
                if (cur_unmixed_data.abs_id == abs_id) & (cur_unmixed_data.standard_type not in ("bd", "ts")):
                    standard_info_list.append("_".join(w.optional_item.info_to_display().split()))
            except:
                pass
        def path_name_func(path):
            # example: 20200407_LPCd31OA_10-03_1_unmixed(2600.0-3200.0, #1).info
            matched = re.fullmatch("(.*\(.*), #.*(\)\.info)", path)
            print(matched[1] + matched[2])
            return matched[1] + matched[2]
        return {"standard_info_list":standard_info_list, "path_name_func":path_name_func}
    def btn_remove_clicked_s(self, event=None):
        if self.spectrum_layout.current_focused_idx is not None:
            cur_content_widget = self.spectrum_layout.get_current_item()
            idxes_to_remove = cur_content_widget.optional_item.remove_item()
            # Tableからの削除
            if idxes_to_remove is None:
                self.spectrum_layout.remove_current_focused_item()
            else:
                self.spectrum_layout.remove_items(idxes_to_remove)
            # ボタンをdisable
            self.btnSetEnabled(enable=False, target_layout="s", key_list=["export", "remove", "hide_show"])
    def btn_hide_show_clicked_s(self, event=None):
        if self.spectrum_layout.current_focused_idx is not None:
            self.spectrum_layout.get_current_item().optional_item.hide_show_item()
    def btn_export_clicked_m(self, event=None, ext=None):
        if self.map_layout.current_focused_idx is not None:
            self.map_layout.get_current_item().optional_item.export_spectrum(ext, ask=True)
    def btn_remove_clicked_m(self, event=None):
        if self.map_layout.current_focused_idx is not None:
            cur_focused_window = self.map_layout.get_current_item().optional_item.parent_window
            idxes_to_remove = self.map_layout.get_current_item().optional_item.remove_item()
            # Tableからの削除
            if idxes_to_remove is None:
                self.map_layout.remove_current_focused_item()
            else:
                self.map_layout.remove_items(idxes_to_remove)
            # ボタンを disable
            self.btnSetEnabled(enable=False, target_layout="m", key_list=["export", "remove", "hide_show"])
            if self.map_layout.count() == 1:
                cur_focused_window.map_widget.all_images_were_removed()
    def btn_hide_show_clicked_m(self, event=None):
        if self.map_layout.current_focused_idx is not None:
            self.map_layout.get_current_item().optional_item.hide_show_item()
    # ウィンドウ間のフォーカス移動
    def data_window_closed(self):
        print("window closed")
        self.map_layout.remove_all()
        self.spectrum_layout.remove_all()
        self.preprocess_layout.remove_all()
        self.btnSetEnabled(enable=False, target_layout="p", key_list=["NR", "CRR"])
        self.btnSetEnabled(enable=False, target_layout="s", key_list=["export", "remove", "hide_show"])
        self.btnSetEnabled(enable=False, target_layout="m", key_list=["export", "remove", "hide_show"])
    def window_focus_changed(self, window):
        print("window_focus_changed")
        if window.window_type in ("t"):
            return
        # レイアウトから一旦全て削除
        self.map_layout.remove_all()
        self.spectrum_layout.remove_all()
        self.preprocess_layout.remove_all()
        # レイアウトに追加
        if window.window_type in ("main", "b"):
            pass
        elif window.window_type in ("s", "ms", "u"):
            for content in window.toolbar_layout.added_content_map_list:
                content_widget = self.add_content(content)
                if content.focused:
                    content_widget.focus()
            for content in window.toolbar_layout.added_content_spectrum_list:
                content_widget = self.add_content(content)
                if content.focused:
                    content_widget.focus()
            for content in window.toolbar_layout.added_content_preprocess_list:
                content_widget = self.add_content(content)
                if content.focused:
                    content_widget.focus()
        else:
            print(window.window_type)
            raise Exception("unknown window type")
        # ボタンの show, enable, disable
        self.btnSetEnabled(enable=False, target_layout="p", key_list=["NR", "CRR"])
        self.btnSetEnabled(enable=False, target_layout="s", key_list=["export", "remove", "hide_show"])
        self.btnSetEnabled(enable=False, target_layout="m", key_list=["export", "remove", "hide_show"])
        if window.window_type == "ms":
            self.btn_p_CRR.setEnabled(True)
            self.btn_p_NR.setEnabled(True)
        elif window.window_type in ("s", "b"):
            self.btn_p_CRR.setEnabled(False)
            self.btn_p_NR.setEnabled(False)
        elif window.window_type == "u":
            self.btn_p_CRR.setEnabled(False)
            self.btn_p_NR.setEnabled(False)
        elif window.window_type in ("main", "t"):
            pass
        else:
            raise Exception("unknown window type")
        # self.btn_p_CRR.repaint()
        # self.btn_p_NR.repaint()
    def bring_to_front(self):
        if not self.isVisible():
            self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.raise_()
        self.activateWindow()
    def grab_focus(self):
        self.setFocus()
    def focusInEvent(self, event=None):
        self.parent.focusChanged(self)
    def focusOutEvent(self, event=None):
        pass
    def closeEvent(self, event=None):
        self.hide()
        event.ignore()











