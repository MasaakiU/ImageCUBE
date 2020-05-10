# -*- Coding: utf-8 -*-


import os
import numpy as np
import re

from PyQt5.QtWidgets import (
    QApplication, 
    QAbstractButton, 
    QSpacerItem, 
    QFrame, 
    QVBoxLayout, 
    QHBoxLayout, 
    QWidget, 
    QLabel, 
    QPushButton, 
    QLineEdit, 
    QFileDialog, 
    QAction, 
    QSizePolicy, 
    QStyle, 
    QStyleOption, 
    QMenu, 
    )
from PyQt5.QtGui import (
    QPainter, 
    QIcon, 
    QPixmap, 
    QMouseEvent, 
    )
from PyQt5.QtCore import (
    Qt, 
    pyqtSignal, 
    QCoreApplication, 
    QEvent, 
    QSize, 
    QPoint, 
    QRect
    )
import pyqtgraph as pg

from . import general_functions as gf
from . import popups

# pyqtgraph の GradientEditorItem.py を変更：__init__内だから直接書き換えないと変更しにくかった…
    # 元
        # def __init__(self, *args, **kargs):
        # ...
        # self.rectSize = 15
    # 後 
        # def __init__(self, rect_size=15, *args, **kargs):
        # ...
        # self.rectSize = rectsize
# pyqtgraph の HistogramLUTItem.py を変更：__init__内だから直接書き換えないと変更しにくかった…
    # 元
        # def __init__(self, image=None, fillHistogram=True):
        # ...
        # self.gradient = GradientEditorItem()
    # 後
        # def __init__(self, image=None, fillHistogram=True, grad_rect_size=15):
        # ...
        # self.gradient = GradientEditorItem(grad_rect_size)

# カスタムボタン：ボタンアイコンに画像を指定できる
class CustomPicButton(QAbstractButton):
    def __init__(self, pixmap, pixmap_hover, pixmap_pressed, base_path=gf.base_path, parent=None, width=gf.icon_width, height=gf.icon_width):
        self.width = width
        self.height = height
        super(CustomPicButton, self).__init__(parent)
        self.pixmap = QPixmap(os.path.join(base_path, pixmap))
        self.pixmap_hover = QPixmap(os.path.join(base_path, pixmap_hover))
        self.pixmap_pressed = QPixmap(os.path.join(base_path, pixmap_pressed))
        self.pressed.connect(self.update)
        self.released.connect(self.update)
    def paintEvent(self, event):
        pix = self.pixmap_hover if self.underMouse() else self.pixmap
        if self.isDown():
            pix = self.pixmap_pressed
        painter = QPainter(self)
        painter.drawPixmap(event.rect(), pix)
    def enterEvent(self, event):
        self.update()
    def leaveEvent(self, event):
        self.update()
    def sizeHint(self):
        return(QSize(self.width, self.height))
    # def mousePressEvent(self, event):
    #     QAbstractButton.mousePressEvent(self, event)
    #     if event.button() == Qt.RightButton :
    #         self.rightClick.emit()
    #         # print ('right click')

