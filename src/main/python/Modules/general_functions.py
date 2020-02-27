# -*- Coding: utf-8 -*-


import sys, os
import numpy as np
import pyqtgraph as pg
import re
import spc
import pickle
from spc.spc import subFile
from scipy.optimize import minimize_scalar
from scipy.stats import t   # method を使用する際に必要

import copy
import glob

from PIL import Image
import struct
import itertools
import functools
import datetime

from PyQt5.QtGui import (
    QColorDialog, 
    QColor, 
    QFont, 
    )
from PyQt5.QtCore import (
    QCoreApplication, 
    )
from PyQt5.QtWidgets import (
    QLabel, 
    QDialog, 
    QVBoxLayout, 
    QHBoxLayout, 
    QGridLayout, 
    QDoubleSpinBox, 
    QPushButton, 
    QWidget, 
    QTabWidget, 
    QLineEdit, 
    QFormLayout, 
    QSpacerItem, 
    QFileDialog, 
    )

# デフォルト値
ver = "0.6.0"
print("version: %s"%ver)

default_last_opened_dir = os.path.expanduser('~') + '/Desktop'
default_method_dir = os.path.expanduser('~') + '/Desktop'
default_plugin_dir = os.path.expanduser('~') + '/Desktop'

base_path = ""
icon_path = ""
settings_path = ""

def set_base_path(base_path_):
    global base_path
    global icon_path
    global settings_path
    base_path = base_path_
    icon_path = os.path.join(base_path, "icons")
    settings_path = os.path.join(base_path, "settings")

CRR_half_window1 = 10
CRR_half_window2 = 1
CRR_SN = 10
CRR_percentile = 80
# CRR_ones = np.ones(CRR_window, dtype=float)

# windows/mac
# if os.name == 'nt':         # windows
#     meta_key = "Alt"
# elif os.name == 'posix':    # mac or linux
#     meta_key = "Meta"


# スペクトルのフォント：o: original, a: added, u: unmixed
selected_set = "set3"
default_keys = ["bg_brush", "graph_line",  "o_color", "a_color", "u_color"]
if selected_set == "set1":
    bg_brush = (0,0,0,255)
    graph_line = (150,150,150,255)
    o_color = "d"
    a_color = "r"
    u_color = "y"
    t_color = (255,0,0,255)
elif selected_set == "set2":
    bg_brush = (0,0,0,255)
    graph_line = (150,150,150,255)
    o_color = (150,150,150,255)
    a_color = (255,0,0,255)
    u_color = (255,255,0,255)
    t_color = (255,0,0,255)
elif selected_set == "set3":
    bg_brush = (255,255,255,255)
    graph_line = (0,0,0,255)
    o_color = (0,0,0,255)
    a_color = (0,0,255,255)
    u_color = (255,0,0,255)
    t_color = (255,0,0,255)
elif selected_set == "set4":
    bg_brush = (255,255,255,255)
    graph_line = (0,0,0,255)
    o_color = "d"
    a_color = "f"
    u_color = "y"
    t_color = (255,0,0,255)
crr_color = "r"

settings = {
    "last opened dir": default_last_opened_dir, 
    "method dir": default_method_dir, 
    "plugin dir": default_plugin_dir, 
    # グラフ背景など
    "bg_brush":bg_brush, 
    "graph_line":graph_line, 
    # ライン色
    "o_color":o_color, 
    "a_color":a_color, 
    "u_color":u_color,
    "t_color":t_color,
    }

# 設定ファイルの読み込み（なければ作る：初回のみ？）
def load_settings_file():
    # 設定ファイルがない場合は新規作成 & 保存（最初に開かれたときのみ）
    if not os.path.exists(settings_path):
        # settingsファイルを新規作成
        with open(settings_path, mode='wb') as f:
            pickle.dump(settings, f)
    # 設定ファイルの読み込み
    with open(settings_path, mode='rb') as f:
        loaded_settings = pickle.load(f)
    for key, value in loaded_settings.items():
        settings[key] = value
    # 存在しないパスは、デスクトップへのパスに変更する。
    if not os.path.exists(settings["last opened dir"]):
        settings["last opened dir"] = default_last_opened_dir
    if not os.path.exists(settings["method dir"]):
        settings["method dir"] = default_method_dir
    if not os.path.exists(settings["plugin dir"]):
        settings["plugin dir"] = default_plugin_dir
    # background, foreground 設定
    pg.setConfigOption("background", settings["bg_brush"])
    pg.setConfigOption("foreground", settings["graph_line"])
def save_settings_file():
    with open(settings_path, mode='wb') as f:
        pickle.dump(settings, f)

# original, added, unmixed
def mk_o_pen():
    return pg.mkPen(settings["o_color"], width=1)
def mk_a_pen():
    return pg.mkPen(settings["a_color"], width=1)
def mk_u_pen():
    return pg.mkPen(settings["u_color"], width=1)
def mk_bg_pen():     # unmixed の condition に統一中
    return pg.mkPen(settings["u_color"], width=1)
# def mk_t_pen():      # unmixed の condition に統一中
#     return pg.mkPen(settings["u_color"], width=1)
def mk_crr_pen():
    return pg.mkPen(crr_color, width=1)

# クロスヘア
c_color = (255,0,0,100)
c_width = 1
def mk_c_pen():
    return pg.mkPen(c_color, width=c_width)

# 色 default_background_color
dbg_color = "white"
brushAlpha = 50
def mk_u_brush():
    color = QColor(*settings["u_color"])
    color.setAlpha(brushAlpha)
    return pg.mkBrush(color)
targetAlpha = 150
t_width = 0.5
def mk_target_color():
    color = QColor(*settings["t_color"])
    color.setAlpha(targetAlpha)
    return pg.mkPen(color=color, width=t_width)

 # サイズ
icon_width = 30
axis_width = 60
dcm = 1 # デフォルトcontentsMargins
dsp = 1 # デフォルトspacing
spacer_size = icon_width / 4
grad_rect_size = 8  # グラジエントの太さ
histogram_height = icon_width * 2 / 3
mainwindow_height = icon_width + 4 * dcm
mainwindow_width = 400
batch_window_min_height = 500
batch_window_min_width = 700
process_widget_height = 40
map_widget_margin = 7

# フォント ###############################
mono_small = QFont("Courier")
mono_small.setPointSize(9)
boldFont=QFont()
boldFont.setBold(True)
def just_small(size):
    just_small = QFont()
    just_small.setPointSize(size)
    return just_small
# デフォ記入地
value_settings_popups_init = 2950

