# -*- Coding: utf-8 -*-

import functools


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
    )
from PyQt5.QtCore import Qt

from . import general_functions as gf
from . import my_widgets as my_w
from . import popups

class PointsOfInterestManager(QWidget):
    def __init__(self, parent=None):
        self.parent = parent
        self.window_type = "t"
        self.allow_closing = False
        super().__init__()
        self.setWindowTitle("Point Of Interest Manager")
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
        self.btn_poi_del = QPushButton("-")
        self.btn_poi_del.setFixedWidth(50)
        self.btn_poi_del.setEnabled(False)
        self.btn_poi_rename = QPushButton("rename")
        self.btn_poi_rename.setFixedWidth(100)
        self.btn_poi_rename.setEnabled(False)
        self.btn_poi_changePos = QPushButton("re-position")
        self.btn_poi_changePos.setFixedWidth(100)
        self.btn_poi_changePos.setEnabled(False)
        btnLayout_poi = QHBoxLayout()
        btnLayout_poi.setContentsMargins(0,0,0,0)
        btnLayout_poi.addWidget(self.btn_poi_rename)
        btnLayout_poi.addWidget(self.btn_poi_changePos)
        btnLayout_poi.addStretch(1)
        btnLayout_poi.addWidget(self.btn_poi_add)
        btnLayout_poi.addWidget(self.btn_poi_del)
        self.btn_name_list_poi = ["rename", "changePos", "-", "+"]
        # レイアウト
        poi_area_layout.addLayout(btnLayout_poi)
        self.resize(300, 450)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.addLayout(poi_area_layout)
        # その他
        self.setFocusPolicy(Qt.StrongFocus)
        self.setLayout(self.layout)
        # イベントコネクト
        self.btn_poi_add.clicked.connect(self.btn_poi_add_clicked)
        self.btn_poi_del.clicked.connect(self.btn_poi_del_clicked)
        self.btn_poi_rename.clicked.connect(self.btn_poi_rename_clicked)
        self.btn_poi_changePos.clicked.connect(self.btn_poi_changePos_clicked)
        self.setFocusPolicy(Qt.StrongFocus)
    def add_poi(self, poi_info):
        # レイアウト
        content_widget = my_w.ClickableQWidget(parent=self.poi_layout, optional_item=poi_info)
        content_widget.setFixedHeight(30)
        content_widget.addWidget(QLabel(" {0}\t{1}".format(poi_info.poi_key, list(poi_info.poi_data))))
        content_widget.addStretch(1)
        content_widget.focuse_changed.connect(poi_info.focus_unfocus)
        content_widget.focuse_changed.connect(functools.partial(self.poi_focus_changed, allowed_btn_list=["rename", "changePos", "del"]))
        self.poi_layout.insertWidget(self.poi_layout.count()-1, content_widget)
        return content_widget
    def del_poi(self):
        if self.poi_layout.current_focused_idx is not None:
            cur_widget = self.poi_layout.get_current_item().widget()
            poi_info = cur_widget.optional_item
            self.poi_layout.remove_current_focused_item()
            self.poi_focus_changed(event=False, allowed_btn_list=["rename", "changePos", "del"])
            return poi_info
    def poi_focus_changed(self, event=None, allowed_btn_list=None):
        # フォーカスされた場合
        if event:
            for allowed_btn in allowed_btn_list:
                cur_btn = getattr(self, "btn_poi_{0}".format(allowed_btn))
                cur_btn.setEnabled(True)
                cur_btn.repaint()
        else:
            for allowed_btn in allowed_btn_list:
                cur_btn = getattr(self, "btn_poi_{0}".format(allowed_btn))
                cur_btn.setEnabled(False)
                cur_btn.repaint()
    # ボタン系
    def get_parent_window(self):
        return self.parent.map_spect_table.get_parent_window()
    def btn_poi_add_clicked(self, event=None):
        poi_info = self.get_parent_window().toolbar_layout.POI_master(mode="add")
        self.add_poi(poi_info)
        # 最後に追加したものをフォーカスする。
        self.poi_layout.itemAt(self.poi_layout.count() - 2).widget().focus()
    def btn_poi_del_clicked(self, event=None):
        poi_info = self.del_poi()
        self.get_parent_window().toolbar_layout.POI_master(mode="del", params={"poi_info":poi_info})
    def btn_poi_rename_clicked(self, event=None, ask=True, **kwargs):
        widget = self.poi_layout.get_current_item().widget()
        poi_info = widget.optional_item
        q_label = widget.layout.itemAt(0).widget()
        label_list = q_label.text().strip().split("\t")
        if ask:
            text_settings_popup = popups.TextSettingsPopup(parent=self, initial_txt=label_list[0], label="Enter a new name for POI.", title="a new name settings")
            done = text_settings_popup.exec_()
            new_poi_key = text_settings_popup.line_edit.text()
        else:
            done = 1
            new_poi_key = kwargs["poi_key"]
        # スペースはNG
        if " " in new_poi_key:
            warning_popup = popups.WarningPopup("Spaces are not allowed in the name.")
            warning_popup.exec_()
            self.btn_poi_rename_clicked(event=event, ask=ask, **kwargs)
            return
        # 無名もNG
        elif new_poi_key == "":
            warning_popup = popups.WarningPopup("Empty name is not allowed.")
            warning_popup.exec_()
            self.btn_poi_rename_clicked(event=event, ask=ask, **kwargs)
            return
        # 同じ名前もNG
        if (new_poi_key in [self.poi_layout.itemAt(idx).widget().optional_item.poi_key for idx in range(self.poi_layout.count() - 1)]) & (new_poi_key != poi_info.poi_key):
            warning_poopup = popups.WarningPopup("The name {0} is already taken. Please choose a different name.".format(new_poi_key), "WARNING")
            warning_poopup.exec_()
            self.btn_poi_rename_clicked(event=event, ask=ask, **kwargs)
            return
        if done == 1:
            # バイナリファイル処理
            old_poi_key = poi_info.poi_key
            poi_info.poi_key = new_poi_key
            self.get_parent_window().toolbar_layout.POI_master(mode="mod_name", params={"poi_info":poi_info, "old_poi_key":old_poi_key})
            # ラベル処理
            q_label.setText(" {0}\t{1}".format(new_poi_key, label_list[1]))
            widget.repaint()
    def btn_poi_changePos_clicked(self, event=None):
        # バイナリアップデート
        widget = self.poi_layout.get_current_item().widget()
        poi_info = widget.optional_item
        poi_info.poi_data = [self.get_parent_window().spectrum_widget.cur_x, self.get_parent_window().spectrum_widget.cur_y]
        self.get_parent_window().toolbar_layout.POI_master(mode="mod_data", params={"poi_info":poi_info})
        # ラベル処理
        q_label = widget.layout.itemAt(0).widget()
        q_label.setText(" {0}\t{1}".format(poi_info.poi_key, poi_info.poi_data))
        widget.repaint()
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
        print("window closed")
        self.poi_layout.remove_all()
    def window_focus_changed(self, window):
        print("window_focus_changed poi")
        if window.window_type in ("t"):
            return
        self.poi_layout.remove_all()
        if window.window_type in ("main", "b", "s", "u"):
            pass
        elif window.window_type in ("ms"):
            for poi_info in window.toolbar_layout.added_info_poi_list:
                content_widget = self.add_poi(poi_info)
                if content_widget.optional_item.focused:
                    content_widget.optional_item.allow_loc_update = False
                    content_widget.focus()
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