class CustomMenuButton(QPushButton):
    def __init__(self, text="", icon_path=None, divide=True, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.change_event_from_outside = True
        self.setStyleSheet("""QPushButton:enabled{color:black; text-align:left}
            :enabled:pressed{color:white; text-align:left}
            :enabled:pressed:!hover{color:black; text-align:left}
            :disabled{color:light gray; text-align:left}"""
        )
        self.divide = divide
        self.menu = QMenu()
        self.menu.addAction("        ", lambda *args: None)     # pseudo menu
        self.clicked_near_arrow = False
        # set icon and label
        self.label_icon = QLabel(" ˇ ")# ∨▾
        self.label_icon.setAttribute(Qt.WA_TranslucentBackground)
        self.label_icon.setAttribute(Qt.WA_TransparentForMouseEvents)
        icon_size = QSize(19, 19)
        self.pixmap_gray = QIcon(os.path.join(icon_path, "line_gray.png")).pixmap(icon_size)
        self.pixmap_white = QIcon(os.path.join(icon_path, "line_white.png")).pixmap(icon_size)
        self.line_icon = QLabel()
        self.line_icon.setAttribute(Qt.WA_TranslucentBackground)
        self.line_icon.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.line_icon.setPixmap(self.pixmap_gray)
        # layout
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 6, 3)
        lay.setSpacing(0)
        lay.addStretch(1)
        if self.divide:
            lay.addWidget(self.line_icon)
        lay.addWidget(self.label_icon)
    def set_icon(self, pressed):
        if pressed:
            color = "white"
            self.line_icon.setPixmap(self.pixmap_white)
        else:
            color = "black"
            self.line_icon.setPixmap(self.pixmap_gray)
        self.label_icon.setStyleSheet("""
            QLabel:enabled{color:""" + color + """; text-align:left}
            :disabled{color:light gray; text-align:left}""")
    def mousePressEvent(self, event):
        if event.type() == QEvent.MouseButtonPress:
            self.set_icon(pressed=True)
            # figure out press location
            topRight = self.rect().topRight()
            bottomRight = self.rect().bottomRight()
            # get the rect from QStyle instead of hardcode numbers here
            arrowTopLeft = QPoint(topRight.x()-19, topRight.y())
            arrowRect = QRect(arrowTopLeft, bottomRight)
            if arrowRect.contains(event.pos()) | (not self.divide):
                self.clicked_near_arrow = True
                self.blockSignals(True)
                QPushButton.mousePressEvent(self, event)
                self.blockSignals(False)
                self.open_context_menu()
            else:
                self.clicked_near_arrow = False
                QPushButton.mousePressEvent(self, event)
    def mouseMoveEvent(self, event):
        if self.rect().contains(event.pos()):
            self.set_icon(pressed=True)
        else:
            self.set_icon(pressed=False)
        QPushButton.mouseMoveEvent(self, event)
    def mouseReleaseEvent(self, event):
        self.set_icon(pressed=False)
        if self.clicked_near_arrow:
            self.blockSignals(True)
            QPushButton.mouseReleaseEvent(self, event)
            self.blockSignals(False)
        else:
            QPushButton.mouseReleaseEvent(self, event)
    def setMenu(self, menu):
        self.menu = menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)
    # ContextMenueのlauncher
    def open_context_menu(self, point=None):
        point = QPoint(7, 23)
        self.menu.exec_(self.mapToGlobal(point))
        event = QMouseEvent(QEvent.MouseButtonRelease, QPoint(10, 10), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        self.mouseReleaseEvent(event)

class CustomAction(QAction):
    def __init__(self, icon_path, icon_name, name, parent):
        icon = QIcon(os.path.join(icon_path, icon_name))
        super().__init__(icon, name, parent)

# ContextMenu; 右クリックで出現するようにできる
        # btnSample = my_w.CustomPicButton("%s.png"%focused_field, "%s.png"%focused_field, "%s.png"%focused_field, base_path=gf.icon_path)
        # btnSample.clicked.connect(functools.partial(self.btn_sample_clicked, item=item, field=focused_field))
        # btnSample.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # menu = my_w.CustomContextMenu(parentBtn=btnSample)
        # btnSample.customContextMenuRequested.connect(functools.partial(my_w.on_context_menu, menu=menu))

class CustomContextMenu(QMenu):
    # action_func_listの最初の引数はbtnでなくてはならない
    def __init__(self, parentBtn=None, action_name_list=None, action_func_list=None):
        self.parentBtn = parentBtn
        self.action_func_list = action_func_list
        self.action_list = []
        super().__init__(self.parentBtn)
        for action_name in action_name_list:
            action = QAction(action_name, self)
            self.addAction(action)
            self.action_list.append(action)
            # self.addSeparator()
# 上記ContextMenueのlauncher
def on_context_menu(point, menu):
    action = menu.exec_(menu.parentBtn.mapToGlobal(point))
    if action:
        action_index = menu.action_list.index(action)
        function = menu.action_func_list[action_index]
        function(btn=menu.parentBtn)

class CustomSmallButton(QPushButton):
    def __init__(self, title):
        # レンジ設定ボタン
        super().__init__(title)
        self.setMaximumWidth(gf.icon_width)
        self.setMaximumHeight(gf.icon_width / 2)
        self.setFont(gf.just_small(9))
        self.setStyleSheet(
            "QPushButton:pressed {background-color:gray; color:white; border-color:black;}"
            "QPushButton {background-color:white; color: black; border-radius:1px; border-color:black; border-style:solid; border-width:1px;}"
            )
class CustomSmallLabel(QLabel):
    def __init__(self, title):
        super().__init__(title)
        self.setFont(gf.mono_small)
        self.setMaximumWidth(gf.icon_width)

class PaintableQWidget(QWidget):
    def __init__(self):
        super().__init__()
    # サブクラスのバックグラウンドの色を設定するのに、implement する必要がある
    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)

