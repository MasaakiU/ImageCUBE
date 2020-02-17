# -*- Coding: utf-8 -*-

import numpy as np
import re

from . import popups
from . import general_functions as gf

def open_output_file(file_path):
    with open(file_path, "r") as f:
        output_all = f.readlines()
    # 正常終了であるかチェック
    for line in output_all[-5:]:
        if "****ORCA TERMINATED NORMALLY****" in line:
            break
    else:
        warning_popup = popups.WarningPopup("The file is broken or ORCA terminated improperly.")
        warning_popup.exec_()
        return None
    # ラマンが含まれてるかどうか
    for s_idx, line in enumerate(output_all[::-1]):
        if "RAMAN SPECTRUM" in line:
            break
    else:
        warning_popup = popups.WarningPopup("The file does not contains RAMAN SPECTRUM.")
        warning_popup.exec_()
        return None
    # スペクトル取得
    data_zone = False
    data_list = []
    for line in output_all[-s_idx-1:]:
        if "Mode" in line:
            col_names = line.replace("freq (", "freq(").split()
            data_zone = True
            continue
        elif not data_zone:
            continue
        else:
            data = line.strip().split()
            if len(data) != 0:
                data[0] = data[0].rstrip(":")
                data_list.append(data)
            else:
                break
    else:
        warning_popup = popups.WarningPopup("Some error in RAMAN SPECTRUM.")
        warning_popup.exec_()
        return None       
    # numpy array へ
    data_set = np.empty((len(data_list), len(col_names)), dtype=float)
    for idx, data in enumerate(data_list[1:]):
        data_set[idx, :] = data
    # 出力
    return Output(col_names, data_set.T)

# 
class Output(gf.SpcLike):
    def __init__(self, col_names, data_set):
        # properties not included in Spc files.
        self.col_names = col_names      # ['Mode', 'freq(cm**-1)', 'Activity', 'Depolarization']
        self.data_set = data_set   # shape = (len(col_names), N_peaks)
        self.N_cols, self.N_peaks = self.data_set.shape
        self.scaling = 0.945
        self.g_width = 3
        self.base_func = gf.gaussian_function
        # properties included in SPC files.
        super().__init__()
        self.set_labels(fxtype=13, fytype=4, fztype=0)
        self.set_x_by_gxy(ffirst=0, flast=5000, fnpts=5000)    # 初期設定
        self.add_empty_subLike(N=1)
        self.set_data(sub_idx=0)
    def set_x_by_gxy(self, ffirst, flast, fnpts):
        self.dat_fmt = "gx-y"   # no x values are given, but they can be generated
        self.ffirst = ffirst
        self.flast = flast
        self.fnpts = fnpts
        self.x = np.linspace(self.ffirst, self.flast, num=self.fnpts)
    def get_col_idx(self, name):
        return self.col_names.index(name)
    def set_data(self, sub_idx):
        freq_list = self.data_set[self.get_col_idx("freq(cm**-1)")]
        intn_list = self.data_set[self.get_col_idx("Activity")]
        y_list = np.zeros_like(self.x)
        for freq, intn in zip(freq_list, intn_list):
            y_list += self.base_func(self.x, u=freq, s=self.g_width, h=intn)
        self.x *= self.scaling
        self.sub[sub_idx].y[:] = y_list

    
















