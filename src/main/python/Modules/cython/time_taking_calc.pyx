# distutils: language=c++
# -*- coding: utf-8 -*-

# ビルド
# python setup.py build_ext --inplace

#from libcpp.vector cimport vector

cimport cython
import numpy as np
cimport numpy as np
DTYPEuint8 = np.uint8
DTYPEint64 = np.int64
DTYPEfloat64 = np.float64
ctypedef np.uint8_t DTYPEUint8_t
ctypedef np.int64_t DTYPEint64_t
ctypedef np.float64_t DTYPEfloat64_t

@cython.boundscheck(False) # turn off bounds-checking for entire function
@cython.wraparound(False)  # turn off negative index wrapping for entire function
@cython.nonecheck(False)
def median_filter_axis1(np.ndarray[DTYPEfloat64_t, ndim=2] data, int half_window, pbar, long[:] segment_list):
        assert data.dtype == DTYPEfloat64
        cdef np.ndarray[DTYPEfloat64_t, ndim=2] result_data = np.empty_like(data)
        cdef int idx
        cdef int window = 2 * half_window
        cdef int N_axis0 = data.shape[0]
        cdef int N_axis1 = data.shape[1]
        cdef int N_middle_loop = N_axis1 - window
        # window幅の前までは、その値までの medianを用いる
        for idx in range(half_window):
                # fm [:, 0] = [:, 0:11]
                # to [:, 9] = [:, 0:20]
                result_data[:, idx] = np.median(data[:, :idx+half_window+1], axis=1)
        # 真ん中らへん：べた書きの方が早い
        for idx in range(N_middle_loop):
                # fm [:, 10] = [:, 0:21]
                # to [:, N_axis1 - 11] = [:, N_axis1 - 21 : N_axis1]
                result_data[:, idx+half_window] = np.median(data[:, idx:idx+window+1], axis=1)
                if idx in segment_list:
                        pbar.setRealValue(idx)
#        # 真ん中らへん：遅かった
#        cdef np.ndarray[DTYPEfloat64_t, ndim=3] tmp_data = np.empty((window + 1, N_axis0, N_middle_loop))
#        for idx in range(window + 1):
#                tmp_data[idx] = data[:, idx:N_middle_loop + idx]
#        result_data[:, half_window:N_axis1 - half_window] = np.median(tmp_data, axis=0)
        # 最後らへん
        for idx in range(half_window):
                # fm [:, N_axis1 - 1]  = [:, N_axis1 - 11 : N_axis1]
                # to [:, N_axis1 - 10] = [:, N_axis1 - 20 : N_axis1]
                result_data[:, N_axis1-idx-1] = np.median(data[:, N_axis1-idx-half_window-1:], axis=1)
        return result_data

@cython.boundscheck(False) # turn off bounds-checking for entire function
@cython.wraparound(False)  # turn off negative index wrapping for entire function
def percentile_filter_axis1(np.ndarray[DTYPEfloat64_t, ndim=2] data, int percentile, int half_window):
        assert data.dtype == DTYPEfloat64
        cdef np.ndarray[DTYPEfloat64_t, ndim=2] result_data = np.empty_like(data)
        cdef int idx
        cdef int window = 2 * half_window
        cdef int N_axis0 = data.shape[0]
        cdef int N_axis1 = data.shape[1]
        cdef int N_middle_loop = N_axis1 - window
        # window幅の前までは、その値までの medianを用いる
        for idx in range(half_window):
                # fm [:, 0] = [:, 0:11]
                # to [:, 9] = [:, 0:20]
                result_data[:, idx] = np.percentile(data[:, :idx+half_window+1], percentile, axis=1)
        # 真ん中らへん：べた書きの方が早い
        for idx in range(N_middle_loop):
                # fm [:, 10] = [:, 0:21]
                # to [:, N_axis1 - 11] = [:, N_axis1 - 21 : N_axis1]
                result_data[:, idx+half_window] = np.percentile(data[:, idx:idx+window+1], percentile, axis=1)
#        # 真ん中らへん：遅かった
#        cdef np.ndarray[DTYPEfloat64_t, ndim=3] tmp_data = np.empty((window + 1, N_axis0, N_middle_loop))
#        for idx in range(window + 1):
#                tmp_data[idx] = data[:, idx:N_middle_loop + idx]
#        result_data[:, half_window:N_axis1 - half_window] = np.percentile(tmp_data, percentile, axis=0)
        # 最後らへん
        for idx in range(half_window):
                # fm [:, N_axis1 - 1]  = [:, N_axis1 - 11 : N_axis1]
                # to [:, N_axis1 - 10] = [:, N_axis1 - 20 : N_axis1]
                result_data[:, N_axis1-idx-1] = np.percentile(data[:, N_axis1-idx-half_window-1:], percentile, axis=1)
        return result_data


@cython.boundscheck(False) # turn off bounds-checking for entire function
@cython.wraparound(False)  # turn off negative index wrapping for entire function
def max_filter_axis1(np.ndarray[DTYPEfloat64_t, ndim=2] data, int half_window):
        assert data.dtype == DTYPEfloat64
        cdef np.ndarray[DTYPEfloat64_t, ndim=2] result_data = np.zeros_like(data)
        cdef int idx
        cdef int window = 2 * half_window
        cdef int N_axis0 = data.shape[0]
        cdef int N_axis1 = data.shape[1]
        cdef int N_middle_loop = N_axis1 - window
        # window幅の前までは、その値までの medianを用いる
        for idx in range(half_window):
                # fm [:, 0] = [:, 0:11]
                # to [:, 9] = [:, 0:20]
                result_data[:, idx] = np.max(data[:, :idx+half_window+1], axis=1)
        # 真ん中らへん：べた書きの方が早い
        for idx in range(N_middle_loop):
                # fm [:, 10] = [:, 0:21]
                # to [:, N_axis1 - 11] = [:, N_axis1 - 21 : N_axis1]
                result_data[:, idx+half_window] = np.max(data[:, idx:idx+window+1], axis=1)
        # 最後らへん
        for idx in range(half_window):
                # fm [:, N_axis1 - 1]  = [:, N_axis1 - 11 : N_axis1]
                # to [:, N_axis1 - 10] = [:, N_axis1 - 20 : N_axis1]
                result_data[:, N_axis1-idx-1] = np.max(data[:, N_axis1-idx-half_window-1:], axis=1)
        return result_data
        









