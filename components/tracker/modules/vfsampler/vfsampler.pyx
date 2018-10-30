#
# Copyright (C) Software Competence Center Hagenberg GmbH (SCCH)
# All rights reserved.
#
# This document contains proprietary information belonging to SCCH.
# Passing on and copying of this document, use and communication of its
# contents is not permitted without prior written authorization.
#
# Created
# by: Dmytro Kotsur
#

import cython


# Declare the prototype of the C++ function we are interested in calling
cdef extern from "./VFSampler/sampler.h":
    void sample_vector_field_xy(double *gvf_x, double *gvf_y, int width, int height, double *points, int points_n, double *result);
    void sample_vector_field_ra(unsigned char *gvf_m, unsigned char *gvf_a, int width, int height, double *points, int point_n, double *result)


# Import the Python-level symbols of numpy
import numpy as np

# Import the C-level symbols of numpy
cimport numpy as np


@cython.boundscheck(False)
@cython.wraparound(False)
def sample_vf(np.ndarray[double, ndim=2, mode="c"] gvf_x not None,
              np.ndarray[double, ndim=2, mode="c"] gvf_y not None,
              np.ndarray[double, ndim=2, mode="c"] points not None):

    width, height = gvf_x.shape[1], gvf_x.shape[0]
    points_n = points.shape[0]

    cpdef np.ndarray[double, ndim=2, mode="c"] result = np.zeros_like(points)

    cdef double* points_ptr = <double*> points.data;
    cdef double* gvf_x_ptr = <double*> gvf_x.data;
    cdef double* gvf_y_ptr = <double*> gvf_y.data;
    #cdef double* result_ptr = <double*> result.data;

    # Call the C function
    sample_vector_field_xy(gvf_x_ptr, gvf_y_ptr, width, height, points_ptr, points_n, <double*> result.data)

    return result


@cython.boundscheck(False)
@cython.wraparound(False)
def decode_vf(np.ndarray[np.uint8_t, ndim=2, mode="c"] gvf_magnitude not None,
              np.ndarray[np.uint8_t, ndim=2, mode="c"] gvf_angle not None,
              np.ndarray[double, ndim=2, mode="c"] points not None):

    width, height = gvf_magnitude.shape[1], gvf_magnitude.shape[0]
    points_n = points.shape[0]

    cpdef np.ndarray[double, ndim=2, mode="c"] result = np.zeros_like(points)

    cdef double* points_ptr = <double*> points.data;
    cdef np.uint8_t* gvf_m_ptr = <np.uint8_t*> gvf_magnitude.data;
    cdef np.uint8_t* gvf_a_ptr = <np.uint8_t*> gvf_angle.data;

    # Call the C function
    sample_vector_field_ra(gvf_m_ptr, gvf_a_ptr, width, height, points_ptr, points_n, <double*>result.data)

    return result

