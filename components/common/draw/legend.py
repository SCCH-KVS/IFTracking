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
import matplotlib as mpl
mpl.use('TkAgg')

from matplotlib.pyplot import get_cmap


def get_random_colors(n, colormap="hsv"):
    """
    Generate random colors with given colormap
    """
    cm = get_cmap(colormap)
    return np.asarray(cm(np.random.rand(n)))[:, :3]


def gen_legend(contours, labels, colors, background, offset=1):
    """
    Generate legend for contours
    """
    init_rgb = np.dstack([background] * 3)
    init_mask = np.zeros_like(background, dtype=np.bool)

    vis_images = [init_rgb.copy()]
    vis_masks = [init_mask.copy()]

    contours_n = len(contours)

    for contour_i in xrange(contours_n):

        contour_name, coordinates = labels[contour_i], contours[contour_i]
        fiber_color = np.array(colors[contour_i])[:3]

        col, row = tuple(coordinates.mean(axis=0).astype(np.int))

        txt_w, txt_h = cv2.getTextSize(contour_name, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]

        col_min, col_max = int(coordinates[..., 0].min()), int(coordinates[..., 0].max())
        row_min, row_max = int(coordinates[..., 1].min()), int(coordinates[..., 1].max())

        curr_mask = init_mask.copy()
        curr_mask[row - txt_h - offset:row + offset, col - offset:col + txt_w + offset] = True
        curr_mask[row_min - offset:row_max + offset, col_min - offset:col_max + offset] = True

        indices = np.arange(len(vis_masks))
        np.random.shuffle(indices)

        is_new_image = True
        for i in indices:
            if not np.logical_and(curr_mask, vis_masks[i]).any():
                is_new_image = False
                vis_masks[i] = np.logical_or(vis_masks[i], curr_mask)
                # draw
                cv2.polylines(vis_images[i], [coordinates.astype(np.int32)], False, fiber_color, 1, cv2.LINE_AA)
                cv2.putText(vis_images[i], contour_name, (col, row), cv2.FONT_HERSHEY_SIMPLEX, 0.4, fiber_color)
                break

        if is_new_image:
            rgb_image = init_rgb.copy()
            # draw
            cv2.polylines(rgb_image, [coordinates.astype(np.int32)], False, fiber_color, 1, 8)
            cv2.putText(rgb_image, contour_name, (col, row), cv2.FONT_HERSHEY_SIMPLEX, 0.4, fiber_color)
            # append to images stack
            vis_masks.append(curr_mask)
            vis_images.append(rgb_image)

    return np.array(vis_images)