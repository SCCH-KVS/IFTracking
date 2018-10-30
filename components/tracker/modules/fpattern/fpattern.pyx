import cython

cdef extern from "fill_pattern_.h":

    void fillPatternFromCoords(long long *x, long long *y, int point_n,
                               double *pattern, int pattern_width, int pattern_height,
                               double *out_pattern, long long *out_mask, int width, int height);


import numpy as np
cimport numpy as np


@cython.boundscheck(False)
@cython.wraparound(False)
def fill_pattern_coords(np.ndarray[long long, ndim=1, mode="c"] x,
                        np.ndarray[long long, ndim=1, mode="c"] y,
                        np.ndarray[double, ndim=2, mode="c"] pattern,
                        int width, int height):

    point_n = x.shape[0]
    pattern_width = pattern.shape[1]
    pattern_height = pattern.shape[0]

    cpdef np.ndarray[double, ndim=2, mode="c"] out_pattern = np.zeros((height, width), dtype=np.double)
    cpdef np.ndarray[long long, ndim=2, mode="c"] out_mask = np.zeros((height, width), dtype='int64')

    cdef double *pattern_ptr = <double *> pattern.data;
    cdef long long *x_ptr = <long long *> x.data;
    cdef long long *y_ptr = <long long *> y.data;
    cdef long long *out_mask_ptr = <long long *> out_mask.data;
    cdef double *out_pattern_ptr = <double *> out_pattern.data;

    fillPatternFromCoords(x_ptr, y_ptr, point_n, pattern_ptr, pattern_width, pattern_height, out_pattern_ptr, out_mask_ptr, width, height);

    return out_pattern, out_mask