class ClickableLayout(QVBoxLayout):
    layout_focuesed = pyqtSignal(bool)
    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        self.setContentsMargins(0,0,0,0)
        self.setSpacing(0)
        self.addStretch(1)
        self.current_focused_idx = None
    def focused(self, child_widget):
        idx = self.indexOf(child_widget)
        # 前のものが unfocus されてから、次のものが focus される
        if self.current_focused_idx is not None:
            self.itemAt(self.current_focused_idx).widget().unfocus()
        self.current_focused_idx = idx
    def unfocused(self):
        self.current_focused_idx = None
    def unfocus_all(self):
        for idx in range(self.count() - 1):
            self.itemAt(idx).widget().unfocus()
    def get_current_item(self):
        if self.current_focused_idx is not None:
            return self.itemAt(self.current_focused_idx).widget()
        else:
            return None
    def get_all_items(self):
        return [self.itemAt(i).widget() for i in range(self.count() - 1)]
    def all_widgets(self):
        return [self.itemAt(idx).widget() for idx in range(self.count()-1)]
    def remove_current_focused_item(self, new_focus=False):
        if self.current_focused_idx is not None:
            cur_widget = self.itemAt(self.current_focused_idx).widget()
            cur_widget.releaseKeyboard()
            self.removeWidget(cur_widget)
            cur_widget.deleteLater()
            del cur_widget
            if new_focus and self.count() > 1:
                if self.current_focused_idx == self.count() - 1:
                    self.current_focused_idx -= 1
                self.itemAt(self.current_focused_idx).widget().focus(event=None, unfocus_parent=False)
            else:
                self.current_focused_idx = None
    def remove_items(self, idxes_to_remove):
        idxes_to_remove = sorted(idxes_to_remove, reverse=True)
        for idx in idxes_to_remove:
            cur_widget = self.itemAt(idx).widget()
            self.removeWidget(cur_widget)
            cur_widget.deleteLater()
            del cur_widget
        self.current_focused_idx = None
    def remove_all(self):
        for idx in range(self.count()-1):
            cur_widget = self.itemAt(0).widget()
            self.removeWidget(cur_widget)
            cur_widget.deleteLater()
            del cur_widget
        self.current_focused_idx = None
    def moveUp_current_focused_item(self):
        if self.current_focused_idx is None:
            return
        if self.current_focused_idx > 0:
            cur_widget = self.itemAt(self.current_focused_idx).widget()
            self.removeWidget(cur_widget)
            self.current_focused_idx -= 1
            self.insertWidget(self.current_focused_idx, cur_widget)
    def moveDown_current_focused_item(self):
        if self.current_focused_idx is None:
            return
        if self.current_focused_idx < self.count() - 2:
            cur_widget = self.itemAt(self.current_focused_idx).widget()
            self.removeWidget(cur_widget)
            self.current_focused_idx += 1
            self.insertWidget(self.current_focused_idx, cur_widget)
    def set_focus(self, idx):
        if idx < 0:
            idx += self.count()
        self.itemAt(idx).widget().focus()
        self.current_focused_idx = idx