# monospaced = QFont("Courier")
# monoBold = QFont("Courier")
# monoBold.setBold(True)
# monoSmall = QFont("Courier")
# monoSmall.setPointSize(10)
# monoBigBold = QFont("Courier")
# monoBigBold.setBold(True)
# monoBigBold.setPointSize(20)
# monoSmallBold = QFont("Courier")
# monoSmallBold.setBold(True)
# monoSmallBold.setPointSize(10)
# timesSmall = QFont("Times")
# timesSmall.setPointSize(10)
# helvetica = QFont("0")

# フォント付きラベル
class QRichLabel(QLabel):
    def __init__(self, text, font=None):
        super().__init__(text)
        if font:
            self.setFont(font)
###########################################


# バイナリファイルへの書き込み用：上書きでなく、挿入の形で書き込み
def insert(f, insert_txt, offset, from_what):   # 0:ファイル頭、1:現在の位置、2:ファイルお尻
    # from_whatからoffsetだけ移動した後、そこよりあとの部分を読み込み、
    f.seek(offset, from_what)
    latter_part = f.read()
    # 読み込んだ時点で最後まで位置が移動してしまっているので元の位置に戻り、"insert_txt, 前もって読んでおいたlatter_part"の順で上書き
    f.seek(offset, from_what)
    f.write(insert_txt)
    f.write(latter_part)

# バイナリファイルへの書き込み用：指定された正規表現の部分を削除
def remove_between(f, remove_re, flags=0):
    f.seek(0, 0)
    matchedObject_list = list(re.finditer(remove_re, f.read(), flags=flags))
    if len(matchedObject_list) > 1:
        raise Exception("Cannot change the map_size: multiple [map_size] sequence was found in the file.")
    matchedObject = matchedObject_list[0]
    s_point, e_point = matchedObject.span()
    # remove_reでマッチした部分より後半の文字列: あとで付け足す用
    f.seek(e_point, 0)
    later_letter = f.read()
    # remove_reでマッチした部分を含め、それよりあとのものを削除
    f.seek(s_point, 0)
    f.truncate()
    # 追加
    f.write(later_letter)
    return matchedObject

# ファイルパスから、ファイル名とフォルダ名、拡張子抜きのファイル名を取得
def file_name_processor(file_path):
    splitted_file_path = file_path.split("/")
    file_name = splitted_file_path[-1]
    file_name_wo_ext = ".".join(file_name.split(".")[:-1])
    dir_path = "/".join(splitted_file_path[:-1])
    return dir_path, file_name, file_name_wo_ext

# y軸を左右に作る時：vb1にvb2を追加する。その時の、vbサイズを同一にする用
def updateViews(vb1, vb2):
    vb2.setGeometry(vb1.sceneBoundingRect())
    vb2.linkedViewChanged(vb1, vb2.XAxis)

# pillowを用いた16bit画像保存
def save_u16_to_tiff(u16in):#, size, tiff_filename):
    """
    Since Pillow has poor support for 16-bit TIFF, I made my own
    save function to properly save a 16-bit TIFF.
    """    # write 16-bit TIFF image
    # PIL interprets mode 'I;16' as "uint16, little-endian"
    w, h = u16in.shape
    return Image.frombytes("I;16", (h, w), u16in.tostring())

    # u16in = u16in.astype(int)
    # img_out = Image.new('I;16', u16in.shape)
    # NUMPY 持ってる場合 # make sure u16in little-endian, output bytes
    # outpil = u16in.astype(u16in.dtype.newbyteorder("<")).tobytes()
    # NUMPY 持ってない場合：何故かエラー出る # little-endian u16 format
    # outpil = struct.pack("<%dH"%(len(u16in)), *u16in)
    # img_out.frombytes(outpil)
    # return(img_out)
    # img_out.save(tiff_filename)

# 素因数を求める（mapサイズを求める用）
def get_prime_factors(n):
    i = 2
    prime_factor_list = []
    while i * i <= n:
        if n % i:
            i += 1
        else:
            n //= i
            prime_factor_list.append(i)
    if n > 1:
        prime_factor_list.append(n)
    return np.array(prime_factor_list)

# ２つの積に分解する
def into_2_products(n):
    # まずは素因数分解
    prime_factor_list = get_prime_factors(n)
    # 使用不使用のリスト
    unique_factors, N_list = np.unique(prime_factor_list, return_counts=True)
    comb_list = np.array(list(itertools.product(*[np.arange(N+1) for N in N_list])))
    product1_list = np.power(unique_factors[np.newaxis, :], comb_list).prod(axis=1)
    product1_list.sort()
    product2_list = (n / product1_list).astype(int)
    return product1_list, product2_list

# """
# get x to minimize ||Ax - b||
# 片側 5% 検定
# """
# def ls_stat(A, b):
#     N_data, N_var = A.shape
#     d_freedom = N_data - N_var
#     result = ll(A, b)
#     Var_x = np.linalg.inv(np.dot(A.T, A)) * np.dot(result.fun.T, result.fun) / d_freedom
#     SE = np.sqrt(np.diag(Var_x))
#     t_vals = np.divide(result.x, SE)
#     p = t.cdf(-np.absolute(t_vals), df=d_freedom)
#     # btm = result.x - t.ppf(0.975, df=d_freedom) * SE
#     # top = result.x + t.ppf(0.975, df=d_freedom) * SE
#     btm95 = result.x - t.ppf(0.95, df=d_freedom) * SE
#     return result.x, SE, t_vals, p, btm95


# 与えられた範囲XにおけるYの最大値・最小値を求める
def get_local_maximum(x_list, y_list, x_range):
    local_area = (x_range[0] <= x_list) & (x_list <= x_range[1])
    return(y_list[local_area].max())
def get_local_minimum(x_list, y_list, x_range):
    local_area = (x_range[0] <= x_list) & (x_list <= x_range[1])
    return(y_list[local_area].min())
def get_local_minmax(x_list, y_list, x_range):
    local_area = (x_range[0] <= x_list) & (x_list <= x_range[1])
    local_y = y_list[local_area]
    return(local_y.min(), local_y.max())
def spectrum_linear_subtraction_core(master_x_list, master_y_list, added_regional_y_list, to_zero):
    # 引き算したあとの関数を直線近似した際の、二乗誤差を求める関数
    if not to_zero:
        def rnorm(n):
            diff_y_list = master_y_list - n * added_regional_y_list
            # 直線近似（a:傾き、b:切片）
            params, residuals, rank, s = np.linalg.lstsq(np.vstack([master_x_list, np.ones(len(master_x_list))]).T, diff_y_list, rcond=-1)
            return residuals[0]
    else:
        def rnorm(n):
            diff_y_list = master_y_list - n * added_regional_y_list
            # 単純に 0 に近づける
            return (diff_y_list ** 2).sum()
    optimization_results = minimize_scalar(rnorm, bounds=(0, np.inf))
    umx_height_value = -optimization_results.x # [係数リスト（-optimization_results.x = -n）, オリジナル]
    return umx_height_value

