# -*- Coding: utf-8 -*-

import numpy as np
import re
import types

from . import popups
from . import general_functions as gf


class CustomNdarray(np.ndarray):
    """
    # テスト用サンプルコード
    def test(self):
        print("oneone")
    a = [1,2,3,4]
    arr = CustomNdarray(a)
    arr.test = types.MethodType(test, arr)
    arr.test()
    print(arr)
    print(arr.sum())
    """
    def __new__(cls, input_array):
        return np.asarray(input_array).view(cls)

    def __array_finalize__(self, obj) -> None:
        if obj is None: return
        # This attribute should be maintained!
        default_attributes = {"attr": 1}
        self.__dict__.update(default_attributes)  # another way to set attributes
class CustomList(list):
    """
    # テスト用サンプルコード
    # def test(self):
    #     print("oneone")
    # a = CustomList([1,2,3,4])
    # a.test = types.MethodType(test, a)
    # a.test()
    # print(a)
    """
    def __init__(self, arg_list):
        super().__init__(arg_list)
class ImgCbInfo():
    def __init__(self, f=None):
        self.header = f.readline().strip()
        self.sub_groups = SubGroup()
        self.func_dict = {}
        # read lines
        line = self.header
        cur_var_list = None
        cur_val_list = None
        self.f_length = 0
        while line:
            line = f.readline()
            self.f_length += len(line)
            if line.startswith("# "):
                self.set_val(cur_var_list, cur_val_list)
                cur_val_list = []
                cur_var_list = line[2:].strip().split()
                continue
            if line.strip() == "":  # 改行は無視
                continue
            cur_val_list.append(line)
        else:
            self.set_val(cur_var_list, cur_val_list)
    def set_val(self, cur_var_list, cur_val_list):
        if cur_var_list is None:
            return
        # 関数の場合
        if cur_var_list[-1].endswith(":"):
            exec("def {0}\n{1}".format("".join(cur_var_list), "".join(cur_val_list)), {}, self.func_dict)
            return
        else:
            cur_val_list = list(map(lambda x: x.strip().split(), cur_val_list))
        # 子オブジェクトの場合：改行無しで書くことが求められる
        if len(cur_var_list) == 1:
            if cur_var_list[0] in self.__dict__.keys():
                raise Exception("overlapped variable")
            if len(cur_val_list) > 1:
                raise Exception("syntax error: must be written in one line.")
            cur_var, val_list, is_str = self.process_val_list(cur_var_list[0], cur_val_list[0])
            is_str_list = [is_str]
            setattr(self, cur_var, val_list)
        # 孫オブジェクトの場合：改行ごとに属性が増えていく（まとまってサブグループとなる）
        elif len(cur_var_list) > 1:
            cur_var_list, zipped_val = self.zip_var_val_list(cur_var_list, cur_val_list)
            is_str_list = []
            for i, cur_var in enumerate(cur_var_list):
                cur_var, val_list, is_str = self.process_val_list(cur_var, zipped_val[i])
                is_str_list.append(is_str)
                setattr(self, cur_var, val_list)
        else:
            raise Exception("some error")
        self.sub_groups.add_subgroup(cur_var_list, is_str_list)
    def process_val_list(self, cur_var, val_list):
        matched1 = re.fullmatch("(.+)(\([0-9,]+\).*)", cur_var)
        # 文字列
        if val_list[0].startswith("'"):
            val_list = CustomList(map(lambda x: x.strip("'"), val_list))
            is_str = True
            # 多重リストの場合（ただし、長さが同じであるリストしか認めない）
            if matched1 is not None:
                cur_var = matched1[1]
                shape = eval(matched1[2])
                for d in shape[::-1][:-1]:
                    q, mod = divmod(len(val_list), d)
                    if mod != 0:
                        print(shape, len(val_list))
                        raise Exception("invaild list length")
                    val_list = [val_list[d*i:d*(i+1)] for i in range(q)]
        # 数値
        else:
            val_list = CustomNdarray(list(map(float, val_list)))
            is_str = False
            # 二次元以上の ndarray になる場合
            if matched1 is not None:
                cur_var = matched1[1]
                shape = eval(matched1[2])
                val_list = val_list.reshape(shape)
        # カスタム関数へのメソッド追加
        def subgroup(self_):
            return self.sub_groups.show_subgroup(cur_var)
        def head(self_):
            return cur_var
        def index_heads(self_):
            return self.sub_groups.show_index_heads(cur_var)
        def indexes(self_, key=None):
            if key is None:
                return [getattr(self, index_head) for index_head in self_.index_heads()]
            else:
                if key not in self_.index_heads():
                    raise Exception("no key")
                return getattr(self, key)
        val_list.subgroup = types.MethodType(subgroup, val_list)
        val_list.head = types.MethodType(head, val_list)
        val_list.index_heads = types.MethodType(index_heads, val_list)
        val_list.indexes = types.MethodType(indexes, val_list)
        return cur_var, val_list, is_str
    def zip_var_val_list(self, cur_var_list, cur_val_list):
        # var 処理
        var_N_list = []
        var_list = []
        N_None = 0
        for cur_var in cur_var_list:
            matched1 = re.fullmatch("(.+)\[([0-9]+)\]", cur_var)
            if matched1 is not None:
                var_list.append(matched1[1])
                var_N_list.append(matched1[2])
            else:
                var_list.append(cur_var)
                var_N_list.append(None)
                N_None += 1
        # 数合わせ
        if N_None > 1:
            var_N_list = [int(var_N) if var_N is not None else 1 for var_N in var_N_list]
            if sum(var_N_list) != len(cur_val_list[0]):
                raise Exception("error: unmatch length")
        elif N_None == 1:
            var_N_list[var_N_list.index(None)] = len(cur_val_list[0]) - sum([int(var_N) for var_N in var_N_list if var_N is not None])
            var_N_list = list(map(int, var_N_list))
        else:
            var_N_list = list(map(int, var_N_list))
        # val 処理
        zipped_val = [[] for i in var_N_list]
        for cur_val in cur_val_list:
            N = 0
            for var_idx, var_N in enumerate(var_N_list):
                zipped_val[var_idx].extend(cur_val[N:N+var_N])
                N += var_N
        return var_list, zipped_val
