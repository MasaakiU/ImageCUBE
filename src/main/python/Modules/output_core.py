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
    data_set_t = np.empty((len(data_list) - 1, len(col_names)), dtype=float)
    for idx, data in enumerate(data_list[1:]):
        data_set_t[idx, :] = data
    # 出力
    output = Output(col_names)
    output.add_data(data_set=data_set_t.T)
    return output

# 
class Output(gf.SpcLike):
    def __init__(self, col_names):
        # properties not included in Spc files.
        self.col_names = col_names      # ['Mode', 'freq(cm**-1)', 'Activity', 'Depolarization']
        self.scaling = 0.945
        self.g_width = 3
        self.base_func = gf.gaussian_function
        # properties included in SPC files.
        super().__init__()
        self.set_labels(fxtype=13, fytype=4, fztype=0)
        self.set_x_by_gxy(ffirst=0, flast=5000, fnpts=5000)    # 初期設定
        self.x_ori = np.copy(self.x)
        #
        self.log_dict = {}
        self.log_dict[b"prep_order"] = [['SCL_master', {"mode":None}]]
    def set_x_by_gxy(self, ffirst, flast, fnpts):
        self.dat_fmt = "gx-y"   # no x values are given, but they can be generated
        self.ffirst = ffirst
        self.flast = flast
        self.fnpts = fnpts
        self.x = np.linspace(self.ffirst, self.flast, num=self.fnpts)
    def add_data(self, data_set):
        self.add_empty_output_sub(N=1)
        self.sub[-1].data_set = data_set
        self.scl_changed(scl=self.scaling, wid=self.g_width)
    def add_empty_output_sub(self, N):
        for i in range(N):
            sub_like = OutputSub()
            sub_like.add_data(y_list=np.zeros_like(self.x), sub_idx=self.fnsub)
            self.fnsub += 1
            self.sub.append(sub_like)
    def get_col_idx(self, name):
        return self.col_names.index(name)
    def get_sub_activity(self, sub_idx):
        return self.sub[sub_idx].get_data(self.get_col_idx("Activity"))
    def get_sub_freq_list(self, sub_idx, scaling):
        if scaling:
            return self.sub[sub_idx].get_data(self.get_col_idx("freq(cm**-1)")) * self.scaling
        else:
            return self.sub[sub_idx].get_data(self.get_col_idx("freq(cm**-1)"))
    def scl_changed(self, scl=None, wid=None):
        if wid is not None:
            self.g_width = wid
            for sub_idx in range(self.fnsub):
                y_list = np.zeros_like(self.x_ori)
                for freq, intn in zip(self.get_sub_freq_list(sub_idx, scaling=False), self.get_sub_activity(sub_idx)):
                    y_list += self.base_func(self.x_ori, u=freq, s=self.g_width, h=intn)
                self.sub[sub_idx].y[:] = y_list
        if scl is not None:
            self.scaling = scl
            self.x = self.x_ori * self.scaling

class OutputSub(gf.SubLike):
    def __init__(self):
        super().__init__()
        self.data_set = None
    def get_data(self, idx):
        return self.data_set[idx]
















