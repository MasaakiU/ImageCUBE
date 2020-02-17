# -*- Coding: utf-8 -*-

import numpy as np

from . import general_functions as gf
# from .cython import time_taking_calc as ttc




def PCA_based_NR(spc_file):
    if spc_file.fnsub < 2:
        return
    spc_set = spc_file.toNumPy_2dArray()
    N_components = spc_file.log_dict[b"noise_reduction_params"]["N_components"]
    X, mean_X, components = PCA(spc_set, N_components)
    noise_filtered_spc_set = np.real(np.dot(X, components.T)) + mean_X
    spc_file.fmNumPy_2dArray(noise_filtered_spc_set)
    return N_components

def PCA(X, N_components):
    # 平均を0にする
    mean_X = X.mean(axis=0)
    X = X - mean_X
    # 共分散行列を作る
    cov = np.cov(X, rowvar=False)
    # 固有値と固有ベクトルを求めて固有値の大きい順にソート
    l, v = np.linalg.eig(cov)
    l_index = np.argsort(l)[::-1]
    l = l[l_index]
    v = v[:,l_index] # 列ベクトルなのに注意
    # print(v.shape, X.shape)
    # components（固有ベクトル行列を途中まで取り出す）を作る
    components = v[:,:N_components]

    # データとcomponentsをかける
    return np.dot(X, components), mean_X, components













