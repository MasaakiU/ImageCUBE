# -*- Coding: utf-8 -*-

import os
import functools
import re
import types

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
    QDialog, 
    QMainWindow, 
    )
from PyQt5.QtCore import (
    Qt, 
    QVariant, 
    )
import pyqtgraph as pg

from . import general_functions as gf
from . import my_widgets as my_w
from . import popups

class MapSpectTable(QMainWindow):
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
        btnLayout_p.setSpacing(7)
        btnLayout_p.addWidget(self.btn_p_CRR)
        btnLayout_p.addWidget(self.btn_p_NR)
        btnLayout_p.addStretch(1)
        btnLayout_p.addWidget(self.btn_p_hide_show)
        btnLayout_p.addWidget(self.btn_p_revert)
        # マップボタンエリア
        btn_width = 97
        self.btn_m_export = my_w.CustomMenuButton("export", icon_path=gf.icon_path, divide=False)
        self.btn_m_export.setFixedWidth(btn_width)
        self.btn_m_export.setEnabled(False)
        self.btn_m_remove = my_w.CustomMenuButton("remove", icon_path=gf.icon_path, divide=True)
        self.btn_m_remove.setFixedWidth(btn_width)
        self.btn_m_remove.setEnabled(False)
        self.btn_m_hide_show = QPushButton("hide/show")#, divide=True)
        self.btn_m_hide_show.setFixedWidth(btn_width)
        self.btn_m_hide_show.setEnabled(False)
        self.btn_m_others = my_w.CustomMenuButton("", icon_path=gf.icon_path, divide=False)
        self.btn_m_others.setFixedWidth(35)
        self.btn_m_others.setEnabled(False)
        btnLayout_m = QHBoxLayout()
        btnLayout_m.setContentsMargins(0,0,0,0)
        btnLayout_m.setSpacing(7)
        btnLayout_m.addStretch(1)
        btnLayout_m.addWidget(self.btn_m_export)
        btnLayout_m.addWidget(self.btn_m_remove)
        btnLayout_m.addWidget(self.btn_m_hide_show)
        btnLayout_m.addWidget(self.btn_m_others)
        # スペクトルボタンエリア
        self.btn_s_export = my_w.CustomMenuButton("export", icon_path=gf.icon_path, divide=False)
        self.btn_s_export.setFixedWidth(btn_width)
        self.btn_s_export.setEnabled(False)
        self.btn_s_remove = my_w.CustomMenuButton("remove", icon_path=gf.icon_path, divide=True)
        self.btn_s_remove.setFixedWidth(btn_width)
        self.btn_s_remove.setEnabled(False)
        self.btn_s_hide_show = my_w.CustomMenuButton("hide/show", icon_path=gf.icon_path, divide=True)
        self.btn_s_hide_show.setFixedWidth(btn_width)
        self.btn_s_hide_show.setEnabled(False)
        self.btn_s_others = my_w.CustomMenuButton("", icon_path=gf.icon_path, divide=False)
        self.btn_s_others.setFixedWidth(35)
        self.btn_s_others.setEnabled(False)
        btnLayout_s = QHBoxLayout()
        btnLayout_s.setContentsMargins(0,0,0,0)
        btnLayout_s.setSpacing(7)
        btnLayout_s.addStretch(1)
        btnLayout_s.addWidget(self.btn_s_export)
        btnLayout_s.addWidget(self.btn_s_remove)
        btnLayout_s.addWidget(self.btn_s_hide_show)
        btnLayout_s.addWidget(self.btn_s_others)
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
        # メニュー
        s_export_menu = QMenu()
        self.s_e_action_dict = {}
        self.s_e_action_dict["as spc"] = s_export_menu.addAction('as spc', functools.partial(self.btn_export_clicked_s, ext=".spc"))
        self.s_e_action_dict["as text"] = s_export_menu.addAction('as text', functools.partial(self.btn_export_clicked_s, ext=".txt"))
        self.s_e_action_dict["as info"] = s_export_menu.addAction('as info', functools.partial(self.btn_export_clicked_s, ext=".info"))
        s_remove_menu = QMenu()
        s_remove_menu.addAction('remove all', self.remove_all_clicked_s)
        s_hide_show_menu = QMenu()
        s_hide_show_menu.addAction('hide/show all', functools.partial(self.hide_show_all_clicked, target_layout="spectrum"))
        s_others_menu = QMenu()
        s_others_menu.addAction("add custom name", functools.partial(self.add_custom_name_clicked, map_or_spc="spc"))
        s_others_menu.addAction("remove custom name", functools.partial(self.add_custom_name_clicked, map_or_spc="spc", text=""))
        m_export_menu = QMenu()
        self.m_e_action_dict = {}
        self.m_e_action_dict["as tiff \& svg"] = m_export_menu.addAction('as tiff / svg', functools.partial(self.btn_export_clicked_m, ext=".tiff .svg"))
        self.m_e_action_dict["as spc"] = m_export_menu.addAction('as spc', functools.partial(self.btn_export_clicked_m, ext=".spc"))
        m_remove_menu = QMenu()
        m_remove_menu.addAction('remove all', self.remove_all_clicked_m)
        m_others_menu = QMenu()
        m_others_menu.addAction("add custom name", functools.partial(self.add_custom_name_clicked, map_or_spc="map"))
        m_others_menu.addAction("remove custom name", functools.partial(self.add_custom_name_clicked, map_or_spc="map", text=""))
        # m_hide_show_menu = QMenu()
        # m_hide_show_menu.addAction('hide/show all', functools.partial(self.hide_show_all_clicked, target_layout="map"))
        # イベントコネクト
        self.btn_p_CRR.clicked.connect(self.btn_CRR_clicked_p)
        self.btn_p_NR.clicked.connect(self.btn_NR_clicked_p)
        self.btn_p_revert.clicked.connect(self.btn_revert_clicked_p)
        self.btn_p_hide_show.clicked.connect(functools.partial(self.btn_hide_show_clicked, target_layout="preprocess"))
        self.btn_s_export.setMenu(s_export_menu)
        self.btn_s_remove.clicked.connect(self.btn_remove_clicked_s)
        self.btn_s_remove.setMenu(s_remove_menu)
        self.btn_s_hide_show.clicked.connect(functools.partial(self.btn_hide_show_clicked, target_layout="spectrum"))
        self.btn_s_hide_show.setMenu(s_hide_show_menu)
        self.btn_s_others.setMenu(s_others_menu)
        self.btn_m_export.setMenu(m_export_menu)
        self.btn_m_remove.clicked.connect(self.btn_remove_clicked_m)
        self.btn_m_remove.setMenu(m_remove_menu)
        self.btn_m_hide_show.clicked.connect(functools.partial(self.btn_hide_show_clicked, target_layout="map"))
        self.btn_m_others.setMenu(m_others_menu)
        # その他
        self.setFocusPolicy(Qt.StrongFocus)
        # self.setLayout(self.layout)
        # tab barが現れるのを防ぐため、QWidget ではなく QMainWindow で window を作成し、TabBarを消去した。
        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)
        self.setUnifiedTitleAndToolBarOnMac(True)
    def add_content(self, added_content):
        # レイアウト
        target_layout = getattr(self, "%s_layout"%added_content.info["content"])
        content_widget = my_w.ClickableQWidget(parent=target_layout, optional_item=added_content)
        for widget in added_content.pre_widgets():
            content_widget.addWidget(widget)
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
        if window_type in ("CRR", "POI"):
            self.btnSetEnabled(enable=True, target_layout="p", key_list=["revert", "hide_show"])
        elif window_type in ("NR"):
            self.btnSetEnabled(enable=True, target_layout="p", key_list=["revert"])
        elif window_type in ("SCL", "Custom"):
            self.btnSetEnabled(enable=True, target_layout="p", key_list=["hide_show"])
        elif window_type in ("range-setting", "SIZE"):
            pass
        else:
            print(window_type)
            raise Exception("unknown button type")
    def spectrum_focus_changed(self, event=None, window_type=None):
        # とりあえず全て disable
        self.btnSetEnabled(enable=False, target_layout="s", key_list=["export", "remove", "hide_show", "others"])
        # フォーカスされなかったた場合
        if not event:
            return
        # フォーカスされた場合
        if window_type == "original":
            self.btnSetEnabled(enable=True, target_layout="s", key_list=["export", "hide_show", "others"])
            self.s_e_action_dict["as info"].setEnabled(False)
        elif window_type in ("added", "subtracted"):
            self.btnSetEnabled(enable=True, target_layout="s", key_list=["export", "remove", "hide_show", "others"])
            self.s_e_action_dict["as info"].setEnabled(False)
        elif window_type == "unmixed":
            self.btnSetEnabled(enable=True, target_layout="s", key_list=["export", "remove", "hide_show", "others"])
            self.s_e_action_dict["as info"].setEnabled(True)
        elif window_type == "POI":
            self.btnSetEnabled(enable=True, target_layout="s", key_list=["remove"])
            self.s_e_action_dict["as info"].setEnabled(False)
        else:
            print(window_type)
            raise Exception("unknown button type")
    def map_focus_changed(self, event=None, window_type=None):
        # とりあえず全て disable
        self.btnSetEnabled(enable=False, target_layout="m", key_list=["export", "remove", "hide_show", "others"])
        # フォーカスされなかったた場合
        if not event:
            return
        # フォーカスされた場合
        if window_type in ("added", "unmixed", "subtracted"):
            self.btnSetEnabled(enable=True, target_layout="m", key_list=["export", "remove", "hide_show", "others"])
            self.m_e_action_dict["as spc"].setEnabled(True)
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
            abs_id = added_content.info["advanced_data"].abs_id
        except:
            abs_id = None
        for w in target_layout.get_all_items():
            # half focus を使う場合
            if abs_id is not None:
                try:
                    # abs_id が同じものを
                    if w.optional_item.info["advanced_data"].abs_id == abs_id:
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
    def btn_export_clicked_s(self, event=None, ext=None):
        if self.spectrum_layout.current_focused_idx is None:
            return
        self.get_parent_window().toolbar_layout.export_spectrum(ext=ext, ask=True)
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
    def remove_all_clicked_s(self, event=None):
        # original は消さない
        for w in self.spectrum_layout.get_all_items()[1:]:
            w.optional_item.remove_item()
        # Tableからの削除
        self.spectrum_layout.remove_items(range(self.spectrum_layout.count() - 1)[1:])
        # ボタンをdisable
        self.btnSetEnabled(enable=False, target_layout="s", key_list=["export", "remove", "hide_show"])
    def btn_export_clicked_m(self, event=None, ext=None):
        if self.map_layout.current_focused_idx is None:
            return
        self.get_parent_window().toolbar_layout.export_map(ext=ext, ask=True)
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
    def remove_all_clicked_m(self, event=None):
        for w in self.map_layout.get_all_items():
            w.optional_item.remove_item()
        # Tableからの削除
        self.map_layout.remove_items(range(self.map_layout.count() - 1))
        # ボタンをdisable
        self.btnSetEnabled(enable=False, target_layout="m", key_list=["export", "remove", "hide_show"])
    def btn_hide_show_clicked(self, event=None, target_layout=None):
        target_layout = getattr(self, "{0}_layout".format(target_layout))
        if target_layout.current_focused_idx is not None:
            target_layout.get_current_item().optional_item.hide_show_item()
    def hide_show_all_clicked(self, event=None, target_layout=None):
        for w in getattr(self, "{0}_layout".format(target_layout)).get_all_items():
            w.optional_item.hide_show_item()
    def add_custom_name_clicked(self, event=None, map_or_spc=None, text=None):
        target_content = getattr(self.get_parent_window(), "cur_displayed_{0}_content".format(map_or_spc))
        if text is None:
            custom_name = target_content.info.get("custom name", "")
            text_popup = popups.TextSettingsPopup(parent=self, initial_txt=custom_name, label="Enter custom name", title="custom name settings")
            done = text_popup.exec_()
            text = text_popup.text()
        else:
            done = 1
        if done:
            target_content.update_custom_name(text)
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
        # ボタンを disable
        self.btnSetEnabled(enable=False, target_layout="p", key_list=["NR", "CRR", "revert", "hide_show"])
        self.btnSetEnabled(enable=False, target_layout="s", key_list=["export", "remove", "hide_show", "others"])
        self.btnSetEnabled(enable=False, target_layout="m", key_list=["export", "remove", "hide_show", "others"])
        # レイアウトに追加
        if window.window_type in ("main", "b"):
            pass
        elif window.window_type in ("s", "ms", "u"):
            for target_layout_name in ["spectrum", "map", "preprocess"]:
                target_content_list = getattr(window.toolbar_layout, "added_content_{0}_list".format(target_layout_name))
                content_to_focus = None
                for content in target_content_list:
                    content_widget = self.add_content(content)
                    if content.focused:
                        content_to_focus = content_widget
                # 全て add_content し終わってから、focus する。
                if content_to_focus is not None:
                    content_to_focus.focus()
        else:
            raise Exception("unknown window type: {0}".format(window.window_type))
        # その他のボタン
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
        self.btn_p_CRR.repaint()
        self.btn_p_NR.repaint()
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

