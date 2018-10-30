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

import cv2
import numpy as np
from skimage.measure import regionprops, label
from linassign import linassign


def track_points(img_prev, img_curr, x, y, max_shift=10.0):
    lk_params = dict(winSize=(21, 21),
                     maxLevel=10,
                     criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 20, 0.01))

    points_num = len(x)
    points = np.zeros((points_num, 1, 2), dtype=np.float32)

    for i in xrange(points_num):
        points[i][0][0] = x[i]
        points[i][0][1] = y[i]

    img_prev_i = (img_prev * 255).astype(np.uint8)
    img_curr_i = (img_curr * 255).astype(np.uint8)

    updated, st, err = cv2.calcOpticalFlowPyrLK(img_prev_i, img_curr_i, points, None, **lk_params)

    x_new = updated[:, :, 0].ravel()
    y_new = updated[:, :, 1].ravel()

    shifts = np.sqrt((x - x_new) ** 2 + (y - y_new) ** 2)

    mask = shifts > max_shift
    x_new[mask] = x[mask]
    y_new[mask] = y[mask]

    return x_new, y_new


def detect_stable_points(enhanced_images, branching_images, coordinates=None):

    # Get number of frames
    frame_n, image_rows, image_cols = enhanced_images.shape

    branching_regions = map(lambda image: regionprops(label(image)), branching_images)
    if coordinates is None:
        coordinates = map(lambda region: region.centroid[::-1], branching_regions)

    shifted_coordinates = [coordinates[0]]
    tracked_coordinates = [coordinates[0]]
    tracked_regions = [np.asarray(branching_regions[0])]
    back_tracking = []

    for frame_i in xrange(1, frame_n):
        # take previous positions
        prev_positions = tracked_coordinates[frame_i - 1]

        # track previous positions using optical flow
        new_x, new_y = track_points(enhanced_images[frame_i - 1], enhanced_images[frame_i], prev_positions[:, 0],
                                    prev_positions[:, 1])
        curr_positions = np.hstack([new_x.reshape(-1, 1), new_y.reshape(-1, 1)])

        shifted_coordinates.append(curr_positions)

        # assign tracked data with detected data at the current frame
        pairs = linassign.linear_assignment(curr_positions.astype(np.double), coordinates[frame_i].astype(np.double), 10.0)

        #
        back_tracking.append(pairs[:, 0])

        # track them back
        tracked_coordinates.append(coordinates[frame_i][pairs[:, 1]])
        tracked_regions.append(np.asarray(branching_regions[frame_i])[pairs[:, 1]])

    for frame_i in xrange(frame_n - 2, -1, -1):
        tracked_coordinates[frame_i] = tracked_coordinates[frame_i][back_tracking[frame_i]]
        tracked_regions[frame_i] = tracked_regions[frame_i][back_tracking[frame_i]]
        if frame_i > 0:
            back_tracking[frame_i - 1] = back_tracking[frame_i - 1][back_tracking[frame_i]]

    stable_coordinates = np.asarray(tracked_coordinates)
    stable_regions = np.asarray(tracked_regions)

    stable_branching = np.zeros((frame_n, image_rows, image_cols), dtype=np.int)

    for image_i in xrange(frame_n):
        for region_id, region in enumerate(stable_regions[image_i]):
            cx, cy = region.coords[:, 0], region.coords[:, 1]
            stable_branching[image_i][cx, cy] = region_id + 1

    return stable_branching, stable_coordinates