class ClickableQWidget(PaintableQWidget):
    focuse_changed = pyqtSignal(bool)   # TrueでFocused, Falseでunfocused
    def __init__(self, parent=None, normal_c="rgb(220,220,220)", hover_c="rgb(160,160,160)", focused_c="rgb(39,93,192)", optional_item=None):
        self.parent = parent
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.optional_item = optional_item
        self.isFocused = False
        self.isHalf = False
        self.normal_c = normal_c
        self.hover_c = hover_c
        self.focused_c = focused_c
        self.half_normal_c = self.average_of_color(self.normal_c, self.focused_c)
        self.half_hover_c = self.average_of_color(self.hover_c, self.focused_c)
        # レイアウト
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.setObjectName("widget")
        self.setStyleSheet(
            """
            ClickableQWidget{border:1px solid gray; background-color:%s; color:black}
            ClickableQWidget:hover:!pressed{border:1px solid gray; background-color:%s; color:black}
            ClickableQWidget:hover{border:1px solid gray; background-color:%s; color:black}
            """%(self.normal_c, self.hover_c, self.focused_c)
            )
        # イベントコネクト
        self.mousePressEvent = self.w_mousePressEvent
    def average_of_color(self, c1, c2):
        color_list1 = re.fullmatch("rgb\(([0-9]+),([0-9]+),([0-9]+)\)", c1)
        color_list2 = re.fullmatch("rgb\(([0-9]+),([0-9]+),([0-9]+)\)", c2)
        c_mean = [int((int(color_list1[i]) + int(color_list2[i])) / 2) for i in range(1,4)]
        return "rgb({0[0]},{0[1]},{0[2]})".format(c_mean)
    def addWidget(self, widget):
        self.layout.addWidget(widget)
    def addStretch(self, value):
        self.layout.addStretch(value)
    def w_mousePressEvent(self, event):
        if self.isFocused:
            self.unfocus()
        else:
            self.focus()
        event.accept()
    def focus(self, event=None, unfocus_parent=True):
        if self.isFocused:
            return
        # self.grabKeyboard()
        if unfocus_parent:  # その他処理をする場合は、先に全て済ませた後、スタイルシートを変更する
            self.parent.focused(self)
        self.setStyleSheet(
            """
            ClickableQWidget{border:1px solid Gray; background-color:%s}
            .QLabel{color:white}
            """%self.focused_c
        )
        self.isFocused = True
        self.focuse_changed.emit(True)
        self.repaint()
        QCoreApplication.processEvents()
    def unfocus(self, event=None):
        if not self.isFocused:
            return
        self.releaseKeyboard()
        self.parent.unfocused() # その他処理をする場合は、先に全て済ませた後、スタイルシートを変更する
        self.setStyleSheet(
            """
            ClickableQWidget{border:1px solid gray; background-color:%s; color:black}
            ClickableQWidget:hover:!pressed{border:1px solid gray; background-color:%s; color:black}
            ClickableQWidget:hover{border:1px solid gray; background-color:%s; color:black}
            """%(self.normal_c, self.hover_c, self.focused_c)
            )
        self.isFocused = False
        self.focuse_changed.emit(False)
        self.repaint()
        QCoreApplication.processEvents()
    # 基本的に、self.isFocused とは無関係。使いたい場合は、勝手に外部からやってください。クラス内部での処理は一切行いません。
    def half_focus(self, event=None):
        if (self.isHalf and event) or ((not self.isHalf) and (not event)):
            return
        if event:
            color_list = (self.half_normal_c, self.half_hover_c, self.focused_c)
        else:
            color_list = (self.normal_c, self.hover_c, self.focused_c)
        self.setStyleSheet(
            """
            ClickableQWidget{border:1px solid gray; background-color:%s; color:black}
            ClickableQWidget:hover:!pressed{border:1px solid gray; background-color:%s; color:black}
            ClickableQWidget:hover{border:1px solid gray; background-color:%s; color:black}
            """%color_list
        )
        self.isHalf = event
        # シグナルは何も出さない
        self.repaint()
        QCoreApplication.processEvents()