class SubGroup():
    def __init__(self):
        self.subgroup_set = []
        self.subgroup_str = []
    def add_subgroup(self, var_list, is_str_list):
        is_in = self.is_in_subgroup(var_list)
        if is_in is None:
            self.subgroup_set.append(var_list)
            self.subgroup_str.append(is_str_list)
        else:
            for var, is_str in zip(var_list, is_str_list):
                if var not in self.subgroup_set[is_in]:
                    self.subgroup_set[is_in].append(var)
                    self.subgroup_str[is_in].append(is_str)
    def is_in_subgroup(self, var_list):
        for var in var_list:
            for idx, subgroup in enumerate(self.subgroup_set):
                if var in subgroup:
                    # 既にある場合は、subgroup の index, 及び subgroup 中の index を返す
                    return idx
        else:
            return None
    def show_subgroup(self, var):
        for subgroup in self.subgroup_set:
            if var in subgroup:
                break
        else:
            return None
        return subgroup
    def show_index_heads(self, var):
        for idx, subgroup in enumerate(self.subgroup_set):
            if var in subgroup:
                break
        else:
            return None
        is_str_list = self.subgroup_str[idx]
        N_key = sum(is_str_list)
        if N_key == 0:
            return "no key"
        elif N_key > 0:
            return [subgroup[i] for i, is_str in enumerate(is_str_list) if is_str]

###
###
###

def open_cspc_file(file_path):
    with open(file_path, "r") as f:
        img_cb_info = ImgCbInfo(f)
    # 出力
    custom_spc = CustomSpc(img_cb_info)
    return custom_spc

# 
class CustomSpc(gf.SpcLike):
    def __init__(self, img_cb_info):
        super().__init__()
        for key, val in img_cb_info.__dict__.items():
            setattr(self, key, val)
        for func_name, func in self.func_dict.items():
            setattr(self, func_name, types.MethodType(func, self))
        self.set_x()
        self.init_data()
    def set_x(self):
        if "x" in self.__dict__.keys():
            self.set_x_by_xy()
        elif set("ffirst", "flast", "fnpts").issubset(set(self.__dict__.keys())):
            self.set_x_by_gxy()
        else:
            raise Exception("x values cannot be determined")
    def set_x_by_xy(self):
        self.dat_fmt = "x-y"   # one global x-data are given
        self.ffirst = self.x[0]
        self.flast = self.x[-1]
        self.fnpts = len(self.x)
    def set_x_by_gxy(self):
        self.dat_fmt = "gx-y"   # no x values are given, but they can be generated
        self.x = np.linspace(self.ffirst, self.flast, num=self.fnpts)
    def add_sub(self, y_data):
        sub_like = CustomSub()
        sub_like.add_data(y_list=y_data, sub_idx=self.fnsub)
        self.fnsub += 1
        self.sub.append(sub_like)
    def set_sub_data(self, sub_idx, y_data):
        self.sub[sub_idx].y = y_data
class CustomSub(gf.SubLike):
    def __init__(self):
        super().__init__()
        self.data_set = None
    def get_data(self, idx):
        return self.data_set[idx]




# import types
# class A():
#     def __init__(self):
#         pass
# def my_func(self, text):
#     print(text)

# a1 = A()
# a2 = A()
# a1.new_func = types.MethodType(my_func, a1)
# a1.new_func("test")











