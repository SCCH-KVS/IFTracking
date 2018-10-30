#
# Copyright (C) Software Competence Center Hagenberg GmbH (SCCH)
# All rights reserved.
#
# This document contains proprietary information belonging to SCCH.
# Passing on and copying of this document, use and communication of its
# contents is not permitted without prior written authorization.
#
# Created by: Roman Yakobenchuk, Dmytro Kotsur
#

import os
import cv2
import sys
import numpy as np

# Add path for common library and src folder
sys.path.append("../common")
sys.path.append('src/')

# Import filament generator
import generator

# Import configurator
from config import Config
from zip import zip_csv, colors_to_csv
from draw.legend import gen_legend, get_random_colors

# Import datetime
from ticker import Ticker
from datetime import datetime

from skimage.external.tifffile import imread, imsave


# Global variables
__PLOT_OVERLAY__ = False


def plot_filaments(filaments, background, colors, title="", show_plots=False, **kwargs):
    """
    Plot filaments. Only for GUI version (Commented)
    """
    # import numpy as np
    # #import matplotlib.pyplot as plt
    #
    # plt.figure(title)
    # plt.title(title)
    # for filament_i, filament in enumerate(filaments):
    #     fiber_coords = np.asarray(filament)
    #     if colors is not None:
    #         color = colors[filament_i]
    #         plt.plot(fiber_coords[..., 0], fiber_coords[..., 1], '-', color=color, **kwargs)
    #     else:
    #         plt.plot(fiber_coords[..., 0], fiber_coords[..., 1], '-', **kwargs)
    # plt.imshow(background, cmap="gray", interpolation="nearest")
    # if show_plots:
    #     plt.show()
    pass


def save_filaments(filaments, output_path, background, colors):

    # Get filament number
    filaments_n = len(filaments)

    # Generate filament names
    filament_names = ["{0:05d}".format(f_id + 1) for f_id in xrange(filaments_n)]

    # Save colors
    colors_to_csv(os.path.join(output_path, "colors.csv"), filament_names, colors)

    # Save filaments as CSV files in ZIP archive
    zip_csv(os.path.join(output_path, "filaments.zip"), filaments)

    # Generate legend
    legend = gen_legend(filaments, filament_names, colors, background)
    imsave(os.path.join(output_path, "legend.tif"),  (legend * 255).astype(np.uint8))

    # Generate mask
    mask = np.zeros_like(background, dtype=np.uint16)
    color_mask = np.dstack([background] * 3)

    for filament_i, filament in enumerate(filaments):
        fiber_coords = np.asarray(filament)
        cv2.polylines(color_mask, [fiber_coords.astype(np.int32)], False, colors[filament_i], 1, 8)
        cv2.polylines(mask, [fiber_coords.astype(np.int32)], False, filament_i + 1)

    imsave(os.path.join(output_path, "overlay.tif"), (color_mask * 255).astype(np.uint8))
    imsave(os.path.join(output_path, "index.tif"), mask)


def main():

    ticker = Ticker()
    ticker.tick("Started filament generation...")

    input_dir = os.path.join("..", "..", "output", "preprocessing")
    output_dir = os.path.join("..", "..", "output", "generator")

    # Read configuration
    common_config = Config(os.path.join("..", "..", "config", "common.config"))

    # Read filaments generator configuration
    generator_config = Config(os.path.join("..", "..", "config", "generator.config"))

    folder_name = common_config["Output"]["Folder"]
    sequence_path = os.path.join(common_config["Image Sequence"]["Path"], common_config["Image Sequence"]["Filename"])

    # Generate filaments
    filaments_original, filaments_filtered = generator.generate(input_dir, folder_name, generator_config)

    directory = os.path.join(output_dir, folder_name)
    # Make folder
    try:
        os.mkdir(directory)
    except:
        pass

    # Output path
    current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_path = os.path.join(directory, "__".join([current_date, str(len(filaments_filtered))]))

    try:
        os.mkdir(output_path)
    except:
        pass

    # Get colors
    colors = get_random_colors(len(filaments_filtered))

    # Get background image
    image_sequence = imread(sequence_path)

    background = np.squeeze(image_sequence)[0].astype(np.float32)
    background /= background.max()

    # Save filaments
    save_filaments(filaments_filtered, output_path, background, colors)

    # Plot sequence
    if __PLOT_OVERLAY__:
        plot_filaments(filaments_original, background, None, "Original filaments")
        plot_filaments(filaments_filtered, background, colors, "Filtered filaments", True)

    ticker.tock(" Generation finished.")


if __name__ == "__main__":
    main()