class PseudoWindow(QWidget):
    def __init__(self, spc_file, added_content):
        super().__init__()
        self.spectrum_widget = pg.PlotWidget()
        self.spectrum_widget.plotItem.vb.addedItems = []
        self.spectrum_widget.plotItem.vb.addedItems.append(added_content.item)
        self.spectrum_widget.spc_file = spc_file
class OptionalMST(QWidget):
    def __init__(self, true_parent_window=None, spc_file=None, added_content=None):
        self.true_parent_window = true_parent_window
        super().__init__()
        self.parent_window = PseudoWindow(spc_file, added_content=added_content)
        self.master_layout = QVBoxLayout()
        self.setLayout(self.master_layout)
        for func_name, kwargs in self.parent_window.spectrum_widget.spc_file.log_dict[b"prep_order"]:
            func = getattr(self, func_name)
            func(**kwargs)
        # 本来の MapSpectTabel の added_content のクリックに相当
        btn_show_hide = QPushButton("show_hide")
        btn_show_hide.clicked.connect(self.btn_show_hide_clicked)
        self.master_layout.addWidget(btn_show_hide)
        self.setAttribute(Qt.WA_DeleteOnClose)
    def pre_widgets(self):
        return []
    def init_widgets(self):
        return []
    def btn_show_hide_clicked(self, event):
        self.added_content.hide_show_item()
    def CustomBtn_master(self, mode=None, params={}):
        self.item = params["item"]
        for func_name, func in params["func_dict"].items():
            setattr(self, func_name, types.MethodType(func, self))
        pre_widgets = self.pre_widgets()
        init_widgets = self.init_widgets()
        layout = QHBoxLayout()
        for widget in pre_widgets + init_widgets:
            layout.addWidget(widget)
        self.master_layout.addLayout(layout)
        # [
        #     [
        #         'CustomBtn_master', {
        #             'mode': 'init_s', 
        #             'params': {
        #                 'item': <Modules.my_widgets.PlotDataItems object at 0x7fb4e21a2ee8>, 
        #                 'detail': 'interpolated', 
        #                 'draw': 'none', 
        #                 'data': [None, None], 
        #                 'func_dict': {'init_widgets': <function init_data.<locals>.init_widgets at 0x7fb4d1f58f28>, 
        #                 'conc_spbx_value_changed': <function init_data.<locals>.conc_spbx_value_changed at 0x7fb4d1f60048>, 
        #                 'contour_spbx_changed': <function init_data.<locals>.contour_spbx_changed at 0x7fb4d1f600d0>}, 
        #                 'master_processes': ["self.parent.spectrum_widget.addItem(params['item'])"]
        #             }
        #         }
        #     ]
        # ]