# Tick無し、axis無しヒストグラム；最大、最小の値を表示してあげられる
# autoかfixのチェックボックス作る
class CustomHistogramLUTWidget(QWidget):
    def __init__(self, grad_rect_size):
        super().__init__()
        self.custom_histogram_LUT_widget = pg.HistogramLUTWidget(grad_rect_size=grad_rect_size)
        # グラジエント自体は変更しないないので、Tickは表示しない
        # for tick in self.custom_histogram_LUT_widget.item.gradient.ticks.keys():
        #     tick.hide()
        self.gradientChanged()
        # ヒストグラムLUTレイアウト
        self.custom_histogram_LUT_widget.item.vb.setMinimumWidth(gf.histogram_height)
        self.custom_histogram_LUT_widget.item.vb.setMaximumWidth(gf.histogram_height)
        self.custom_histogram_LUT_widget.setMinimumWidth(gf.icon_width)
        self.custom_histogram_LUT_widget.setMaximumWidth(gf.icon_width)
        self.custom_histogram_LUT_widget.item.vb.removeItem(self.custom_histogram_LUT_widget.axis)
        self.custom_histogram_LUT_widget.item.layout.removeAt(0)
        # ラベル
        self.min_label = CustomSmallLabel("0")
        self.max_label = CustomSmallLabel("1")
        # レンジ固定ボタン
        self.fix_btn = QPushButton("FIX")
        self.fix_btn.setMaximumWidth(gf.icon_width)
        self.fix_btn.setMaximumHeight(gf.icon_width / 2)
        # self.fix_btn.setDown(True)
        self.fix_btn.setFont(gf.just_small(9))
        self.FIX = True
        self.btn_fix_pressed()  # 初期設定は、fixしない設定
        # レンジ設定ボタン
        self.range_set_btn = CustomSmallButton("SET")
        # レンジ設定ボタン
        self.BIT = 16
        self.bit_btn = CustomSmallButton("16B")
        # 全体レイアウト
        self.v_layout = QVBoxLayout()
        self.v_layout.setContentsMargins(0, 0, 0, 0)
        self.v_layout.setSpacing(1)
        self.v_layout.addWidget(self.max_label)
        self.v_layout.addWidget(self.custom_histogram_LUT_widget)
        self.v_layout.addWidget(self.min_label)
        self.v_layout.addWidget(self.fix_btn)
        self.v_layout.addWidget(self.range_set_btn)
        self.v_layout.addWidget(self.bit_btn)
        self.setLayout(self.v_layout)
        # イベントコネクト（コントラスト変更時にラベルの数値をアップデート）
        self.custom_histogram_LUT_widget.item.vb.sigRangeChanged.connect(self.viewRangeChanged)
        self.custom_histogram_LUT_widget.item.region.sigRegionChanged.connect(self.viewRangeChanged)
        self.custom_histogram_LUT_widget.item.gradient.sigGradientChanged.connect(self.gradientChanged)
        self.fix_btn.clicked.connect(self.btn_fix_pressed)
        self.range_set_btn.clicked.connect(self.range_btn_pressed)
        self.bit_btn.clicked.connect(self.bit_btn_pressed)
    def __getattr__(self, attr):
        return getattr(self.custom_histogram_LUT_widget, attr)
    def viewRangeChanged(self):
        min_value, max_value = self.custom_histogram_LUT_widget.getLevels()
        self.min_label.setText('{0:>4.4g}'.format(min_value))
        self.max_label.setText('{0:>4.4g}'.format(max_value))
    def gradientChanged(self):
        for tick in self.custom_histogram_LUT_widget.item.gradient.ticks.keys():
            tick.hide()
    def btn_fix_pressed(self, event=None):
        if self.FIX:
            self.fix_btn.setStyleSheet(
                "QPushButton:pressed {background-color:gray; color:white; border-color:black;}"
                "QPushButton {background-color:white; color: gray; border-radius:1px; border-color:gray; border-style:solid; border-width:1px;}"
                )
        else:
            self.fix_btn.setStyleSheet(
                "QPushButton:pressed {background-color:white; color:gray; border-color:gray;}"
                "QPushButton {background-color:gray; color: white; border-radius:1px; border-color:black; border-style:solid; border-width:1px;}"
                )
        self.FIX = not self.FIX
    def range_btn_pressed(self, event=None):
        im_min_value, im_max_value = self.imageItem().getLevels()
        range_settings_popup = popups.RangeSettingsPopup(parent=None, initial_values=(im_max_value, im_min_value), labels=("maximum values", "minimum values"))
        done = range_settings_popup.exec_()
        if done == 1:
            set_max_value = range_settings_popup.spbx_RS1.value()
            set_min_value = range_settings_popup.spbx_RS2.value()
            # 表示できるgradietの範囲は、 (LinearRegionItemを動かせる範囲) 画像輝度の範囲とsetされた範囲を全てカバーできるような範囲に設定する
            self.setRange(set_min_value, set_max_value)
            # self.item.region.setBounds([min(im_min_value, set_min_value), max(im_max_value, set_max_value)])
            # self.setLevels(set_min_value, set_max_value)
            # self.imageItem().setLevels([set_min_value, set_max_value])
        else:
            return
    def bit_btn_pressed(self, event):
        if self.BIT == 16:
            self.BIT = 32
        elif self.BIT == 32:
            self.BIT = 8
        elif self.BIT == 8:
            self.BIT = 16
        self.bit_btn.setText("%dbit"%self.BIT)
    def setRange(self, set_min_value, set_max_value):
        im_min_value, im_max_value = self.imageItem().getLevels()
        self.item.region.setBounds([min(im_min_value, set_min_value), max(im_max_value, set_max_value)])
        self.setLevels(set_min_value, set_max_value)
        self.imageItem().setLevels([set_min_value, set_max_value])