###########################

# カイザーのidxを求める（インスタンスメソッド追加の形で使う）
def get_idx(self, RS):
    RS_idx = np.argmin(np.absolute(self.x - RS))
    return RS_idx
# 範囲のデータを取り出す：ソートはされない
def get_data(self, sRS, eRS, sub_idx=0):    #, sort=False
    # (sRS, eRS)と(sRS-idx, eRS-idx)は必ずしも一致しない（RSは降順にもなりうるがidxはあくまで昇順に並ぶ）
    sRS_idx, eRS_idx = np.sort([self.get_idx(sRS), self.get_idx(eRS)])
    y_list = self.sub[sub_idx].y[sRS_idx:eRS_idx + 1]
    x_list = self.x[sRS_idx:eRS_idx + 1]
    # # sortがTRUEなら、x_listで昇順に並べ替えた形で表示
    # if sort:
    #     order = np.argsort(x_list)
    #     x_list = x_list[order]
    #     y_list = y_list[order]
    return x_list, y_list
# # x軸方向のインターバルを求める
# def get_RS_diff(self):
#     RS_diff = np.absolute((self.ffirst - self.flast) / self.fnpts)
#     return(RS_diff)

# ポイント強度によるmap作成
def get_point_intensity_list(self, RS):
    RS_idx = self.get_idx(RS)
    return np.array([self.sub[sub_idx].y[RS_idx] for sub_idx in range(self.fnsub)])
def get_total_intensity_list(self):
    return np.array([self.sub[sub_idx].y.sum() for sub_idx in range(self.fnsub)])
# カーブフィットのための関数
def gaussian_fitting_function(x, u, s, h, a, b):
    y = h * np.exp(-(((x - u) / s)**2 / 2)) + a * x + b
    return y
def gaussian_function(x, u, s, h):
    y = h * np.exp(-(((x - u) / s)**2 / 2))
    return y

# logboxのサイズ変更（マイナスもありうる）
def update_logsizd(file_path, flogoff=None, added_length=None):
    with open(file_path, 'rb+') as f:
        if flogoff is None:
            f.seek(248)
            flogoff = struct.unpack("<i".encode("utf-8"), f.read(4))[0]
        f.seek(flogoff)
        logsizd = struct.unpack("<i".encode("utf-8"), f.read(4))[0]
        logsizd += added_length
        f.seek(flogoff)
        f.write(struct.pack("<i".encode("utf-8"), logsizd))
# def isInBinary(file_path, search_re, flags=0):
#     with open(file_path,'rb') as f:
#         matchedObject = re.finditer(search_re, f.read(), flags=flags)
#     return matchedObject

# spcファイルのcell_free_positionをオリジナルのファイルに上書きするための関数
def get_shape(self):
    try:
        return int(self.log_dict[b"map_y"]), int(self.log_dict[b"map_x"])
    except:
        return 0, 0
def get_size(self):
    try:
        return int(self.log_dict[b"map_x"]), int(self.log_dict[b"map_y"]), int(self.log_dict[b"map_z"])
    except:
        return 0, 0, 0
def get_sub_idx(self, x_idx, y_idx):
    try:
        return y_idx * int(self.log_dict[b"map_x"]) + x_idx
    except:
        return 0

def set_cfp(self, file_path, x, y, z=1):
    # ファイルの存在チェック
    if os.path.exists(file_path):
        # 既に一度書かれていたら、一度削除
        if b"[cfp]" in self.log_other:
            deleted_length = delete_cfp(file_path)
        else:
            deleted_length = 0
        inserted_length = generate_cfp(file_path, x, y, z)
        update_logsizd(file_path, self.flogoff, inserted_length-deleted_length)
    else:
        from . import popups
        warning_popup = popups.WarningPopup("Cannot find the original '.spc' file. \nIt could be moved or deleted. \nThe Cell Free Position will not be saved.")
        warning_popup.exec_()
        return
    # 実際に更新されたバイナルファイルに合うように、辞書など追加
    self.log_other.append(b"[cfp]")
    self.log_dict[b"cfp_x"] = x
    self.log_dict[b"cfp_y"] = y
    self.log_dict[b"cfp_z"] = z
def generate_cfp(file_path, x, y, z=1):
    with open(file_path,'rb+') as f:
        insert_txt = ("\n[cfp]\r\ncfp_x=%d\r\ncfp_y=%d\r\ncfp_z=%d\r\n[cfp]\r\n"%(x, y, z)).encode("utf-8")
        insert(f, insert_txt, -1, 2)
    return len(insert_txt)
def delete_cfp(file_path):
    with open(file_path,'rb+') as f:
        remove_re = b"\n\[cfp\]\r\ncfp_x=[0-9]+\r\ncfp_y=[0-9]+\r\ncfp_z=[0-9]+\r\n\[cfp\]\r\n"
        matchedObject = remove_between(f, remove_re)
    return len(matchedObject.group(0))

# 書き込み
def write_to_binary(self, file_path, master_key, key_list, data_list, log_dict=True):
    # ファイルの存在チェック
    if os.path.exists(file_path):
        np.set_printoptions(threshold=np.inf)   # これ必要です
        # 書き込み
        txt_data = "\r\n".join(["{0}={1}".format(key, data2txt(data)) for key, data in zip(key_list, data_list)])
        with open(file_path,'rb+') as f:
            insert_txt = ("\n[{0}]\r\n{1}\r\n[{0}]\r\n".format(master_key, txt_data)).encode("utf-8")
            insert(f, insert_txt, -1, 2)
        update_logsizd(file_path, self.flogoff, len(insert_txt))
    else:
        from . import popups
        warning_popup = popups.WarningPopup("Cannot find the original '.spc' file. \nIt could be moved or deleted.")
        warning_popup.exec_()
        return
    # 実際に更新されたバイナルファイルに合うように、辞書など追加
    if log_dict:
        for key, data in zip(key_list, data_list):
            self.log_dict[key.encode()] = data
        self.log_other.append("[{0}]".format(master_key).encode())
def data2txt(data):
    return str(data).replace("\n", "").replace(" ", "")
