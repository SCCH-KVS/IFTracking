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
import sys
import numpy as np

# Add path for common library
sys.path.append("../common")

# Import configurator
from config import Config

# Import image sequence
from image import ImageSequence

# Import stable branching detection
from modules.stable_points import detect_stable_points

from ticker import Ticker
from datetime import datetime
from input import tyx_to_tzcyx


def finallize(directory, image_sequence, config):
    # Import imsave
    from skimage.external.tifffile import imsave
    from zip import zip_csv

    ticker = Ticker()

    ticker.tick("\nSaving to the folder: " + directory)

    # Make folder
    try:
        os.mkdir(directory)
        ticker.tock(" Folder was created.")
    except:
        ticker.tock(" The folder with this name exists, it's content might be overwritten.")

    # Obtain skeleton images
    skeletons = np.asarray([d["skeleton"] for d in image_sequence.image_data])
    # Obtain enhanced images
    enhanced = np.asarray([d["enhanced_image"] for d in image_sequence.image_data])
    # Obtain binary images
    binaries = np.asarray([d["binary_image"] for d in image_sequence.image_data])
    # Branching images
    branching_images = np.asarray([d["branching_image"] for d in image_sequence.image_data])
    # Branching points coordinates
    branching_points = np.asarray([d["branching_coords"] for d in image_sequence.image_data])

    ticker.tick("\nCalculating stable branching points...")
    stable_branching, stable_coordinates = detect_stable_points(enhanced, branching_images, branching_points)
    ticker.tock(" Finished.")

    ticker.tick("\nStart coding gradient vector flow...")
    gvf_encoded = encode_gvf(image_sequence, processors_num=config["Parallel Computing"]["processors_number_i"])
    ticker.tock(" Finished.")

    # TIFF metadata
    meta = {'axes': 'TZCYX'}

    ticker.tick("\nSaving files...")
    # Save skeleton images
    imsave(os.path.join(directory, 'skeletons.tif'), tyx_to_tzcyx(skeletons), metadata=meta)
    # Save enhanced images
    imsave(os.path.join(directory, 'enhanced.tif'), tyx_to_tzcyx(enhanced), metadata=meta)
    # Save binary images
    imsave(os.path.join(directory, 'binaries.tif'), tyx_to_tzcyx(binaries), metadata=meta)
    # Save branching images
    imsave(os.path.join(directory, 'branching.tif'), tyx_to_tzcyx(branching_images), metadata=meta)
    # Save branching points
    zip_csv(os.path.join(directory, "branching_coords.zip"), np.asarray(branching_points))
    # Save GVF
    imsave(os.path.join(directory, 'gvf_magnitude.tif'), tyx_to_tzcyx(gvf_encoded[:, 0], np.uint8, 1), metadata=meta)

    imsave(os.path.join(directory, 'gvf_angle.tif'), tyx_to_tzcyx(gvf_encoded[:, 1], np.uint8, 1), metadata=meta)
    # Save stable branching points
    imsave(os.path.join(directory, 'stable_branching.tif'), tyx_to_tzcyx(stable_branching, np.uint16, 1), metadata=meta)
    zip_csv(os.path.join(directory, 'stable_coords.zip'), stable_coordinates)

    ticker.tock(" Finished.")

    print "\nProcessing completed:", str(datetime.now())


def encode_gvf(image_sequence, compute_error=False, processors_num=None):
    # Obrain GVF images
    from coder import ParallelVFCoder

    vf_coder = ParallelVFCoder(processors_num)
    gvf_data = np.asarray([data["gvf"] for data in image_sequence])
    gvf_encoded = np.asarray(vf_coder.encode(gvf_data, np.uint8))

    if compute_error:
        # decode back
        gvf_decoded = np.asarray(vf_coder.decode(gvf_encoded))
        # compute error
        error_val = np.abs(gvf_decoded - gvf_data).max()
        error_proc = error_val / gvf_data.max()
        # print error
        print " Encoding maximum error: {0} or {1}%.".format(error_val, error_proc)

    return gvf_encoded


def main():
    # Read configuration
    common_config = Config(os.path.join("..", "..", "config", "common.config"))

    # Read image preprocessing configuration
    preprocess_config = Config(os.path.join("..", "..", "config", "preprocess.config"))

    image_sequence_path = common_config["Image Sequence"]["Path"]
    image_sequence_name = common_config["Image Sequence"]["Filename"]

    # Read image sequence
    image_sequence = ImageSequence(os.path.join(image_sequence_path, image_sequence_name))
    image_sequence.apply(preprocess_config)

    # Save image sequence
    finallize(os.path.join("..", "..", "output", "preprocessing", common_config['Output']['Folder']),
              image_sequence, preprocess_config)


if __name__ == "__main__":
    main()
