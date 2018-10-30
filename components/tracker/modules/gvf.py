#
# Copyright (C) Software Competence Center Hagenberg GmbH (SCCH)
# All rights reserved.
#
# This document contains proprietary information belonging to SCCH.
# Passing on and copying of this document, use and communication of its
# contents is not permitted without prior written authorization.
#
# Created by: Dmytro Kotsur
#

import numpy as np
from skimage.filters import sobel_h, sobel_v, sobel, gaussian, laplace


def gradient_vector_flow(f_x, f_y, mu=0.2, max_iter=10, keep_calm=True):
    # calculate parameters of flow
    dt = 0.5 / (4.0 * mu)
    r = mu * dt
    # make copy of data
    ux = np.copy(f_x)
    uy = np.copy(f_y)
    
    B = np.power(f_x, 2.0) + np.power(f_y, 2.0)
    C = B * f_x
    D = B * f_y
    
    # iterate flow    
    for it in xrange(max_iter):
        ux = (1.0 - B * dt) * ux - r * laplace(ux) + C * dt
        uy = (1.0 - B * dt) * uy - r * laplace(uy) + D * dt
        if it % 100 == 0 and not keep_calm:
            print "  [GVF] Iteration:", it
    if not keep_calm:
        print "  [GVF] Finished: {0} iterations".format(max_iter)
    return ux, uy


def compute_vector_field(image, mu=0.01, max_iter=20, quiet=True):
    f_x = sobel_v(-image)
    f_y = sobel_h(-image)
    return gradient_vector_flow(f_x, f_y, mu, max_iter, quiet)


def sample_gvf(gvf, points):
    p = points.astype(np.int)
    return np.hstack([gvf[0][p[:,1], p[:,0]].reshape(-1, 1), gvf[1][p[:,1], p[:,0]].reshape(-1, 1)])

