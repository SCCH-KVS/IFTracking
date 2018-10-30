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
sys.path.append("../common")

import traceback
import numpy as np
import multiprocessing as mp

from modules.track import Tracker, TrackerParams
from modules.parametrize import uniform_contour_reparametrization as reparametrize
from ticker import Ticker
from zip import zip_csv
from utils import unpack_values, pack_shared_memory, to_image_sequence


Global_Parameters = None
Global_Sequence = None
Global_Lock = None

Output_Folder = ""


def track_individual(input):

    # Initialize global variables
    global Global_Sequence
    global Global_Parameters
    global Global_Lock
    global Output_Folder

    # Initialize ticker
    ticker = Ticker(Global_Lock)

    # Unpack data
    index, data = input
    filename, initial_polyline = data

    ticker.tick(" Started tracking {0}.".format(filename))

    # Reparametrize contour
    new_x, new_y, new_step = reparametrize(initial_polyline[:, 0], initial_polyline[:, 1],
                                           Global_Parameters.delta, 'linear')

    initial_points = np.dstack([new_x, new_y])[0]
    tracking_result = None

    try:
        # Create tracker
        tracker = Tracker(Global_Sequence, Global_Parameters)

        # Initialize log
        log = ""
        result = tracker.track(initial_points, log)

        ticker.tock("  Finished: " + filename)

        if result is not None:
            if Global_Lock is not None:
                Global_Lock.acquire()
            try:
                zip_path = os.path.join(Output_Folder, '{0}.zip'.format(filename))
                # Save ZIP
                zip_csv(zip_path, result["snake_trajectory"][:, -1])
            except:
                pass
            if Global_Lock is not None:
                Global_Lock.release()
    except Exception as e:
        print e
        traceback.print_exc()
        ticker.tock("  Failed: " + filename)

    return tracking_result


def init_process(*args):

    global Global_Sequence
    global Global_Parameters
    global Global_Lock
    global Output_Folder

    # Initialize globals
    Global_Parameters = args[0]
    Output_Folder = args[1]
    Global_Lock = args[2]

    unpacked_values = unpack_values(args[3:])
    Global_Sequence = to_image_sequence(unpacked_values)


def track_all(initial_positions, image_sequence, tracker_config, output_folder):

    # Retrieve tracker parameters
    params = TrackerParams()
    params.alpha = tracker_config.get("Evolution", "Alpha_f", 1.0)
    params.beta = tracker_config.get("Evolution", "Beta_f", 1.0)
    params.dt = tracker_config.get("Evolution", "Dt_f", 0.01)
    params.max_iter_n = tracker_config.get("Evolution", "Maximum_Iterations_i", 600)
    params.kernel_size = tracker_config.get("Evolution", "Kernel_Size_i", 11)
    params.kernel_sigma = tracker_config.get("Evolution", "Kernel_Sigma_f", 2.5)
    params.delta = tracker_config.get("Evolution", "Discretization_Step_f", 1.0)
    params.min_shift = tracker_config.get("Evolution", "Minimum_Shift_f", 1.0e-7)

    # Create lock
    manager = mp.Manager()
    locker = manager.Lock()

    if not tracker_config["Parallel Computing"]["Enabled_b"]:
        global Global_Sequence, Global_Parameters, Global_Lock, Output_Folder
        # Initialize global variables
        Global_Parameters = params
        Global_Lock = None
        Global_Sequence = to_image_sequence(image_sequence)
        Output_Folder = output_folder

        results = []
        for item in enumerate(initial_positions.items()):
            results.append(track_individual(item))
    else:
        # Get number of processors
        try:
            proc_num = tracker_config["Parallel Computing"]["Processors_Number_i"]
        except:
            proc_num = mp.cpu_count()

        # Initialize arguments list
        arguments = [params, output_folder, locker]
        arguments.extend(pack_shared_memory(image_sequence))

        # Create pool and start jobs
        pool = mp.Pool(proc_num, initializer=init_process, initargs=tuple(arguments))
        results = pool.map(track_individual, enumerate(initial_positions.items()))
        pool.close()

    return results