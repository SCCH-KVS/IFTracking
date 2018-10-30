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
import cv2
import gvf

from vfsampler.vfsampler import sample_vf


def generate_matrix(N, alpha, beta, is_open=True):
    if is_open:
        A1 = 2.0 * np.eye(N, N) - np.eye(N, N, 1) - np.eye(N, N, -1)
        A1[0, 0] = A1[-1, -1] = 1.0

        A2 = -6.0 * np.eye(N, N) + 4.0 * (np.eye(N, N, 1) + np.eye(N, N, -1)) - (np.eye(N, N, 2) + np.eye(N, N, -2))
        A2[0, 0] = A2[-1, -1] = -1.0
        A2[1, 1] = A2[-2, -2] = -5.0
        A2[0, 1] = A2[1, 0] = A2[-1, -2] = A2[-2, -1] = 2.0
    else:
        A1 = 2.0 * np.eye(N, N) - np.roll(np.eye(N), 1, axis=0) - np.roll(np.eye(N), -1, axis=0)
        A2 = -6.0 * np.eye(N, N) + 4.0 * (np.roll(np.eye(N), 1, axis=0) + np.roll(np.eye(N), -1, axis=0)) - (
        np.roll(np.eye(N), 2, axis=0) + np.roll(np.eye(N), -2, axis=0))

    return -alpha * A1 + beta * A2


def bilinear_interp((v00, v01, v10, v11), x, y):
    return (v00 * (1 - x) + v01 * x) * (1 - y) + (v10 * (1 - x) + v11 * x) * y


def sample_sf(image, points, interp=True):
    """
    Sample scalar field (with bilinear interpolation)
    """
    rows, cols = image.shape
    points_int = points.astype(np.int)
    res = np.zeros((len(points), 1), dtype=image.dtype)
    for i, point_int in enumerate(points_int):
        xi, yi = tuple(point_int)
        if xi < 0 or yi < 0 or xi >= cols or yi >= rows:
            continue
        if not interp:
            res[i, 0] = image[yi, xi]
            continue
        # Bilinear interpolation
        if xi == cols - 1 and yi == rows - 1:
            vals = image[yi, xi], 0.0, 0.0, 0.0
        elif xi == cols - 1:
            vals = image[yi, xi], 0.0, image[yi + 1, xi], 0.0
        elif yi == rows - 1:
            vals = image[yi, xi], image[yi, xi + 1], 0.0, 0.0
        else:
            vals = image[yi, xi], image[yi, xi + 1], image[yi + 1, xi], image[yi + 1, xi + 1]
        # calculate residual
        residual_x, residual_y = tuple(points[i] - point_int)
        # interpolate
        res[i, 0] = bilinear_interp(vals, residual_x, residual_y)
    return res


def get_contour_length(points):
    return np.sum(np.linalg.norm(points[1:] - points[:-1], axis=1))


def constraint_forces(stretching_potential, vf_br0, vf_br1, snake_coords, b_mult=100.0):
    """
    @param stretching_potential is stretching potential
    @param (vf_br0, vf_br1) are vector field of branching potential (for each endpoint)
    @param snake_coords are coordinates of snake
    """
    # initialize constraint forces by zeros
    f = np.zeros_like(snake_coords)
    # find tangent verctors
    d0 = snake_coords[0] - snake_coords[1]
    d1 = snake_coords[-1] - snake_coords[-2]
    # normalize tangent vectors to unit vectors
    t0 = d0 / np.linalg.norm(d0)
    t1 = d1 / np.linalg.norm(d1)
    # get endpoints of the snake
    endpoints = snake_coords[[0, -1], :]
    # sample attraction forces from gradients
    branching_grad0 = sample_vf(vf_br0[0], vf_br0[1], endpoints[0].reshape(1, 2))
    branching_grad1 = sample_vf(vf_br1[0], vf_br1[1], endpoints[1].reshape(1, 2))
    # stretching forces
    stretching_vals = sample_sf(stretching_potential, endpoints)
    # set constraint forces at the endpoints
    f[0] = b_mult * branching_grad0 + stretching_vals[0, 0] * t0
    f[-1] = b_mult * branching_grad1 + stretching_vals[1, 0] * t1
    return f


def gen_gauss_kernel(sigma, size):
    """
    Generate gaussian kernel
    """
    gker1d = cv2.getGaussianKernel(size, sigma).reshape(-1,1)
    gker2d = gker1d.dot(gker1d.T)
    return (gker2d - gker2d.min()) / (gker2d.max() - gker2d.min())


def compute_gvf(image, omega=0.5, mu=1.0, max_iter=100):
    image_gvf = image

    gvf_ux, gvf_uy = gvf.compute_vector_field(image_gvf, mu=mu, max_iter=max_iter)
    gvf_m = np.sqrt(gvf_ux ** 2.0 + gvf_uy ** 2.0)

    gvf_m_th = 1.0e-100
    gvf_m[gvf_m < gvf_m_th] = gvf_m_th

    gvf_ux = omega * (gvf_ux / gvf_m) + (1.0 - omega) * gvf_ux / gvf_ux.max()
    gvf_uy = omega * (gvf_uy / gvf_m) + (1.0 - omega) * gvf_uy / gvf_uy.max()

    return gvf_ux, gvf_uy
