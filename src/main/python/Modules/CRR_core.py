# -*- Coding: utf-8 -*-

import numpy as np
from numpy.linalg import lstsq
import copy

from . import popups
from . import general_functions as gf
from .cython import time_taking_calc as ttc

def divide_omitted_idx_set(spc_idx_list, is_data_diff_positive):    # shape(fnpts - 1), shape(fnpts - 1)
    crevas_idxes = np.argwhere(np.logical_not(np.diff(spc_idx_list) < gf.CRR_half_window1))[:, 0] + 1
    crevas_idxes = np.hstack(( np.array([0], dtype=int), crevas_idxes, np.array([len(spc_idx_list)], dtype=int) ))
    se_idx_set = []
    for s_crevas_idx, e_crevas_idx in zip(crevas_idxes[:-1], crevas_idxes[1:]):
        cur_spc_idx_list = spc_idx_list[s_crevas_idx:e_crevas_idx]
        cur_is_data_diff_positive = is_data_diff_positive[s_crevas_idx:e_crevas_idx]
        # is_data_diff_positive 中に、True, Falseの順で出現するものが必須。
        if not(cur_is_data_diff_positive.any() and np.logical_not(cur_is_data_diff_positive).any()):
            continue
        # s_crevas_idx について、最初にポジティブとなっているものを求める
        for s_idx, pn in zip(cur_spc_idx_list, cur_is_data_diff_positive):
            if pn:
                break
        else:
            raise Exception("some error")
        # e_crevas_idx について、最後にネガティブとなっているものを求める
        for e_idx, pn in zip(cur_spc_idx_list[::-1], cur_is_data_diff_positive[::-1]):
            if not pn:
                break
        else:
            raise Exception("some error")
        if s_idx < e_idx:
            se_idx_set.append([s_idx, e_idx])
    return se_idx_set
# sub_around_list: 上下左右の順
def confirm_cosmic_ray(sub_center, sub_around_list, omitted_se_idx_set):
    sub_center = np.diff(sub_center)
    selected_se_idx_set = []
    # 宇宙線候補領域毎に回していく
    for s_idx, e_idx in omitted_se_idx_set:
        e_idx -= 1      # np.diffするので、e_idx を調整
        # 宇宙線以外の領域を取得
        if gf.CRR_half_window1 <= s_idx:
            data_without_cosmic_ray_center = np.hstack([sub_center[s_idx-gf.CRR_half_window1:s_idx], sub_center[e_idx+1:e_idx+gf.CRR_half_window1+1]])
            s1 = s_idx-gf.CRR_half_window1
            e1 = e_idx+gf.CRR_half_window1+1
        else:
            # 端っこの方に宇宙線候補があって、gf.CRR_half_window1 を付け足すとはみ出る場合
            try:
                data_without_cosmic_ray_center = np.hstack([sub_center[0:s_idx], sub_center[e_idx+1:e_idx+gf.CRR_half_window1+1]])
                s1 = 0
                e1 = e_idx+gf.CRR_half_window1+1
            except:
                data_without_cosmic_ray_center = np.hstack([sub_center[s_idx-gf.CRR_half_window1:s_idx], sub_center[e_idx+1:]])
                s1 = s_idx-gf.CRR_half_window1
                e1 = len(sub_center)
        ave_without_cosmic_ray_center = data_without_cosmic_ray_center.mean()
        # 宇宙線近傍領域（±gf.half_window）を取得
        regional_sub_center = sub_center[s1:e1]
        std_regional_sub_center = regional_sub_center.std()
        # 格納庫
        isProminent_list = np.ones(4, dtype=bool)
        # 上下左右方向へ回す
        for idx, sub_around in enumerate(sub_around_list):
            # sub around が None の場合もあるので、try する
            try:
                sub_around = np.diff(sub_around)
                data_without_cosmic_ray_around = np.hstack([sub_around[s1:s_idx], sub_around[e_idx+1:e1]])
                # 宇宙線候補領域以外の周辺の平均で揃えて、宇宙線含めた ±gf.CRR_half_window1 領域全体でのの分散・残差平方和で補正
                regional_sub_around = sub_around[s1:e1]
                corrected_regional_sub_around = (regional_sub_around - data_without_cosmic_ray_around.mean()) / regional_sub_around.std() * std_regional_sub_center + ave_without_cosmic_ray_center
                # ±gf.CRR_half_window1 領域における残差二乗和の平均
                isProminent_list[idx] = (regional_sub_center - corrected_regional_sub_around).var() > regional_sub_around.var() * gf.CRR_SN
            except:
                pass
        if isProminent_list.all():
            selected_se_idx_set.append((s_idx, e_idx+1))    # 最初に e_idx-1してるので、戻す
    return selected_se_idx_set