# 削除
def delete_from_binary(self, file_path, master_key, key_list, log_dict=True):
    # ファイルの存在チェック
    if os.path.exists(file_path):
        with open(file_path, 'rb+') as f:
            # CRR results 除去
            remove_re = "\n\[{0}\]\r\n.+\r\n\[{0}\]\r\n".format(master_key).encode()
            matchedObject = remove_between(f, remove_re, flags=re.DOTALL)
            # logsizd を update
            update_logsizd(file_path, flogoff=None, added_length= -len(matchedObject.group(0)))
    else:
        from . import popups
        warning_popup = popups.WarningPopup("Cannot find the original '.spc' file. \nIt could be moved or deleted.")
        warning_popup.exec_()
        return
    if log_dict:
        for key in key_list:
            del self.log_dict[key.encode()]
        self.log_other.remove("[{0}]".format(master_key).encode())
# 更新
def update_binary(self, file_path, master_key, key_list, data_list, log_dict=True):
    self.delete_from_binary(file_path, master_key, key_list, log_dict=log_dict)
    self.write_to_binary(file_path, master_key, key_list, data_list, log_dict=log_dict)
def modify_prep_order(self, file_path, mode, key, kwargs, log_dict):
    new_prep_order = self.log_dict[b"prep_order"]
    if mode == "remove":
        for idx, prep in enumerate(new_prep_order):
            if prep[0] == key:
                break
        else:
            raise Exception("error {0}".foramt(new_prep_order))
        del new_prep_order[idx]
    if mode == "append":
        new_prep_order.append([key, kwargs])
    self.update_binary(file_path, master_key="PreP", key_list=["prep_order"], data_list=[new_prep_order], log_dict=log_dict)
# to ndArray with shape(self.fnsub, self.fnpts)
def toNumPy_2dArray(self):
    spc_set = np.full((self.fnsub, self.fnpts), np.nan, dtype=float)
    for sub_idx in range(self.fnsub):
        spc_set[sub_idx] = self.sub[sub_idx].y
    return spc_set
def fmNumPy_2dArray(self, numpy2dArray):
    for sub_idx, data in enumerate(numpy2dArray):
        self.sub[sub_idx].y = data
def spc_transplant(acceptor_spc, donor_spc):
    for sub_idx in range(donor_spc.fnsub):
        acceptor_spc.sub[sub_idx].y[:] = donor_spc.sub[sub_idx].y
def spc_init(spc_file, file_path):
    ###
    # 古いバージョンで開いたspcファイルは、log blockのサイズ (self.logsizd) 情報がupdateされていないものがある。それの対処。
        # flogoff + logtxto ~ flogoff + logtxto + logsizd
    # を読んでるから、長く読んでしまっていた。正しくは下記。（オリジナルの spc.py のライブラリを編集して使うこと）
        # flogoff + logtxto ~ flogoff + logtxto + logsizd - logtxto
    # logファイルは幸いなことに一番最後に書かれてる（プラスして\x00が1文字入ってはいるが）:一致してるかを見る

    print("init")

    update = legacy_function_to_correct_logsizd(file_path, spc_file.flogoff, spc_file.length)
    if update:
        spc_file = open_spc_spcl(file_path)
    ###
    # Preprocesses の前処理
    if b"[PreP]" not in spc_file.log_other:
        new_prep_order = []
        spc_file.write_to_binary(file_path, master_key="PreP", key_list=["prep_order"], data_list=[new_prep_order], log_dict=True)
    else:
        new_prep_order = eval(spc_file.log_dict[b"prep_order"].decode("utf-8"))
    # サイズ
    if b"[map_size]" not in spc_file.log_other:
        product_x_list, product_y_list = into_2_products(spc_file.fnsub)
        middle_idx = int(len(product_x_list) / 2)
        x = product_x_list[middle_idx]
        y = product_y_list[middle_idx]
        z = 1
        size = [x, y, z]
        spc_file.write_to_binary(file_path, master_key="map_size", key_list=["map_x", "map_y", "map_z"], data_list=size, log_dict=True)        
    else:
        size = spc_file.get_size()
    for prep in new_prep_order:
        if prep[0] == "set_size":
            break
    else:
        new_prep_order.append(["set_size", {"size":None, "mode":"init"}])
    # CRR
    if b'[CRR]' in spc_file.log_other:
        spc_file.log_dict[b"cosmic_ray_locs"] = eval(spc_file.log_dict[b"cosmic_ray_locs"].replace(b"array", b"np.array"))
        spc_file.log_dict[b"cosmic_ray_removal_params"] = eval(spc_file.log_dict[b"cosmic_ray_removal_params"].replace(b"array", b"np.array"))
        # 古いファイルでCRRしてる時用
        if ["CRR_master", {"ask":False, "mode":"init"}] not in new_prep_order:
            new_prep_order.append(["CRR_master", {"ask":False, "mode":"init"}])
    else:
        pass
    # NR
    if b'[NR]' in spc_file.log_other:
        spc_file.log_dict[b"noise_reduction_params"] = eval(spc_file.log_dict[b"noise_reduction_params"].replace(b"array", b"np.array"))
        # 古いファイルでNRは使用していいない（記録されない仕様）
    else:
        pass
    spc_file.update_binary(file_path, master_key="PreP", key_list=["prep_order"], data_list=[new_prep_order], log_dict=True)
    return spc_file

class CustomColorButton(QPushButton):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("QPushButton{border:1px solid black; background-color:white}")
        self.btn_color = (255,255,255,255)
    def set_color(self, rgba_color):
        self.btn_color = rgba_color
        self.setStyleSheet("QPushButton{border:1px solid black; background-color:rgba%s}"%str(rgba_color))
class HorizontalLayout(QHBoxLayout):
    def __init__(self, widgets, stretch=False):
        super().__init__()
        for widget in widgets:
            self.addWidget(widget)
        if stretch:
            self.addStretch(1)

# settings 設定 popup ##########################
class SettingsPopup(QDialog):
    def __init__(self, settings):
        super().__init__()
        self.setWindowTitle("Preferences")
        # ボタン
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")
        btn_ok.clicked.connect(self.btn_ok_clicked)
        btn_cancel.clicked.connect(self.btn_cancel_clicked)
        ok_cancel_layout = QHBoxLayout()
        ok_cancel_layout.addStretch(1)
        ok_cancel_layout.addWidget(btn_cancel)
        ok_cancel_layout.addWidget(btn_ok)
        # タブ
        self.temp_settings = {}
        self.settings = settings
        tab = QTabWidget()
        tab.addTab(ColorSettings(parent=self), "color")
        tab.addTab(PathSettings(parent=self), "path")
        # レイアウト
        layout = QVBoxLayout()
        layout.addWidget(tab)
        layout.addLayout(ok_cancel_layout)
        self.setLayout(layout)
    def btn_ok_clicked(self, event=None):
        for key, value in self.temp_settings.items():
            self.settings[key] = value
        # save_settings_file()
        with open(settings_path, mode='wb') as f:
            pickle.dump(self.settings, f)
        self.close()
    def btn_cancel_clicked(self, event=None):
        self.close()
