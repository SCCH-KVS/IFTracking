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


from libcpp.vector cimport vector

import numpy as np
cimport numpy as np


cdef extern from "linear_assignment_.hpp":

    vector[vector[int]] linearAssignment(const vector[vector[double]] &points1,
                                         const vector[vector[double]] &points2,
                                         double max_distance);


cpdef linear_assignment(np.ndarray[np.double_t, ndim=2] points1, np.ndarray[np.double_t, ndim=2] points2, double dist):
    return np.array(linearAssignment(points1, points2, dist))

