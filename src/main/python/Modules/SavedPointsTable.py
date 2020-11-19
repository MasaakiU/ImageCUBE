# -*- Coding: utf-8 -*-

import functools
import types


from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout,  
    QSizePolicy, 
    QSpacerItem, 
    QDesktopWidget, 
    QMenuBar, 
    QScrollArea, 
    QLabel, 
    QPushButton, 
    QSplitter, 
    QLineEdit, 
    QMainWindow, 
    )
from PyQt5.QtCore import Qt

from . import general_functions as gf
from . import my_widgets as my_w
from . import popups
from . import draw

class PointsOfInterestManager(QMainWindow):
    def __init__(self, parent=None):
        self.parent = parent
        self.window_type = "t"
        self.allow_closing = False
        super().__init__()
        self.setWindowTitle("Point Of Interest Manager")
        self.poi_settings_popups = None
        # Saved Points エリア
        self.poi_layout = my_w.ClickableLayout(parent=self)
        poi_inside_widget = QWidget()
        poi_inside_widget.setLayout(self.poi_layout)
        poi_inside_widget.setObjectName("poi_inside_widget")
        poi_inside_widget.setStyleSheet("QWidget#poi_inside_widget{background-color: white}")
        poi_scroll_area = QScrollArea()
        poi_scroll_area.setWidgetResizable(True)
        poi_scroll_area.setWidget(poi_inside_widget)
        poi_area_layout = QVBoxLayout()
        poi_area_layout.setContentsMargins(0,0,0,0)
        poi_area_layout.setSpacing(0)
        poi_area_layout.addWidget(gf.QRichLabel("Saved Points List", font=gf.boldFont))
        poi_area_layout.addWidget(poi_scroll_area)
        # Saved Points ボタンエリア
        self.btn_poi_add = QPushButton("+")
        self.btn_poi_add.setFixedWidth(50)
        self.btn_poi_add.setEnabled(False)
        self.btn_poi_del = QPushButton("-")
        self.btn_poi_del.setFixedWidth(50)
        self.btn_poi_del.setEnabled(False)
        self.btn_poi_mod = QPushButton("modify")
        self.btn_poi_mod.setFixedWidth(100)
        self.btn_poi_mod.setEnabled(False)
        btnLayout_poi = QHBoxLayout()
        btnLayout_poi.setContentsMargins(0,0,0,0)
        btnLayout_poi.addWidget(self.btn_poi_mod)
        btnLayout_poi.addStretch(1)
        btnLayout_poi.addWidget(self.btn_poi_add)
        btnLayout_poi.addWidget(QLabel("  "))
        btnLayout_poi.addWidget(self.btn_poi_del)
        # レイアウト
        poi_area_layout.addLayout(btnLayout_poi)
        self.resize(300, 450)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.addLayout(poi_area_layout)
        # その他
        self.setFocusPolicy(Qt.StrongFocus)
        # self.setLayout(self.layout)
        # tab barが現れるのを防ぐため、QWidget ではなく QMainWindow で window を作成し、TabBarを消去した。
        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)
        self.setUnifiedTitleAndToolBarOnMac(True)
        # イベントコネクト
        self.btn_poi_add.clicked.connect(functools.partial(self.btn_poi_mod_add_clicked, mode="add"))
        self.btn_poi_del.clicked.connect(self.btn_poi_del_clicked)
        self.btn_poi_mod.clicked.connect(functools.partial(self.btn_poi_mod_add_clicked, mode="mod"))
        self.setFocusPolicy(Qt.StrongFocus)
    def add_poi(self, poi_info):
        # レイアウト
        content_widget = my_w.ClickableQWidget(parent=self.poi_layout, optional_item=poi_info)
        content_widget.setFixedHeight(30)
        content_widget.addWidget(QLabel(" {0}\t{1}".format(poi_info.poi_key, list(poi_info.poi_data))))
        content_widget.addStretch(1)
        content_widget.focuse_changed.connect(poi_info.focus_unfocus)
        content_widget.focuse_changed.connect(self.poi_focus_changed)
        self.poi_layout.insertWidget(self.poi_layout.count()-1, content_widget)
        return content_widget
    def btnSetEnabled(self, enable=None, key_list=None):
        for key in key_list:
            cur_btn = getattr(self, "btn_poi_{0}".format(key))
            cur_btn.setEnabled(enable)
            cur_btn.repaint()
    def del_poi(self):
        if self.poi_layout.current_focused_idx is not None:
            cur_widget = self.poi_layout.get_current_item()
            poi_info = cur_widget.optional_item
            self.poi_layout.remove_current_focused_item()
            self.poi_focus_changed(event=False)
            return poi_info
    def poi_focus_changed(self, event=None):
        self.btnSetEnabled(enable=False, key_list=["mod", "del", "add"])
        self.focusInEvent() # widgetをクリックした場合、window focus が更新されない。
        # フォーカスされた場合
        if event:
            self.btnSetEnabled(enable=True, key_list=["mod", "del", "add"])
        else:
            self.btnSetEnabled(enable=True, key_list=["add"])
    # ボタン系
    def get_parent_window(self):
        return self.parent.map_spect_table.get_parent_window()
    def execute_poi_add_fm_macro(self, event=None, poi_key=None, poi_data=None):
        poi_info = draw.POI_Info(poi_key=poi_key, poi_data=poi_data, parent_window=self.get_parent_window())
        self.get_parent_window().toolbar_layout.POI_master(mode="add", poi_info=poi_info)  # 名前が重複する場合は、予め del されてるので、単純に add で OK
        # 最後に追加したものをフォーカスする。
        self.window_focus_changed(poi_info.parent_window)
        self.poi_layout.itemAt(self.poi_layout.count() - 2).widget().focus()
        return "continue"
    def btn_poi_del_clicked(self, event=None):
        poi_info = self.del_poi()
        self.get_parent_window().toolbar_layout.POI_master(mode="del", poi_info=poi_info)
    def btn_poi_mod_add_clicked(self, event=None, mode=None):
        if mode == "mod":
            poi_info = self.poi_layout.get_current_item().optional_item
        elif mode == "add":
            parent_window = self.get_parent_window()
            # 被らない poi_key を探す
            poi_dict = parent_window.spectrum_widget.spc_file.log_dict[b"point_of_interest_dict"]
            idx = 1
            while "poi{0}".format(idx) in poi_dict.keys():
                idx += 1
            poi_key = "poi{0}".format(idx)
            poi_data = (parent_window.spectrum_widget.cur_x, parent_window.spectrum_widget.cur_y)
            poi_info = draw.POI_Info(poi_key=poi_key, poi_data=poi_data, parent_window=parent_window)
        else:
            raise Exception("unknown mode: {0}".format(mode))
        # popup
        self.poi_settings_popups = popups.PoiSettingsPopup(
            parent=poi_info.parent_window, 
            initial_values=poi_info.poi_data, 
            labels=("x", "y"), 
            title="POI setting", 
            double=False, 
            poi_key=poi_info.poi_key
            )
        self.poi_settings_popups.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.poi_settings_popups.set_spinbox_ranges_fm_parent()
        # イベントコネクト・表示
        def pressedOK(self_, event):
            ###
            # poi_key
            ###
            new_poi_key = self_.poi_key.text()
            new_poi_loc = self_.values()
            # 名前にスペースはNG
            if " " in new_poi_key:
                warning_popup = popups.WarningPopup("Spaces are not allowed in the name.")
                warning_popup.exec_()
                return
            # 無名もNG
            elif new_poi_key == "":
                warning_popup = popups.WarningPopup("Empty name is not allowed.")
                warning_popup.exec_()
                return
            # 同じ名前もNG
            if (new_poi_key in [w.optional_item.poi_key for w in self.poi_layout.get_all_items()]) & (new_poi_key != poi_info.poi_key):
                warning_poopup = popups.WarningPopup("The name {0} is already taken. Please choose a different name.".format(new_poi_key), "WARNING")
                warning_poopup.exec_()
                return
            # バイナリファイル処理
            old_poi_key = poi_info.poi_key
            poi_info.poi_key = new_poi_key
            poi_info.poi_data = new_poi_loc    # poi_loc update
            poi_info.parent_window.toolbar_layout.POI_master(mode=mode, poi_info=poi_info, old_poi_key=old_poi_key)
            # ラベル処理
            poi_info.parent_window.map_widget.scene().sigMouseClicked.disconnect(self_.on_map_widget_click)
            self.window_focus_changed(poi_info.parent_window)
            self_.done(1)
        def pressedCancel(self_, event):
            poi_info.parent_window.map_widget.scene().sigMouseClicked.disconnect(self_.on_map_widget_click)
            self_.done(0)
        poi_info.parent_window.map_widget.scene().sigMouseClicked.connect(self.poi_settings_popups.on_map_widget_click)
        self.poi_settings_popups.disconnect_btns()
        self.poi_settings_popups.pressedOK = types.MethodType(pressedOK, self.poi_settings_popups)
        self.poi_settings_popups.pressedCancel = types.MethodType(pressedCancel, self.poi_settings_popups)
        self.poi_settings_popups.reconnect_btns()
        # 表示
        self.poi_settings_popups.show()
    # 情報取得
    def get_poi_idx(self, poi_key):
        for idx in range(self.poi_layout.count() - 1):
            widget = self.poi_layout.itemAt(idx).widget()
            if widget.optional_item.poi_key == poi_key:
                return idx
        else:
            return None
    def get_poi_info(self, poi_key):
        for idx in range(self.poi_layout.count() - 1):
            widget = self.poi_layout.itemAt(idx).widget()
            if widget.optional_item.poi_key == poi_key:
                return widget.optional_item
        else:
            return None
    # フォーカス
    def data_window_closed(self):
        print("window closed, saved points table")
        self.poi_layout.remove_all()
    def window_focus_changed(self, window):
        print("window_focus_changed poi")
        if window.window_type in ("t"):
            return
        # レイアウトから一度すべて削除
        self.poi_layout.remove_all()
        print("#####  removed")
        self.btnSetEnabled(enable=False, key_list=["mod", "del", "add"])
        if window.window_type in ("main", "b", "s", "u"):
            pass
        elif window.window_type in ("ms"):
            print(window.toolbar_layout.added_info_poi_list)
            self.btnSetEnabled(enable=True, key_list=["add"])
            for poi_info in window.toolbar_layout.added_info_poi_list:
                content_widget = self.add_poi(poi_info)
                if content_widget.optional_item.focused:
                    content_widget.optional_item.allow_loc_update = False
                    content_widget.unfocus()
                    content_widget.optional_item.allow_loc_update = True
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