def locate_cosmic_ray(spc_file):
    x_size = int(spc_file.log_dict[b"map_x"])
    # y_size = int(spc_file.log_dict[b"map_y"])
    candidate_cosmic_ray_locs = detect_cosmic_ray(spc_file, half_window1=gf.CRR_half_window1, half_window2=gf.CRR_half_window2, SN=gf.CRR_SN)   # shape(fnsub, fnpts - 1)
    omitted_se_idx_set_list = []
    cosmic_ray_sub_idx_list = []
    # ±gf.half_window の範囲で discrete になっており、かつ diff>0, diff<0 がセットになっているようなものを探す
    for sub_idx, candidate_cosmic_ray_loc in enumerate(candidate_cosmic_ray_locs):
        spc_idx_list = list(np.where(candidate_cosmic_ray_loc)[0])
        # スパイクの場合、最低でも2箇所（上って、下って）に優位に差がある点が出るはず
        if len(spc_idx_list) < 2:
            continue
        se_idx_set = divide_omitted_idx_set(spc_idx_list, (spc_file.sub[sub_idx].y[1:] > spc_file.sub[sub_idx].y[:-1])[spc_idx_list])   # shape(fnpts - 1), shape(fnpts - 1)
        # 上記スクリーニング操作で空になってしまったものは除く
        if len(se_idx_set):
            omitted_se_idx_set_list.append(se_idx_set)
            cosmic_ray_sub_idx_list.append(sub_idx)
    # 上下左右の4つのものと比較していき、宇宙線を最終選定
    cosmic_ray_locs = {} # cosmic_ray_locs = {sub_idx: [(s_idx, e_idx), ...]}
    for sub_idx, omitted_se_idx_set in zip(cosmic_ray_sub_idx_list, omitted_se_idx_set_list):
        sub_center = spc_file.sub[sub_idx].y
        cur_y, cur_x = divmod(sub_idx, x_size)
        TopBottomLeftRight_idxes = np.full(4, -1, dtype=int)
        # 上
        sub_up_idx = (cur_y - 1) * x_size + cur_x
        if (sub_up_idx >= 0) and (sub_up_idx not in cosmic_ray_sub_idx_list):
                                                                                    sub_up = spc_file.sub[sub_up_idx].y
                                                                                    TopBottomLeftRight_idxes[0] = sub_up_idx
        else:                                                                       sub_up = None
        # 下
        try:
            sub_down_idx = (cur_y + 1) * x_size + cur_x
            if sub_down_idx not in cosmic_ray_sub_idx_list:
                                                                                    sub_down = spc_file.sub[sub_down_idx].y
                                                                                    TopBottomLeftRight_idxes[1] = sub_down_idx
            else:                                                                   sub_down = None
        except:                                                                     sub_down = None
        # 左
        sub_left_idx = sub_idx - 1
        if (cur_x != 0) and (sub_left_idx not in cosmic_ray_sub_idx_list):
                                                                                    sub_left = spc_file.sub[sub_left_idx].y
                                                                                    TopBottomLeftRight_idxes[2] = sub_left_idx
        else:                                                                       sub_left = None
        # 右
        sub_right_idx = sub_idx + 1
        if (cur_x != x_size-1) and (sub_right_idx not in cosmic_ray_sub_idx_list):  
                                                                                    sub_right = spc_file.sub[sub_right_idx].y
                                                                                    TopBottomLeftRight_idxes[3] = sub_right_idx
        else:                                                                       sub_right = None
        # 周囲のデータを元に、データ補正を行う
        selected_se_idx_set = confirm_cosmic_ray(sub_center, [sub_up, sub_down, sub_left, sub_right], omitted_se_idx_set)
        if len(selected_se_idx_set):
            cosmic_ray_locs[sub_idx] = (selected_se_idx_set, TopBottomLeftRight_idxes, [])

    CRR_params = {"CRR_half_window":gf.CRR_half_window1, "CRR_SN":gf.CRR_SN}                        # ⇣original_data_set
    return cosmic_ray_locs, CRR_params    # cosmic_ray_locs = {sub_idx: ([(s_idx, e_idx), ...], np.array([top_idx, bottom_idx, left_idx, right_idx]), [])}

    # # 描画
    # for sub_idx in cosmic_ray_locs.keys():
    #     for s, e, other in cosmic_ray_locs[sub_idx]:
    #         print(sub_idx, "#", s, e, other)
    #         # a = MainWindowFmTest(np.diff(spc_file.sub[sub_idx].y), spc_file.sub[sub_idx].y, [s, e])
    #         # a.exec_()

# 太いCosmic Rayをしっかり検出できないかも。
def detect_cosmic_ray(spc_file, half_window1=gf.CRR_half_window1, half_window2=gf.CRR_half_window2, SN=gf.CRR_SN):
    data_set = gf.spc2ndarray(spc_file) # shape(fnsub, fnpts)
    ad_data_set = np.absolute(np.diff(data_set, axis=1))
    ad_data_set_med = ttc.median_filter_axis1(ad_data_set, half_window=half_window1)
    # ad_data_set_med = ttc.percentile_filter_axis1(ad_data_set, gf.CRR_percentile, half_window=half_window1)
    ad_data_set_max = ttc.max_filter_axis1(ad_data_set, half_window=half_window2)
    ad_data_set_SN = ad_data_set_max / ad_data_set_med
    return ad_data_set_SN > gf.CRR_SN    # shape(fnsub, fnpts - 1)

    # こちらを計算しなくても、ほとんど検出されたものが変わらない？
    # ad_data_set_SN_med = ttc.median_filter_axis1(ad_data_set_SN, half_window=half_window1)
    # return ad_data_set_SN - (ad_data_set_SN_med * SN) > 0





















