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

import cv2
import numpy as np

from skimage import filters
from fpattern.fpattern import fill_pattern_coords


def track_points(img_prev, img_curr, x, y, max_shift=10.0):

    lk_params = dict(winSize=(15, 15),
                     maxLevel=6,
                     criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 20, 0.01))

    points_num = len(x)
    points = np.zeros((points_num, 1, 2), dtype=np.float32)

    for i in xrange(points_num):
        points[i][0][0] = x[i]
        points[i][0][1] = y[i]

    img_prev_i = (img_prev * 255).astype(np.uint8)
    img_curr_i = (img_curr * 255).astype(np.uint8)

    print "RUN cv2.calcOpticalFlowPyrLK"
    updated, st, err = cv2.calcOpticalFlowPyrLK(img_prev_i, img_curr_i, points, None, **lk_params)
    print "FINISH cv2.calcOpticalFlowPyrLK"

    x_new = updated[:, :, 0].ravel()
    y_new = updated[:, :, 1].ravel()

    shifts = np.sqrt((x - x_new) ** 2 + (y - y_new) ** 2)

    mask = shifts > max_shift
    x_new[mask] = x[mask]
    y_new[mask] = y[mask]

    return x_new, y_new


def find_closest(query_point, point_set, th=10.0):
    dist = np.linalg.norm(point_set - query_point, axis=1)
    res_index = np.argmin(dist)
    if dist[res_index] < th:
        return res_index
    return -1


def track_branching_point(curr_index, curr_points, next_points):

    next_index = find_closest(curr_points[curr_index], next_points)
    if next_index >= 0:
        return next_index, next_points[next_index]
    else:
        return -1, np.array([0.0, 0.0])


def track_branching_points(image_i, branch_traj, branch_index, branching_coords):
    branch_index[image_i][0] = branch_index[image_i][1] = -1

    if image_i == 0:
        return

    ok0, ok1 = False, False
    idx0, idx1 = tuple(branch_index[image_i - 1])
    # print "track_branching_points:", idx0, idx1

    if idx0 >= 0:
        next_idx0, next_pos0 = track_branching_point(idx0, branching_coords[image_i - 1], branching_coords[image_i])
        branch_index[image_i][0] = next_idx0
        branch_traj[image_i][0] = next_pos0
        ok0 = True

    if idx1 >= 0:
        next_idx1, next_pos1 = track_branching_point(idx1, branching_coords[image_i - 1], branching_coords[image_i])
        branch_index[image_i][1] = next_idx1
        branch_traj[image_i][1] = next_pos1
        ok1 = True

    return ok0, ok1


def gen_potential(points, image_shape, kernel):
    """
    Generate vector field for give `points` of size `image_shape` using kernel function `kernel` as potential.
    """

    # Generate branching potential
    branching_potential, branching_mask = fill_pattern_coords(points[:, 0].astype(np.int64),
                                                              points[:, 1].astype(np.int64),
                                                              kernel, image_shape[1], image_shape[0])

    # Find attraction forces from potential
    f_br_x = filters.sobel_v(branching_potential)
    f_br_y = filters.sobel_h(branching_potential)

    return branching_potential, (f_br_x, f_br_y), branching_mask

