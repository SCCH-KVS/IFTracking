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
import shutil

# Add path for common library
sys.path.append("../common")
sys.path.append("../common/formats")

import numpy as np
import pandas as pd

# Import configurator
from config import Config
from ticker import Ticker
from readroi import read_roi
from input import get_latest_folder
from zip import unzip_trajectories
from coder import ParallelMap, ParallelApply
from datetime import datetime


from image import ImageSequence, transform_binary, transform_distance
from parallel import track_all
from skimage.exposure import rescale_intensity
from utils import to_shared_memory


def upload_sequence(path, processors_num=None, use_shared_memory=False):

    filenames = [
        'enhanced.tif',
        'skeletons.tif',
        'binaries.tif',
        'branching.tif', # check if we really need this one
        'gvf_magnitude.tif',
        'gvf_angle.tif',
        'branching_coords.zip'
    ]

    ticker = Ticker()

    ticker.tick("\nLoading image sequence...")
    image_sequence = ImageSequence.load(path, filenames)
    ticker.tock(" Finished.")

    return transform_images(image_sequence, processors_num, use_shared_memory)


def transform_images(image_sequence, processors_num=None, use_shared_memory=False):

    ticker = Ticker()

    image_sequence["enhanced"] = ('i', rescale_intensity(image_sequence["enhanced"][1].astype(np.double)))
    image_sequence["skeletons"] = ('i', (image_sequence["skeletons"][1] > 0).astype(np.uint8))

    ticker.tick("\nTransforming images...")
    transform = ParallelMap(processors_num)
    image_sequence["binaries"] = ('i', transform.map(transform_binary, image_sequence["binaries"][1]))
    image_sequence["branching"] = ('i', transform.map(transform_distance, image_sequence["branching"][1]))
    ticker.tock(" Finished.")

    if use_shared_memory:
        ticker.tick("\nMapping to shared memory...")
        image_sequence_shared = to_shared_memory(image_sequence)
        ticker.tock(" Finished.")
        # Return shared memory
        return image_sequence_shared

    return image_sequence


def upload_initialization(path):
    result = dict()
    if os.path.isdir(path):
        filenames = os.listdir(path)
        for filename in filenames:
            name, ext = os.path.splitext(filename)
            full_path = os.path.join(path, filename)
            try:
                if ext.lower() == '.roi':
                    with open(full_path, 'rb') as roi_fin:
                        result[name] = read_roi(roi_fin)[u'polygons'][:, :2]
                elif ext.lower() == '.csv':
                    result[name] = pd.read_csv(full_path, header=None).as_matrix()
            except Exception as e:
                print e.__doc__
                print e.message
                print ' Cannot load file:', full_path
    elif os.path.splitext(path)[1].lower() == '.zip':
        return unzip_trajectories(path)
    return result


def main():

    # Read configuration
    common_config = Config(os.path.join('..', '..', 'config', 'common.config'))

    # Read image preprocessing configuration
    tracker_config = Config(os.path.join('..', '..', 'config', 'tracker.config'))

    # Get output folder
    output_folder = common_config['Output']['Folder']

    # Use multiprocessing
    is_parallel = tracker_config['Parallel Computing']['Enabled_b']

    # Read preprocessed data
    image_sequence = upload_sequence(os.path.join('..', '..', 'output', 'preprocessing', output_folder),
                                     use_shared_memory=is_parallel)

    try:
        init_path = tracker_config['Initialization']['Path']
        if init_path == '':
            raise Exception("Empty Path")
    except:
        sequence_path = os.path.join('../../output/generator', output_folder)
        try:
            input_folder = get_latest_folder(sequence_path)
            init_path = os.path.join(sequence_path, input_folder, "filaments.zip")
        except:
            return

    ticker = Ticker()
    ticker.tick("\nReading initial filaments...")
    initialization = upload_initialization(init_path)
    ticker.tock(" Finished.")

    sequence_output = os.path.join("../../output/tracking", output_folder)
    try:
        os.mkdir(sequence_output)
    except:
        pass

    run_output = os.path.join(sequence_output, datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    try:
        os.mkdir(run_output)
    except:
        pass

    try:
        shutil.copy2(os.path.join(sequence_path, input_folder, 'colors.csv'), run_output)
    except:
        pass

    # Track all filaments
    ticker.tick("\nStarting tracking...")
    track_all(initialization, image_sequence, tracker_config, run_output)
    ticker.tock(" Tracking completed!")


if __name__ == "__main__":
    main()