class CustomFillBetweenItems():
    def __init__(self, curve1=None, curve2=None, brush=None, pen=None):
        self.curve1 = curve1
        self.curve2 = curve2
        self.fbtwn_item = pg.FillBetweenItem(curve1=self.curve1, curve2=self.curve2, brush=brush, pen=None)
        for m in ["opts"]:
            setattr(self, m, getattr(self.curve1, m))
        self.opts["fillBrush"] = self.fbtwn_item.brush()
        self.setPen(pen)
    def setBrush(self, *args, **kwds):
        self.fbtwn_item.setBrush(*args, **kwds)
        self.opts["fillBrush"] = self.fbtwn_item.brush()
    def setPen(self, *args, **kwds):
        self.curve1.setPen(*args, **kwds)
        self.curve2.setPen(*args, **kwds)
        self.opts["pen"] = self.curve1.opts["pen"]
    def all_items(self):
        return self.curve1, self.curve2, self.fbtwn_item
    def setVisible(self, arg):
        self.curve1.setVisible(arg)
        self.curve2.setVisible(arg)
        self.fbtwn_item.setVisible(arg)

class PlotDataItems(pg.PlotDataItem):
    def __init__(self, xy_data_set=None, **kwargs):    # [(xData1,yData1),(xData2,yData2),(xData3,yData3)...]
        super().__init__()
        if xy_data_set is not None:
            self.setData_set(xy_data_set, **kwargs)
    def setData_set(self, xy_data_set, **kwargs):
        x_data_list, y_data_list = zip(*xy_data_set)
        x_data = np.hstack(x_data_list)
        y_data = np.hstack(y_data_list)
        connect = np.ones_like(x_data, dtype=int)
        loc = 0
        for i in x_data_list:
            loc += len(i)
            connect[loc - 1] = 0
        self.setData(x_data, y_data, connect=connect, **kwargs)

# class CustomPathSetLayout(QHBoxLayout):
#     def __init__(self, initial_text=""):
#         super().__init__()
#         self.path_entry = QLineEdit()
#         self.path_entry.setText(initial_text)
#         btnSetPath = QPushButton("...")
#         btnSetPath.clicked.connect(self.btnSetPath_clicked)
#     def btnSetPath_clicked(self, event):
#         dir_path = QFileDialog.getExistingDirectory(self, 'select folder', self.parent.settings["last opened dir"])
#         if len(dir_path):
#             self.path_entry.setText(dir_path)

# スペーサー
class CustomSpacer(QSpacerItem):
    def __init__(self, width=gf.icon_width, height=gf.spacer_size):
        super().__init__(width, height, QSizePolicy.Minimum, QSizePolicy.Minimum)

# セパレーター
class CustomSeparator(QFrame):
    def __init__(self, color=gf.dbg_color):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        self.setStyleSheet("QFrame{background-color: %s}"%color)










