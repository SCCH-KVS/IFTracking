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

import os
import cv2

import sys
sys.path.append("../common")

import numpy as np
import matplotlib as mpl
mpl.use('TkAgg')

# Import individual functions and classes
from zip import unzip_csv, colors_from_csv
from config import Config
from input import get_latest_folder
from draw.legend import gen_legend, get_random_colors
from skimage.external.tifffile import imread, imsave


def main():

    # Initialize common configurations
    common_config = Config("../../config/common.config")

    # Get image sequence path and filename
    path = common_config["Image Sequence"]["Path"]
    filename = common_config["Image Sequence"]["Filename"]

    try:
        input_folder = sys.argv[1]
        make_legend = True
    except:
        # Get output folder
        output_folder = os.path.join("..", "..", "output", "tracking/", common_config["Output"]["Folder"])
        # Get latest folder
        latest_results = get_latest_folder(output_folder)
        # Make input folder
        input_folder = os.path.join(output_folder, latest_results)
        # Do not make legend
        make_legend = False

    print "Input folder:", input_folder

    # Read trajectories
    filenames = filter(lambda fn: fn.lower().endswith(".zip"), os.listdir(input_folder))
    labels = map(lambda fn: os.path.splitext(fn)[0], filenames)

    # Upload trajectories
    contours = {label : unzip_csv(os.path.join(input_folder, filename)) for filename, label in zip(filenames, labels)}
    contours_n = len(contours)

    # Read image sequence
    input_sequence = np.squeeze(imread(os.path.join(path, filename))).astype(np.float32)
    input_sequence /= input_sequence.max()

    frame_n = len(input_sequence)

    try:
        fns, colors = colors_from_csv(os.path.join(input_folder, "colors.csv"))
        color_map = {fn: clr for fn, clr in zip(fns, colors)}
    except:
        colors = get_random_colors(contours_n, "hsv")
        color_map = {fn: clr for fn, clr in zip(labels, colors)}

    rgb_stack = []
    filaments_mask = np.zeros_like(input_sequence[0], dtype=np.uint16)

    for frame_i in xrange(frame_n):
        sys.stdout.write("\r Frame: " + str(frame_i))
        image_rgb = np.dstack([input_sequence[frame_i]] * 3)
        for filament_i, filament_data in enumerate(contours.items()):
            tname, tcoords = filament_data
            try:
                fiber_color = color_map[tname]
            except:
                fiber_color = colors[fiber_color]
            cv2.polylines(image_rgb, [tcoords[frame_i].astype(np.int32)], False, fiber_color, 1, 8)
            cv2.polylines(filaments_mask[frame_i], [tcoords[frame_i].astype(np.int32)], False, filament_i + 1)

        rgb_stack.append((image_rgb * 255).astype(np.uint8))

    sys.stdout.write("\r Finished.\n")
    imsave(os.path.join(input_folder, "overlay.tif"), np.asarray(rgb_stack))
    imsave(os.path.join(input_folder, "index.tif"), filaments_mask)

    # Make legend
    if make_legend:
        labels = contours.keys()
        filament = [contour[0] for contour in contours.values()]

        legend = gen_legend(filament, labels, colors, input_sequence[0])
        # Save legend
        imsave(os.path.join(input_folder, "legend.tif"), (legend * 255).astype(np.uint8))


if __name__ == "__main__":
    main()