class PathSettings(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        # 中身
        self.last_opened_dir = QLineEdit(self.parent.settings["last opened dir"])
        self.method_dir = QLineEdit(self.parent.settings["method dir"])
        self.plugin_dir = QLineEdit(self.parent.settings["plugin dir"])
        btn_set_last_opened_dir = QPushButton("...")
        btn_set_method_dir = QPushButton("...")
        btn_set_plugin_dir = QPushButton("...")
        # レイアウト
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.addLayout(HorizontalLayout([QLabel("last opened file folder")], stretch=False))
        layout.addLayout(HorizontalLayout([self.last_opened_dir, btn_set_last_opened_dir]))
        layout.addItem(QSpacerItem(0,5))
        layout.addLayout(HorizontalLayout([QLabel("last opened method folder")], stretch=False))
        layout.addLayout(HorizontalLayout([self.method_dir, btn_set_method_dir]))
        layout.addItem(QSpacerItem(0,5))
        layout.addLayout(HorizontalLayout([QLabel("plugin directory (reboot to apply)")], stretch=False))
        layout.addLayout(HorizontalLayout([self.plugin_dir, btn_set_plugin_dir]))
        layout.addItem(QSpacerItem(0,5))
        layout.addStretch(1)
        self.setLayout(layout)
        # イベントコネクト
        btn_set_last_opened_dir.clicked.connect(self.set_last_opened_dir)
        btn_set_method_dir.clicked.connect(self.set_method_dir)
        btn_set_plugin_dir.clicked.connect(self.set_plugin_dir)

    def set_last_opened_dir(self, event=None):
        dir_path = QFileDialog.getExistingDirectory(self, 'select folder', settings["last opened dir"])
        settings["last opened dir"] = dir_path
    def set_method_dir(self, event=None):
        dir_path = QFileDialog.getExistingDirectory(self, 'select folder', settings["method dir"])
        settings["method dir"] = dir_path
    def set_plugin_dir(self, event=None):
        dir_path = QFileDialog.getExistingDirectory(self, 'select folder', settings["plugin dir"])
        settings["plugin dir"] = dir_path

class ColorSettings(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        # 中身
        self.bg_brush = CustomColorButton()
        self.bg_brush.clicked.connect(functools.partial(self.get_color, btn_type="bg_brush"))
        self.graph_line = CustomColorButton()
        self.graph_line.clicked.connect(functools.partial(self.get_color, btn_type="graph_line"))
        self.o_color = CustomColorButton()
        self.o_color.clicked.connect(functools.partial(self.get_color, btn_type="o_color"))
        self.a_color = CustomColorButton()
        self.a_color.clicked.connect(functools.partial(self.get_color, btn_type="a_color"))
        self.u_color = CustomColorButton()
        self.u_color.clicked.connect(functools.partial(self.get_color, btn_type="u_color"))
        self.set_icon_color()
        # ボタン
        btn_reset = QPushButton("Reset")
        btn_reset.clicked.connect(self.btn_reset_clicked)
        # レイアウト
        grid_layout = QGridLayout()
        grid_layout.addWidget(QLabel("color"), 0, 1)
        grid_layout.addWidget(QLabel("graph background\n(reboot to apply)"), 1, 0)
        grid_layout.addWidget(self.bg_brush, 1, 1)
        grid_layout.addWidget(QLabel("graph lines\n(reboot to apply)"), 2, 0)
        grid_layout.addWidget(self.graph_line, 2, 1)
        grid_layout.addWidget(QLabel("original spectrum"), 3, 0)
        grid_layout.addWidget(self.o_color, 3, 1)
        grid_layout.addWidget(QLabel("added spectrum"), 4, 0)
        grid_layout.addWidget(self.a_color, 4, 1)
        grid_layout.addWidget(QLabel("unmixed spectrum"), 5, 0)
        grid_layout.addWidget(self.u_color, 5, 1)
        reset_layout = QHBoxLayout()
        reset_layout.addStretch(1)
        reset_layout.addWidget(btn_reset)
        layout = QVBoxLayout()
        layout.addLayout(grid_layout)
        layout.addLayout(reset_layout)
        self.setLayout(layout)
    def set_icon_color(self):
        for key, value in self.parent.settings.items():
            try:
                getattr(self, key).set_color(value)
            except:
                pass
    def get_color(self, event=None, btn_type=None):
        cur_btn = getattr(self, btn_type)
        color_dialog = QColorDialog(QColor(*cur_btn.btn_color))
        done = color_dialog.exec_()
        if done == 1:
            color = color_dialog.selectedColor().getRgb()
            cur_btn.setStyleSheet("QPushButton{border:1px solid black; background-color:rgba%s}"%str(color))
            self.parent.temp_settings[btn_type] = color
    def btn_reset_clicked(self, event=None):
        for key in default_keys:
            value = eval(key)
            self.parent.temp_settings[key] = value
            try:
                getattr(self, key).setStyleSheet("QPushButton{border:1px solid black; background-color:rgba%s}"%str(value))
            except:
                pass

###########################

# アンミックスメソッド。中身は基本、spcを踏襲する形で…
class UnmixingMethod():
    def __init__(self, procedures, *argsm, **kwargs):
        self.version = "2.0"
        self.spc_like_list = []
        self.file_path_list = []    # spc_like_listとindexごとに対応
        self.isBackgroundSet = False
        self.procedures = procedures    # 文字列からなるリスト形式å
        self.target_range = [None, None]
    # def add_spectrum(self, x_list, y_list):
    #     # subFileの作成
    #     subLike = SubLike()
    #     sub_like.init_fmt(self.spc_file.sub[0])
    #     subLike.add_data(y_list, sub_idx=0)
    #     # spcFileの作成
    #     spcLike = SpcLike()
    #     spcLike.x = x_list
    #     spcLike.add_subLike(subLike)
    #     self.spc_like_list.append(spcLike)
    # def add_spc_file(self, spc_file):
    #     self.spc_file_list.append(spc_file)
    


# スペクトル描画の際はspcファイル毎にwidgetに渡されるので、その形に似せといたほうが良い
#  {
    # 'length': 5573, 
    # 'ftflg': b'\x00', 
    # 'fversn': b'K', 
    # 'fexper': 11, 
    # 'fexp': 128, 
    # 'fnpts': 1015, 
    # 'ffirst': 4708.185546875, 
    # 'flast': 100.810546875, 
    # 'fnsub': 1, 
    # 'fxtype': 13, 
    # 'fytype': 4, 
    # 'fztype': 0, 
    # 'fpost': b'\x00', 
    # 'fdate': 1282953736, 
    # 'fres': b'\x00\x00\x00\x00\x00\x00\x00\x00\x00', 
    # 'fsource': b'\x00\x00\x00\x00\x00\x00\x00\x00\x00', 
    # 'fpeakpt': 0, 
    # 'fspare': b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', 
    # 'fcmnt': "b'\\x92P\\x88\\xea\\x83X\\x83L\\x83\\x83\\x83\\x93\\x91\\xaa\\x92\\xe8 6\\xe6\\xb8\\xac\\xe5\\xae\\x9a 6\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'", 
    # 'fcatxt': b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', 
    # 'flogoff': 4604, 
    # 'fmods': 0, 
    # 'fprocs': b'\x00', 
    # 'flevel': b'\x00', 
    # 'fsampin': 0, 
    # 'ffactor': 0.0, 
    # 'fmethod': b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', 
    # 'fzinc': 0.0, 
    # 'fwplanes': 0, 
    # 'fwinc': 0.0, 
    # 'fwtype': b'\x00', 
    # 'freserv': b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', 
    # 'tsprec': False, 
    # 'tcgram': False, 
    # 'tmulti': False, 
    # 'trandm': False, 
    # 'tordrd': False, 
    # 'talabs': False, 
    # 'txyxys': False, 
    # 'txvals': False, 
    # 'year': 1223, 
    # 'month': 8, 
    # 'day': 10, 
    # 'hour': 8, 
    # 'minute': 8, 
    # 'cmnt': "b'\\x92P\\x88\\xea\\x83X\\x83L\\x83\\x83\\x83\\x93\\x91\\xaa\\x92\\xe8 6\\xe6\\xb8\\xac\\xe5\\xae\\x9a 6\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'", 
    # 'dat_fmt': 'gx-y', 
    # 'x': array([4708.18554688, 4703.64178455, 4699.09802222, ...,  109.89807153, 105.3543092 ,  100.81054688]), 
    # 'sub': [<spc.sub.subFile object at 0x7fc650a2ec50>], 
    # 'logsizd': 968, 
    # 'logsizm': 4096, 
    # 'logtxto': 64, 
    # 'logbins': 0, 
    # 'logdsks': 0, 
    # 'logspar': b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', 
    # 'log_content': [
    #     b'Operator=Raman', 
    #     b'Scan_type=Static', 
    #     b'Measurement_type=SingleScan', 
    #     b'XListType=1', b'YListType=4', 
    #     b'Description=WiRE \x83X\x83y\x83N\x83g\x83\x8b\x8e\xe6\x93\xbe\x83E\x83B\x83U\x81[\x83h\x82\xc9\x82\xe6\x82\xe8\x90\xb6\x90\xac\x82\xb3\x82\xea\x82\xbd\x92P\x88\xea\x83X\x83L\x83\x83\x83\x93\x91\xaa\x92\xe8\x81B', 
    #     b'Filter_wavenum=Image wavenumber: 2750', 
    #     b'Exposure_time=Time: 1000', 
    #     b'Accumulations=Accumulations: 30', 
    #     b'Cosmic_ray_removal=Cosmic ray removal: 0', 
    #     b'Camera_gain=Gain: High', 
    #     b'Camera_speed=Speed: Low', 
    #     b'Camera_Serial_Number=0MCN30', 
    #     b'Serial_number=11RQ83', 
    #     b'Laser=Laser: 532 nm edge', 
    #     b'Grating_grooves=Grating: 600 l/mm', 
    #     b'Focus_mode=Confocal', 
    #     b'Laser_power=Laser_power: 100%', 
    #     b'Laser_focus=Laser focus: 0 Percent', 
    #     b'Pinhole=Out', 
    #     b'Podule_upper_selector_wheel=Laser', 
    #     b'Podule_lower_selector_wheel=Sample', 
    #     b'Calibration_lamp=Off', 
    #     b'Calibration_lamp_intensity=0', 
    #     b'Illumination_lamp=Off', 
    #     b'Illumination_lamp_intensity=0', 
    #     b'Neon_lamp=Off', 
    #     b'Slit_opening=20\x83\xcam', 
    #     b'', 
    #     b'[WiRE2 ZeroLevelAndDarkCurrent]', 
    #     b'Version=5.0.1.7483', 
    #     b'24/04/2018 19:16:50', 
    #     b'Operator=Raman', 
    #     b'[WiRE2 ZeroLevelAndDarkCurrent]', 
    #     b''
    #     ], 
    # 'log_dict': {
    #     b'Operator': b'Raman', 
    #     b'Scan_type': b'Static', 
    #     b'Measurement_type': b'SingleScan', 
    #     b'XListType': b'1', 
    #     b'YListType': b'4', 
    #     b'Description': b'WiRE \x83X\x83y\x83N\x83g\x83\x8b\x8e\xe6\x93\xbe\x83E\x83B\x83U\x81[\x83h\x82\xc9\x82\xe6\x82\xe8\x90\xb6\x90\xac\x82\xb3\x82\xea\x82\xbd\x92P\x88\xea\x83X\x83L\x83\x83\x83\x93\x91\xaa\x92\xe8\x81B', 
    #     b'Filter_wavenum': b'Image wavenumber: 2750', 
    #     b'Exposure_time': b'Time: 1000', 
    #     b'Accumulations': b'Accumulations: 30', 
    #     b'Cosmic_ray_removal': b'Cosmic ray removal: 0', 
    #     b'Camera_gain': b'Gain: High', 
    #     b'Camera_speed': b'Speed: Low', 
    #     b'Camera_Serial_Number': b'0MCN30', 
    #     b'Serial_number': b'11RQ83', 
    #     b'Laser': b'Laser: 532 nm edge', 
    #     b'Grating_grooves': b'Grating: 600 l/mm', 
    #     b'Focus_mode': b'Confocal', 
    #     b'Laser_power': b'Laser_power: 100%', 
    #     b'Laser_focus': b'Laser focus: 0 Percent', 
    #     b'Pinhole': b'Out', 
    #     b'Podule_upper_selector_wheel': b'Laser', 
    #     b'Podule_lower_selector_wheel': b'Sample', 
    #     b'Calibration_lamp': b'Off', 
    #     b'Calibration_lamp_intensity': b'0', 
    #     b'Illumination_lamp': b'Off', 
    #     b'Illumination_lamp_intensity': b'0', 
    #     b'Neon_lamp': b'Off', 
    #     b'Slit_opening': b'20\x83\xcam', 
    #     b'Version': b'5.0.1.7483'
    #     }, 
    # 'log_other': [
    #     b'', 
    #     b'[WiRE2 ZeroLevelAndDarkCurrent]', 
    #     b'24/04/2018 19:16:50', 
    #     b'[WiRE2 ZeroLevelAndDarkCurrent]', 
    #     b''
    # ], 
    # 'spacing': -4.543762327416173, 
    # 'xlabel': 'Raman Shift (cm-1)', 
    # 'zlabel': 'Arbitrary', 
    # 'ylabel': 'Counts', 
    # 'exp_type': 'Fluorescence Spectrum'
    # }
# {
    # 'subflgs': 0, 
    # 'subexp': 128, 
    # 'subindx': 0, 
    # 'subtime': 0.0, 
    # 'subnext': 0.0, 
    # 'subnois': 0.0, 
    # 'subnpts': 1015, 
    # 'subscan': 30, 
    # 'subwlevel': 0.0, 
    # 'subresv': b'\x00\x00\x00\x00', 
    # 'y': array([149.07777405, 137.9009552 , 131.74209595, ..., 255.42512512, 250.27589417, 209.69833374])
    # }
class SpcLike(spc.File):
    def __init__(self):
        # main header
        self.length = None
        self.ftflg = None
        self.fversn = b'\x4b'   # NEW FORMAT (LSB)
        self.fexper = None
        self.fexp = None
        self.fnpts = None
        self.ffirst = None
        self.flast = None
        self.fnsub = 0
        self.fxtype = None
        self.fytype = None
        self.fztype = None
        self.fpost = None
        self.fdate = None
        self.fres = None
        self.fsource = None
        self.fpeakpt = None
        self.fspare = None
        self.fcmnt = None
        self.fcatxt = None
        self.flogoff = 512
        self.fmods = None
        self.fprocs = None
        self.flevel = None
        self.fsampin = None
        self.ffactor = None
        self.fmethod = None
        self.fzinc = None
        self.fwplanes = None
        self.fwinc = None
        self.fwtype = None
        self.freserv = None
        #
        self.tsprec = None
        self.tcgram = None
        self.tmulti = None
        self.trandm = None
        self.tordrd = None
        self.talabs = False     ###
        self.txyxys = False     # if True, x values are given
        self.txvals = False     # if True, only one subfile, which contains the x data
        self.year = None
        self.month = None
        self.day = None
        self.hour = None
        self.minute = None
        self.cmnt = None
        self.dat_multi = None
        self.dat_fmt = None     # "-xy", "x-y" or "gx-y"
        self.x = None
        self.sub = []
        # log header
        self.logsizd = 64
        self.logsizm = 4096
        self.logtxto = 64
        self.logbins = 0
        self.logdsks = 0
        self.logspar = b"\x00" * 44
        # log information
        self.log_content = None
        self.log_dict = None
        self.log_other = None
        # additional information
        self.spacing = None
        self.xlabel = None
        self.zlabel = None
        self.ylabel = None
        self.exp_type = None
    def init_fmt(self, spc_file):
        attrib_list = [
            "ftflg", 
            "fversn", 
            "fexper", 
            "fexp", 
            "fxtype", 
            "fytype", 
            "fztype", 
            "fpost", 
            "fres", 
            "fsource", 
            "fpeakpt", 
            "fspare", 
            "fcmnt", 
            "fcatxt", 
            "fmods", 
            "fprocs", 
            "flevel", 
            "fsampin", 
            "ffactor", 
            "fmethod", 
            "fzinc", 
            "fwplanes", 
            "fwinc", 
            "fwtype", 
            "freserv", 
            #
            "log_content"
        ]
        for attrib in attrib_list:
            setattr(self, attrib, getattr(spc_file, attrib))
        self.fdate = datetime2decimal(datetime.datetime.now())
    def set_labels(self, fxtype=0, fytype=0, fztype=0):
        self.fxtype, self.fytype, self.fztype = fxtype, fytype, fztype
        super().set_labels()
        # --------------------------
        # units for x,z,w axes
        # --------------------------
        # fxtype_op = ["Arbitrary",
        #              "Wavenumber (cm-1)",
        #              "Micrometers (um)",
        #              "Nanometers (nm)",
        #              "Seconds ",
        #              "Minutes", 
        #              "Hertz (Hz)",
        #              "Kilohertz (KHz)",
        #              "Megahertz (MHz) ",
        #              "Mass (M/z)",
        #              "Parts per million (PPM)",
        #              "Days",
        #              "Years",
        #              "Raman Shift (cm-1)",
        #              "eV",
        #              "XYZ text labels in fcatxt (old 0x4D version only)",
        #              "Diode Number",
        #              "Channel",
        #              "Degrees",
        #              "Temperature (F)",
        #              "Temperature (C)",
        #              "Temperature (K)",
        #              "Data Points",
        #              "Milliseconds (mSec)",
        #              "Microseconds (uSec) ",
        #              "Nanoseconds (nSec)",
        #              "Gigahertz (GHz)",
        #              "Centimeters (cm)",
        #              "Meters (m)",
        #              "Millimeters (mm)",
        #              "Hours"]
        # --------------------------
        # units y-axis
        # --------------------------
        # fytype_op = ["Arbitrary Intensity",
        #              "Interferogram",
        #              "Absorbance",
        #              "Kubelka-Munk",
        #              "Counts",
        #              "Volts",
        #              "Degrees",
        #              "Milliamps",
        #              "Millimeters",
        #              "Millivolts",
        #              "Log(1/R)",
        #              "Percent",
        #              "Intensity",
        #              "Relative Intensity",
        #              "Energy",
        #              "",
        #              "Decibel",
        #              "",
        #              "",
        #              "Temperature (F)",
        #              "Temperature (C)",
        #              "Temperature (K)",
        #              "Index of Refraction [N]",
        #              "Extinction Coeff. [K]",
        #              "Real",
        #              "Imaginary",
        #              "Complex"]
        # fytype_op2 = ["Transmission",
        #               "Reflectance",
        #               "Arbitrary or Single Beam with Valley Peaks",
        #               "Emission"]
    def add_xData(self, xData):
        self.x = xData
        self.fnpts = len(self.x)
        self.ffirst = self.x[0]
        self.flast = self.x[-1]
    def add_subLike(self, subLike):
        fnpts = len(subLike.y)
        if self.fnpts != fnpts:
            raise Exception("self.fnpts and length of added spectrum does not match")
        self.fnsub += 1
        self.sub.append(subLike)
    def add_empty_subLike(self, N):
        for i in range(N):
            sub_like = SubLike()
            sub_like.add_data(y_list=np.zeros_like(self.x), sub_idx=self.fnsub)
            self.fnsub += 1
            self.sub.append(sub_like)
    def save_as_spcl(self, save_path):
        with open(save_path, 'wb') as f:
            pickle.dump(self, f)
    def save_as_spc(self, save_path):
        from . import popups
        self.pbar_widget = popups.ProgressBarWidget(parent=self, message="Exporting spc file... please wait.        ")
        self.pbar_widget.show()
        segment_list = self.pbar_widget.get_segment_list(self.fnsub, segment=95)
        QCoreApplication.processEvents()
        # data block
        sub_str_all = "<"
        sub_data_all = []
        for i, sub in enumerate(self.sub):
            sub_str, sub_data = sub.toPrepareBinary()
            sub_str_all += sub_str
            sub_data_all += sub_data
            # プログレスバー処理
            if i in segment_list:
                self.pbar_widget.addValue(1)
                QCoreApplication.processEvents()
        datablock_binary = struct.pack(sub_str_all, *sub_data_all)
        self.flogoff = len(datablock_binary) + 512  # main header の分
        # log block
        logblock_binary = self.logblock2binary()
        # main header block (512)
        mainheader_binary = self.mainheader2binary()
        # connect
        spcfile_binary = mainheader_binary + datablock_binary + logblock_binary + b"\x00"
        with open(save_path, 'wb') as f:
            f.write(spcfile_binary)
        # プログレスバー閉じる
        self.pbar_widget.is_close_allowed = True
        self.pbar_widget.close()
    def mainheader2binary(self):
        # byte 文字列にする
        self.fexper = self.fexper.to_bytes(1, byteorder="little")
        self.fexp = self.fexp.to_bytes(1, byteorder="little")
        self.fxtype = self.fxtype.to_bytes(1, byteorder="little")
        self.fytype = self.fytype.to_bytes(1, byteorder="little")
        self.fztype = self.fztype.to_bytes(1, byteorder="little")
        self.fcmnt = self.fcmnt.encode('utf-8')
        attrib_list = [
            "ftflg", 
            "fversn", 
            "fexper", 
            "fexp", 
            "fnpts",    ###
            "ffirst",   ###
            "flast",    ###
            "fnsub",    ###
            "fxtype", 
            "fytype", 
            "fztype", 
            "fpost", 
            "fdate",    ###
            "fres", 
            "fsource", 
            "fpeakpt", 
            "fspare", 
            "fcmnt", 
            "fcatxt", 
            "flogoff",  ###
            "fmods", 
            "fprocs", 
            "flevel", 
            "fsampin", 
            "ffactor", 
            "fmethod", 
            "fzinc", 
            "fwplanes", 
            "fwinc", 
            "fwtype", 
            "freserv"
        ]
        head_str = "<cccciddicccci9s9sh32s130s30siicchf48sfifc187s"
        attrib_data = [getattr(self, attrib) for attrib in attrib_list]
        return struct.pack(head_str, *attrib_data)
    def logblock2binary(self):
        # log dict
        logcontent_binary = b"\r\n".join(self.log_content)
        logcontent_binary = logcontent_binary.replace(b"\r\n\r\n", b"\r\n\n")
        self.logsizd = len(logcontent_binary) + 64
        # log header
        attrib_list = [
            "logsizd", 
            "logsizm", 
            "logtxto", 
            "logbins", 
            "logdsks", 
            "logspar"
        ]
        loghead_str = "<iiiii44s"
        attrib_data = [getattr(self, attrib) for attrib in attrib_list]
        loghead_binary = struct.pack(loghead_str, *attrib_data)
        return loghead_binary + logcontent_binary
class SubLike(subFile):
    def __init__(self, *argsm, **kwargs):
        self.subflgs = None
        self.subexp = 128       #  Floating y-values
        self.subindx = None     ###
        self.subtime = None
        self.subnext = None
        self.subnois = None
        self.subnpts = None     ###
        self.subscan = None
        self.subwlevel = None
        self.subresv = None
        self.y = None
    def init_fmt(self, sub):
        attrib_list = [
            "subflgs", 
            "subtime", 
            "subnext", 
            "subnois", 
            "subscan", 
            "subwlevel", 
            "subresv"
        ]
        for attrib in attrib_list:
            setattr(self, attrib, getattr(sub, attrib))
    def add_data(self, y_list, sub_idx):
        self.y = y_list
        self.subindx = sub_idx
        self.subnpts = len(self.y)
    def toPrepareBinary(self):
        self.subflgs = self.subflgs.to_bytes(1, byteorder="little")
        self.subexp = self.subexp.to_bytes(1, byteorder="little")
        subhead_str = "ccHfffiif4s" # <
        subattrib_list = [
            "subflgs", 
            "subexp",  ##
            "subindx", ###
            "subtime", 
            "subnext", 
            "subnois", 
            "subnpts", ###
            "subscan", 
            "subwlevel", 
            "subresv"
        ]
        subattrib_data = [getattr(self, attrib) for attrib in subattrib_list]
        return subhead_str + "f"*self.subnpts, subattrib_data + list(self.y)
def open_spc_spcl(file_path):
    # spcファイルの場合
    if file_path.endswith(".spc"):
        spc_file = spc.File(file_path)
    # spclファイル（自作漬物ファイル）の場合
    elif file_path.endswith(".spcl"):
        with open(file_path, 'rb') as f:
            spc_file = pickle.load(f)
    return spc_file

def legacy_function_to_correct_logsizd(file_path, flogoff, length):
    with open(file_path, "rb+") as f:
        f.seek(flogoff)
        logsizd_written = struct.unpack("<i".encode("utf-8"), f.read(4))[0]
        logsizd_actual = length - flogoff - 1   # 最後1文字 "\x00" が入っているため
        # これらが一致していない場合、古いファイルです ➙ 一致させるようにupdateする
        if logsizd_written != logsizd_actual:
            from . import popups
            warning_popup = popups.WarningPopup("Old file was opened. Automatically updated.")
            warning_popup.exec_()
            f.seek(flogoff)
            f.write(struct.pack("<i".encode("utf-8"), logsizd_actual))
            update = True
        else:
            update = False
    return update

# return nd_array(fnsub, fnpts) version of spc_file
def spc2ndarray(spc_file):
    x = spc_file.fnpts
    y = spc_file.fnsub
    data_set = np.empty((y, x), dtype=float)
    for sub_idx in range(y):
        data_set[sub_idx] = spc_file.sub[sub_idx].y
    return data_set

def datetime2decimal(dt_now):
    year = dt_now.year
    month = dt_now.month
    day = dt_now.day
    hour = dt_now.hour
    minute = dt_now.minute
    d = (year << 20) \
         + (month << 16) \
         + (day << 11) \
         + (hour << 6) \
         + minute 
    return d






